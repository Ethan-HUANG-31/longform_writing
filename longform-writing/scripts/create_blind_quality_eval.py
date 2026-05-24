#!/usr/bin/env python3
"""Create blind sample packages for Phase D0.5 text-quality evaluation."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blind_quality_eval_runs" / "phase_d0_5"

CASES = {
    "case_05": {
        "name": "05_medium_length_single_protagonist",
        "test_case": "test_cases/05_medium_length_single_protagonist.md",
        "mapping": {
            "A": ("simple_engineered", "baseline_runs/simple_engineered/05_medium_length_single_protagonist/manuscript.md"),
            "B": ("full_skill", "runs/integrated_05_v2/manuscript/final.md"),
            "C": ("direct_write", "baseline_runs/direct_write/05_medium_length_single_protagonist/manuscript.md"),
        },
    },
    "case_07": {
        "name": "07_dual_timeline_continuity",
        "test_case": "test_cases/07_dual_timeline_continuity.md",
        "mapping": {
            "A": ("full_skill", "runs/integrated_07_v4/manuscript/final.md"),
            "B": ("direct_write", "baseline_runs/direct_write/07_dual_timeline_continuity/manuscript.md"),
            "C": ("simple_engineered", "baseline_runs/simple_engineered/07_dual_timeline_continuity/manuscript.md"),
        },
    },
    "case_10": {
        "name": "10_mystery_clue_fairness_smoke",
        "test_case": "test_cases/10_mystery_clue_fairness_smoke.md",
        "mapping": {
            "A": ("direct_write", "baseline_runs/direct_write/10_mystery_clue_fairness_smoke/manuscript.md"),
            "B": ("simple_engineered", "baseline_runs/simple_engineered/10_mystery_clue_fairness_smoke/manuscript.md"),
            "C": ("full_skill", "runs/integrated_10/manuscript/final.md"),
        },
    },
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def section(md: str, names: list[str]) -> str:
    for name in names:
        pattern = rf"^##\s+{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
        match = re.search(pattern, md, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return md.strip()


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    public = OUT / "public"
    private_mapping = {}
    for case_id, spec in CASES.items():
        case_dir = public / case_id
        test_md = read_text(ROOT / spec["test_case"])
        request = section(test_md, ["User Request", "Initial User Request", "Base Request"])
        write_text(
            case_dir / "request.md",
            f"# Request\n\n{request}\n\n# Evaluation Note\n\nJudge the samples as real longform fiction manuscripts. Do not infer or identify the writing method.\n",
        )
        write_text(case_dir / "case_name.txt", spec["name"] + "\n")
        private_mapping[case_id] = {"case_name": spec["name"], "samples": {}}
        for sample_id, (method, rel_path) in spec["mapping"].items():
            src = ROOT / rel_path
            write_text(case_dir / f"sample_{sample_id}.md", read_text(src).strip() + "\n")
            private_mapping[case_id]["samples"][sample_id] = {
                "method": method,
                "source": rel_path,
            }
    write_text(OUT / "private_mapping.json", json.dumps(private_mapping, ensure_ascii=False, indent=2) + "\n")
    write_text(
        OUT / "README.md",
        "# Phase D0.5 Blind Quality Evaluation Package\n\n"
        "Give evaluators only `public/`. Do not give them `private_mapping.json` until after judging is complete.\n",
    )
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
