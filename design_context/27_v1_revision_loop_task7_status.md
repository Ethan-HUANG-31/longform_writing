# V1 Revision Loop Task 7 Status

## Current State

V1 implementation work is complete through the documentation and workflow-contract stage on branch `codex/v1-chapter-revision-loop`.

Verified local checks:

```text
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
18 tests OK
```

Committed V1 scope includes:

- chapter review prompt/schema contracts
- deterministic revision helpers
- chapter review and revision planning artifacts
- chapter rewrite and revised summary generation
- four-way blind package builder
- acceptance decision helper requiring both `rubric` and `reader` rankings
- V1 documentation and workflow contract

## Task 7 Attempt

Command attempted:

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --provider deepseek \
  --allow-external-model-export \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --max-iterations 3
```

First attempt failed because `.env` was missing in the current worktree. The local ignored `.env` was restored from a sibling worktree, and `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL` are present.

Second attempt reached the first model call and failed under sandboxed network with DNS resolution error. Retrying with escalated network permission was rejected by policy because the run would send local test-case prompts, generated project context, and manuscript content to the external DeepSeek API.

## Partial Generated Artifacts

The failed first-model-call attempt created a partial run directory:

```text
runs/05_medium_length_single_protagonist_v1_revision_iter_01/
```

Current files there are pre-prose setup artifacts only:

```text
00_request.md
01_project_brief.md
02_codex.json
03_outline.json
run_records/step_manifest.jsonl
writing_log.md
```

No `final_unrevised.md`, `final_revised.md`, or blind package exists yet.

## Blocker

Task 7 requires a real model channel to generate reader-facing manuscripts. The current runner supports `deepseek` for real generation. However, using DeepSeek sends local writing task context to an external API, and the current execution environment requires explicit user approval for that data transfer.

This is not a V1 implementation failure. It is an execution-authorization blocker before manuscript generation.

## Next Required Decision

To continue the planned Task 7 path, the user must explicitly approve the DeepSeek data transfer for this V1 writing test. Suggested approval text:

```text
我批准这轮把测试 case、生成上下文和稿件内容发送到 DeepSeek API 执行 V1 写作测试。
```

After approval, rerun with `--allow-external-model-export`; the runner now aborts before dotenv loading or run artifact creation unless that flag is present for the DeepSeek external API path.

If that approval is not given, the safer fallback is to use internal Codex agents to generate and evaluate the manuscripts. That can still test the revision concept and blind evaluation process, but it will not verify the actual DeepSeek-backed runner path.
