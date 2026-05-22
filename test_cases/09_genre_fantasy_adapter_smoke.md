# Phase C Test 09: Fantasy Adapter Smoke

## Purpose

Validate dynamic prompt routing for a simple fantasy story with explicit magic rules.

This test is expected to fail until genre adapter routing is implemented.

## User Request

写一个 4 章中文低魔奇幻短篇。主角叫小帅，是城中档案馆的见习抄写员。小美是负责看守旧钟塔的钟匠。这个世界只有一种魔法：写在银纸上的名字会在下一次钟响前被所有人遗忘，但使用者也会失去一段自己的记忆。第一章建立档案馆和银纸规则；第二章小帅发现有人用银纸抹掉了一个孩子的名字；第三章小帅和小美追查到旧钟塔，但不能让魔法随便解决问题；第四章小帅必须决定是否牺牲自己的一段重要记忆来恢复孩子的名字。不要写成恋爱主线，不要加入新的魔法体系。

## Expected Adapter Routing Checks

- `parse_request` identifies fantasy or low-magic fantasy.
- Rendered prompts include a `fantasy` genre adapter.
- Rendered prompts do not include romance or mystery-only adapters unless explicitly combined.
- Magic-system constraints appear in Global Codex or Rules/Lore.

## Expected Fantasy Checks

- The silver-paper magic rule is explicit and consistent.
- Magic has a cost: the user loses one memory.
- No additional magic system appears.
- Fantasy elements affect character choices rather than solving all conflict.
- Worldbuilding details support the plot instead of stopping it.
- Terminology is introduced naturally.

## Codex Checks

- Codex contains 小帅, 小美, 档案馆, 旧钟塔, 银纸魔法.
- 银纸魔法 is a Rules/Lore entry and should be global or always included.
- The cost and limitation are included in the magic rule description.

## Failure Signals

- The story adds unrelated magic powers.
- Magic solves the final problem without memory cost.
- Rendered prompts lack fantasy adapter text.
- The story becomes romance-first despite the user saying not to.

