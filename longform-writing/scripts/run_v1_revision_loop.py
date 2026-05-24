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

from run_acceptance import AcceptanceRun, load_dotenv, parse_test_case, read_text, write_text  # noqa: E402


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
            raise FileNotFoundError(
                f"{chapter_dir} has no source draft: expected 02_revised_draft.md or 02_draft.md"
            )
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


def clean_blind_output_root(output_root: Path) -> None:
    resolved_root = output_root.expanduser().resolve()
    dangerous_roots = {Path(resolved_root.anchor), Path.home().resolve(), ROOT.resolve()}
    if resolved_root in dangerous_roots:
        raise ValueError(f"Refusing to clean dangerous blind output root: {resolved_root}")

    for child_name in ("public", "private_mapping.json", "README.md"):
        child = resolved_root / child_name
        if child.is_dir():
            shutil.rmtree(child)
        elif child.exists():
            child.unlink()


def build_blind_package(output_root: Path, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    clean_blind_output_root(output_root)
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


def collect_previous_summaries(run_dir: Path, chapter_id: int) -> str:
    chunks: list[str] = []
    for cid in range(1, chapter_id):
        chapter_dir = run_dir / "chapters" / f"chapter_{cid:02d}"
        revised = chapter_dir / "03_summary_after_revised.md"
        original = chapter_dir / "03_summary_after.md"
        chosen = revised if revised.exists() and revised.read_text(encoding="utf-8").strip() else original
        if chosen.exists():
            chunks.append(f"Chapter {cid} summary:\n{chosen.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(chunks)


def builtin_chapter_review(chapter_id: int, chapter_text: str) -> dict[str, Any]:
    issues = find_repetition_signals(chapter_text)
    checklist_markers = ["**一、", "**二、", "**三、", "一、旧", "二、日期", "三、书号"]
    if any(marker in chapter_text for marker in checklist_markers):
        issues.append({
            "dimension": "Scene & Prose Flow",
            "location": f"chapter_{chapter_id:02d}",
            "issue": "Deduction is presented as an explicit checklist.",
            "evidence": " / ".join(marker for marker in checklist_markers if marker in chapter_text),
            "suggested_fix": "Rewrite the deduction as scene movement, dialogue pressure, or incremental discovery.",
        })
    return {
        "rubric_version": "longform_text_quality_rubric_v1",
        "chapter_id": chapter_id,
        "overall_score": 3.0 if issues else 4.0,
        "revision_required": bool(issues),
        "strengths_to_preserve": [],
        "blocking_issues": issues,
        "continuity_risks": [],
        "revision_targets": [issue["suggested_fix"] for issue in issues],
    }


class V1RevisionRun:
    def __init__(
        self,
        skill_path: Path,
        test_case_path: Path,
        run_dir: Path,
        provider: str,
        iteration_id: int,
    ) -> None:
        self.skill_path = skill_path.resolve()
        self.test_case_path = test_case_path.resolve()
        self.test_case = parse_test_case(self.test_case_path)
        self.run_dir = run_dir.resolve()
        self.provider = provider
        self.iteration_id = iteration_id
        self.acceptance = AcceptanceRun(
            self.skill_path,
            self.test_case,
            self.run_dir,
            provider,
            "full_auto",
            4,
            260,
        )

    def template(self, filename: str) -> str:
        return read_text(self.skill_path / "core_spec" / "prompts" / filename)

    def ensure_unrevised_draft(self) -> None:
        if (self.run_dir / "manuscript" / "final.md").exists():
            return
        self.acceptance.run()
        final = self.run_dir / "manuscript" / "final.md"
        if final.exists():
            write_text(self.run_dir / "manuscript" / "final_unrevised.md", final.read_text(encoding="utf-8"))

    def review_chapter(self, chapter_id: int) -> dict[str, Any]:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        chapter_text = read_text(chapter_dir / "02_draft.md")
        builtin = builtin_chapter_review(chapter_id, chapter_text)
        write_text(chapter_dir / "04_chapter_review.json", json.dumps(builtin, ensure_ascii=False, indent=2) + "\n")
        lines = ["# Chapter Review", "", f"Revision required: `{str(builtin['revision_required']).lower()}`", "", "## Blocking Issues"]
        for issue in builtin["blocking_issues"]:
            lines.append(f"- {issue['dimension']}: {issue['issue']} Evidence: {issue['evidence']}")
        if not builtin["blocking_issues"]:
            lines.append("- None")
        write_text(chapter_dir / "04_chapter_review.md", "\n".join(lines) + "\n")
        return builtin

    def plan_revision(self, chapter_id: int, review: dict[str, Any]) -> dict[str, Any]:
        plan = {
            "chapter_id": chapter_id,
            "must_fix": [
                {
                    "issue": issue["issue"],
                    "evidence": issue["evidence"],
                    "rewrite_instruction": issue["suggested_fix"],
                }
                for issue in review.get("blocking_issues", [])
            ],
            "preserve": ["Preserve required plot facts, reveal order, POV, and chapter function."],
            "rewrite_strategy": [
                "Compress repeated object handling.",
                "Convert clue confirmation into character pressure.",
                "Replace checklist deduction with scene or dialogue when possible.",
            ],
            "continuity_constraints": ["Do not add new major facts that contradict previous summaries."],
            "expected_quality_gains": review.get("revision_targets", []),
            "risk_notes": [],
        }
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        write_text(chapter_dir / "05_revision_plan.json", json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
        write_text(
            chapter_dir / "05_revision_plan.md",
            "# Revision Plan\n\n```json\n" + json.dumps(plan, ensure_ascii=False, indent=2) + "\n```\n",
        )
        return plan


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
