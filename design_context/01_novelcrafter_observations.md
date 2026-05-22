# NovelCrafter Observations

Source: extracted from the ChatGPT conversation export in `GPT对话记录/`.

## Core Workflow Observed

NovelCrafter helps longform fiction through a staged workflow rather than direct full-story generation:

1. Build stable story memory in Codex.
2. Use chapter or scene summaries as executable plans.
3. Generate scene beats from summaries.
4. Expand each beat into prose through Scene Beat Completion.
5. Apply, retry, or discard generated prose.
6. Summarize written scenes or chapters into compact memory.
7. Use summaries as `story so far` context for later chapters.
8. Optionally run Developmental Editor as a critic/evaluator.

Simplified chain:

```text
Codex -> Chapter Summary -> Scene Beats -> Beat Completion -> Prose -> Summary After -> Next Chapter
```

## Useful Product Mechanisms

- Codex stores relatively stable facts: characters, locations, rules, lore, style constraints.
- Plan or chapter summaries provide the next writing target.
- Scene beats are the main execution unit. They turn a chapter summary into concrete actions and reveals.
- Beat Completion is faithful to the current beat. If the beat is wrong, prose will usually expand the error instead of correcting it.
- Scene or chapter summaries compress written prose into future context.
- Developmental Editor is closer to critic/evaluator than an automatic revision engine.
- Text replacement, expand, and shorten are local edit tools, not the main V0 workflow.

## Failure Observed

During the NovelCrafter test, a timeline error entered Chapter 2 beats and was then faithfully expanded into prose. This exposed a key workflow requirement:

Scene beats must be validated before prose generation.

Validation should check:

- timeline consistency
- alignment with chapter summary
- consistency with previous summaries
- no premature reveal of later twists
- enough concrete references for Codex grounding

## Engineering Takeaway

For our own workflow, the key is not UI replication. The key is preserving intermediate representations:

- project brief
- codex
- outline
- chapter summary
- scene beats
- chapter draft
- chapter summary after writing
- manuscript

