# Step-Level Workflow Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the validated clean `longform-writing` full-skill generation path into step-level workflow modules while preserving current behavior.

**Architecture:** Keep `run_acceptance.py` as a thin CLI. Move shared IO/model/prompt/manifest helpers into `workflow_core.py`, clean writing actions into `workflow_steps.py`, orchestration into `workflow_runner.py`, and read-only acceptance/report logic into `acceptance_checker.py`. Use explicit step classes plus a shared `WorkflowContext`; do not add revision behavior or testcase-specific generation patches.

**Tech Stack:** Python standard library, existing Markdown prompt templates, existing `unittest` test suite, DeepSeek/mock provider abstraction, local file artifacts under `runs/`.

---

## File Structure

Create:

- `longform-writing/scripts/workflow_core.py`
  Shared infrastructure: model client, dotenv, file IO, prompt rendering, JSON extraction/repair, genre adapter helpers, `WorkflowContext`, `WorkflowState`, `WorkflowResult`.
- `longform-writing/scripts/workflow_steps.py`
  Step classes for clean V0 workflow: parse request, build brief, build codex, generate outline, chapter summary, beats, beat validation, prose, summary, merge, user checkpoint.
- `longform-writing/scripts/workflow_runner.py`
  Orchestrator that initializes a run, executes steps in order, tracks story state, stops on validation failure, returns `WorkflowResult`.
- `longform-writing/scripts/acceptance_checker.py`
  Read-only checker and report writer. Only allowed output mutation is `acceptance_report.md`.
- `longform-writing/tests/test_workflow_modularization.py`
  Fast tests for module boundaries, checker read-only behavior, context/manifest behavior, and thin CLI compatibility.

Modify:

- `longform-writing/scripts/run_acceptance.py`
  Reduce to CLI wiring and compatibility re-exports.
- `longform-writing/tests/test_v1_revision_helpers.py`
  Only if needed to keep imports passing after helper extraction. Prefer compatibility re-exports in `run_acceptance.py`.

Do not modify:

- `longform-writing/core_spec/prompts/*.md`
- `test_cases/*.md`
- content-specific acceptance criteria, except moving code into `acceptance_checker.py` unchanged.

---

## Task 1: Add Boundary Tests Before Refactor

**Files:**
- Create: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Create tests that define the target module contracts**

Add this file:

