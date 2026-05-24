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

from run_acceptance import AcceptanceRun, load_dotenv, parse_test_case, read_text, render_template, write_text  # noqa: E402


DEFAULT_CASES = [
    "05_medium_length_single_protagonist",
    "10_mystery_clue_fairness_smoke",
    "07_dual_timeline_continuity",
]


METHOD_ORDER = ["direct_write", "simple_engineered", "full_unrevised", "full_revised"]
SAMPLE_IDS = ["A", "B", "C", "D"]
REQUIRED_JUDGES = ["rubric", "reader"]


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


def decide_acceptance(case_id: str, iteration_id: int, judge_rankings: dict[str, list[str]]) -> dict[str, Any]:
    failures: list[str] = []
    required_methods = set(METHOD_ORDER)
    for judge in REQUIRED_JUDGES:
        ranking = judge_rankings.get(judge)
        if not ranking:
            failures.append(f"{judge} ranking missing.")
            continue
        unknown = sorted(set(ranking) - required_methods)
        missing = sorted(required_methods - set(ranking))
        if unknown:
            failures.append(f"{judge} ranking has unknown methods: {', '.join(unknown)}.")
        if missing:
            failures.append(f"{judge} ranking missing required methods: {', '.join(missing)}.")
        if len(ranking) != len(set(ranking)):
            failures.append(f"{judge} ranking contains duplicate methods.")
        if unknown or missing or len(ranking) != len(set(ranking)):
            continue
        if ranking.index("full_revised") > ranking.index("direct_write"):
            failures.append(f"{judge}: direct_write beats full_revised.")
        if ranking.index("full_revised") > ranking.index("full_unrevised"):
            failures.append(f"{judge}: full_unrevised beats full_revised.")
    return {
        "case_id": case_id,
        "iteration_id": iteration_id,
        "judge_rankings": judge_rankings,
        "revealed_ranking": judge_rankings.get("reader") or judge_rankings.get("rubric") or [],
        "pass": not failures,
        "evidence": [],
        "failure_reason": "; ".join(failures),
        "next_iteration_strategy": [
            "Reduce repetition and checklist prose.",
            "Increase character pressure and scene flow.",
        ] if failures else [],
    }


def iteration_root(output_root: Path, iteration: int) -> Path:
    return output_root / f"iter_{iteration:02d}"


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


