from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from workflow_core import (
    WorkflowContext,
    WorkflowState,
    append_text,
    extract_json,
    render_template,
    requested_chapter_count,
    sanitize_scene_beats,
    write_text,
    read_text,
)


@dataclass
class StepResult:
    value: Any = None


@dataclass
class BeatValidationResult:
    passed: bool
    issues: list[dict[str, Any]]


class WorkflowStep:
    workflow_step = ""

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        raise NotImplementedError


class ParseRequestStep(WorkflowStep):
    workflow_step = "parse_request"

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        raw = ctx.test_case["request"]
        output = ctx.model_step(
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
            ctx.major.append(f"parse_request did not return valid JSON: {exc}")
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
                "automation_mode": ctx.mode,
            }
        parsed["automation_mode"] = ctx.mode
        requested_chapters = requested_chapter_count(raw)
        if requested_chapters:
            parsed["target_chapters"] = requested_chapters
        ctx.genre_adapter_key = ctx.detect_genre_adapter(parsed)
        ctx.genre_adapter_text = ctx.render_genre_adapter(ctx.genre_adapter_key)
        parsed["genre_adapter"] = ctx.genre_adapter_key
        if not parsed.get("genre"):
            parsed["genre"] = ctx.genre_adapter_key
        return StepResult(parsed)


class BuildProjectBriefStep(WorkflowStep):
    workflow_step = "build_project_brief"

    def __init__(self, parsed: dict[str, Any]) -> None:
        self.parsed = parsed

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        brief = ctx.model_step(
            "build_project_brief",
            "02_build_project_brief.md",
            {
                "user_request": ctx.read_project("00_request.md"),
                "parsed_requirement": self.parsed,
                "genre_adapter": ctx.genre_adapter_text,
            },
            ["00_request.md"],
            ["01_project_brief.md"],
            ["User Request", "Parsed Requirement"] + ctx.genre_context(),
            1600,
            0.2,
            ctx.genre_extra(),
        )
        write_text(ctx.run_dir / "01_project_brief.md", brief.strip() + "\n")
        return StepResult(brief)


class BuildCodexStep(WorkflowStep):
    workflow_step = "build_codex"

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        codex_text = ctx.model_step(
            "build_codex",
            "03_build_codex.md",
            {"project_brief": ctx.read_project("01_project_brief.md"), "genre_adapter": ctx.genre_adapter_text},
            ["00_request.md", "01_project_brief.md"],
            ["02_codex.json"],
            ["Project Brief"] + ctx.genre_context(),
            2200,
            0.1,
            ctx.genre_extra(),
        )
        codex = ctx.parse_or_retry_json(
            codex_text,
            workflow_step="build_codex",
            input_files=["00_request.md", "01_project_brief.md"],
            output_files=["02_codex.json"],
            expected_shape='{"version": "0.1", "entries": [...]}',
        )
        codex = ctx.normalize_codex(codex)
        write_text(ctx.run_dir / "02_codex.json", json.dumps(codex, ensure_ascii=False, indent=2) + "\n")
        return StepResult(codex)


class GenerateOutlineStep(WorkflowStep):
    workflow_step = "generate_outline"

    def __init__(self, parsed: dict[str, Any]) -> None:
        self.parsed = parsed

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        global_codex, relevant_codex = ctx.select_codex(ctx.read_project("01_project_brief.md"))
        outline_text = ctx.model_step(
            "generate_outline",
            "04_generate_outline.md",
            {
                "project_brief": ctx.read_project("01_project_brief.md"),
                "global_codex": global_codex,
                "relevant_codex": relevant_codex,
                "target_chapters": self.parsed.get("target_chapters", 3),
                "genre_adapter": ctx.genre_adapter_text,
            },
            ["01_project_brief.md", "02_codex.json"],
            ["03_outline.json"],
            ["Project Brief", "Global Codex", "Relevant Codex"] + ctx.genre_context(),
            2200,
            0.2,
            ctx.genre_extra(),
        )
        outline = ctx.parse_or_retry_json(
            outline_text,
            workflow_step="generate_outline",
            input_files=["01_project_brief.md", "02_codex.json"],
            output_files=["03_outline.json"],
            expected_shape='[{"chapter_id": 1, "title": "", "summary": ""}]',
        )
        if not isinstance(outline, list):
            raise RuntimeError("Outline is not an array")
        write_text(ctx.run_dir / "03_outline.json", json.dumps(outline, ensure_ascii=False, indent=2) + "\n")
        return StepResult(outline)


