from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_core import WorkflowContext, WorkflowResult, WorkflowState, append_text, write_text
from workflow_steps import (
    BuildCodexStep,
    BuildProjectBriefStep,
    GenerateChapterSummaryStep,
    GenerateOutlineStep,
    GenerateSceneBeatsStep,
    MergeManuscriptStep,
    ParseRequestStep,
    SummarizeChapterStep,
    UserCheckpointStep,
    ValidateSceneBeatsStep,
    WriteBeatProseStep,
)


class WorkflowRunner:
    def __init__(
        self,
        skill_path: Path | None = None,
        test_case: dict[str, Any] | None = None,
        run_dir: Path | None = None,
        provider: str = "mock",
        mode: str = "full_auto",
        beat_count: int = 4,
        prose_word_count: int = 260,
        context: WorkflowContext | None = None,
    ) -> None:
        if context is not None:
            self.ctx = context
        else:
            if skill_path is None or test_case is None or run_dir is None:
                raise ValueError("skill_path, test_case, and run_dir are required without context")
            self.ctx = WorkflowContext(
                skill_path=skill_path,
                test_case=test_case,
                run_dir=run_dir,
                provider=provider,
                mode=mode,
                beat_count=beat_count,
                prose_word_count=prose_word_count,
            )
        self.state = WorkflowState()

    def result(self, success: bool = True) -> WorkflowResult:
        return WorkflowResult(
            success=success and not self.ctx.failures,
            failures=list(self.ctx.failures),
            major=list(self.ctx.major),
            minor=list(self.ctx.minor),
            feedback_applied=list(self.ctx.feedback_applied),
            expected_validation_guard=self.ctx.expected_validation_guard,
            validation_guard_triggered=self.ctx.validation_guard_triggered,
            genre_adapter_key=self.ctx.genre_adapter_key,
        )

    def run(self) -> WorkflowResult:
        ctx = self.ctx
        state = self.state
        ctx.initialize_project()

        parsed = ParseRequestStep().run(ctx, state).value
        state.parsed_requirement = parsed

        BuildProjectBriefStep(parsed).run(ctx, state)
        feedback = UserCheckpointStep(
            name="requirement_alignment",
            input_files=["01_project_brief.md"],
            feedback_key="checkpoint_1",
            upstream_files_changed=["01_project_brief.md"],
            downstream_steps_invalidated=[
                "build_codex",
                "generate_outline",
                "generate_chapter_summary",
                "generate_scene_beats",
                "write_beat_prose",
            ],
        ).run(ctx, state).value
        if feedback:
            write_text(ctx.run_dir / "01_project_brief.md", ctx.apply_brief_feedback(ctx.read_project("01_project_brief.md"), feedback))
            ctx.feedback_applied.append("checkpoint_1")

        BuildCodexStep().run(ctx, state)
        outline = GenerateOutlineStep(parsed).run(ctx, state).value
        state.outline = outline

        feedback = UserCheckpointStep(
            name="story_plan_alignment",
            input_files=["01_project_brief.md", "02_codex.json", "03_outline.json"],
            feedback_key="checkpoint_2",
            upstream_files_changed=["03_outline.json"],
            downstream_steps_invalidated=["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        ).run(ctx, state).value
        if feedback:
            state.outline = ctx.apply_outline_feedback(state.outline, feedback)
            write_text(ctx.run_dir / "03_outline.json", json.dumps(state.outline, ensure_ascii=False, indent=2) + "\n")
            append_text(ctx.run_dir / "writing_log.md", "- Story plan feedback should constrain downstream generation.\n")
            ctx.feedback_applied.append("checkpoint_2")

        for chapter in state.outline:
            chapter_id = int(chapter.get("chapter_id", len(state.previous_summary_files) + 1))
            summary = GenerateChapterSummaryStep(chapter, chapter_id).run(ctx, state).value
            beats = GenerateSceneBeatsStep(chapter, chapter_id, summary).run(ctx, state).value
            validation = ValidateSceneBeatsStep(chapter_id, summary, beats).run(ctx, state).value
            if not validation.passed:
                if ctx.expected_validation_guard:
                    ctx.validation_guard_triggered = True
                    append_text(ctx.run_dir / "writing_log.md", "\n- Validation guard triggered as expected before prose generation.\n")
                else:
                    ctx.failures.append(f"Beat validation failed for chapter {chapter_id}: {validation.issues}")
                return self.result(success=False)

            WriteBeatProseStep(chapter, chapter_id, summary, beats).run(ctx, state)
            summary_after = SummarizeChapterStep(chapter_id).run(ctx, state).value
            state.add_summary(chapter_id, summary_after)

            if chapter_id == 1:
                feedback = UserCheckpointStep(
                    name="first_chapter_direction_check",
                    input_files=[
                        f"chapters/chapter_{chapter_id:02d}/02_draft.md",
                        f"chapters/chapter_{chapter_id:02d}/03_summary_after.md",
                    ],
                    feedback_key="checkpoint_3",
                    upstream_files_changed=["01_project_brief.md"],
                    downstream_steps_invalidated=["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
                ).run(ctx, state).value
                if feedback:
                    append_text(ctx.run_dir / "01_project_brief.md", f"\n## First Chapter Direction Feedback\n{feedback}\n")
                    ctx.feedback_applied.append("checkpoint_3")

        MergeManuscriptStep().run(ctx, state)
        return self.result(success=True)
