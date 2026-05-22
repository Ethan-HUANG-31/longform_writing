# Smoke Test 03: Beat Validation Guard

## Purpose

Validate that the skill treats beat validation as a required step before prose generation.

This test focuses on workflow correctness, not final prose quality.

## Base Request

写一个 3 章短篇。主角叫小帅，旧同事叫小美。小帅发现一把蓝色钥匙。第一章只建立钥匙和警告，第二章让钥匙引发冲突，第三章才揭示钥匙其实是旧录音装置的启动器。不要超自然，不要血腥。

## Invalid Beat To Inject

Before prose generation for chapter 1 or chapter 2, manually or programmatically introduce this invalid beat into `01_beats.json`:

```json
{
  "beat_id": 3,
  "text": "小帅已经知道第三章才应该揭示的真相，并直接向小美解释蓝色钥匙是旧录音装置的启动器。"
}
```

## Expected Behavior

The validation step should flag the beat before prose generation.

## Acceptance Checks

- Validation identifies premature reveal.
- Validation identifies mismatch with current chapter summary if the chapter summary does not require this reveal.
- `step_manifest.jsonl` records the validation failure.
- Prose generation should not proceed silently with the invalid beat.
- The workflow should either regenerate/patch beats once or stop with a clear failure before prose.
- A rendered validation prompt exists and includes the chapter summary, current beats, relevant Codex, and previous summaries if available.

