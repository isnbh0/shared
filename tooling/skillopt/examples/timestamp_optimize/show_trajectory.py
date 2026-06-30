"""Print a run's optimization trajectory from its checkpoint.json.

Groups the frozen-val score cache by skill-doc hash so the score climb across
the initial skill and each gated candidate is visible at a glance. Reads the run
directory from ``$OUT_DIR``.
"""
import json
import os

ckpt = json.load(open(os.path.join(os.environ["OUT_DIR"], "checkpoint.json")))
print(f"best_score = {ckpt.get('best_score')}   "
      f"epoch = {ckpt.get('epoch')}   step = {ckpt.get('step')}   "
      f"sigma_gate = {ckpt.get('sigma_gate')}")

by_hash: dict[str, list] = {}
for key, v in ckpt.get("cache", {}).items():
    parts = key.split("|")
    by_hash.setdefault(parts[0], []).append((parts[1] if len(parts) > 1 else key, v))

for h, rows in by_hash.items():
    rows.sort()
    mean_hard = sum(v.get("hard", 0) for _, v in rows) / max(1, len(rows))
    print(f"  skill-doc {h}:  mean_hard={mean_hard:.3f}")
    for task, v in rows:
        print(f"      {task}: hard={v.get('hard')} soft={v.get('soft')}")
