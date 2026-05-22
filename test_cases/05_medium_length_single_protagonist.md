# Phase B Test 05: Medium-Length Single-Protagonist Continuity

## Purpose

Validate that the V0 workflow can handle a 5-chapter single-protagonist story with a longer reveal chain.

This test raises length and continuity pressure while keeping the protagonist structure simple.

## User Request

写一个 5 章的中文悬疑短篇。主角叫小帅，重要关联人物叫小美，但全文只以小帅为唯一现实视角。小帅在旧办公室的档案柜里发现一份被拆掉封面的项目评估报告。第一章只发现报告和缺失封面；第二章发现报告里有三处被涂黑的数据；第三章发现小美三年前曾经要求暂停项目；第四章发现小帅当年亲手批准继续推进；第五章揭示缺失封面上原本写着“高风险，不建议上线”，并让小帅面对自己一直回避的责任。不要血腥、超自然或动作追逐。风格冷静、克制。

## Expected Story Checks

- Outline has 5 chapters unless the runner explicitly records a justified interpretation.
- 小帅 remains the only present-time viewpoint.
- 小美 may appear through documents, recordings, messages, or memories, but not as a second protagonist.
- Chapter 1 introduces the report and missing cover only.
- Chapter 2 reveals the three redacted data points but does not reveal the cover warning.
- Chapter 3 reveals 小美 requested suspension.
- Chapter 4 reveals 小帅 approved continuation.
- Chapter 5 reveals the missing cover warning and resolves 小帅's responsibility arc.
- No chapter before chapter 5 directly states the missing cover warning.

## Expected Trace Checks

- Chapter 4 and chapter 5 generation/prose prompts include earlier `03_summary_after.md` context.
- The manifest records all five chapter summary, beat, validation, prose, and summary-after steps.
- Rendered prompts for chapter 2+ include `Story So Far`.
- Rendered prose prompts do not include future chapter summaries.

## Codex Checks

- `02_codex.json` contains 小帅, 小美, 项目评估报告, 缺失封面, and the delayed warning rule.
- The missing cover warning is represented as protected future information until chapter 5.

## Failure Signals

- The final cover warning appears before chapter 5.
- Chapter 5 never writes the cover warning in prose.
- Chapter 4 or 5 ignores earlier report facts.
- The story becomes an ensemble or external investigation story.

