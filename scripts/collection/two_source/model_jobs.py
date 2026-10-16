"""Bounded, resumable fixed-prompt API tasks; keys only come from the environment."""

import collections
import concurrent.futures
import json
import os
import threading
import time
import urllib.error
import urllib.request
from pipeline import ROOT, read, save, digest, now
from derived import annotation


def strict_json(text):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate_json_key:" + key)
            value[key] = item
        return value

    return json.loads(text, object_pairs_hook=pairs)


class Jobs:
    def __init__(self, folder, online=False):
        self.folder = folder
        self.config = read(ROOT / "data/two-source/model-jobs.json")
        assert self.config["endpoint"] == "https://api.deepseek.com/chat/completions"
        self.online = online
        self.key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.stop, self.lock = threading.Event(), threading.Lock()
        self.count = 0
        self.states, self.usage = {}, collections.Counter()

    def payload(self, prompt, task):
        return {
            "model": self.config["model"],
            **self.config["settings"],
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(task, ensure_ascii=False, sort_keys=True),
                },
            ],
        }

    def progress(self):
        with self.lock:
            save(
                self.folder / "progress.json",
                {
                    "updated_at": now(),
                    "requests_this_run": self.count,
                    "online": self.online,
                    "stopped": self.stop.is_set(),
                    "states": dict(collections.Counter(self.states.values())),
                    "tasks": dict(self.states),
                    "usage_this_run": dict(self.usage),
                },
            )

    def process(self, kind, task_id, prompt, task, validate):
        payload = self.payload(prompt, task)
        signature = digest(
            {
                "endpoint": self.config["endpoint"],
                "payload": payload,
                "retry": self.config["repair_instruction"],
                "attempts": self.config["attempts"],
            }
        )
        folder = self.folder / kind / signature
        target = folder / "accepted.json"
        state_key = kind + ":" + task_id
        if target.exists():
            accepted = read(target)
            assert accepted["task_sha256"] == signature and accepted[
                "request_sha256"
            ] == digest(read(folder / accepted["request_file"]))
            envelope = read(folder / accepted["response_file"])
            assert (
                envelope["http"] == 200
                and envelope["request_sha256"] == accepted["request_sha256"]
            )
            response = envelope["response"]
            assert accepted["response_sha256"] == digest(
                response
            ), "Saved model response changed"
            raw = response["choices"][0]["message"]["content"]
            parsed = strict_json(raw)
            validate(parsed)
            assert accepted["raw_response"] == raw and accepted["value"] == parsed
            with self.lock:
                self.states[state_key] = "cached"
            self.progress()
            return accepted
        if not self.online:
            with self.lock:
                self.states[state_key] = "not_executed"
            self.progress()
            return None
        assert self.key, "DEEPSEEK_API_KEY is required for --execute-ai"
        last_error = None
        # Accepted results are immutable. Retrying an unaccepted task preserves
        # all earlier attempts under monotonically increasing file numbers.
        offset = len(list(folder.glob("response-*.json")))
        for attempt in range(self.config["attempts"]):
            if self.stop.is_set():
                break
            index = offset + attempt
            request_path = folder / ("request-%06d.json" % index)
            response_path = folder / ("response-%06d.json" % index)
            current = json.loads(json.dumps(payload))
            if last_error:
                current["messages"].append(
                    {
                        "role": "user",
                        "content": self.config["repair_instruction"].format(
                            reason=last_error
                        ),
                    }
                )
            save(request_path, current)
            if response_path.exists():
                envelope = read(response_path)
                assert envelope["request_sha256"] == digest(
                    current
                ), "Saved request/response mismatch"
                status, response = envelope["http"], envelope["response"]
            else:
                with self.lock:
                    if self.count >= self.config["max_requests_per_run"]:
                        self.stop.set()
                        break
                    self.count += 1
                    self.states[state_key] = "running"
                self.progress()
                request = urllib.request.Request(
                    self.config["endpoint"],
                    data=json.dumps(current, ensure_ascii=False).encode("utf-8"),
                    headers={
                        "Authorization": "Bearer " + self.key,
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(
                        request, timeout=self.config["timeout_seconds"]
                    ) as handle:
                        status, body = handle.status, handle.read().decode("utf-8")
                    response = strict_json(body)
                except urllib.error.HTTPError as error:
                    status, response = error.code, {
                        "error_body": error.read()
                        .decode("utf-8", errors="replace")
                        .replace(self.key, "[redacted]")[:1500]
                    }
                except Exception as error:
                    status, response = 0, {
                        "error": str(error).replace(self.key, "[redacted]")[:500]
                    }
                envelope = {
                    "request_sha256": digest(current),
                    "received_at": now(),
                    "http": status,
                    "response": response,
                }
                save(response_path, envelope)
                with self.lock:
                    for key, count in response.get("usage", {}).items():
                        if isinstance(count, int):
                            self.usage[key] += count
            try:
                assert status == 200, "http_" + str(status)
                choice = response["choices"][0]
                assert choice["finish_reason"] == "stop", "incomplete_model_response"
                raw = choice["message"]["content"]
                value = strict_json(raw)
                validate(value)
                accepted = {
                    "task_sha256": signature,
                    "input_sha256": digest(task),
                    "model": self.config["model"],
                    "returned_model": response.get("model"),
                    "settings": self.config["settings"],
                    "prompt_sha256": digest(prompt.encode("utf-8")),
                    "request_sha256": digest(current),
                    "request_file": request_path.name,
                    "response_file": response_path.name,
                    "response_sha256": digest(response),
                    "raw_response": raw,
                    "value": value,
                }
                save(target, accepted)
                with self.lock:
                    self.states[state_key] = "ready"
                self.progress()
                return accepted
            except (AssertionError, ValueError, KeyError, TypeError) as error:
                last_error = str(error) or type(error).__name__
                save(
                    folder / ("rejected-%06d.json" % index),
                    {"reason": last_error, "task_id": task_id},
                )
                if status in (401, 402, 403):
                    self.stop.set()
                    break
                if status in (0, 429) or status >= 500:
                    time.sleep(min(10, 2**attempt))
        with self.lock:
            self.states[state_key] = "failed:" + str(last_error or "run_stopped")
        self.progress()
        return None


def run_keywords(output, jobs, limit=None):
    tasks = [
        json.loads(line)
        for line in (output / "05-keyword-pending.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    if limit:
        tasks = tasks[:limit]
    inputs = output.parents[1] / "inputs"
    vocabulary = read(inputs / "vocabulary.json")
    prompt_bytes = (inputs / "keywords.txt").read_bytes()
    prompt = (
        prompt_bytes.decode("utf-8")
        + "\nVocabulary:\n"
        + json.dumps(vocabulary, ensure_ascii=False, sort_keys=True)
    )
    allowed = {p["id"] for p in vocabulary["keywords"]}

    def process(task):
        supplied = {
            k: task[k] for k in ("paper_id", "title", "abstract", "input_sha256")
        }

        def validate(value):
            assert set(value) == {
                "paper_id",
                "input_sha256",
                "keyword_ids",
                "evidence",
            }, "unexpected_model_output_fields"
            assert (
                value["paper_id"] == task["paper_id"]
                and value["input_sha256"] == task["input_sha256"]
            ), "model_task_identity_mismatch"
            annotation(task, value, allowed)

        accepted = jobs.process(
            "keywords", task["paper_id"], prompt, supplied, validate
        )
        if not accepted:
            return None
        return {
            **accepted["value"],
            "vocabulary_sha256": digest(vocabulary),
            "prompt_sha256": digest(prompt_bytes),
            "model": accepted["model"],
            "returned_model": accepted["returned_model"],
            "settings": accepted["settings"],
            "raw_response": accepted["raw_response"],
            "response_sha256": digest(accepted["raw_response"]),
            "job_sha256": accepted["task_sha256"],
            "full_prompt_sha256": accepted["prompt_sha256"],
        }

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=jobs.config["workers"]
    ) as pool:
        rows = [r for r in pool.map(process, tasks) if r]
    path = output / "05-model-keyword-results.jsonl"
    path.write_bytes(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    )
    status = {
        "tasks": len(tasks),
        "completed": len(rows),
        "pending": len(tasks) - len(rows),
        "task_states": jobs.states,
    }
    save(output / "05-model-keyword-status.json", status)
    return path, status


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--execute-ai", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    output = ROOT / args.output
    jobs = Jobs(output.parents[1] / "ai", args.execute_ai)
    path, status = run_keywords(output, jobs, args.limit)
    print(
        json.dumps(
            {
                "output": str(path.relative_to(ROOT)),
                "tasks": status["tasks"],
                "completed": status["completed"],
                "pending": status["pending"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
