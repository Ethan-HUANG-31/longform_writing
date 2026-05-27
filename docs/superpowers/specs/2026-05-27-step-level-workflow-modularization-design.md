# Step-Level Workflow Modularization Design

## 1. Purpose

This design splits the already validated clean `longform-writing` generation path into small, composable workflow steps.

The goal is not to add writing capability, improve prose quality, introduce revision loops, or restore old testcase-specific patches. The goal is to preserve the current clean full-skill behavior while making the workflow easy to inspect, test, and extend with later revision steps.

Target workflow:

```text
User Request
-> Project Brief
-> Codex
-> Outline
-> Chapter Summary
-> Scene Beats
-> Beat Validation
-> Beat Prose
-> Summary After
-> Manuscript
```

The implementation should move this from a large `AcceptanceRun.run()` method into step-level modules with one clear orchestrator.

## 2. Confirmed Decisions

- Use the step class approach with a shared `WorkflowContext`.
- Keep the modules under `longform-writing/scripts/` for this iteration.
- Treat this as a V0 clean full-skill refactor only.
- Do not optimize prompts, text quality, genre routing, or acceptance pass rate in this task.
- Do not add revision loop behavior in this task.
- Do not design around `run_v1_revision_loop.py` compatibility as a blocker; V1 can be reconnected later on top of the modular workflow.
- Keep `run_acceptance.py` as the CLI entrypoint, but make it thin.
- Keep AcceptanceChecker read-only except for writing `acceptance_report.md`.

## 3. Non-Goals

This task does not implement:

- outline revision;
- beat revision;
- chapter revision;
- manuscript revision;
- judge/rubric changes;
- prompt rewrites;
- package restructuring;
- YAML workflow configuration;
- dynamic plugin registries;
- new testcase-specific logic;
- fixes for old acceptance failures caused by the clean generation cleanup.

If old cases fail after the split, that is acceptable unless the failure is caused by changed workflow behavior, missing artifacts, broken manifest records, or newly introduced contamination.

## 4. Current Problem

`longform-writing/scripts/run_acceptance.py` currently contains three responsibilities in one `AcceptanceRun` class:

```text
1. generation infrastructure
   ModelClient, prompt rendering, JSON repair, file IO, manifest recording

2. clean full-skill workflow
   parse request, build brief, build codex, outline, chapters, prose, summaries, merge

3. acceptance checking
   artifact checks, trace checks, genre checks, content checks, report writing
```

This makes the current flow hard to extend. Adding revision at the outline, beat, chapter, or manuscript level would require editing a large monolithic method and risks mixing generation logic with evaluation logic again.

The split should make the generation path look like an explicit sequence of steps while preserving the artifact and manifest contract that has already been validated by the clean generation audit.

## 5. Proposed Files

```text
longform-writing/scripts/
  workflow_core.py
  workflow_steps.py
  workflow_runner.py
  acceptance_checker.py
  run_acceptance.py
```

### 5.1 `workflow_core.py`

Owns shared infrastructure used by workflow steps.

Responsibilities:

- `ModelClient`
- dotenv loading
- `read_text`, `write_text`, `append_text`
- `slugify`, `section`, `first_code_block`, `parse_test_case`
- `extract_json`, `render_template`, `sanitize_scene_beats`
- genre adapter constants and rendering
- request chapter-count detection
- `WorkflowContext`
- `WorkflowRecorder`
- shared helpers such as `select_codex`, `render_codex`, `parse_or_retry_json`, and `cjk_ratio`

`WorkflowContext` should hold the runtime state that steps need:

```text
skill_path
test_case
run_dir
provider
mode
beat_count
prose_word_count
client
recorder
genre_adapter_key
genre_adapter_text
failures
major
minor
feedback_applied
expected_validation_guard
validation_guard_triggered
```

It should also expose small helper methods so steps do not duplicate IO and prompt-rendering code.

### 5.2 `workflow_steps.py`

Owns step classes for the clean V0 writing workflow.

Base shape:

```python
class WorkflowStep:
    workflow_step: str

    def run(self, ctx: WorkflowContext, state: WorkflowState) -> StepResult:
        ...
```

The implementation can stay lightweight. It does not need a full framework, registry, or dependency injection system.

Initial concrete steps:

