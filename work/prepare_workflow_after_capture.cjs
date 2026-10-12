const fs=require('node:fs');let s=fs.readFileSync('work/capture_workflow_audit.cjs','utf8').replaceAll('-before.png','-after.png');fs.writeFileSync('work/capture_workflow_audit_after.cjs',s);