```python
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "longform-writing" / "scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowModularizationTests(unittest.TestCase):
    def test_core_exports_context_and_helpers(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")

        self.assertTrue(hasattr(core, "WorkflowContext"))
        self.assertTrue(hasattr(core, "WorkflowState"))
        self.assertTrue(hasattr(core, "WorkflowResult"))
        self.assertTrue(hasattr(core, "ModelClient"))
        self.assertTrue(hasattr(core, "parse_test_case"))
        self.assertTrue(hasattr(core, "render_template"))

    def test_context_records_manifest_and_prompt(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            ctx = core.WorkflowContext(
                skill_path=ROOT / "longform-writing",
                test_case={"name": "unit_case", "request": "写一个三章中文故事。", "markdown": "", "feedback": {}},
                run_dir=run_dir,
                provider="mock",
                mode="full_auto",
                beat_count=4,
                prose_word_count=260,
            )
            ctx.initialize_project()
            ctx.record(
                "unit_step",
                "unit_template",
                "rendered prompt",
                ["00_request.md"],
                ["01_project_brief.md"],
                "success",
                ["Unit Context"],
                {"genre_adapter": "general"},
            )

            manifest = run_dir / "run_records" / "step_manifest.jsonl"
            rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(rows[0]["workflow_step"], "unit_step")
            self.assertEqual(rows[0]["context_sections"], ["Unit Context"])
            prompt_path = run_dir / rows[0]["rendered_prompt"]
            self.assertEqual(prompt_path.read_text(encoding="utf-8"), "rendered prompt")

    def test_acceptance_checker_only_writes_report(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")
        checker_module = load_module("acceptance_checker", "acceptance_checker.py")

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "chapters" / "chapter_01").mkdir(parents=True)
            (run_dir / "manuscript").mkdir()
            (run_dir / "run_records" / "rendered_prompts").mkdir(parents=True)
            files = {
                "00_request.md": "写一个中文故事。\n",
                "01_project_brief.md": "Language: zh\n",
                "02_codex.json": "{\"entries\": []}\n",
                "03_outline.json": "[{\"chapter_id\": 1, \"title\": \"一\", \"summary\": \"开端\"}]\n",
                "chapters/chapter_01/00_summary.md": "第一章摘要。\n",
                "chapters/chapter_01/01_beats.json": "[{\"beat_id\": 1, \"text\": \"小明进入房间并发现信。\"}]\n",
                "chapters/chapter_01/02_draft.md": "小明进入房间。\n",
                "chapters/chapter_01/03_summary_after.md": "小明发现信。\n",
                "manuscript/draft_full.md": "小明进入房间。\n",
                "manuscript/final.md": "小明进入房间。\n",
            }
            for rel, text in files.items():
                path = run_dir / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            prompt = run_dir / "run_records" / "rendered_prompts" / "001_parse_request.md"
            prompt.write_text("prompt\n", encoding="utf-8")
            manifest = {
                "step_id": "001_parse_request",
                "workflow_step": "parse_request",
                "prompt_template": "core_spec/prompts/01_parse_request.md",
                "input_files": ["00_request.md"],
                "context_sections": ["User Request"],
                "rendered_prompt": "run_records/rendered_prompts/001_parse_request.md",
                "output_files": ["00_request.md"],
                "status": "success",
            }
            (run_dir / "run_records" / "step_manifest.jsonl").write_text(
                json.dumps(manifest, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            before = {rel: (run_dir / rel).read_text(encoding="utf-8") for rel in files}

            result = core.WorkflowResult(
                success=True,
                failures=[],
                major=[],
                minor=[],
                feedback_applied=[],
                expected_validation_guard=False,
                validation_guard_triggered=False,
                genre_adapter_key="general",
            )
            checker = checker_module.AcceptanceChecker(
                skill_path=ROOT / "longform-writing",
                test_case={"name": "unit_case", "request": "写一个中文故事。", "markdown": "", "feedback": {}},
                run_dir=run_dir,
                mode="full_auto",
                result=result,
            )
            checker.write_report()

            self.assertTrue((run_dir / "acceptance_report.md").exists())
            after = {rel: (run_dir / rel).read_text(encoding="utf-8") for rel in files}
            self.assertEqual(before, after)

    def test_run_acceptance_keeps_compatibility_exports(self) -> None:
        module = load_module("run_acceptance", "run_acceptance.py")

        self.assertTrue(hasattr(module, "AcceptanceRun"))
        self.assertTrue(hasattr(module, "ModelClient"))
        self.assertTrue(hasattr(module, "load_dotenv"))
        self.assertTrue(hasattr(module, "parse_test_case"))
        self.assertTrue(hasattr(module, "read_text"))
        self.assertTrue(hasattr(module, "render_template"))
        self.assertTrue(hasattr(module, "write_text"))
```

- [ ] **Step 2: Run the new tests and verify they fail for missing modules**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py -v
```

Expected: FAIL or ERROR because `workflow_core.py` and `acceptance_checker.py` do not exist yet.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add longform-writing/tests/test_workflow_modularization.py
git commit -m "test: define workflow modularization contracts"
```

Expected: commit succeeds with only the new test file staged.

---

## Task 2: Extract Core Infrastructure

**Files:**
- Create: `longform-writing/scripts/workflow_core.py`
- Modify: `longform-writing/scripts/run_acceptance.py`
- Test: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Create `workflow_core.py` with shared utilities and runtime types**