def apply_builtin_revision(text: str) -> str:
    revised: list[str] = []
    seen: set[str] = set()
    for paragraph in re.split(r"\n\s*\n", text):
        stripped = paragraph.strip()
        if not stripped:
            continue
        key = re.sub(r"\s+", "", stripped)
        if key in seen:
            continue
        seen.add(key)
        revised.append(stripped)
    return "\n\n".join(revised).strip() + "\n"


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
        final = self.run_dir / "manuscript" / "final.md"
        final_unrevised = self.run_dir / "manuscript" / "final_unrevised.md"
        if final.exists():
            if not final_unrevised.exists():
                write_text(final_unrevised, final.read_text(encoding="utf-8"))
            return
        self.acceptance.run()
        if final.exists() and not final_unrevised.exists():
            write_text(final_unrevised, final.read_text(encoding="utf-8"))

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

    def rewrite_chapter(self, chapter_id: int, revision_plan: dict[str, Any]) -> str:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        original = read_text(chapter_dir / "02_draft.md")
        must_fix = revision_plan.get("must_fix", [])
        if not must_fix:
            revised = original
            notes = "No blocking revision items; original chapter preserved.\n"
        else:
            chapter_summary = self.acceptance.read_project(f"chapters/chapter_{chapter_id:02d}/00_summary.md")
            _, relevant_codex = self.acceptance.select_codex(original + "\n\n" + chapter_summary)
            rendered = render_template(
                self.template("14_rewrite_chapter.md"),
                {
                    "project_brief": self.acceptance.read_project("01_project_brief.md"),
                    "previous_summaries": collect_previous_summaries(self.run_dir, chapter_id),
                    "chapter_summary": chapter_summary,
                    "relevant_codex": relevant_codex,
                    "original_chapter_text": original,
                    "revision_plan": revision_plan,
                },
            )
            model_revised = self.acceptance.client.complete(rendered, max_tokens=4200, temperature=0.25).strip()
            if not model_revised or model_revised == "MOCK_OUTPUT":
                revised = apply_builtin_revision(original)
                notes = "Used builtin duplicate-paragraph fallback because model rewrite was empty or MOCK_OUTPUT.\n"
            else:
                revised = model_revised.strip() + "\n"
                notes = "Used model rewrite from 14_rewrite_chapter.md.\n"
            self.acceptance.record(
                "rewrite_chapter",
                "core_spec/prompts/14_rewrite_chapter.md",
                rendered,
                [
                    "01_project_brief.md",
                    "02_codex.json",
                    f"chapters/chapter_{chapter_id:02d}/00_summary.md",
                    f"chapters/chapter_{chapter_id:02d}/02_draft.md",
                    f"chapters/chapter_{chapter_id:02d}/05_revision_plan.json",
                ],
                [
                    f"chapters/chapter_{chapter_id:02d}/02_revised_draft.md",
                    f"chapters/chapter_{chapter_id:02d}/06_revision_notes.md",
                ],
                "success",
                ["Project Brief", "Previous Summaries", "Chapter Summary", "Relevant Codex", "Revision Plan"],
            )
        write_text(chapter_dir / "02_revised_draft.md", revised.strip() + "\n")
        write_text(chapter_dir / "06_revision_notes.md", notes)
        return revised

    def summarize_revised_chapter(self, chapter_id: int, revised_chapter_text: str) -> str:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        rendered = render_template(
            self.template("15_summarize_revised_chapter.md"),
            {
                "project_brief": self.acceptance.read_project("01_project_brief.md"),
                "revised_chapter_text": revised_chapter_text,
            },
        )
        model_summary = self.acceptance.client.complete(rendered, max_tokens=900, temperature=0.1).strip()
        if not model_summary or model_summary == "MOCK_OUTPUT":
            summary = self.acceptance.read_project(f"chapters/chapter_{chapter_id:02d}/03_summary_after.md").strip()
        else:
            summary = model_summary
        self.acceptance.record(
            "summarize_revised_chapter",
            "core_spec/prompts/15_summarize_revised_chapter.md",
            rendered,
            ["01_project_brief.md", f"chapters/chapter_{chapter_id:02d}/02_revised_draft.md"],
            [f"chapters/chapter_{chapter_id:02d}/03_summary_after_revised.md"],
            "success",
            ["Project Brief", "Revised Chapter Text"],
        )
        write_text(chapter_dir / "03_summary_after_revised.md", summary.strip() + "\n")
        return summary.strip() + "\n"

    def revise_all_chapters(self) -> str:
        self.ensure_unrevised_draft()
        for chapter_dir in sorted((self.run_dir / "chapters").glob("chapter_*")):
            match = re.search(r"chapter_(\d+)$", chapter_dir.name)
            if not match:
                continue
            chapter_id = int(match.group(1))
            review = self.review_chapter(chapter_id)
            plan = self.plan_revision(chapter_id, review)
            revised = self.rewrite_chapter(chapter_id, plan)
            self.summarize_revised_chapter(chapter_id, revised)
        final = self.run_dir / "manuscript" / "final.md"
        final_unrevised = self.run_dir / "manuscript" / "final_unrevised.md"
        if final.exists() and not final_unrevised.exists():
            write_text(final_unrevised, final.read_text(encoding="utf-8"))
        return merge_revised_chapters(self.run_dir)


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
    for iteration in range(1, args.max_iterations + 1):
        iter_root = iteration_root(args.output_root, iteration)
        iter_root.mkdir(parents=True, exist_ok=True)
        for case in args.cases:
            runner = V1RevisionRun(
                args.skill_path,
                args.test_dir / f"{case}.md",
                ROOT / "runs" / f"{case}_v1_revision_iter_{iteration:02d}",
                args.provider,
                iteration,
            )
            runner.revise_all_chapters()
        blind_cases: dict[str, dict[str, Any]] = {}
        for case in args.cases:
            test_case_path = args.test_dir / f"{case}.md"
            request = parse_test_case(test_case_path)["request"]
            run_dir = ROOT / "runs" / f"{case}_v1_revision_iter_{iteration:02d}"
            blind_cases[f"case_{case[:2]}"] = {
                "case_name": case,
                "request": request,
                "methods": {
                    "direct_write": ROOT / "baseline_runs" / "direct_write" / case / "manuscript.md",
                    "simple_engineered": ROOT / "baseline_runs" / "simple_engineered" / case / "manuscript.md",
                    "full_unrevised": run_dir / "manuscript" / "final_unrevised.md",
                    "full_revised": run_dir / "manuscript" / "final_revised.md",
                },
            }
        mapping = build_blind_package(iter_root / "blind", blind_cases)
        write_text(iter_root / "private_mapping.json", json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
        print(f"iteration {iteration:02d} complete")
        break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
