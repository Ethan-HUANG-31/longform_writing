# Phase C Test 10: Mystery Clue Fairness Smoke

## Purpose

Validate dynamic prompt routing for a clue-driven mystery.

This test checks fair clue planting, red herring control, and final deduction.

This test is expected to fail until genre adapter routing and clue-state tracking are implemented.

## User Request

写一个 4 章中文本格感轻悬疑短篇。主角叫小帅，是社区图书馆的临时管理员。小美是图书馆的老读者。图书馆每晚闭馆后会有一本书被移动到错误书架。第一章发现第一本错放的书，线索是书页里夹着一张旧借书卡；第二章出现误导线索，大家以为是小美做的，但小帅发现借书卡日期对不上；第三章小帅发现所有错放书的编号连起来是一串储物柜密码；第四章揭示真正移动书的人是前管理员阿强，他想让人发现储物柜里被遗忘的捐赠名单。最终推理必须使用前三章已经出现的线索，不要突然空降证据。

## Expected Adapter Routing Checks

- `parse_request` identifies mystery or clue-driven suspense.
- Rendered prompts include a `mystery` or `clue_fairness` genre adapter.
- Rendered prompts do not include romance or fantasy adapters.
- Future quality judge should apply clue fairness checks.

## Expected Mystery Checks

- Chapter 1 plants the old borrowing card clue.
- Chapter 2 introduces 小美 as a red herring but also plants the date mismatch.
- Chapter 3 reveals the book numbers combine into a locker password.
- Chapter 4 reveal uses the borrowing card, date mismatch, and book-number clue.
- 阿强 is not revealed as culprit before chapter 4.
- Final deduction does not rely on new evidence introduced only in chapter 4.

## Codex Checks

- Codex contains 小帅, 小美, 阿强, 图书馆, 旧借书卡, 错放书, 储物柜密码.
- Clue entries distinguish:
  - planted clue
  - red herring
  - final payoff

## Trace Checks

- `summary_after` records clue state after each chapter.
- Later prompts include earlier clue summaries.
- Rendered prompts for chapter 4 include story-so-far clue state.

## Failure Signals

- 阿强 appears as culprit before chapter 4.
- Final reveal depends on a clue first introduced in chapter 4.
- 小美 red herring contradicts the final solution.
- Rendered prompts lack mystery/clue-fairness adapter text.

