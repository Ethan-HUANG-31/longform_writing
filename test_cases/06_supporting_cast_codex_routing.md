# Phase B Test 06: Supporting Cast Codex Routing

## Purpose

Validate that the workflow can include several supporting characters without losing the single-protagonist structure or Codex relevance control.

## User Request

写一个 4 章中文心理悬疑短篇。主角叫小帅，他是唯一主角和唯一现实视角。配角包括小美、阿强、老周和林姐。小帅收到一封匿名邮件，邮件指向三年前一次产品灰度实验。小美是当年提出风险提醒的人；阿强是负责数据清洗的同事；老周是当年的直属领导；林姐是后来接手善后的人。第一章小帅收到邮件并回到旧公司楼下；第二章他分别从阿强和林姐留下的材料中发现数据异常；第三章老周的录音证明小帅当年知道风险；第四章揭示匿名邮件来自小美留下的定时系统。不要让配角变成群像主角，不要写成刑侦破案。

## Expected Story Checks

- 小帅 remains the only protagonist and present-time viewpoint.
- 小美, 阿强, 老周, 林姐 have stable roles.
- Supporting characters do not take over the narrative.
- Chapter 2 uses 阿强 and 林姐 as evidence sources, not as independent POV characters.
- Chapter 3 uses 老周's recording to reveal 小帅 knew the risk.
- Chapter 4 reveals 小美's timed system as the email source.

## Codex Checks

- `02_codex.json` contains entries for 小帅, 小美, 阿强, 老周, 林姐, 匿名邮件, 灰度实验.
- Each supporting character has a distinct role description.
- Rendered prompts for beats involving 阿强 include 阿强 in relevant Codex.
- Rendered prompts for beats involving 林姐 include 林姐 in relevant Codex.
- Rendered prompts for beats involving 老周 include 老周 in relevant Codex.
- Global Codex should not become a dump of every supporting character unless the runner explicitly chooses full minimal Codex and labels it.

## Trace Checks

- `required_codex` appears in chapter or beat planning when supporting characters are used.
- Beat-to-prose prompts include relevant Codex for the character or evidence source in the current beat.
- Later chapter prompts include earlier `summary_after` facts about the supporting characters.

## Failure Signals

- A supporting character becomes a second viewpoint without user request.
- Character roles drift, such as 阿强 becoming the anonymous sender.
- Relevant Codex is missing when a beat depends on a supporting character.
- The story turns into police investigation rather than psychological suspense.