class UserCheckpointStep(WorkflowStep):
    workflow_step = "user_checkpoint"

    def __init__(
        self,
        name: str,
        input_files: list[str],
        feedback_key: str | None = None,
        upstream_files_changed: list[str] | None = None,
        downstream_steps_invalidated: list[str] | None = None,
    ) -> None:
        self.name = name
        self.input_files = input_files
        self.feedback_key = feedback_key
        self.upstream_files_changed = upstream_files_changed
        self.downstream_steps_invalidated = downstream_steps_invalidated

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        feedback = ctx.checkpoint(
            self.name,
            self.input_files,
            self.feedback_key,
            self.upstream_files_changed,
            self.downstream_steps_invalidated,
        )
        return StepResult(feedback)


class GenerateChapterSummaryStep(WorkflowStep):
    workflow_step = "generate_chapter_summary"

    def __init__(self, chapter: dict[str, Any], chapter_id: int) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        chapter_dir = ctx.run_dir / "chapters" / f"chapter_{self.chapter_id:02d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        required = self.chapter.get("required_codex", [])
        g_codex, r_codex = ctx.select_codex(json.dumps(self.chapter, ensure_ascii=False), required)
        summary_inputs = ["01_project_brief.md", "02_codex.json", "03_outline.json"] + state.previous_summary_files
        summary = ctx.model_step(
            "generate_chapter_summary",
            "05_generate_chapter_summary.md",
            {
                "project_brief": ctx.read_project("01_project_brief.md"),
                "story_so_far": state.story_so_far,
                "outline_chapter": self.chapter,
                "global_codex": g_codex,
                "relevant_codex": r_codex,
                "genre_adapter": ctx.genre_adapter_text,
            },
            summary_inputs,
            [f"chapters/chapter_{self.chapter_id:02d}/00_summary.md"],
            ["Project Brief", "Story So Far", "Current Outline Chapter", "Global Codex", "Relevant Codex"] + ctx.genre_context(),
            1400,
            0.2,
            ctx.genre_extra(),
        )
        write_text(chapter_dir / "00_summary.md", summary.strip() + "\n")
        return StepResult(summary)


class GenerateSceneBeatsStep(WorkflowStep):
    workflow_step = "generate_scene_beats"

    def __init__(self, chapter: dict[str, Any], chapter_id: int, summary: str) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id
        self.summary = summary

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        required = self.chapter.get("required_codex", [])
        g_codex, r_codex = ctx.select_codex(json.dumps(self.chapter, ensure_ascii=False), required)
        beat_inputs = [
            "01_project_brief.md",
            "02_codex.json",
            f"chapters/chapter_{self.chapter_id:02d}/00_summary.md",
        ] + state.previous_summary_files
        beats_text = ctx.model_step(
            "generate_scene_beats",
            "06_generate_scene_beats.md",
            {
                "project_brief": ctx.read_project("01_project_brief.md"),
                "story_so_far": state.story_so_far,
                "chapter_summary": self.summary,
                "global_codex": g_codex,
                "relevant_codex": r_codex,
                "beat_count": ctx.beat_count,
                "genre_adapter": ctx.genre_adapter_text,
            },
            beat_inputs,
            [f"chapters/chapter_{self.chapter_id:02d}/01_beats.json"],
            ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex"] + ctx.genre_context(),
            2200,
            0.2,
            ctx.genre_extra(),
        )
        beats = ctx.parse_or_retry_json(
            beats_text,
            workflow_step="generate_scene_beats",
            input_files=beat_inputs,
            output_files=[f"chapters/chapter_{self.chapter_id:02d}/01_beats.json"],
            expected_shape='[{"beat_id": 1, "text": "", "purpose": "", "required_codex": [], "reveals": [], "must_not_reveal": []}]',
        )
        beats = sanitize_scene_beats(beats)
        write_text(
            ctx.run_dir / "chapters" / f"chapter_{self.chapter_id:02d}" / "01_beats.json",
            json.dumps(beats, ensure_ascii=False, indent=2) + "\n",
        )
        return StepResult(beats)