```text
ParseRequestStep
BuildProjectBriefStep
BuildCodexStep
GenerateOutlineStep
GenerateChapterSummaryStep
GenerateSceneBeatsStep
ValidateSceneBeatsStep
WriteBeatProseStep
SummarizeChapterStep
MergeManuscriptStep
UserCheckpointStep
```

`UserCheckpointStep` remains generic milestone-review behavior. It may write feedback into `writing_log.md` and update upstream artifacts only according to current generic feedback handling. It must not contain testcase-specific story patches.

`ValidateSceneBeatsStep` remains part of generation because it gates prose generation and records validation in the manifest. It should not be moved to AcceptanceChecker.

### 5.3 `workflow_runner.py`

Owns orchestration.

Responsibilities:

- initialize the run directory from the template;
- write `00_request.md`;
- run top-level steps in order;
- maintain story state across chapters;
- call chapter-level steps for each outline chapter;
- stop early if beat validation fails;
- merge the manuscript;
- return a `WorkflowResult` describing state needed by the checker.

The runner should be explicit rather than over-abstracted:

```python
ctx.initialize_project()
parsed = ParseRequestStep().run(ctx, state).parsed
BuildProjectBriefStep(parsed).run(ctx, state)
BuildCodexStep().run(ctx, state)
outline = GenerateOutlineStep(parsed).run(ctx, state).outline

for chapter in outline:
    summary = GenerateChapterSummaryStep(chapter).run(ctx, state).summary
    beats = GenerateSceneBeatsStep(chapter, summary).run(ctx, state).beats
    validation = ValidateSceneBeatsStep(chapter, summary, beats).run(ctx, state).validation
    if not validation.passed:
        return WorkflowResult(...)
    WriteBeatProseStep(chapter, summary, beats).run(ctx, state)
    summary_after = SummarizeChapterStep(chapter).run(ctx, state).summary_after
    state.add_summary(chapter_id, summary_after)

MergeManuscriptStep().run(ctx, state)
```

This is intentionally not a generic DAG engine. It is a readable orchestrator with step objects.

### 5.4 `acceptance_checker.py`

Owns read-only acceptance and report logic.

Responsibilities:

- artifact checks;
- workflow trace checks;
- phase B trace checks;
- checkpoint checks;
- genre adapter checks;
- content checks;
- beat validation checks for reports;
- `acceptance_report.md` writing.

Allowed write:

```text
acceptance_report.md
```

Disallowed writes:

```text
00_request.md
01_project_brief.md
02_codex.json
03_outline.json
chapters/**
manuscript/**
run_records/step_manifest.jsonl
rendered_prompts/**
```

The checker should receive:

```text
skill_path
test_case
run_dir
mode
workflow_result
```

It may read manifest entries and artifacts from disk. It must not call the model, render generation prompts, run workflow steps, or repair artifacts.

### 5.5 `run_acceptance.py`

Becomes a thin CLI:

```python
def main() -> int:
    parse args
    load dotenv
    test_case = parse_test_case(...)
    runner = WorkflowRunner(...)
    result = runner.run()
    checker = AcceptanceChecker(..., result)
    checker.write_report()
    print output
```

It may keep compatibility re-exports during the transition if tests import helper names from `run_acceptance.py`, but business logic should live in the new modules.

## 6. Data Flow

### 6.1 Top-Level Flow

```text
run_acceptance.py
  -> WorkflowRunner.run()
       -> WorkflowContext + WorkflowRecorder
       -> WorkflowStep classes
       -> files and step_manifest.jsonl
  -> AcceptanceChecker.write_report()
       -> reads files and manifest
       -> writes acceptance_report.md
```

### 6.2 Chapter State

The runner should keep a small `WorkflowState`:

```text
parsed_requirement
outline
story_so_far
previous_summary_files
```

For chapter 2 and later, summary, beat, validation, and prose prompts must still include prior `03_summary_after.md` files exactly as the current clean generation path does.

### 6.3 Future Revision Readiness

This task does not implement revision. It should still avoid blocking future insertion points:

```text
GenerateOutlineStep
-> future OutlineRevisionStep
-> GenerateChapterSummaryStep

GenerateSceneBeatsStep
-> future BeatRevisionStep
-> ValidateSceneBeatsStep

WriteBeatProseStep
-> future ChapterRevisionStep
-> SummarizeChapterStep

MergeManuscriptStep
-> future ManuscriptRevisionStep
```

