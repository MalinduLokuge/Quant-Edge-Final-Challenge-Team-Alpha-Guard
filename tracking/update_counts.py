"""Recount subtask progress from SUBTASKS.md and refresh the summary table in TASKS.md.

    python tracking/update_counts.py
"""
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
subtasks = (HERE / "SUBTASKS.md").read_text(encoding="utf-8")
tasks_md = HERE / "TASKS.md"

status = {}  # task -> Counter
for line in subtasks.splitlines():
    m = re.match(r"^\| (T\d+)\.\d+ \|", line)
    if m:
        cell = [c.strip() for c in line.strip("|").split("|")][6]
        key = "Blocked" if cell.startswith("Blocked") else cell
        status.setdefault(m.group(1), Counter())[key] += 1

out, total, in_summary = [], Counter(), True
for line in tasks_md.read_text(encoding="utf-8").splitlines():
    if line.startswith("## "):
        in_summary = False  # only the first table (above the first section heading) holds counts
    m = re.match(r"^\| (T\d+) \|", line)
    if in_summary and m and m.group(1) in status:
        cells = [c.strip() for c in line.strip("|").split("|")]
        c = status[m.group(1)]
        n = sum(c.values())
        total.update(c)
        total["n"] += n
        cells[6:11] = [str(n), str(c["Done"]), str(c["In progress"]), str(c["Blocked"]), f"{c['Done'] / n:.0%}"]
        line = "| " + " | ".join(cells) + " |"
    elif line.startswith("| | **Total**"):
        n = total["n"]
        line = (f"| | **Total** | | | | | **{n}** | **{total['Done']}** | **{total['In progress']}** | "
                f"**{total['Blocked']}** | **{total['Done'] / n:.0%}** |")
    out.append(line)
tasks_md.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"{total['n']} subtasks: {total['Done']} done, {total['In progress']} in progress, {total['Blocked']} blocked")
