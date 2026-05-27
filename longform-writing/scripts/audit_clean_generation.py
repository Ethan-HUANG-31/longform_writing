#!/usr/bin/env python3
"""Audit a completed longform-writing run for clean generation-path behavior."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


LEGACY_CONTAMINATION_TOKENS = [
    "小帅",
    "小美",
    "阿强",
    "老周",
    "林姐",
    "选择室",
    "审判者",
    "蓝色钥匙",
    "旧录音装置",
    "缺失封面",
    "旧借书卡",
    "错放书",
    "储物柜密码",
    "高风险，不建议上线",
]

CORE_WORKFLOW = [
    "parse_request",
    "build_project_brief",
    "build_codex",
    "generate_outline",
    "generate_chapter_summary",
    "generate_scene_beats",
    "validate_scene_beats",
    "write_beat_prose",
    "summarize_chapter",
    "merge_manuscript",
]

GENERATED_ARTIFACT_SUFFIXES = {
    ".md",
    ".json",
    ".jsonl",
}

READ_ONLY_EXCLUSIONS = {
    "acceptance_report.md",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_manifest(path: Path) -> list[dict]:
    return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]


def artifact_paths(run_dir: Path) -> list[Path]:
    roots = [
        run_dir / "00_request.md",
        run_dir / "01_project_brief.md",
        run_dir / "02_codex.json",
        run_dir / "03_outline.json",
        run_dir / "manuscript",
        run_dir / "chapters",
        run_dir / "run_records" / "rendered_prompts",
    ]
    results: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            results.append(root)
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in GENERATED_ARTIFACT_SUFFIXES:
                results.append(path)
    return sorted(results)


def chapter_id_from_output_files(output_files: list[str]) -> int | None:
    joined = " ".join(output_files)
    match = re.search(r"chapter_(\d{2})", joined)
    if not match:
        return None
    return int(match.group(1))


def audit_trace(run_dir: Path, entries: list[dict]) -> list[str]:
    issues: list[str] = []
    steps = [entry.get("workflow_step", "") for entry in entries]
    seen = {step: steps.index(step) for step in steps}

    for required in CORE_WORKFLOW:
        if required not in steps:
            issues.append(f"Missing workflow step in manifest: {required}")

    if "write_beat_prose" in seen:
        prose_idx = seen["write_beat_prose"]
        if "generate_scene_beats" not in seen or seen["generate_scene_beats"] > prose_idx:
            issues.append("write_beat_prose appears before generate_scene_beats")
        if "validate_scene_beats" not in seen or seen["validate_scene_beats"] > prose_idx:
            issues.append("write_beat_prose appears before validate_scene_beats")

    for entry in entries:
        workflow_step = entry.get("workflow_step", "")
        rendered = run_dir / entry.get("rendered_prompt", "")
        if workflow_step == "write_beat_prose":
            chapter_id = chapter_id_from_output_files(entry.get("output_files", []))
            text = read_text(rendered) if rendered.exists() else ""
            if chapter_id and chapter_id >= 2:
                required_prev = f"chapters/chapter_{chapter_id - 1:02d}/03_summary_after.md"
                if required_prev not in entry.get("input_files", []):
                    issues.append(
                        f"{entry.get('step_id')} missing previous summary_after input: {required_prev}"
                    )
                if f"Chapter {chapter_id + 1} summary:" in text:
                    issues.append(f"{entry.get('step_id')} prose prompt includes a future chapter summary")
            if "[Current Beat]" not in text:
                issues.append(f"{entry.get('step_id')} rendered prompt missing [Current Beat] section")
            if "[Current Chapter Summary]" not in text:
                issues.append(f"{entry.get('step_id')} rendered prompt missing [Current Chapter Summary] section")

        if workflow_step == "generate_scene_beats":
            chapter_id = chapter_id_from_output_files(entry.get("output_files", []))
            if chapter_id and chapter_id >= 2:
                required_prev = f"chapters/chapter_{chapter_id - 1:02d}/03_summary_after.md"
                if required_prev not in entry.get("input_files", []):
                    issues.append(
                        f"{entry.get('step_id')} beat-generation step missing previous summary_after input: {required_prev}"
                    )
    return issues


def audit_contamination(run_dir: Path) -> list[str]:
    issues: list[str] = []
    for path in artifact_paths(run_dir):
        relative = path.relative_to(run_dir).as_posix()
        if relative in READ_ONLY_EXCLUSIONS:
            continue
        text = read_text(path)
        for token in LEGACY_CONTAMINATION_TOKENS:
            if token in text:
                issues.append(f"Legacy contamination token `{token}` found in {relative}")
    return issues


def audit_shape(run_dir: Path) -> list[str]:
    issues: list[str] = []
    required = [
        "00_request.md",
        "01_project_brief.md",
        "02_codex.json",
        "03_outline.json",
        "manuscript/final.md",
        "run_records/step_manifest.jsonl",
    ]
    for relative in required:
        if not (run_dir / relative).exists():
            issues.append(f"Missing required artifact: {relative}")
    chapters = sorted((run_dir / "chapters").glob("chapter_*"))
    if not chapters:
        issues.append("No chapter directories were generated")
    for chapter_dir in chapters:
        for name in ["00_summary.md", "01_beats.json", "02_draft.md", "03_summary_after.md"]:
            if not (chapter_dir / name).exists():
                issues.append(f"Missing chapter artifact: {chapter_dir.name}/{name}")
    return issues


def build_report(run_dir: Path, shape_issues: list[str], trace_issues: list[str], contamination_issues: list[str]) -> str:
    all_issues = shape_issues + trace_issues + contamination_issues
    lines = [
        "# Clean Generation Audit",
        "",
        "## Run Directory",
        str(run_dir),
        "",
        "## Result",
        "Pass" if not all_issues else "Fail",
        "",
        "## Shape Checks",
        "Passed" if not shape_issues else "\n".join(f"- {item}" for item in shape_issues),
        "",
        "## Trace Checks",
        "Passed" if not trace_issues else "\n".join(f"- {item}" for item in trace_issues),
        "",
        "## Legacy Contamination Checks",
        "Passed" if not contamination_issues else "\n".join(f"- {item}" for item in contamination_issues),
        "",
        "## Summary",
        "Clean generation path confirmed." if not all_issues else "See failures above.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--report-path", type=Path)
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    manifest = run_dir / "run_records" / "step_manifest.jsonl"
    if not manifest.exists():
        print(f"Missing manifest: {manifest}", file=sys.stderr)
        return 1

    try:
        entries = parse_manifest(manifest)
    except Exception as exc:
        print(f"Manifest parse failed: {exc}", file=sys.stderr)
        return 1

    shape_issues = audit_shape(run_dir)
    trace_issues = audit_trace(run_dir, entries)
    contamination_issues = audit_contamination(run_dir)
    report = build_report(run_dir, shape_issues, trace_issues, contamination_issues)

    report_path = args.report_path or (run_dir / "clean_generation_audit.md")
    report_path.write_text(report, encoding="utf-8")
    print(report)
    return 0 if not (shape_issues or trace_issues or contamination_issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())
