# Phase C Test 08: Romance Adapter Smoke

## Purpose

Validate dynamic prompt routing for a romance story.

This test is expected to fail until genre adapter routing is implemented.

## User Request

写一个 4 章中文现代职场爱情短篇。主角叫小帅，另一位主角叫小美。两人是同一家公司的同事，曾因一次项目误会疏远。第一章让两人因为新项目被迫合作；第二章让他们在合作中发现对方当年的真实顾虑；第三章出现一次关系黑暗时刻，小帅误以为小美再次选择了项目利益；第四章解除误会并让两人做出成熟的关系选择。不要写成悬疑审判，不要超自然，不要狗血误会堆叠。重点是关系推进、潜台词和职业选择。

## Expected Adapter Routing Checks

- `parse_request` identifies romance or relationship-focused genre.
- Rendered prose prompts include a `romance` genre adapter.
- Rendered prose prompts do not include fantasy, mystery, or locked-room moral-trial adapters.
- Future quality judge should use romance-specific criteria.

## Expected Romance Checks

- 小帅 and 小美 both have distinct goals and vulnerabilities.
- Relationship milestones progress across chapters.
- Chapter 3 contains an earned black moment or relationship rupture.
- Chapter 4 resolves the central emotional conflict without rushing.
- Dialogue uses subtext and does not only explain backstory.
- Both characters have lives or stakes beyond the relationship.

## Codex Checks

- Codex contains both leads with desire/fear/flaw or equivalent relationship-driving traits.
- Codex includes the past project misunderstanding as relationship history.
- Codex distinguishes professional stakes from romantic stakes.

## Failure Signals

- The story uses psychological-thriller trial language or审判者 mechanics.
- The romance adapter is missing from rendered prompts.
- Relationship progression is replaced by generic project conflict.
- Chapter 4 resolves through coincidence rather than character choice.