Move these existing definitions from `run_acceptance.py` into `workflow_core.py` without changing behavior:

```text
load_dotenv
read_text
write_text
append_text
slugify
section
first_code_block
parse_test_case
endpoint_from_base_url
ModelClient
extract_json
render_template
sanitize_scene_beats
requested_chapter_count
BASE_ADAPTER
GENRE_ADAPTERS
```

Add these runtime dataclasses:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkflowResult:
    success: bool
    failures: list[str] = field(default_factory=list)
    major: list[str] = field(default_factory=list)
    minor: list[str] = field(default_factory=list)
    feedback_applied: list[str] = field(default_factory=list)
    expected_validation_guard: bool = False
    validation_guard_triggered: bool = False
    genre_adapter_key: str = "general"


@dataclass
class WorkflowState:
    parsed_requirement: dict[str, Any] = field(default_factory=dict)
    outline: list[dict[str, Any]] = field(default_factory=list)
    story_so_far: str = ""
    previous_summary_files: list[str] = field(default_factory=list)

    def add_summary(self, chapter_id: int, summary_after: str) -> None:
        self.story_so_far += f"\n\nChapter {chapter_id} summary:\n{summary_after.strip()}\n"
        self.previous_summary_files.append(f"chapters/chapter_{chapter_id:02d}/03_summary_after.md")
