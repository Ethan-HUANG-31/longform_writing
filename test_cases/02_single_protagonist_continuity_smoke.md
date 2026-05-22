# Smoke Test 02: Single-Protagonist Continuity

## Purpose

Validate whether summaries after writing are used as story-so-far context for later chapters.

The story remains intentionally simple: one protagonist, one related person, one object, one delayed reveal.

## User Request

写一个 3 章的短篇悬疑故事。主角叫小帅，旧同事叫小美。第一章里，小帅在储物柜里发现一把蓝色钥匙和一张纸条，纸条上写着：“不要把蓝色钥匙交给小美。”第二章必须让蓝色钥匙成为冲突核心，但不要解释钥匙真正用途。第三章揭示蓝色钥匙不是开门用的，而是某个旧录音装置的启动器。风格克制、冷静，避免超自然。

## Expected Story Checks

- Chapter 1 introduces 小帅, 小美, blue key, and the exact warning.
- Chapter 2 remembers the blue key and uses it as a conflict object.
- Chapter 2 does not reveal the recorder-trigger function too early.
- Chapter 3 reveals the key's recorder-trigger function.
- `03_summary_after.md` for each chapter contains the continuity facts needed later.

## Expected Trace Checks

- Chapter 2 beat-generation step reads or references chapter 1 `03_summary_after.md`.
- Chapter 2 prose-generation step includes story-so-far context derived from chapter 1.
- Chapter 3 beat-generation step reads or references chapter 1 and chapter 2 summaries after writing.
- Chapter 3 prose-generation step includes story-so-far context derived from earlier summaries.
- No chapter 1 or chapter 2 rendered prompt includes chapter 3's final reveal unless the reveal is present only as a protected future constraint and not visible in prose-generation context.

## Prompt Assembly Checks

For each chapter 2+ beat-to-prose rendered prompt:

- Includes `Story So Far`.
- Includes `Current Chapter Summary`.
- Includes `Relevant Codex`.
- Includes `Current Beat`.
- Includes `Text Before`.
- Does not include future chapter summary text.

