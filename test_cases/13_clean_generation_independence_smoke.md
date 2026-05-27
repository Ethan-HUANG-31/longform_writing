# Smoke Test 13: Clean Generation Independence

## Purpose

Validate that the current `longform-writing` full skill can run end to end on a fresh case without leaking historical testcase-specific story content into the generation path.

This test is not primarily about literary quality. It is about:

- clean workflow execution
- prompt assembly integrity
- chapter-to-chapter continuity through `03_summary_after.md`
- independence from old testcase names, props, reveals, and patch residue

## User Request

写一个 3 章中文冷调悬疑短篇。主角叫林澈，重要关联人物叫周眠，但全文只使用林澈作为唯一现实视角。林澈回到一座废弃旧天文台，在资料柜里发现一只玻璃鸟和一张写着“不要在第三次校准前交给周眠”的便条。第一章只建立旧天文台、玻璃鸟和便条；第二章让玻璃鸟成为冲突核心，但不要解释它真正用途；第三章揭示玻璃鸟不是纪念品，而是旧观测仪的校准钥。不要血腥、超自然、刑侦追捕或爱情主线。风格冷静、克制、压抑。

## Expected Story Artifacts

- `00_request.md`
- `01_project_brief.md`
- `02_codex.json`
- `03_outline.json`
- `chapters/chapter_01/00_summary.md`
- `chapters/chapter_01/01_beats.json`
- `chapters/chapter_01/02_draft.md`
- `chapters/chapter_01/03_summary_after.md`
- same chapter files for chapter 02 and chapter 03
- `manuscript/draft_full.md`
- `manuscript/final.md`
- `writing_log.md`

## Expected Trace Artifacts

- `run_records/step_manifest.jsonl`
- `run_records/rendered_prompts/`
- rendered prompt for request parsing
- rendered prompt for project brief generation
- rendered prompt for codex generation
- rendered prompt for outline generation
- rendered prompt for each chapter's summary generation
- rendered prompt for each chapter's beat generation
- rendered prompt for each chapter's beat validation
- rendered prompt for each chapter's prose generation
- rendered prompt for each chapter's summary-after generation
- rendered prompt for manuscript merge

## Content Acceptance Checks

- The story has one clear protagonist: 林澈.
- 周眠 may appear as an important related person, but the story should not become a multi-protagonist ensemble.
- Outline has 3 chapters unless the runner explicitly records a justified interpretation.
- Chapter 1 introduces the old observatory, the glass bird, and the warning note.
- Chapter 2 keeps the glass bird as a conflict object but does not reveal that it is a calibration key.
- Chapter 3 reveals that the glass bird is the calibration key for the old observation device.
- Each chapter draft follows its beats.
- Each `03_summary_after.md` records what actually happened.
- Chapter 2 and chapter 3 use earlier `03_summary_after.md` content as story-so-far context.

## Independence Checks

The following historical testcase-specific tokens should not appear anywhere in generated story artifacts or rendered workflow prompts for this run:

- `小帅`
- `小美`
- `阿强`
- `老周`
- `林姐`
- `选择室`
- `审判者`
- `蓝色钥匙`
- `旧录音装置`
- `缺失封面`
- `旧借书卡`
- `错放书`
- `储物柜密码`
- `高风险，不建议上线`

If any of these appear, the run should be flagged as contaminated unless the token only appears inside an external read-only evaluation/report artifact.

## Workflow Acceptance Checks

- `step_manifest.jsonl` is valid JSONL.
- Every successful step lists `workflow_step`, `prompt_template`, `input_files`, `context_sections`, `rendered_prompt`, `output_files`, and `status`.
- Every listed prompt template exists.
- Every listed rendered prompt exists.
- Prose generation happens after beat generation and beat validation.
- Manuscript merge happens after all chapter drafts exist.

## Prompt Assembly Checks

For beat-to-prose rendered prompts:

- Chapter 1 prompt includes project brief, current chapter summary, relevant codex, text before, and current beat.
- Chapter 2 and chapter 3 prompts include previous chapter `03_summary_after.md` content as story so far.
- Prompts do not include future chapter summaries.
- Prompts do not directly write from only the original user request.

## Pass / Fail Use

This case is a clean-generation audit target.

It passes only if:

- the workflow runs end to end,
- required artifacts and rendered prompts exist,
- prompt assembly follows the designed writing process,
- and no old testcase-specific story content leaks into generation artifacts.