class ValidateSceneBeatsStep(WorkflowStep):
    workflow_step = "validate_scene_beats"

    def __init__(self, chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> None:
        self.chapter_id = chapter_id
        self.summary = summary
        self.beats = beats

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        issues: list[dict[str, Any]] = []
        if not isinstance(self.beats, list) or not self.beats:
            issues.append({"type": "empty_beats", "detail": "No beats generated", "severity": "critical"})
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in self.summary or f"第 {numeral} 阶段" in self.summary:
                expected_stage = idx
                break
        for beat in self.beats if isinstance(self.beats, list) else []:
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
            if "下一阶段" in text or ("第三阶段" in text and self.chapter_id == 2):
                if "第三阶段" not in self.summary:
                    issues.append({"beat_id": beat.get("beat_id"), "type": "chapter_scope_drift", "detail": text, "severity": "critical"})
        rendered = render_template(
            ctx.template("07_validate_scene_beats.md"),
            {
                "story_so_far": state.story_so_far,
                "chapter_summary": self.summary,
                "global_codex": ctx.select_codex(self.summary)[0],
                "relevant_codex": ctx.select_codex(self.summary)[1],
                "scene_beats": self.beats,
                "genre_adapter": ctx.genre_adapter_text,
            },
        )
        result = {"passed": not issues, "issues": issues}
        input_files = ["02_codex.json", f"chapters/chapter_{self.chapter_id:02d}/00_summary.md", f"chapters/chapter_{self.chapter_id:02d}/01_beats.json"]
        if state.story_so_far:
            input_files.extend(f"chapters/chapter_{idx:02d}/03_summary_after.md" for idx in range(1, self.chapter_id))
        ctx.record(
            "validate_scene_beats",
            "core_spec/prompts/07_validate_scene_beats.md",
            rendered,
            input_files,
            ["run_records/step_manifest.jsonl"],
            "success" if result["passed"] else "failed",
            ["Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Scene Beats"] + ctx.genre_context(),
            {"validation": result, **ctx.genre_extra()},
        )
        return StepResult(BeatValidationResult(passed=not issues, issues=issues))


class WriteBeatProseStep(WorkflowStep):
    workflow_step = "write_beat_prose"

    def __init__(self, chapter: dict[str, Any], chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id
        self.summary = summary
        self.beats = beats

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        chapter_dir = ctx.run_dir / "chapters" / f"chapter_{self.chapter_id:02d}"
        draft_parts: list[str] = [f"# Chapter {self.chapter_id}: {self.chapter.get('title', '')}\n"]
        text_before = ""
        write_text(chapter_dir / "02_draft.md", "")
        for beat in self.beats:
            current = json.dumps(beat, ensure_ascii=False, indent=2)
            g_codex, r_codex = ctx.select_codex(self.summary + "\n" + current, beat.get("required_codex", []))
            prose_inputs = [
                "01_project_brief.md",
                "02_codex.json",
                f"chapters/chapter_{self.chapter_id:02d}/00_summary.md",
                f"chapters/chapter_{self.chapter_id:02d}/01_beats.json",
            ] + state.previous_summary_files
            prose = ctx.model_step(
                "write_beat_prose",
                "08_write_beat_prose.md",
                {
                    "project_brief": ctx.read_project("01_project_brief.md"),
                    "story_so_far": state.story_so_far,
                    "chapter_summary": self.summary,
                    "global_codex": g_codex,
                    "relevant_codex": r_codex,
                    "text_before": text_before[-1800:],
                    "current_beat": current,
                    "additional_context": "",
                    "word_count": ctx.prose_word_count,
                    "genre_adapter": ctx.genre_adapter_text,
                },
                prose_inputs,
                [f"chapters/chapter_{self.chapter_id:02d}/02_draft.md"],
                ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Text Before", "Current Beat"] + ctx.genre_context(),
                1400,
                0.35,
                ctx.genre_extra(),
            )
            draft_parts.append(prose.strip() + "\n")
            text_before = "\n".join(draft_parts)
            write_text(chapter_dir / "02_draft.md", "\n".join(draft_parts).strip() + "\n")
        return StepResult(ctx.read_project(f"chapters/chapter_{self.chapter_id:02d}/02_draft.md"))


class SummarizeChapterStep(WorkflowStep):
    workflow_step = "summarize_chapter"

    def __init__(self, chapter_id: int) -> None:
        self.chapter_id = chapter_id

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        draft_path = ctx.current_chapter_draft_path(self.chapter_id)
        draft_rel = str(draft_path.relative_to(ctx.run_dir))
        summary_after = ctx.model_step(
            "summarize_chapter",
            "09_summarize_chapter.md",
            {
                "project_brief": ctx.read_project("01_project_brief.md"),
                "chapter_draft": ctx.read_project(draft_rel),
                "genre_adapter": ctx.genre_adapter_text,
            },
            ["01_project_brief.md", draft_rel],
            [f"chapters/chapter_{self.chapter_id:02d}/03_summary_after.md"],
            ["Project Brief", "Chapter Draft"] + ctx.genre_context(),
            900,
            0.1,
            ctx.genre_extra(),
        )
        if ctx.cjk_ratio(summary_after) < 0.15 and ctx.cjk_ratio(ctx.read_project("01_project_brief.md")) > 0.15:
            retry_prompt = (
                "请用中文重写下面的章节事实摘要。只输出中文摘要，不要解释，不要使用英文。\n\n"
                f"{summary_after}"
            )
            summary_after = ctx.client.complete(retry_prompt, max_tokens=900, temperature=0)
            ctx.record(
                "summarize_chapter_retry_language",
                "core_spec/prompts/09_summarize_chapter.md",
                retry_prompt,
                [draft_rel],
                [f"chapters/chapter_{self.chapter_id:02d}/03_summary_after.md"],
                "success",
                ["Language Retry", "Chapter Draft"],
            )
        write_text(ctx.run_dir / "chapters" / f"chapter_{self.chapter_id:02d}" / "03_summary_after.md", summary_after.strip() + "\n")
        return StepResult(summary_after)


class MergeManuscriptStep(WorkflowStep):
    workflow_step = "merge_manuscript"

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        drafts = sorted((ctx.run_dir / "chapters").glob("chapter_*/02_draft.md"))
        parts = [read_text(draft).strip() for draft in drafts]
        full = "\n\n".join(parts).strip() + "\n"
        write_text(ctx.run_dir / "manuscript" / "draft_full.md", full)
        write_text(ctx.run_dir / "manuscript" / "final.md", full)
        rendered = ctx.template("10_merge_manuscript.md") + "\n\n[Chapter Draft Paths]\n" + "\n".join(
            str(p.relative_to(ctx.run_dir)) for p in drafts
        )
        ctx.record(
            "merge_manuscript",
            "core_spec/prompts/10_merge_manuscript.md",
            rendered,
            [str(p.relative_to(ctx.run_dir)) for p in drafts],
            ["manuscript/draft_full.md", "manuscript/final.md"],
            "success",
            ["Chapter Drafts"],
        )
        return StepResult(full)
