# Smoke Test 01: Single-Protagonist Choice Room

## Purpose

Validate the default end-to-end V0 workflow with a low-complexity story.

This test intentionally uses:

- one protagonist
- simple names without heavy semantic meaning
- one core room
- one past event
- one main moral reversal
- three chapters

It should not use a seven-person ensemble.

## User Request

我想写一个原创密室心理惊悚短篇，3 章左右。主角叫小帅，另一个重要关联人物叫小美。小帅醒在一间选择室里，被一个看不见的审判者要求重新面对三年前一次项目选择。这个选择曾经让小帅获益，但也间接伤害了小美。故事要有一点类似电锯惊魂的道德选择感，但不要血腥、肢体伤害或超自然解释。重点写心理压力、规则、旧案真相和最后的道德反转。风格冷静、克制、压抑。

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

- The story has one clear protagonist: 小帅.
- 小美 may appear as an important related person, but the story should not become a multi-protagonist ensemble.
- Outline has 3 chapters unless the user request is explicitly interpreted otherwise.
- `02_codex.json` contains 小帅, 小美, 选择室, 审判者, and the central rule.
- Beats are concrete actions or reveals, not abstract mood statements.
- Each chapter draft follows its beats.
- Each chapter summary after writing records what actually happened.
- Later chapters use earlier `03_summary_after.md` content.
- The prose avoids gore, bodily harm, and supernatural explanation.

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

