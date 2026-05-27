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

    def artifact_checks(self) -> list[str]:
        missing = []
        required = [
            "00_request.md",
            "01_project_brief.md",
            "02_codex.json",
            "03_outline.json",
            "manuscript/draft_full.md",
            "manuscript/final.md",
            "run_records/step_manifest.jsonl",
        ]
        for rel in required:
            if not (self.run_dir / rel).exists() or not self.read_project(rel).strip():
                missing.append(rel)
        try:
            outline = json.loads(self.read_project("03_outline.json"))
        except Exception:
            outline = []
            missing.append("03_outline.json parse")
        for chapter in outline if isinstance(outline, list) else []:
            cid = int(chapter.get("chapter_id", 0))
            for rel in ["00_summary.md", "01_beats.json", "02_draft.md", "03_summary_after.md"]:
                path = self.run_dir / "chapters" / f"chapter_{cid:02d}" / rel
                if not path.exists() or not read_text(path).strip():
                    missing.append(str(path.relative_to(self.run_dir)))
        return missing

    def trace_checks(self) -> list[str]:
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"manifest invalid: {exc}"]
        steps = [entry["workflow_step"] for entry in entries]
        for entry in entries:
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                issues.append(f"missing rendered prompt: {entry.get('rendered_prompt')}")
            template = entry.get("prompt_template", "")
            if template.startswith("core_spec/") and not (self.skill_path / template).exists():
                issues.append(f"missing prompt template: {template}")
        for idx, step in enumerate(steps):
            if step == "write_beat_prose":
                before = steps[:idx]
                if "generate_scene_beats" not in before or "validate_scene_beats" not in before:
                    issues.append("write_beat_prose occurred before beats/validation")
        for entry in entries:
            if entry["workflow_step"] in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose"}:
                rendered = self.run_dir / entry.get("rendered_prompt", "")
                if rendered.exists() and "Chapter 1 summary:" in read_text(rendered):
                    if "chapters/chapter_01/03_summary_after.md" not in entry.get("input_files", []):
                        issues.append(f"{entry['step_id']} uses chapter 1 story_so_far but omits chapter_01/03_summary_after.md from input_files")
            if entry["workflow_step"] == "validate_scene_beats":
                rendered = self.run_dir / entry.get("rendered_prompt", "")
                if rendered.exists() and "Chapter 1 summary:" in read_text(rendered):
                    if "chapters/chapter_01/03_summary_after.md" not in entry.get("input_files", []):
                        issues.append(f"{entry['step_id']} validation uses story_so_far but omits previous summary input_files")
        leak_terms = ["录音装置", "启动器", "recorder trigger", "old recorder trigger", "真正伤害了小美", "直接伤害了小美"]
        for entry in entries:
            if entry["workflow_step"] != "write_beat_prose":
                continue
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                continue
            output = "".join(entry.get("output_files", []))
            if ("chapter_01" in output or "chapter_02" in output) and any(term in read_text(rendered) for term in leak_terms):
                issues.append(f"{entry['step_id']} early prose prompt leaks protected future reveal")
        issues.extend(self.phase_b_trace_checks(entries))
        return issues

    def phase_b_trace_checks(self, entries: list[dict[str, Any]]) -> list[str]:
        name = self.test_case["name"]
        if name not in {
            "05_medium_length_single_protagonist",
            "06_supporting_cast_codex_routing",
            "07_dual_timeline_continuity",
        }:
            return []
        issues: list[str] = []

        def rendered_text(entry: dict[str, Any]) -> str:
            path = self.run_dir / entry.get("rendered_prompt", "")
            return read_text(path) if path.exists() else ""

        if name == "05_medium_length_single_protagonist":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose"}:
                    continue
                output = "".join(entry.get("output_files", []))
                if "chapter_04" in output or "chapter_05" in output:
                    input_files = set(entry.get("input_files", []))
                    for cid in [1, 2, 3]:
                        rel = f"chapters/chapter_{cid:02d}/03_summary_after.md"
                        if rel not in input_files:
                            issues.append(f"{entry['step_id']} for chapter 4/5 omits earlier summary_after input: {rel}")
                if entry["workflow_step"] == "write_beat_prose":
                    output_chapter = re.search(r"chapter_(\d{2})", output)
                    if output_chapter:
                        cid = int(output_chapter.group(1))
                        text = rendered_text(entry)
                        for future in range(cid + 1, 6):
                            if f"Chapter {future} summary:" in text:
                                issues.append(f"{entry['step_id']} prose prompt includes future chapter {future} summary")

        if name == "06_supporting_cast_codex_routing":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_scene_beats", "write_beat_prose"}:
                    continue
                text = rendered_text(entry)
                if entry["workflow_step"] == "write_beat_prose" and "[Current Beat]" in text:
                    current_scope = text.split("[Current Beat]", 1)[1]
                elif "[Current Chapter Summary]" in text:
                    current_scope = text.split("[Current Chapter Summary]", 1)[1]
                else:
                    current_scope = text
                for character in ["阿强", "林姐", "老周"]:
                    if character in current_scope and f"### {character}" not in text:
                        issues.append(f"{entry['step_id']} mentions {character} but relevant Codex omits that character")
            outline_text = self.read_project("03_outline.json")
            if "required_codex" not in outline_text:
                issues.append("Phase B 06 outline does not record required_codex routing")

        if name == "07_dual_timeline_continuity":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose", "validate_scene_beats"}:
                    continue
                output = "".join(entry.get("output_files", []))
                if "chapter_03" in output or "chapter_04" in output:
                    match = re.search(r"chapter_(\d{2})", output)
                    if not match:
                        continue
                    input_files = set(entry.get("input_files", []))
                    for cid in range(1, int(match.group(1))):
                        rel = f"chapters/chapter_{cid:02d}/03_summary_after.md"
                        if rel not in input_files:
                            issues.append(f"{entry['step_id']} omits dual-timeline story-so-far input: {rel}")
        return issues

    def checkpoint_checks(self) -> list[str]:
        if self.mode != "milestone_review":
            return []
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"Cannot parse manifest for checkpoint checks: {exc}"]
        checkpoints = [e for e in entries if e.get("workflow_step") == "user_checkpoint"]
        names = {e.get("checkpoint_name") for e in checkpoints}
        for required in ["requirement_alignment", "story_plan_alignment", "first_chapter_direction_check"]:
            if required not in names:
                issues.append(f"Missing checkpoint: {required}")
        for entry in checkpoints:
            if entry.get("status") == "feedback_received" and not entry.get("upstream_files_changed"):
                issues.append(f"Checkpoint {entry.get('checkpoint_name')} has feedback but no upstream_files_changed")
        outline_text = self.read_project("03_outline.json")
        if "第三章再揭示" in self.test_case["markdown"] and "user_feedback_constraints" not in outline_text:
                issues.append("Story plan feedback was not written into outline JSON")
        return issues

    def genre_adapter_checks(self) -> list[str]:
        if self.genre_adapter_key == "general":
            return []
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"Cannot parse manifest for genre adapter checks: {exc}"]
        routed_steps = {"generate_outline", "generate_chapter_summary", "generate_scene_beats", "validate_scene_beats", "write_beat_prose", "summarize_chapter"}
        for entry in entries:
            if entry.get("workflow_step") in routed_steps:
                if entry.get("genre_adapter") != self.genre_adapter_key:
                    issues.append(f"{entry.get('step_id')} missing genre_adapter={self.genre_adapter_key}")
                if "Genre Adapter" not in entry.get("context_sections", []):
                    issues.append(f"{entry.get('step_id')} missing Genre Adapter context section")
        prose_entries = [entry for entry in entries if entry.get("workflow_step") == "write_beat_prose"]
        expected_token = GENRE_ADAPTERS[self.genre_adapter_key]["label"]
        forbidden: dict[str, list[str]] = {
            "romance": ["Selected adapter: fantasy", "Selected adapter: mystery_clue_fairness", "Selected adapter: locked_room_moral_trial"],
            "fantasy": ["Selected adapter: romance", "Selected adapter: mystery_clue_fairness"],
            "mystery_clue_fairness": ["Selected adapter: romance", "Selected adapter: fantasy", "Selected adapter: locked_room_moral_trial"],
            "locked_room_moral_trial": ["Selected adapter: romance", "Selected adapter: fantasy"],
        }
        for entry in prose_entries:
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                continue
            text = read_text(rendered)
            if "[Genre Adapter]" not in text or expected_token not in text:
                issues.append(f"{entry.get('step_id')} rendered prompt missing {expected_token} adapter")
            for token in forbidden.get(self.genre_adapter_key, []):
                if token in text:
                    issues.append(f"{entry.get('step_id')} includes unrelated adapter token: {token}")
        codex_text = self.read_project("02_codex.json")
        if self.genre_adapter_key == "romance":
            for token in ["项目误会关系历史", "小帅关系驱动", "小美关系驱动", "职业 stakes", "情感 stakes"]:
                if token not in codex_text:
                    issues.append(f"Romance Codex missing {token}")
        elif self.genre_adapter_key == "fantasy":
            for token in ["银纸魔法", "失去一段自己的记忆", "只有一种魔法"]:
                if token not in codex_text:
                    issues.append(f"Fantasy Codex missing {token}")
        elif self.genre_adapter_key == "mystery_clue_fairness":
            for token in ["旧借书卡", "小美误导线索", "储物柜密码", "planted_clue", "red_herring", "final_payoff"]:
                if token not in codex_text:
                    issues.append(f"Mystery Codex missing {token}")
            for cid in range(1, 5):
                summary = self.read_project(f"chapters/chapter_{cid:02d}/03_summary_after.md")
                if "Clue State:" not in summary:
                    issues.append(f"Chapter {cid} summary_after missing clue state")
            chapter4_prompts = [
                self.run_dir / entry.get("rendered_prompt", "")
                for entry in prose_entries
                if "chapter_04" in "".join(entry.get("output_files", []))
            ]
            if chapter4_prompts and not any("旧借书卡" in read_text(path) and "日期" in read_text(path) and "储物柜密码" in read_text(path) for path in chapter4_prompts if path.exists()):
                issues.append("Chapter 4 prose prompts do not include prior clue state")
        return issues

    def content_checks(self) -> list[str]:
        issues = []
        brief = self.read_project("01_project_brief.md")
        request = self.read_project("00_request.md")
        zh_expected = "Language" in brief and ("zh" in brief.lower() or "中文" in brief)
        try:
            codex = json.loads(self.read_project("02_codex.json"))
            names = "\n".join(entry.get("name", "") for entry in codex.get("entries", []))
            for required in ["小帅", "小美"]:
                if required not in names and required in self.read_project("00_request.md"):
                    issues.append(f"Codex missing requested entity: {required}")
        except Exception as exc:
            issues.append(f"Codex parse failed during content checks: {exc}")
        try:
            outline = json.loads(self.read_project("03_outline.json"))
        except Exception:
            outline = []
        for chapter in outline if isinstance(outline, list) else []:
            cid = int(chapter.get("chapter_id", 0))
            summary = self.read_project(f"chapters/chapter_{cid:02d}/00_summary.md")
            beats_raw = self.read_project(f"chapters/chapter_{cid:02d}/01_beats.json")
            try:
                beats = json.loads(beats_raw)
            except Exception as exc:
                issues.append(f"Chapter {cid} beats JSON invalid: {exc}")
                beats = []
            validation = self.validate_beats_for_report(cid, summary, beats)
            issues.extend(validation)
            if cid < 3:
                for rel in [f"chapters/chapter_{cid:02d}/00_summary.md", f"chapters/chapter_{cid:02d}/01_beats.json", f"chapters/chapter_{cid:02d}/02_draft.md"]:
                    early_text = self.read_project(rel)
                    if "录音装置" in early_text or "启动器" in early_text or "真正伤害了小美" in early_text or "直接伤害了小美" in early_text:
                        issues.append(f"{rel} reveals protected key function before chapter 3")
            if zh_expected:
                for rel in [f"chapters/chapter_{cid:02d}/00_summary.md", f"chapters/chapter_{cid:02d}/03_summary_after.md"]:
                    text = self.read_project(rel)
                    if text and self.cjk_ratio(text) < 0.15:
                        issues.append(f"{rel} appears not to follow Chinese language setting")
        final_text = self.read_project("manuscript/final.md")
        if "旧录音装置" in request and "启动器" in request:
            if not ("旧录音装置" in final_text and ("启动器" in final_text or "启动" in final_text)):
                issues.append("Final manuscript does not fulfill required reveal: blue key as old recorder trigger")
        protected_harm_reveal = "\n".join([request, brief, json.dumps(outline, ensure_ascii=False)])
        if "真正伤害了小美" in protected_harm_reveal:
            harm_revealed = any(
                marker in final_text
                for marker in [
                    "真正伤害了小美",
                    "伤害了小美",
                    "直接伤害了小美",
                    "我失去了工作",
                    "失去了小林",
                    "被调离核心团队",
                    "姓名栏：小美",
                    "项目压力导致焦虑症状",
                    "她离开后",
                ]
            )
            if not harm_revealed:
                issues.append("Final manuscript does not fulfill required reveal: 小帅当年的选择真正伤害了小美")
        issues.extend(self.phase_b_content_checks(outline))
        return issues

    def phase_b_content_checks(self, outline: Any) -> list[str]:
        name = self.test_case["name"]
        if name not in {
            "05_medium_length_single_protagonist",
            "06_supporting_cast_codex_routing",
            "07_dual_timeline_continuity",
        }:
            return []
        issues: list[str] = []
        codex_text = self.read_project("02_codex.json")
        final_text = self.read_project("manuscript/final.md")

        def chapter_text(cid: int, rel: str = "02_draft.md") -> str:
            return self.read_project(f"chapters/chapter_{cid:02d}/{rel}")

        def require_text(label: str, text: str, groups: list[list[str]]) -> None:
            for group in groups:
                if not any(token in text for token in group):
                    issues.append(f"{label} missing expected marker: {'/'.join(group)}")

        if name == "05_medium_length_single_protagonist":
            if not isinstance(outline, list) or len(outline) != 5:
                issues.append("Phase B 05 expected outline with exactly 5 chapters")
            for marker in ["小帅", "小美", "项目评估报告", "缺失封面", "高风险，不建议上线"]:
                if marker not in codex_text:
                    issues.append(f"Phase B 05 Codex missing marker: {marker}")
            if "第五章" not in codex_text and "chapter 5" not in codex_text.lower():
                issues.append("Phase B 05 Codex does not mark missing-cover warning as chapter-5 protected future information")
            require_text("Phase B 05 chapter 1", chapter_text(1), [["项目评估报告", "报告"], ["缺失封面", "封面"]])
            require_text("Phase B 05 chapter 2", chapter_text(2), [["涂黑"], ["三处", "3处", "三个"]])
            require_text("Phase B 05 chapter 3", chapter_text(3), [["小美"], ["暂停", "停止", "暂缓", "叫停"]])
            require_text("Phase B 05 chapter 4", chapter_text(4), [["小帅"], ["批准", "签批", "同意继续", "继续推进"]])
            require_text("Phase B 05 chapter 5", chapter_text(5), [["高风险，不建议上线"], ["责任", "回避", "承担", "面对"]])
            early = "\n".join(chapter_text(cid) for cid in range(1, 5))
            if "高风险，不建议上线" in early:
                issues.append("Phase B 05 missing-cover warning appears before chapter 5")
            if any(token in final_text for token in ["小美走进旧办公室", "小美站在旧办公室", "小美坐在旧办公室"]):
                issues.append("Phase B 05 risks turning 小美 into a present-time co-protagonist")

        if name == "06_supporting_cast_codex_routing":
            expected_roles = {
                "小帅": ["唯一", "现实视角", "主角"],
                "小美": ["风险", "定时系统", "匿名邮件"],
                "阿强": ["数据清洗"],
                "老周": ["直属领导", "录音"],
                "林姐": ["善后"],
                "匿名邮件": ["邮件"],
                "灰度实验": ["灰度实验"],
            }
            for marker, role_tokens in expected_roles.items():
                if marker not in codex_text:
                    issues.append(f"Phase B 06 Codex missing marker: {marker}")
                elif not any(token in codex_text for token in role_tokens):
                    issues.append(f"Phase B 06 Codex role for {marker} is not distinct enough")
            require_text("Phase B 06 chapter 2", chapter_text(2), [["阿强"], ["林姐"], ["数据异常", "异常"]])
            require_text("Phase B 06 chapter 3", chapter_text(3), [["老周"], ["录音"], ["知道风险", "知情"]])
            require_text("Phase B 06 chapter 4", chapter_text(4), [["小美"], ["定时系统", "定时"], ["匿名邮件"]])
            for drift in ["阿强发来匿名邮件", "老周发来匿名邮件", "林姐发来匿名邮件"]:
                if drift in final_text:
                    issues.append(f"Phase B 06 character role drift: {drift}")
            if any(token in final_text for token in ["警方", "刑警", "侦查", "审讯"]):
                issues.append("Phase B 06 drifted into police investigation")

        if name == "07_dual_timeline_continuity":
            require_text("Phase B 07 chapter 1", chapter_text(1), [["旧会议室"], ["第一段录像", "第一段"], ["改方案", "方案"]])
            require_text("Phase B 07 chapter 2", chapter_text(2), [["第二段录像", "第二段"], ["小美"], ["反对", "不同意"]])
            require_text("Phase B 07 chapter 3", chapter_text(3), [["第三段录像", "第三段"], ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"]])
            require_text("Phase B 07 chapter 4", chapter_text(4), [["第四段录像", "第四段"], ["小美"], ["承担责任", "担责"], ["离职", "离开"]])
            early = "\n".join(chapter_text(cid) for cid in [1, 2])
            if any(token in early for token in ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"]):
                issues.append("Phase B 07 risk-warning deletion is revealed before chapter 3")
            for cid in range(1, 5):
                summary_after = chapter_text(cid, "03_summary_after.md")
                for marker in ["现在时间线", "过去揭示", "尚未知"]:
                    if marker not in summary_after:
                        issues.append(f"Phase B 07 chapter {cid} summary_after missing dual-timeline marker: {marker}")
                beats_text = chapter_text(cid, "01_beats.json")
                if "现在" not in beats_text or not any(token in beats_text for token in ["录像", "三年前", "过去"]):
                    issues.append(f"Phase B 07 chapter {cid} beats do not identify present action and past/video content")
            if "小美心想" in final_text or "小美觉得" in final_text:
                issues.append("Phase B 07 switches into 小美 internal POV")
        return issues

    def validate_beats_for_report(self, chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> list[str]:
        issues = []
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in summary:
                expected_stage = idx
        if self.test_case["name"] == "04_checkpoint_interaction_smoke":
            expected_stage = None
        for beat in beats if isinstance(beats, list) else []:
            text = beat.get("text", "")
            for idx, numeral in enumerate(stage_numerals, 1):
                if expected_stage and idx != expected_stage and f"第{numeral}阶段" in text:
                    issues.append(f"Chapter {chapter_id} beat {beat.get('beat_id')} stage mismatch with summary")
        return issues

    def write_report(self) -> None:
        artifact_missing = self.artifact_checks()
        trace_issues = self.trace_checks()
        content_issues = [] if (self.expected_validation_guard and self.validation_guard_triggered) else self.content_checks()
        checkpoint_issues = self.checkpoint_checks()
        genre_issues = self.genre_adapter_checks()
        if self.expected_validation_guard and self.validation_guard_triggered:
            genre_issues = []
            artifact_missing = [
                item
                for item in artifact_missing
                if not (
                    item.startswith("chapters/")
                    or item.startswith("manuscript/")
                    or item in {"manuscript/draft_full.md", "manuscript/final.md"}
                )
            ]
        critical = self.failures + [f"Missing or invalid artifact: {x}" for x in artifact_missing] + trace_issues + genre_issues + content_issues + checkpoint_issues
        passed = not critical
        lines = [
            "# Acceptance Report",
            "",
            "## Test Case",
            self.test_case["name"],
            "",
            "## Pass / Fail",
            "Pass" if passed else "Fail",
            "",
            "## Artifact Checks",
            "All required artifacts present." if not artifact_missing else "\n".join(f"- {x}" for x in artifact_missing),
            "",
            "## Workflow Trace Checks",
            "Trace checks passed." if not trace_issues else "\n".join(f"- {x}" for x in trace_issues),
            "",
            "## Prompt Assembly Checks",
            "Rendered prompts are recorded for workflow steps." if not genre_issues else "\n".join(f"- {x}" for x in genre_issues),
            "",
            "## Content Checks",
            "Validation guard triggered before prose generation as expected."
            if self.expected_validation_guard and self.validation_guard_triggered
            else ("Content checks passed." if not content_issues else "\n".join(f"- {x}" for x in content_issues)),
            "",
            "## Checkpoint Process Checks",
            "Checkpoint process checks passed." if not checkpoint_issues else "\n".join(f"- {x}" for x in checkpoint_issues),
            "",
            "## Critical Failures",
            "None" if not critical else "\n".join(f"- {x}" for x in critical),
            "",
            "## Major Issues",
            "None" if not self.major else "\n".join(f"- {x}" for x in self.major),
            "",
            "## Minor Issues",
            "None" if not self.minor else "\n".join(f"- {x}" for x in self.minor),
            "",
            "## Patch Recommendations",
            "No critical patch required." if passed else "Patch the critical failures above and rerun acceptance.",
            "",
        ]
        write_text(self.run_dir / "acceptance_report.md", "\n".join(lines))


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
