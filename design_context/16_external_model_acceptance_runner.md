# External Model Acceptance Runner

This document records the decision for low-cost acceptance testing.

## Problem

Longform writing acceptance tests may consume many model tokens. Running every smoke test with the main Codex model could be unnecessarily expensive.

The user has access to a lower-cost external API, referred to here as `DeepStack`.

## Current Codex Constraint

Within the current Codex subagent environment, spawned agents can use only the available built-in model overrides exposed by the agent tool. They cannot be assigned an arbitrary third-party API endpoint as their own underlying reasoning model.

Therefore V0 should not assume we can create a native Codex subagent whose model is `DeepStack`.

## Recommended Design

Use a hybrid pattern:

```text
Codex coordinator / acceptance agent
  -> calls an external model runner script
  -> external runner calls DeepStack API for writing-generation steps
  -> runner writes project artifacts and run_records
  -> Codex reviews artifacts, trace, and acceptance_report
```

In other words:

- Codex remains the orchestrator and reviewer.
- DeepStack is used as the cheaper generation backend for smoke-test writing steps.
- The skill remains platform-neutral and model-agnostic.

## Where This Fits

Add optional runner support under the skill:

```text
longform_writing_skill_v0/
├── scripts/
│   ├── run_acceptance.py
│   ├── model_client.py
│   └── render_prompt.py
└── core_spec/
```

The runner can be optional. The skill should still be usable manually by Codex if no external API key is configured.

## API Key Handling

Do not write API keys into the repository.

Recommended environment variables for DeepSeek:

```text
LONGFORM_MODEL_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Keep provider-specific details inside `model_client.py`.

Before building the full acceptance runner, test connectivity with:

```bash
DEEPSEEK_API_KEY='sk-...' python3 scripts/test_deepseek_api.py
```

The test script uses the OpenAI-compatible `/chat/completions` endpoint, sends a tiny prompt, and does not save or print the API key.

## Runner Responsibilities

The external runner should:

1. Read a test case.
2. Initialize a run directory.
3. Render prompts from skill templates and project files.
4. Save each rendered prompt under `run_records/rendered_prompts/`.
5. Call the configured external model for generation steps.
6. Write generated artifacts to the expected project paths.
7. Append `run_records/step_manifest.jsonl`.
8. Validate JSON outputs.
9. Stop before prose generation if beat validation fails.
10. Write `acceptance_report.md`.

## What The Runner Should Not Do

- It should not silently change the skill design.
- It should not repair prompt templates during acceptance.
- It should not bypass required workflow steps.
- It should not generate the manuscript directly from the user request.

## Acceptance Modes

Support two acceptance modes:

### 1. Static / Mock Mode

No external model call.

Use for:

- file existence checks
- prompt rendering checks
- step manifest schema checks
- workflow order checks

### 2. External Model Mode

Calls the configured cheap model API.

Use for:

- end-to-end prose generation
- continuity checks
- summary-after checks
- validation guard tests

## Practical Recommendation

For initial development:

1. Build static validation first.
2. Add prompt rendering and trace checks.
3. Add external model runner only after the skill templates exist.
4. Run the expensive/real generation tests only on the single-protagonist smoke tests.
