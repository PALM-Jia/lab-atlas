"""Resumable, per-paper DeepSeek annotation runner. No production writes."""

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import os
from pathlib import Path
import random
import re
import tempfile
import threading
import time
import urllib.error
import urllib.request

import validate

ENDPOINT = "https://api.deepseek.com/chat/completions"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        # Windows denies replacement while the progress page briefly reads it.
        # Retry publication without reissuing a completed model request.
        for publication_attempt in range(100):
            try:
                os.replace(name, str(path))
                break
            except PermissionError:
                if publication_attempt == 99:
                    raise
                time.sleep(0.05)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    return json.loads(
        text,
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("invalid number")),
    )


def redact(value, key):
    text = str(value)
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"(?i)(bearer\s+|sk-)[A-Za-z0-9_.-]+", "[REDACTED]", text)


def retry_after(value):
    try:
        return max(0.0, float(value))
    except (ValueError, TypeError):
        try:
            return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
        except (ValueError, TypeError, OverflowError):
            return 0.0


class Runner:
    def __init__(self, args, transport=None):
        self.args = args
        self.root = args.root.resolve()
        self.key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.transport = transport or self.request
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.stop_reason = None
        self.cooldown_until = 0.0
        self.limit = args.concurrency
        self.spent = 0.0
        self.reserved = 0.0
        self.unknown_cost_reserve = 0.0
        self.tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 0,
        }
        self.attempt_count = 0
        self.completed = 0
        self.states = {}
        self.details = {}
        self.papers = {}
        self.session_id = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            + "-"
            + str(os.getpid())
        )

    def freeze(self):
        errors = validate.check_fingerprints(self.root)["errors"]
        if errors:
            self.halt("input_freeze_changed")
            raise ValueError("; ".join(errors))

    def halt(self, reason):
        with self.lock:
            if not self.stop_reason:
                self.stop_reason = reason
            self.stop.set()

    def load(self):
        self.freeze()
        self.schema = validate.read_json(self.root / "output.schema.json")
        self.vocabulary = validate.read_json(self.root / "vocabulary.json")
        self.keywords = {k["id"]: k for k in self.vocabulary["keywords"]}
        self.instructions = (self.root / "annotation-instructions.txt").read_text(
            encoding="utf-8-sig"
        )
        for path in sorted((self.root / "inputs").glob("batch-*.json")):
            for paper in validate.read_json(path)["papers"]:
                pid = paper["paper_id"]
                if not re.fullmatch(r"[A-Za-z0-9_-]+", pid) or pid in self.papers:
                    raise ValueError("unsafe or duplicate paper_id")
                if not isinstance(paper.get("title"), str) or not (
                    paper.get("abstract") is None
                    or isinstance(paper.get("abstract"), str)
                ):
                    raise ValueError("invalid paper input: " + pid)
                self.papers[pid] = paper
                dest = self.root / "results" / (pid + ".json")
                state, errors = "missing", []
                if dest.exists():
                    try:
                        record = validate.read_json(dest)
                        errors = self.record_errors(record, paper)
                        state = (
                            "invalid"
                            if errors
                            else (
                                "flag_for_review" if record["input_issues"] else "done"
                            )
                        )
                    except (ValueError, TypeError, KeyError, OSError) as exc:
                        state, errors = "invalid", [str(exc)]
                self.states[pid] = state
                self.details[pid] = {
                    "errors": errors,
                    "skipped_existing_valid": state in ("done", "flag_for_review"),
                }

    def record_errors(self, record, paper):
        errors = validate.validate_record(record, paper, self.keywords, self.schema)
        if not isinstance(record, dict) or record.get("paper_id") != paper["paper_id"]:
            errors.append("paper_id mismatch")
        return errors

    def payload(self, paper):
        return {
            "model": "deepseek-flash",
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
            "max_tokens": 32768,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": self.instructions
                    + "\n\n固定词表：\n"
                    + json.dumps(self.vocabulary, ensure_ascii=False)
                    + "\n\n输出Schema：\n"
                    + json.dumps(self.schema, ensure_ascii=False)
                    + "\n只分析user消息中这一篇。只返回一个符合Schema的JSON对象。",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {k: paper[k] for k in ("paper_id", "title", "abstract")},
                        ensure_ascii=False,
                    ),
                },
            ],
        }

    def request(self, payload):
        request = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.args.timeout) as response:
                return (
                    response.status,
                    dict(response.headers),
                    response.read().decode("utf-8"),
                )
        except urllib.error.HTTPError as exc:
            return (
                exc.code,
                dict(exc.headers),
                exc.read().decode("utf-8", errors="replace"),
            )

    def reserve_cost(self, payload):
        # UTF-8 byte count bounds ordinary byte-token encodings; overhead margin
        # also covers role/template tokens. Reserve full output including reasoning.
        prompt_bound = (
            sum(len(m["content"].encode("utf-8")) for m in payload["messages"]) + 4096
        )
        if self.args.max_cost_usd is None:
            return 0.0
        return (
            prompt_bound
            * max(
                self.args.input_miss_usd_per_million,
                self.args.input_hit_usd_per_million,
            )
            + payload["max_tokens"] * self.args.output_usd_per_million
        ) / 1000000

    def account(self, usage, reservation):
        with self.lock:
            self.reserved -= reservation
            if (
                not isinstance(usage, dict)
                or "prompt_tokens" not in usage
                or "completion_tokens" not in usage
                or any(
                    type(usage.get(k, 0)) is not int or usage.get(k, 0) < 0
                    for k in self.tokens
                )
            ):
                self.unknown_cost_reserve += reservation
                return
            for key in self.tokens:
                self.tokens[key] += int(usage.get(key, 0))
            if self.args.input_miss_usd_per_million is not None:
                hit = int(usage.get("prompt_cache_hit_tokens", 0))
                miss = int(
                    usage.get(
                        "prompt_cache_miss_tokens", int(usage["prompt_tokens"]) - hit
                    )
                )
                self.spent += (
                    hit * self.args.input_hit_usd_per_million
                    + miss * self.args.input_miss_usd_per_million
                    + int(usage["completion_tokens"]) * self.args.output_usd_per_million
                ) / 1000000
                if self.args.max_cost_usd is not None and (
                    self.spent + self.reserved + self.unknown_cost_reserve
                    > self.args.max_cost_usd
                ):
                    self.halt("budget_limit")

    def snapshot(self):
        with self.lock:
            groups = {
                s: sorted(pid for pid, state in self.states.items() if state == s)
                for s in ("done", "invalid", "missing", "flag_for_review")
            }
            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                "model": "deepseek-flash",
                "semantic_review_performed": False,
                "stop_reason": self.stop_reason,
                "counts": {s: len(ids) for s, ids in groups.items()},
                "paper_ids": groups,
                "completed_this_run": self.completed,
                "attempts_this_run": self.attempt_count,
                "active_concurrency_limit": self.limit,
                "usage_this_run": dict(self.tokens),
                "details": dict(self.details),
                "cost_usd_this_run": (
                    self.spent
                    if self.args.input_miss_usd_per_million is not None
                    else None
                ),
                "max_cost_usd": self.args.max_cost_usd,
                "in_flight_cost_reserve_usd": self.reserved,
                "unknown_cost_reserve_usd": self.unknown_cost_reserve,
                "cost_note": "Token-based estimate using explicit CLI prices; unknown usage retains full reservation.",
            }
            atomic_json(self.root / "control" / "progress.json", report)
            return report

    def process(self, paper):
        pid = paper["paper_id"]
        payload = self.payload(paper)
        dest = self.root / "results" / (pid + ".json")
        attempt_dir = self.root / "attempts" / pid
        for attempt in range(1, self.args.retries + 2):
            if self.stop.is_set():
                return
            while time.monotonic() < self.cooldown_until:
                if self.stop.wait(
                    min(1.0, max(0.0, self.cooldown_until - time.monotonic()))
                ):
                    return
            try:
                self.freeze()
                if dest.exists():
                    try:
                        current = validate.read_json(dest)
                        if not self.record_errors(current, paper):
                            with self.lock:
                                self.states[pid] = (
                                    "flag_for_review"
                                    if current["input_issues"]
                                    else "done"
                                )
                            self.snapshot()
                            return
                    except (ValueError, TypeError, KeyError):
                        pass
                    # Preserve invalid existing output before any replacement.
                    atomic_json(
                        attempt_dir / (self.session_id + ".existing.result.json"),
                        {"content": dest.read_text(encoding="utf-8-sig")},
                    )
            except (ValueError, OSError) as exc:
                with self.lock:
                    self.details[pid]["errors"] = [redact(exc, self.key)]
                self.snapshot()
                return
            reservation = self.reserve_cost(payload)
            with self.lock:
                if self.stop.is_set():
                    return
                if self.args.max_cost_usd is not None and (
                    self.spent + self.reserved + self.unknown_cost_reserve + reservation
                    > self.args.max_cost_usd
                ):
                    self.halt("budget_limit")
                    return
                self.reserved += reservation
                self.attempt_count += 1
            started = time.monotonic()
            status, headers, body, usage = None, {}, None, None
            raw, errors, record, finish = None, [], None, None
            metadata = {
                "paper_id": pid,
                "attempt": attempt,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                status, headers, body = self.transport(payload)
                if status == 200:
                    response = strict_json(body)
                    usage = response.get("usage")
                    choice = response["choices"][0]
                    finish = choice.get("finish_reason")
                    raw = choice["message"].get("content")
                    metadata.update(
                        {
                            "id": response.get("id"),
                            "model": response.get("model"),
                            "usage": usage,
                            "finish_reason": finish,
                        }
                    )
                    if finish != "stop":
                        errors.append("non-stop finish_reason: " + str(finish))
                    if not isinstance(raw, str):
                        errors.append("missing string message.content")
                    else:
                        try:
                            record = strict_json(raw)
                            errors.extend(self.record_errors(record, paper))
                        except (ValueError, TypeError, KeyError) as exc:
                            errors.append(str(exc))
                else:
                    errors.append(
                        "HTTP " + str(status) + ": " + redact(body, self.key)[:2000]
                    )
                    if status in (401, 402):
                        self.halt(
                            "authentication_failed"
                            if status == 401
                            else "insufficient_balance"
                        )
                    if status == 429:
                        with self.lock:
                            self.limit = max(1, self.limit // 2)
                            delay = max(
                                retry_after(
                                    headers.get("Retry-After")
                                    or headers.get("retry-after")
                                ),
                                min(60.0, 2**attempt + random.random()),
                            )
                            self.cooldown_until = max(
                                self.cooldown_until, time.monotonic() + delay
                            )
            except Exception as exc:
                errors.append(redact(exc, self.key)[:2000])
            finally:
                self.account(usage, reservation)
            metadata.update(
                {
                    "status": status,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "errors": [redact(e, self.key) for e in errors],
                    "valid": not errors,
                }
            )
            name = self.session_id + "." + str(attempt)
            # Never persist the complete API envelope or reasoning_content.
            atomic_json(attempt_dir / (name + ".response.json"), {"content": raw})
            atomic_json(attempt_dir / (name + ".metadata.json"), metadata)
            if not errors:
                try:
                    self.freeze()
                    # Another writer may have produced a valid record while this
                    # request ran. Preserve that result rather than relabel it.
                    if dest.exists():
                        try:
                            existing = validate.read_json(dest)
                            if not self.record_errors(existing, paper):
                                record = existing
                        except (ValueError, TypeError, KeyError):
                            pass
                    atomic_json(dest, record)
                    with self.lock:
                        self.states[pid] = (
                            "flag_for_review" if record["input_issues"] else "done"
                        )
                        self.details[pid] = {
                            "errors": [],
                            "attempt": attempt,
                            "skipped_existing_valid": False,
                        }
                    self.snapshot()
                    return
                except (ValueError, OSError) as exc:
                    errors.append(redact(exc, self.key))
            with self.lock:
                if status == 200:
                    self.states[pid] = "invalid"
                self.details[pid]["errors"] = [redact(e, self.key) for e in errors]
                self.details[pid]["attempt"] = attempt
            self.snapshot()
            if self.stop.is_set() or (
                status is not None
                and status not in (200, 408, 409, 429)
                and status < 500
            ):
                return
            if attempt <= self.args.retries:
                self.stop.wait(min(30.0, 2**attempt + random.random()))

    def run(self):
        self.load()
        self.snapshot()
        if self.args.dry_run:
            return self.snapshot()
        if not self.key:
            self.halt("missing_api_key")
            return self.snapshot()
        queue = iter(
            p
            for pid, p in self.papers.items()
            if self.states[pid] in ("missing", "invalid")
        )
        active, exhausted = {}, False
        with ThreadPoolExecutor(max_workers=self.args.concurrency) as pool:
            while active or (not exhausted and not self.stop.is_set()):
                while (
                    not exhausted
                    and not self.stop.is_set()
                    and len(active) < self.limit
                ):
                    try:
                        paper = next(queue)
                    except StopIteration:
                        exhausted = True
                        break
                    active[pool.submit(self.process, paper)] = paper["paper_id"]
                if not active:
                    break
                done, _ = wait(active, timeout=1, return_when=FIRST_COMPLETED)
                for future in done:
                    pid = active.pop(future)
                    try:
                        future.result()
                    except Exception as exc:
                        with self.lock:
                            self.details[pid]["errors"] = [redact(exc, self.key)]
                    self.completed += 1
                    self.snapshot()
                    if self.completed % 20 == 0:
                        print(
                            json.dumps(
                                {
                                    s: list(self.states.values()).count(s)
                                    for s in (
                                        "done",
                                        "invalid",
                                        "missing",
                                        "flag_for_review",
                                    )
                                }
                            ),
                            flush=True,
                        )
        report = self.snapshot()
        atomic_json(self.root / "control" / "deepseek-run-report.json", report)
        return report


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work" / "keyword-full",
    )
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Technical retries after first attempt (0..2)",
    )
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--input-hit-usd-per-million", type=float)
    parser.add_argument("--input-miss-usd-per-million", type=float)
    parser.add_argument("--output-usd-per-million", type=float)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify frozen inputs and existing results without network",
    )
    args = parser.parse_args(argv)
    prices = [
        args.input_hit_usd_per_million,
        args.input_miss_usd_per_million,
        args.output_usd_per_million,
    ]
    if (
        not 1 <= args.concurrency <= 100
        or not 0 <= args.retries <= 2
        or not math.isfinite(args.timeout)
        or args.timeout <= 0
    ):
        parser.error("concurrency must be 1..100, retries 0..2, timeout positive")
    if any(x is not None for x in prices) and not all(
        x is not None and math.isfinite(x) and x >= 0 for x in prices
    ):
        parser.error("provide all three nonnegative official USD prices or none")
    if args.max_cost_usd is not None and (
        not math.isfinite(args.max_cost_usd)
        or args.max_cost_usd <= 0
        or any(x is None for x in prices)
    ):
        parser.error(
            "positive --max-cost-usd requires all three explicit official USD prices"
        )
    return args


if __name__ == "__main__":
    args = arguments()
    try:
        result = Runner(args).run()
        print(
            json.dumps(
                {
                    "counts": result["counts"],
                    "stop_reason": result["stop_reason"],
                    "usage_this_run": result["usage_this_run"],
                    "cost_usd_this_run": result["cost_usd_this_run"],
                }
            ),
            flush=True,
        )
        raise SystemExit(
            1
            if result["stop_reason"]
            or result["counts"]["missing"]
            or result["counts"]["invalid"]
            else 0
        )
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(
            json.dumps({"error": redact(exc, os.environ.get("DEEPSEEK_API_KEY", ""))}),
            flush=True,
        )
        raise SystemExit(1)