`SummarizeChapterStep` should read the current effective chapter draft through a helper such as:

```text
ctx.current_chapter_draft_path(chapter_id)
```

For this task the helper returns `02_draft.md`. Later it can prefer `02_revised_draft.md` without changing the summarization step contract.

## 7. Behavior Preservation Requirements

The refactor must preserve:

- output file paths;
- prompt templates used by each workflow step;
- rendered prompt recording under `run_records/rendered_prompts/`;
- manifest fields and workflow step names;
- previous-summary input file semantics;
- beat validation gating before prose generation;
- milestone-review checkpoints;
- clean generation path without old testcase-specific patches.

The refactor must not change:

- prompt text;
- model temperatures and max token settings, unless directly required to preserve existing behavior;
- output schemas;
- acceptance criteria;
- testcase content;
- clean audit contamination list.

## 8. Error Handling

The current behavior should be preserved:

- JSON parse failure triggers a JSON repair prompt and records a retry step.
- invalid outline shape raises a runtime error.
- beat validation failure stops prose generation and writes an acceptance report.
- runner exceptions are captured by the CLI and reported through `acceptance_report.md` when possible.
- language retry for chapter summary remains in the summarization step.

Checker failures should never mutate generation artifacts.

## 9. Testing and Verification

Required static checks:

```bash
python3 -m py_compile longform-writing/scripts/run_acceptance.py
python3 -m py_compile longform-writing/scripts/workflow_core.py
python3 -m py_compile longform-writing/scripts/workflow_steps.py
python3 -m py_compile longform-writing/scripts/workflow_runner.py
python3 -m py_compile longform-writing/scripts/acceptance_checker.py
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
git diff --check
```

Required clean smoke:

```bash
python3 longform-writing/scripts/run_acceptance.py \
  --test-case test_cases/13_clean_generation_independence_smoke.md \
  --output-dir runs/13_clean_generation_modular_smoke \
  --provider deepseek

python3 longform-writing/scripts/audit_clean_generation.py \
  --run-dir runs/13_clean_generation_modular_smoke
```

Smoke expectations:

- artifacts are complete;
- `step_manifest.jsonl` is complete and parseable;
- `write_beat_prose` occurs only after beat generation and validation;
- chapter 2+ prompts include prior summary files;
- rendered prompts are present;
- no old testcase contamination appears in generated artifacts or rendered prompts.

It is acceptable for old content-specific acceptance checks to fail if the failure reflects real model output rather than broken workflow structure.

## 10. Implementation Boundaries

The implementation should proceed in small moves:

1. Extract shared utilities and infrastructure into `workflow_core.py`.
2. Extract read-only checker logic into `acceptance_checker.py`.
3. Introduce `WorkflowContext`, `WorkflowState`, and `WorkflowResult`.
4. Move workflow actions into step classes in `workflow_steps.py`.
5. Implement `WorkflowRunner` orchestration in `workflow_runner.py`.
6. Reduce `run_acceptance.py` to CLI wiring.
7. Preserve compatibility imports only where needed by current tests.
8. Run static checks and clean smoke.

Do not add any testcase-specific generation patch while doing the split.

## 11. Risks

### Risk: accidental behavior change

Mitigation: keep prompt files, step names, file paths, input file lists, output file lists, and model parameters identical.

### Risk: checker mutates output again

Mitigation: put checker in a module without model client access and document that only `acceptance_report.md` may be written.

### Risk: over-engineering

Mitigation: no registry, no YAML DAG, no package restructuring, no revision implementation in this task.

### Risk: tests import old names from `run_acceptance.py`

Mitigation: keep temporary re-exports for helpers such as `ModelClient`, `parse_test_case`, `read_text`, `write_text`, and `render_template` if needed.

## 12. Acceptance Criteria

The task is complete when:

- `run_acceptance.py` is a thin entrypoint;
- clean V0 generation logic lives in step-level modules;
- acceptance logic lives in `acceptance_checker.py`;
- AcceptanceChecker is read-only except `acceptance_report.md`;
- clean smoke passes `audit_clean_generation.py`;
- required static checks pass;
- no old testcase-specific patch is introduced into generation steps.
