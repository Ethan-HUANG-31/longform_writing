#!/usr/bin/env python3
"""Run V1 chapter-level revision loops for longform-writing.

The script has two layers:
1. deterministic helpers that unit tests can run without model calls;
2. model-backed revision orchestration used by long-running acceptance tasks.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_acceptance import load_dotenv, read_text, write_text  # noqa: E402


DEFAULT_CASES = [
    "05_medium_length_single_protagonist",
    "10_mystery_clue_fairness_smoke",
    "07_dual_timeline_continuity",
]


METHOD_ORDER = ["direct_write", "simple_engineered", "full_unrevised", "full_revised"]
SAMPLE_IDS = ["A", "B", "C", "D"]


def find_repetition_signals(text: str) -> list[dict[str, str]]:
    patterns = [
        "举到灯光下",
        "并排放在",
        "边缘对齐",
        "再次确认",
        "三张借书卡",
        "四张便签纸",
        "线索图",
    ]
    signals: list[dict[str, str]] = []
    for pattern in patterns:
        count = text.count(pattern)
        if count >= 2:
            signals.append({
                "dimension": "Scene & Prose Flow",
                "issue": f"Repeated phrase appears {count} times.",
                "evidence": pattern,
                "suggested_fix": "Compress repeated physical confirmation and replace with new pressure, conflict, or consequence.",
            })
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    seen: dict[str, int] = {}
    for paragraph in paragraphs:
        key = re.sub(r"\s+", "", paragraph)[:80]
        if len(key) < 20:
            continue
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            signals.append({
                "dimension": "Repetition",
                "issue": "Near-duplicate paragraph appears more than once.",
                "evidence": paragraph[:160],
                "suggested_fix": "Delete the duplicate and preserve only the version that advances the scene.",
            })
    return signals


def merge_revised_chapters(run_dir: Path) -> str:
    parts: list[str] = []
    manifest_rows: list[dict[str, str]] = []
    for chapter_dir in sorted((run_dir / "chapters").glob("chapter_*")):
        revised = chapter_dir / "02_revised_draft.md"
        original = chapter_dir / "02_draft.md"
        chosen = revised if revised.exists() and revised.read_text(encoding="utf-8").strip() else original
        if not chosen.exists():
            continue
        parts.append(chosen.read_text(encoding="utf-8").strip())
        manifest_rows.append({
            "chapter": chapter_dir.name,
            "source": str(chosen.relative_to(run_dir)),
            "mode": "revised" if chosen == revised else "original_fallback",
        })
    manuscript = "\n\n".join(parts).strip() + "\n"
    write_text(run_dir / "manuscript" / "final_revised.md", manuscript)
    manifest = "\n".join(json.dumps(row, ensure_ascii=False) for row in manifest_rows) + "\n"
    write_text(run_dir / "run_records" / "revision_manifest.jsonl", manifest)
    return manuscript


def build_blind_package(output_root: Path, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if output_root.exists():
        shutil.rmtree(output_root)
    public = output_root / "public"
    mapping: dict[str, Any] = {}
    for case_id, case in cases.items():
        case_public = public / case_id
        write_text(case_public / "request.md", "# Request\n\n" + case["request"].strip() + "\n")
        write_text(case_public / "case_name.txt", case["case_name"] + "\n")
        mapping[case_id] = {"case_name": case["case_name"], "samples": {}}
        methods = case["methods"]
        for sample_id, method in zip(SAMPLE_IDS, METHOD_ORDER):
            source = Path(methods[method])
            write_text(case_public / f"sample_{sample_id}.md", source.read_text(encoding="utf-8").strip() + "\n")
            mapping[case_id]["samples"][sample_id] = {
                "method": method,
                "source": str(source),
            }
    write_text(output_root / "private_mapping.json", json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    write_text(
        output_root / "README.md",
        "# V1 Blind Revision Evaluation Package\n\nGive evaluators only `public/` until judging is complete.\n",
    )
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", type=Path, default=ROOT / "longform-writing")
    parser.add_argument("--test-dir", type=Path, default=ROOT / "test_cases")
    parser.add_argument("--output-root", type=Path, default=ROOT / "revision_eval_runs" / "v1_chapter_revision")
    parser.add_argument("--provider", choices=["deepseek"], default="deepseek")
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    print("V1 runner helper layer is installed.")
    print(f"cases={','.join(args.cases)}")
    print(f"max_iterations={args.max_iterations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
