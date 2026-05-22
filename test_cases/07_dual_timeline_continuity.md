# Phase B Test 07: Dual Timeline Continuity

## Purpose

Validate that the workflow can distinguish event chronology from revelation chronology.

The story uses a present-time investigation line and a past-time memory line. The skill must track what happened in the past and when 小帅 learns it in the present.

## User Request

写一个 4 章中文心理悬疑短篇。主角叫小帅，故事有两条时间线：现在，小帅在一间旧会议室里逐步查看四段会议录像；三年前，录像内容逐步还原一次失败项目。第一章现在的小帅只看到第一段录像，知道项目曾经被临时改方案；第二章通过第二段录像知道小美曾反对改方案；第三章通过第三段录像知道小帅当时删掉了风险提示；第四章通过第四段录像揭示，小帅删掉提示后项目上线，导致小美被迫承担责任离职。不要在前两章提前说出删掉风险提示这件事。全文保持小帅限知视角。

## Expected Story Checks

- Present-time scenes happen in the old meeting room.
- Past-time events appear through video, memory, or document evidence.
- Chapter 1 reveals only that the plan changed.
- Chapter 2 reveals 小美 opposed the change.
- Chapter 3 reveals 小帅 deleted the risk warning.
- Chapter 4 reveals the consequence for 小美.
- Chapters 1 and 2 do not state or strongly imply that 小帅 deleted the warning.
- POV remains limited to 小帅's knowledge.

## Summary Checks

- Each `03_summary_after.md` distinguishes:
  - what happened in present time
  - what past information was revealed
  - what remains unknown
- Chapter 3 and chapter 4 prompts use earlier summary-after files as story-so-far.

## Beat Checks

- Beats should identify whether an event is present-time action or past-time video content.
- Beats should not confuse "the past event happened" with "小帅 currently knows it."

## Failure Signals

- The prose reveals deleted warning information before chapter 3.
- `summary_after` collapses the dual timeline into a single unclear chronology.
- 小帅 knows information before he sees the relevant recording.
- The story switches to 小美's internal POV.

