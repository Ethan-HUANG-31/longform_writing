# Auto-Development Execution Plan

This document defines how Codex should automatically design, implement, review, and iterate `longform_writing_skill_v0`.

The overall process is a two-phase loop:

1. Skill Create: build or patch the skill.
2. Skill Acceptance: use the skill in a fresh context on test cases, then feed failures back into creation.

See `design_context/11_skill_create_acceptance_loop.md` for the detailed loop.

## Final Objective

Produce a usable longform fiction writing skill that can take a user writing request, create a structured writing project, and generate a complete first draft through traceable intermediate files.

The skill should encode the NovelCrafter-style workflow extracted from the GPT conversation:

```text
User Request -> Project Brief -> Codex -> Outline -> Chapter Summary -> Scene Beats -> Beat Validation -> Beat Prose -> Summary After -> Manuscript
```

## Recommended Development Strategy

Use a staged automation loop instead of asking one agent to design everything at once.

### Phase 1: Requirements Freeze

Inputs:

- `design_context/01_novelcrafter_observations.md`
- `design_context/02_longform_writing_skill_v0_scope.md`
- `design_context/03_writing_project_v0_directory.md`
- `design_context/04_skill_v0_directory.md`
- `design_context/05_prompt_patterns_from_novelcrafter.md`
- `design_context/06_context_policy.md`
- `design_context/07_acceptance_checklist.md`
- `design_context/08_autodev_execution_plan.md`
- `design_context/10_execution_trace_testing.md`
- `design_context/11_skill_create_acceptance_loop.md`
- `design_context/14_novelcrafter_macro_mapping.md`
- `design_context/15_codex_design.md`
- `design_context/17_user_request_contract.md`
- `design_context/18_user_checkpoint_policy.md`
- `design_context/19_dual_agent_checkpoint_acceptance.md`
- `design_context/16_external_model_acceptance_runner.md`

Output:

- Confirmed V0 scope.
- Confirmed runtime directory structure.
- Confirmed platform target.
- Confirmed smoke test cases.

Default assumption if the user does not specify otherwise:

- Build a Codex-compatible skill first.
- Keep a platform-neutral `core_spec/` so Claude Code adaptation remains possible.
- Install or stage the skill inside this repo first, then optionally copy to `$CODEX_HOME/skills`.

### Phase 2: Skill Create / Skeleton Implementation

Create `longform_writing_skill_v0/` with:

- `SKILL.md`
- `core_spec/workflow.md`
- `core_spec/context_policy.md`
- `core_spec/runtime_contract.yaml`
- `core_spec/prompts/*.md`
- `core_spec/schemas/*.json`
- `templates/writing_project_v0/`
- trace records under `run_records/`
- optional `scripts/` only if deterministic validation or project initialization is needed
- optional external model runner scripts for low-cost acceptance testing

Do not overbuild:

- no complex revision
- no SFT export
- no preference pair export
- no multi-agent runtime
- no full evaluator framework

### Phase 3: Structural Review

Use a separate reviewer pass to check:

- Does every workflow step have a prompt?
- Does every step declare reads and writes?
- Is every downstream input produced upstream?
- Does context policy match the runtime contract?
- Does the template match the runtime output paths?
- Did the implementation add V0-out-of-scope modules?

The reviewer should produce a patch list, not rewrite the whole design.

### Phase 4: Skill Acceptance / Smoke Test

Run the skill against the default smoke test cases in `test_cases/`.

Acceptance should happen in a fresh context or fresh agent. The acceptance agent should receive only the skill path, the test case path, and the output directory. It should use the skill as a normal workflow and produce an acceptance report.

Minimum successful run:

- creates a fresh project directory
- produces all required runtime files
- writes at least 3 chapters
- generates beats before prose
- records prompt assembly and step execution in `run_records/`
- writes `03_summary_after.md` for each chapter
- merges `manuscript/draft_full.md`
- copies or writes `manuscript/final.md`

### Phase 5: Patch And Iterate

Iterate only on concrete failures:

- missing file
- malformed JSON
- step reads a file that was never produced
- prompt output cannot be consumed by the next step
- rendered prompt is missing required context sections
- step trace shows prose generated before beat validation
- chapter continuity breaks in a way the context policy should have prevented
- beat validation fails to catch obvious contradictions

Avoid broad prompt polishing until the pipeline is structurally reliable.

After patching, rerun acceptance. Continue until the single-protagonist smoke tests and trace checks pass.

## Multi-Agent Use

Multi-agent work is useful for this task, but only with clear ownership.

Recommended roles:

1. Main coordinator
   - Owns scope, integration, final decisions, and user communication.

2. Implementation worker
   - Creates or edits `longform_writing_skill_v0/`.
   - Owns concrete file changes.

3. Structural reviewer
   - Reads implementation and `design_context/`.
   - Reports contract mismatches, missing files, and V0 scope drift.

4. Smoke test agent
   - Uses the generated skill on one test case as a normal user would.
   - Reports whether expected artifacts are produced.
   - Produces `acceptance_report.md`.

6. Checkpoint test agent, optional after base smoke tests pass
   - Runs `test_cases/04_checkpoint_interaction_smoke.md`.
   - Verifies milestone review and feedback application.
   - Uses a dual-role setup: user simulator plus writing executor.

5. Prompt-pattern reviewer, optional
   - Checks whether prompt templates preserve the NovelCrafter-style mechanisms.
   - Should not optimize literary style in V0.

## User Inputs Needed

The following inputs would improve the result. Defaults are provided so work can continue if the user does not want to decide everything upfront.

### Required Before Final Packaging

1. Target platform
   - Default: Codex skill with platform-neutral core spec.
   - Alternative: Claude Code-first package.

2. Installation target
   - Default: create in this repo for review.
   - Alternative: install into `$CODEX_HOME/skills` for active use.

3. Output language
   - Default: support Chinese fiction requests and Chinese generated prose first.
   - Alternative: bilingual or English-first.

4. Expected story scale for V0
   - Default: 3 chapters for smoke testing, configurable chapter count in prompts.
   - Alternative: fixed 5 chapters or user-defined.

### Helpful But Not Blocking

1. One or more preferred test prompts.
2. A genre or style the user cares about most.
3. Prohibited content boundaries beyond normal safety rules.
4. Desired degree of user confirmation during writing.
   - Default: fully automatic after the initial request.
   - Alternative: require confirmation after brief, codex, or outline.
5. Whether project runs should be kept under `runs/` or another directory.
   - Default: `runs/{project_slug}/`.

## Default Acceptance Standard

The skill is acceptable for V0 when it can:

1. Initialize a writing project from a user request.
2. Generate all required project files in the expected locations.
3. Maintain a coherent context chain across chapters.
4. Avoid writing prose directly from the original request.
5. Validate beats before prose.
6. Produce a full manuscript from chapter drafts.
7. Keep SKILL.md concise and place detailed prompt/context material in referenced resources.

## Not Yet Required

These belong in future versions:

- iterative literary revision
- chapter-level critique and retry loop
- preference data export
- SFT trajectory export
- multi-agent writing runtime
- complex subplot/open-thread tracker
- UI or web app
- direct NovelCrafter integration
