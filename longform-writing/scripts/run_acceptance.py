#!/usr/bin/env python3
"""Run longform-writing acceptance tests.

This is intentionally lightweight and stdlib-only. It is a test harness for the
skill workflow, not a polished product runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from acceptance_checker import AcceptanceChecker
from workflow_core import (  # noqa: F401
    BASE_ADAPTER,
    CHINESE_NUMERALS,
    GENRE_ADAPTERS,
    ModelClient,
    WorkflowContext,
    WorkflowResult,
    WorkflowState,
    append_text,
    endpoint_from_base_url,
    extract_json,
    first_code_block,
    load_dotenv,
    parse_test_case,
    read_text,
    render_template,
    requested_chapter_count,
    sanitize_scene_beats,
    section,
    slugify,
    write_text,
)


class AcceptanceRun(WorkflowContext):
    def parse_request(self) -> dict[str, Any]:
        raw = self.test_case["request"]
        output = self.model_step(
            "parse_request",
            "01_parse_request.md",
            {"user_request": raw},
            ["00_request.md"],
            ["00_request.md"],
            ["User Request"],
            800,
            0,
        )
        try:
            parsed = extract_json(output)
        except Exception as exc:
            self.major.append(f"parse_request did not return valid JSON: {exc}")
            parsed = {
                "version": "0.1",
                "language": "zh",
                "genre": None,
                "target_chapters": 3,
                "target_length": "short_draft",
                "protagonist": None,
                "key_supporting_characters": [],
                "premise": raw,
                "setting": None,
                "tone": [],
                "pov": "third_person_limited",
                "style_constraints": [],
                "prohibited_elements": [],
                "must_include": [],
                "must_not_reveal_early": [],
                "final_reveal": None,
                "automation_mode": self.mode,
            }
        parsed["automation_mode"] = self.mode
        requested_chapters = requested_chapter_count(raw)
        if requested_chapters:
            parsed["target_chapters"] = requested_chapters
        self.genre_adapter_key = self.detect_genre_adapter(parsed)
        self.genre_adapter_text = self.render_genre_adapter(self.genre_adapter_key)
        parsed["genre_adapter"] = self.genre_adapter_key
        if not parsed.get("genre"):
            parsed["genre"] = self.genre_adapter_key
        return parsed

    def run(self) -> None:
        self.initialize()
        parsed = self.parse_request()
        raw_request = self.read_project("00_request.md")
        brief = self.model_step(
            "build_project_brief",
            "02_build_project_brief.md",
            {"user_request": raw_request, "parsed_requirement": parsed, "genre_adapter": self.genre_adapter_text},
            ["00_request.md"],
            ["01_project_brief.md"],
            ["User Request", "Parsed Requirement"] + self.genre_context(),
            1600,
            0.2,
            self.genre_extra(),
        )
        write_text(self.run_dir / "01_project_brief.md", brief.strip() + "\n")
        feedback = self.checkpoint(
            "requirement_alignment",
            ["01_project_brief.md"],
            "checkpoint_1",
            ["01_project_brief.md"],
            ["build_codex", "generate_outline", "generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        )
        if feedback:
            write_text(self.run_dir / "01_project_brief.md", self.apply_brief_feedback(self.read_project("01_project_brief.md"), feedback))
            self.feedback_applied.append("checkpoint_1")

        codex_text = self.model_step(
            "build_codex",
            "03_build_codex.md",
            {"project_brief": self.read_project("01_project_brief.md"), "genre_adapter": self.genre_adapter_text},
            ["00_request.md", "01_project_brief.md"],
            ["02_codex.json"],
            ["Project Brief"] + self.genre_context(),
            2200,
            0.1,
            self.genre_extra(),
        )
        codex = self.parse_or_retry_json(
            codex_text,
            workflow_step="build_codex",
            input_files=["00_request.md", "01_project_brief.md"],
            output_files=["02_codex.json"],
            expected_shape='{"version": "0.1", "entries": [...]}',
        )
        codex = self.normalize_codex(codex)
        write_text(self.run_dir / "02_codex.json", json.dumps(codex, ensure_ascii=False, indent=2) + "\n")

        global_codex, relevant_codex = self.select_codex(self.read_project("01_project_brief.md"))
        outline_text = self.model_step(
            "generate_outline",
            "04_generate_outline.md",
            {
                "project_brief": self.read_project("01_project_brief.md"),
                "global_codex": global_codex,
                "relevant_codex": relevant_codex,
                "target_chapters": parsed.get("target_chapters", 3),
                "genre_adapter": self.genre_adapter_text,
            },
            ["01_project_brief.md", "02_codex.json"],
            ["03_outline.json"],
            ["Project Brief", "Global Codex", "Relevant Codex"] + self.genre_context(),
            2200,
            0.2,
            self.genre_extra(),
        )
        outline = self.parse_or_retry_json(
            outline_text,
            workflow_step="generate_outline",
            input_files=["01_project_brief.md", "02_codex.json"],
            output_files=["03_outline.json"],
            expected_shape='[{"chapter_id": 1, "title": "", "summary": ""}]',
        )
        if not isinstance(outline, list):
            raise RuntimeError("Outline is not an array")
        write_text(self.run_dir / "03_outline.json", json.dumps(outline, ensure_ascii=False, indent=2) + "\n")
        feedback = self.checkpoint(
            "story_plan_alignment",
            ["01_project_brief.md", "02_codex.json", "03_outline.json"],
            "checkpoint_2",
            ["03_outline.json"],
            ["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        )
        if feedback:
            outline = self.apply_outline_feedback(outline, feedback)
            write_text(self.run_dir / "03_outline.json", json.dumps(outline, ensure_ascii=False, indent=2) + "\n")
            append_text(self.run_dir / "writing_log.md", "- Story plan feedback should constrain downstream generation.\n")
            self.feedback_applied.append("checkpoint_2")

        story_so_far = ""
        previous_summary_files: list[str] = []
        for chapter in outline:
            chapter_id = int(chapter.get("chapter_id", len(list((self.run_dir / "chapters").glob("chapter_*"))) + 1))
            chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            required = chapter.get("required_codex", [])
            g_codex, r_codex = self.select_codex(json.dumps(chapter, ensure_ascii=False), required)
            summary_inputs = ["01_project_brief.md", "02_codex.json", "03_outline.json"] + previous_summary_files
            summary = self.model_step(
                "generate_chapter_summary",
                "05_generate_chapter_summary.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "story_so_far": story_so_far,
                    "outline_chapter": chapter,
                    "global_codex": g_codex,
                    "relevant_codex": r_codex,
                    "genre_adapter": self.genre_adapter_text,
                },
                summary_inputs,
                [f"chapters/chapter_{chapter_id:02d}/00_summary.md"],
                ["Project Brief", "Story So Far", "Current Outline Chapter", "Global Codex", "Relevant Codex"] + self.genre_context(),
                1400,
                0.2,
                self.genre_extra(),
            )
            write_text(chapter_dir / "00_summary.md", summary.strip() + "\n")
            beat_inputs = [
                "01_project_brief.md",
                "02_codex.json",
                f"chapters/chapter_{chapter_id:02d}/00_summary.md",
            ] + previous_summary_files
            beats_text = self.model_step(
                "generate_scene_beats",
                "06_generate_scene_beats.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "story_so_far": story_so_far,
                    "chapter_summary": summary,
                    "global_codex": g_codex,
                    "relevant_codex": r_codex,
                    "beat_count": self.beat_count,
                    "genre_adapter": self.genre_adapter_text,
                },
                beat_inputs,
                [f"chapters/chapter_{chapter_id:02d}/01_beats.json"],
                ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex"] + self.genre_context(),
                2200,
                0.2,
                self.genre_extra(),
            )
            beats = self.parse_or_retry_json(
                beats_text,
                workflow_step="generate_scene_beats",
                input_files=beat_inputs,
                output_files=[f"chapters/chapter_{chapter_id:02d}/01_beats.json"],
                expected_shape='[{"beat_id": 1, "text": "", "purpose": "", "required_codex": [], "reveals": [], "must_not_reveal": []}]',
            )
            beats = sanitize_scene_beats(beats)
            write_text(chapter_dir / "01_beats.json", json.dumps(beats, ensure_ascii=False, indent=2) + "\n")
            validation = self.validate_beats(chapter_id, summary, beats, story_so_far)
            if not validation["passed"]:
                if self.expected_validation_guard:
                    self.validation_guard_triggered = True
                    append_text(self.run_dir / "writing_log.md", "\n- Validation guard triggered as expected before prose generation.\n")
                else:
                    self.failures.append(f"Beat validation failed for chapter {chapter_id}: {validation['issues']}")
                self.write_report()
                return
            draft_parts: list[str] = [f"# Chapter {chapter_id}: {chapter.get('title', '')}\n"]
            text_before = ""
            write_text(chapter_dir / "02_draft.md", "")
            for beat in beats:
                current = json.dumps(beat, ensure_ascii=False, indent=2)
                g_codex, r_codex = self.select_codex(summary + "\n" + current, beat.get("required_codex", []))
                prose_inputs = [
                    "01_project_brief.md",
                    "02_codex.json",
                    f"chapters/chapter_{chapter_id:02d}/00_summary.md",
                    f"chapters/chapter_{chapter_id:02d}/01_beats.json",
                ] + previous_summary_files
                prose = self.model_step(
                    "write_beat_prose",
                    "08_write_beat_prose.md",
                    {
                        "project_brief": self.read_project("01_project_brief.md"),
                        "story_so_far": story_so_far,
                        "chapter_summary": summary,
                        "global_codex": g_codex,
                        "relevant_codex": r_codex,
                        "text_before": text_before[-1800:],
                        "current_beat": current,
                        "additional_context": "",
                        "word_count": self.prose_word_count,
                        "genre_adapter": self.genre_adapter_text,
                    },
                    prose_inputs,
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                    ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Text Before", "Current Beat"] + self.genre_context(),
                    1400,
                    0.35,
                    self.genre_extra(),
                )
                draft_parts.append(prose.strip() + "\n")
                text_before = "\n".join(draft_parts)
                write_text(chapter_dir / "02_draft.md", "\n".join(draft_parts).strip() + "\n")
            summary_after = self.model_step(
                "summarize_chapter",
                "09_summarize_chapter.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "chapter_draft": self.read_project(f"chapters/chapter_{chapter_id:02d}/02_draft.md"),
                    "genre_adapter": self.genre_adapter_text,
                },
                ["01_project_brief.md", f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                [f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                ["Project Brief", "Chapter Draft"] + self.genre_context(),
                900,
                0.1,
                self.genre_extra(),
            )
            if self.cjk_ratio(summary_after) < 0.15 and self.cjk_ratio(self.read_project("01_project_brief.md")) > 0.15:
                retry_prompt = (
                    "请用中文重写下面的章节事实摘要。只输出中文摘要，不要解释，不要使用英文。\n\n"
                    f"{summary_after}"
                )
                summary_after = self.client.complete(retry_prompt, max_tokens=900, temperature=0)
                self.record(
                    "summarize_chapter_retry_language",
                    "core_spec/prompts/09_summarize_chapter.md",
                    retry_prompt,
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                    [f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                    "success",
                    ["Language Retry", "Chapter Draft"],
                )
            write_text(chapter_dir / "03_summary_after.md", summary_after.strip() + "\n")
            story_so_far += f"\n\nChapter {chapter_id} summary:\n{summary_after.strip()}\n"
            previous_summary_files.append(f"chapters/chapter_{chapter_id:02d}/03_summary_after.md")
            if chapter_id == 1:
                feedback = self.checkpoint(
                    "first_chapter_direction_check",
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md", f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                    "checkpoint_3",
                    ["01_project_brief.md"],
                    ["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
                )
                if feedback:
                    append_text(self.run_dir / "01_project_brief.md", f"\n## First Chapter Direction Feedback\n{feedback}\n")
                    self.feedback_applied.append("checkpoint_3")
        self.merge_manuscript()
        self.write_report()

    def validate_beats(self, chapter_id: int, summary: str, beats: list[dict[str, Any]], story_so_far: str) -> dict[str, Any]:
        issues = []
        if not isinstance(beats, list) or not beats:
            issues.append({"type": "empty_beats", "detail": "No beats generated", "severity": "critical"})
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in summary or f"第 {numeral} 阶段" in summary:
                expected_stage = idx
                break
        for beat in beats if isinstance(beats, list) else []:
            text = beat.get("text", "")
            if len(text) < 12:
                issues.append({"beat_id": beat.get("beat_id"), "type": "vague_beat", "detail": text, "severity": "major"})
            for idx, numeral in enumerate(stage_numerals, 1):
                if expected_stage and idx != expected_stage and f"第{numeral}阶段" in text:
                    issues.append({
                        "beat_id": beat.get("beat_id"),
                        "type": "summary_mismatch",
                        "detail": f"Beat mentions 第{numeral}阶段 but chapter summary is 第{stage_numerals[expected_stage-1]}阶段.",
                        "severity": "critical",
                    })
            if "下一阶段" in text or ("第三阶段" in text and chapter_id == 2):
                if "第三阶段" not in summary:
                    issues.append({"beat_id": beat.get("beat_id"), "type": "chapter_scope_drift", "detail": text, "severity": "critical"})
        rendered = render_template(
            self.template("07_validate_scene_beats.md"),
            {
                "story_so_far": story_so_far,
                "chapter_summary": summary,
                "global_codex": self.select_codex(summary)[0],
                "relevant_codex": self.select_codex(summary)[1],
                "scene_beats": beats,
                "genre_adapter": self.genre_adapter_text,
            },
        )
        result = {"passed": not issues, "issues": issues}
        input_files = ["02_codex.json", f"chapters/chapter_{chapter_id:02d}/00_summary.md", f"chapters/chapter_{chapter_id:02d}/01_beats.json"]
        if story_so_far:
            input_files.extend(f"chapters/chapter_{idx:02d}/03_summary_after.md" for idx in range(1, chapter_id))
        self.record(
            "validate_scene_beats",
            "core_spec/prompts/07_validate_scene_beats.md",
            rendered,
            input_files,
            ["run_records/step_manifest.jsonl"],
            "success" if result["passed"] else "failed",
            ["Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Scene Beats"] + self.genre_context(),
            {"validation": result, **self.genre_extra()},
        )
        return result

    def merge_manuscript(self) -> None:
        parts = []
        for draft in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md")):
            parts.append(read_text(draft).strip())
        full = "\n\n".join(parts).strip() + "\n"
        write_text(self.run_dir / "manuscript" / "draft_full.md", full)
        write_text(self.run_dir / "manuscript" / "final.md", full)
        rendered = self.template("10_merge_manuscript.md") + "\n\n[Chapter Draft Paths]\n" + "\n".join(
            str(p.relative_to(self.run_dir)) for p in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md"))
        )
        self.record(
            "merge_manuscript",
            "core_spec/prompts/10_merge_manuscript.md",
            rendered,
            [str(p.relative_to(self.run_dir)) for p in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md"))],
            ["manuscript/draft_full.md", "manuscript/final.md"],
            "success",
            ["Chapter Drafts"],
        )

    def workflow_result(self) -> WorkflowResult:
        return WorkflowResult(
            success=not self.failures,
            failures=list(self.failures),
            major=list(self.major),
            minor=list(self.minor),
            feedback_applied=list(self.feedback_applied),
            expected_validation_guard=self.expected_validation_guard,
            validation_guard_triggered=self.validation_guard_triggered,
            genre_adapter_key=self.genre_adapter_key,
        )

    def write_report(self) -> None:
        AcceptanceChecker(
            self.skill_path,
            self.test_case,
            self.run_dir,
            self.mode,
            self.workflow_result(),
        ).write_report()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--test-case", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--provider", choices=["deepseek", "mock"], default=os.environ.get("LONGFORM_MODEL_PROVIDER", "deepseek"))
    parser.add_argument("--mode", choices=["full_auto", "milestone_review"], default="full_auto")
    parser.add_argument("--beat-count", type=int, default=int(os.environ.get("LONGFORM_BEAT_COUNT", "4")))
    parser.add_argument("--prose-word-count", type=int, default=int(os.environ.get("LONGFORM_PROSE_WORD_COUNT", "260")))
    args = parser.parse_args()

    repo_root = args.skill_path.resolve().parents[0]
    load_dotenv(repo_root / ".env")
    load_dotenv(Path.cwd() / ".env")

    test_case = parse_test_case(args.test_case)
    output_dir = args.output_dir or (Path.cwd() / "runs" / slugify(test_case["name"]))
    runner = AcceptanceRun(
        args.skill_path.resolve(),
        test_case,
        output_dir.resolve(),
        args.provider,
        args.mode,
        args.beat_count,
        args.prose_word_count,
    )
    start = time.monotonic()
    try:
        runner.run()
    except Exception as exc:
        runner.failures.append(f"Runner exception: {exc}")
        try:
            runner.write_report()
        except Exception:
            pass
        print(f"Acceptance run failed: {exc}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - start
    print(f"Acceptance run complete: {output_dir}")
    print(f"elapsed_sec={elapsed:.2f}")
    report = output_dir / "acceptance_report.md"
    if report.exists():
        print(read_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