```

Add `WorkflowContext` with these methods:

```python
class WorkflowContext:
    def __init__(
        self,
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ) -> None:
        self.skill_path = skill_path
        self.test_case = test_case
        self.run_dir = run_dir
        self.provider = provider
        self.mode = mode
        self.beat_count = beat_count
        self.prose_word_count = prose_word_count
        self.client = ModelClient(provider)
        self.step_no = 0
        self.failures: list[str] = []
        self.major: list[str] = []
        self.minor: list[str] = []
        self.feedback_applied: list[str] = []
        self.expected_validation_guard = "beat_validation_guard" in test_case["name"]
        self.validation_guard_triggered = False
        self.genre_adapter_key = "general"
        self.genre_adapter_text = self.render_genre_adapter("general")

    @property
    def manifest(self) -> Path:
        return self.run_dir / "run_records" / "step_manifest.jsonl"

    @property
    def prompts_dir(self) -> Path:
        return self.run_dir / "run_records" / "rendered_prompts"

    def template(self, name: str) -> str:
        return read_text(self.skill_path / "core_spec" / "prompts" / name)

    def initialize_project(self) -> None:
        template_dir = self.skill_path / "templates" / "writing_project_v0"
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        shutil.copytree(template_dir, self.run_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        write_text(self.manifest, "")
        write_text(self.run_dir / "00_request.md", self.test_case["request"].strip() + "\n")
        append_text(self.run_dir / "writing_log.md", f"\n- Initialized run from {self.test_case['name']}.\n")

    def record(
        self,
        workflow_step: str,
        prompt_template: str,
        rendered_prompt: str,
        input_files: list[str],
        output_files: list[str],
        status: str = "success",
        context_sections: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.step_no += 1
        step_id = f"{self.step_no:03d}_{workflow_step}"
        prompt_path = self.prompts_dir / f"{step_id}.md"
        write_text(prompt_path, rendered_prompt)
        entry = {
            "step_id": step_id,
            "workflow_step": workflow_step,
            "prompt_template": prompt_template,
            "input_files": input_files,
            "context_sections": context_sections or [],
            "rendered_prompt": str(prompt_path.relative_to(self.run_dir)),
            "output_files": output_files,
            "status": status,
        }
        if extra:
            entry.update(extra)
        append_text(self.manifest, json.dumps(entry, ensure_ascii=False) + "\n")
```

Also move these existing `AcceptanceRun` helper methods into `WorkflowContext` unchanged except replacing `self` with context state:

```text
detect_genre_adapter
render_genre_adapter
genre_extra
genre_context
model_step
parse_or_retry_json
read_project
codex_entries
select_codex
render_codex
checkpoint
checkpoint_artifact_summary
normalize_codex
apply_outline_feedback
apply_brief_feedback
cjk_ratio
current_chapter_draft_path
```

Define `current_chapter_draft_path` as:

```python
def current_chapter_draft_path(self, chapter_id: int) -> Path:
    return self.run_dir / "chapters" / f"chapter_{chapter_id:02d}" / "02_draft.md"
```

- [ ] **Step 2: Update `run_acceptance.py` to import core names**

At the top of `run_acceptance.py`, import and re-export these names:

```python
from workflow_core import (  # noqa: F401
    GENRE_ADAPTERS,
    ModelClient,
    WorkflowContext,
    WorkflowResult,
    WorkflowState,
    append_text,
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
```

Remove duplicate definitions from `run_acceptance.py` after imports are confirmed.

- [ ] **Step 3: Run core contract tests**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py::WorkflowModularizationTests.test_core_exports_context_and_helpers -v
```

Expected: PASS.

- [ ] **Step 4: Run existing helper tests**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected: existing helper tests still pass.

- [ ] **Step 5: Commit core extraction**

Run:

```bash
git add longform-writing/scripts/workflow_core.py longform-writing/scripts/run_acceptance.py longform-writing/tests/test_workflow_modularization.py
git commit -m "refactor: extract workflow core infrastructure"
```

---

## Task 3: Extract Read-Only Acceptance Checker

**Files:**
- Create: `longform-writing/scripts/acceptance_checker.py`
- Modify: `longform-writing/scripts/run_acceptance.py`
- Test: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Create `AcceptanceChecker`**

Move these methods from `AcceptanceRun` into `AcceptanceChecker`:

```text
artifact_checks
trace_checks
phase_b_trace_checks
checkpoint_checks
genre_adapter_checks
content_checks
phase_b_content_checks
validate_beats_for_report
write_report
```

Use this class shape:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from workflow_core import GENRE_ADAPTERS, WorkflowResult, read_text, write_text


class AcceptanceChecker:
    def __init__(
        self,
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        mode: str,
        result: WorkflowResult,
    ) -> None:
        self.skill_path = skill_path
        self.test_case = test_case
        self.run_dir = run_dir
        self.mode = mode
        self.result = result
        self.failures = result.failures
        self.major = result.major
        self.minor = result.minor
        self.expected_validation_guard = result.expected_validation_guard
        self.validation_guard_triggered = result.validation_guard_triggered
        self.genre_adapter_key = result.genre_adapter_key

    @property
    def manifest(self) -> Path:
        return self.run_dir / "run_records" / "step_manifest.jsonl"

    def read_project(self, rel: str) -> str:
        path = self.run_dir / rel
        return read_text(path) if path.exists() else ""

    def cjk_ratio(self, text: str) -> float:
        chars = [ch for ch in text if not ch.isspace()]
        if not chars:
            return 0
        cjk = sum(1 for ch in chars if "\u4e00" <= ch <= "\u9fff")
        return cjk / len(chars)
```

Keep logic unchanged when moving checks. The checker must not import `ModelClient` and must not call workflow steps.

- [ ] **Step 2: Wire `run_acceptance.py` to use `AcceptanceChecker.write_report()`**

Temporarily keep the current monolithic `AcceptanceRun.run()` if steps are not extracted yet, but replace `AcceptanceRun.write_report()` with:

```python
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
```

Import:

```python
from acceptance_checker import AcceptanceChecker
```

- [ ] **Step 3: Run checker read-only test**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py::WorkflowModularizationTests.test_acceptance_checker_only_writes_report -v
```

Expected: PASS. The test confirms report writing does not mutate generation artifacts.

- [ ] **Step 4: Run existing helper tests**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected: PASS.

- [ ] **Step 5: Commit checker extraction**

Run:

```bash
git add longform-writing/scripts/acceptance_checker.py longform-writing/scripts/run_acceptance.py longform-writing/tests/test_workflow_modularization.py
git commit -m "refactor: extract read-only acceptance checker"
```

---

## Task 4: Extract Workflow Step Classes

**Files:**
- Create: `longform-writing/scripts/workflow_steps.py`
- Modify: `longform-writing/scripts/run_acceptance.py`
- Test: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Create base step result classes**

Add to `workflow_steps.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_core import (
    WorkflowContext,
    WorkflowState,
    append_text,
    render_template,
    sanitize_scene_beats,
    write_text,
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
```

- [ ] **Step 2: Move top-level generation steps**

Move the current logic from `AcceptanceRun` into these classes:

```text
ParseRequestStep
BuildProjectBriefStep
BuildCodexStep
GenerateOutlineStep
```

Preserve prompt names, input file lists, output file lists, context sections, token counts, and temperatures.

The step constructors should be:

```python
class ParseRequestStep(WorkflowStep):
    workflow_step = "parse_request"

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        ...


class BuildProjectBriefStep(WorkflowStep):
    workflow_step = "build_project_brief"

    def __init__(self, parsed: dict[str, Any]) -> None:
        self.parsed = parsed

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        ...
```

`ParseRequestStep` must still apply generic fallback only:

```python
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
```

- [ ] **Step 3: Move chapter-level generation steps**

Move the current chapter-loop logic into:

```text
GenerateChapterSummaryStep
GenerateSceneBeatsStep
ValidateSceneBeatsStep
WriteBeatProseStep
SummarizeChapterStep
MergeManuscriptStep
UserCheckpointStep
```

Use constructor signatures:

```python
class GenerateChapterSummaryStep(WorkflowStep):
    def __init__(self, chapter: dict[str, Any], chapter_id: int) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id


class GenerateSceneBeatsStep(WorkflowStep):
    def __init__(self, chapter: dict[str, Any], chapter_id: int, summary: str) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id
        self.summary = summary


class ValidateSceneBeatsStep(WorkflowStep):
    def __init__(self, chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> None:
        self.chapter_id = chapter_id
        self.summary = summary
        self.beats = beats


class WriteBeatProseStep(WorkflowStep):
    def __init__(self, chapter: dict[str, Any], chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> None:
        self.chapter = chapter
        self.chapter_id = chapter_id
        self.summary = summary
        self.beats = beats
```

`SummarizeChapterStep` must use:

```python
chapter_draft_path = ctx.current_chapter_draft_path(self.chapter_id)
chapter_draft = ctx.read_project(str(chapter_draft_path.relative_to(ctx.run_dir)))
```

This preserves current behavior while allowing future revised draft routing.

- [ ] **Step 4: Keep validation as a generation gate**

`ValidateSceneBeatsStep.run()` should return:

```python
StepResult(BeatValidationResult(passed=not issues, issues=issues))
```

If validation fails:

```python
ctx.record(
    "validate_scene_beats",
    "core_spec/prompts/07_validate_scene_beats.md",
    rendered,
    input_files,
    ["run_records/step_manifest.jsonl"],
    "failed",
    ["Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Scene Beats"] + ctx.genre_context(),
    {"validation": {"passed": False, "issues": issues}, **ctx.genre_extra()},
)
```

Use the same stage-drift validation logic currently in `AcceptanceRun.validate_beats`.

- [ ] **Step 5: Run syntax checks**

Run:

```bash
python3 -m py_compile longform-writing/scripts/workflow_steps.py longform-writing/scripts/workflow_core.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Commit step extraction**

Run:

```bash
git add longform-writing/scripts/workflow_steps.py longform-writing/scripts/run_acceptance.py
git commit -m "refactor: extract clean workflow steps"
```

---

## Task 5: Add WorkflowRunner Orchestrator

**Files:**
- Create: `longform-writing/scripts/workflow_runner.py`
- Modify: `longform-writing/scripts/run_acceptance.py`
- Test: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Create `WorkflowRunner`**

Add `workflow_runner.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_core import WorkflowContext, WorkflowResult, WorkflowState, append_text
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
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ) -> None:
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
        UserCheckpointStep(
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
        ).run(ctx, state)

        BuildCodexStep().run(ctx, state)
        outline = GenerateOutlineStep(parsed).run(ctx, state).value
        state.outline = outline

        UserCheckpointStep(
            name="story_plan_alignment",
            input_files=["01_project_brief.md", "02_codex.json", "03_outline.json"],
            feedback_key="checkpoint_2",
            upstream_files_changed=["03_outline.json"],
            downstream_steps_invalidated=["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        ).run(ctx, state)

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
                UserCheckpointStep(
                    name="first_chapter_direction_check",
                    input_files=[
                        f"chapters/chapter_{chapter_id:02d}/02_draft.md",
                        f"chapters/chapter_{chapter_id:02d}/03_summary_after.md",
                    ],
                    feedback_key="checkpoint_3",
                    upstream_files_changed=["01_project_brief.md"],
                    downstream_steps_invalidated=["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
                ).run(ctx, state)

        MergeManuscriptStep().run(ctx, state)
        return self.result(success=True)
```

The concrete implementation may adjust imports to match final names, but must preserve this explicit orchestration shape.

- [ ] **Step 2: Replace `AcceptanceRun.run()` with runner delegation**

In `run_acceptance.py`, keep a compatibility wrapper:

```python
class AcceptanceRun:
    def __init__(
        self,
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ) -> None:
        self.skill_path = skill_path
        self.test_case = test_case
        self.run_dir = run_dir
        self.provider = provider
        self.mode = mode
        self.beat_count = beat_count
        self.prose_word_count = prose_word_count
        self.result: WorkflowResult | None = None

    def run(self) -> None:
        runner = WorkflowRunner(
            self.skill_path,
            self.test_case,
            self.run_dir,
            self.provider,
            self.mode,
            self.beat_count,
            self.prose_word_count,
        )
        self.result = runner.run()
        AcceptanceChecker(
            self.skill_path,
            self.test_case,
            self.run_dir,
            self.mode,
            self.result,
        ).write_report()

    @property
    def failures(self) -> list[str]:
        if self.result is None:
            return []
        return self.result.failures

    def write_report(self) -> None:
        result = self.result or WorkflowResult(success=False, failures=["Runner did not produce a result."])
        AcceptanceChecker(self.skill_path, self.test_case, self.run_dir, self.mode, result).write_report()
```

- [ ] **Step 3: Run compatibility export test**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py::WorkflowModularizationTests.test_run_acceptance_keeps_compatibility_exports -v
```

Expected: PASS.

- [ ] **Step 4: Run syntax checks**

Run:

```bash
python3 -m py_compile \
  longform-writing/scripts/run_acceptance.py \
  longform-writing/scripts/workflow_core.py \
  longform-writing/scripts/workflow_steps.py \
  longform-writing/scripts/workflow_runner.py \
  longform-writing/scripts/acceptance_checker.py
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit runner extraction**

Run:

```bash
git add longform-writing/scripts/workflow_runner.py longform-writing/scripts/run_acceptance.py
git commit -m "refactor: orchestrate workflow with step runner"
```

---

## Task 6: Reduce `run_acceptance.py` to Thin CLI

**Files:**
- Modify: `longform-writing/scripts/run_acceptance.py`
- Test: `longform-writing/tests/test_workflow_modularization.py`

- [ ] **Step 1: Keep only imports, `AcceptanceRun`, and `main()`**

After extraction, `run_acceptance.py` should contain:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from acceptance_checker import AcceptanceChecker
from workflow_core import (  # noqa: F401
    ModelClient,
    WorkflowResult,
    load_dotenv,
    parse_test_case,
    read_text,
    render_template,
    slugify,
    write_text,
)
from workflow_runner import WorkflowRunner
```

The `main()` function should:

```python
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
    start = time.monotonic()
    runner = WorkflowRunner(
        args.skill_path.resolve(),
        test_case,
        output_dir.resolve(),
        args.provider,
        args.mode,
        args.beat_count,
        args.prose_word_count,
    )
    try:
        result = runner.run()
        AcceptanceChecker(args.skill_path.resolve(), test_case, output_dir.resolve(), args.mode, result).write_report()
    except Exception as exc:
        result = WorkflowResult(success=False, failures=[f"Runner exception: {exc}"])
        try:
            AcceptanceChecker(args.skill_path.resolve(), test_case, output_dir.resolve(), args.mode, result).write_report()
        except Exception:
            pass
        print(f"Acceptance run failed: {exc}", file=sys.stderr)
        return 1

    elapsed = time.monotonic() - start
    print(f"Acceptance run complete: {output_dir.resolve()}")
    print(f"elapsed_sec={elapsed:.2f}")
    report = output_dir.resolve() / "acceptance_report.md"
    if report.exists():
        print(report)
    return 0
```

Keep `AcceptanceRun` compatibility wrapper below imports or above `main()`.

- [ ] **Step 2: Ensure no large workflow/checker methods remain in `run_acceptance.py`**

Run:

```bash
rg -n "def artifact_checks|def trace_checks|def content_checks|def phase_b_content_checks|def parse_request|def validate_beats|def merge_manuscript" longform-writing/scripts/run_acceptance.py
```

Expected: no matches.

- [ ] **Step 3: Run modularization tests**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit thin CLI**

Run:

```bash
git add longform-writing/scripts/run_acceptance.py longform-writing/tests/test_workflow_modularization.py
git commit -m "refactor: make acceptance runner a thin CLI"
```

---

## Task 7: Full Static Verification

**Files:**
- No new files
- Verify all changed Python modules

- [ ] **Step 1: Run py_compile**

Run:

```bash
python3 -m py_compile \
  longform-writing/scripts/run_acceptance.py \
  longform-writing/scripts/workflow_core.py \
  longform-writing/scripts/workflow_steps.py \
  longform-writing/scripts/workflow_runner.py \
  longform-writing/scripts/acceptance_checker.py \
  longform-writing/scripts/audit_clean_generation.py
```

Expected: no output and exit code 0.

- [ ] **Step 2: Run all existing V1 helper tests**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected: all tests pass.

- [ ] **Step 3: Run modularization tests**

Run:

```bash
python3 -m unittest longform-writing/tests/test_workflow_modularization.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Run diff whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit verification-only cleanup if needed**

If previous steps required small import or formatting fixes, commit them:

```bash
git add longform-writing/scripts longform-writing/tests
git commit -m "test: verify modular workflow split"
```

If no files changed, do not create an empty commit.

---

## Task 8: Clean Smoke Run

**Files:**
- Uses existing `test_cases/13_clean_generation_independence_smoke.md`
- Writes run output under `runs/13_clean_generation_modular_smoke`

- [ ] **Step 1: Run full skill through thin CLI**

Run:

```bash
python3 longform-writing/scripts/run_acceptance.py \
  --test-case test_cases/13_clean_generation_independence_smoke.md \
  --output-dir runs/13_clean_generation_modular_smoke \
  --provider deepseek
```

Expected:

```text
Acceptance run complete: .../runs/13_clean_generation_modular_smoke
elapsed_sec=<number>
.../runs/13_clean_generation_modular_smoke/acceptance_report.md
```

The acceptance report may pass or fail based on content checks. This task only fails if the workflow crashes, required artifacts are missing, manifest semantics break, or old testcase contamination reappears.

- [ ] **Step 2: Run clean generation audit**

Run:

```bash
python3 longform-writing/scripts/audit_clean_generation.py \
  --run-dir runs/13_clean_generation_modular_smoke
```

Expected:

```text
Clean generation audit passed: runs/13_clean_generation_modular_smoke/clean_generation_audit.md
```

- [ ] **Step 3: Inspect manifest for step-level preservation**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
manifest = Path("runs/13_clean_generation_modular_smoke/run_records/step_manifest.jsonl")
rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
steps = [row["workflow_step"] for row in rows]
required = [
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
missing = [step for step in required if step not in steps]
print("missing=", missing)
print("row_count=", len(rows))
PY
```

Expected:

```text
missing= []
row_count= <positive integer>
```

- [ ] **Step 4: Commit smoke report artifacts only if project convention allows tracked run outputs**

Check whether `runs/` outputs are tracked:

```bash
git check-ignore -v runs/13_clean_generation_modular_smoke || true
git ls-files runs | head
```

Expected handling:

- If `runs/` is ignored or prior convention is not to commit run outputs, do not commit smoke outputs.
- If prior convention tracks specific run reports, commit only lightweight reports such as `acceptance_report.md` and `clean_generation_audit.md`, not full generated manuscripts.

---

## Task 9: Final Review and Handoff

**Files:**
- No required new files

- [ ] **Step 1: Confirm no testcase-specific generation patch was introduced**

Run:

```bash
rg -n "ensure_phase_c|finalize_chapter_draft|redact_protected_reveals|clue_state_for_chapter|旧录音装置|蓝色钥匙|缺失封面|旧借书卡|高风险，不建议上线|小帅|小美|阿强|老周|林姐" \
  longform-writing/scripts/workflow_core.py \
  longform-writing/scripts/workflow_steps.py \
  longform-writing/scripts/workflow_runner.py
```

Expected: no matches in generation modules.

- [ ] **Step 2: Confirm testcase-specific strings are checker-only if still present**

Run:

```bash
rg -n "旧录音装置|蓝色钥匙|缺失封面|旧借书卡|高风险，不建议上线|小帅|小美|阿强|老周|林姐" longform-writing/scripts
```

Expected:

- Matches may appear in `acceptance_checker.py` read-only content checks.
- Matches must not appear in `workflow_core.py`, `workflow_steps.py`, or `workflow_runner.py`.

- [ ] **Step 3: Summarize final diff**

Run:

```bash
git status --short
git log --oneline -8
```

Expected:

- Worktree contains only expected untracked run outputs, if any.
- Recent commits show the modularization tasks.

- [ ] **Step 4: Final response**

Report:

```text
- modules created
- behavior preserved checks run
- clean smoke result
- whether old acceptance content checks passed or failed
- any remaining known issue, especially genre routing false positives if still observed
```

Do not claim text quality improved. This task is architecture-only.

---

## Self-Review Notes

Spec coverage:

- Step-level modular workflow is covered by Tasks 4 and 5.
- Thin `run_acceptance.py` is covered by Task 6.
- Read-only checker separation is covered by Task 3.
- Clean behavior preservation is covered by Tasks 7 and 8.
- No testcase patch regression is covered by Task 9.
- Future revision insertion space is covered by `WorkflowContext.current_chapter_draft_path` and explicit step classes.

Scope check:

- This plan does not implement revision loop, prompt changes, text-quality improvements, or acceptance pass-rate patches.
- The plan is one implementable refactor and does not require decomposition into separate projects.

Type consistency:

- `WorkflowContext`, `WorkflowState`, `WorkflowResult`, `AcceptanceChecker`, and `WorkflowRunner` are named consistently across tasks.
- The `WorkflowResult` fields match what `AcceptanceChecker` consumes.

Placeholder scan:

- The plan does not use incomplete-marker tokens or unspecified future steps.
- Large moves are described as exact method extractions from existing code and paired with concrete target class shapes and tests.
