# Prompt Source Requests

This document lists the NovelCrafter prompt/source details that are still unclear and worth asking the user to paste.

Do not copy official prompts verbatim into the final skill. Use them to extract portable prompt patterns, context assembly rules, and failure guards.

## Already Clear Enough

From the GPT conversation, the following mechanisms are clear enough for V0:

- Longform writing should not directly generate the whole story.
- Core flow is Codex -> Chapter Summary -> Scene Beats -> Beat Completion -> Prose -> Summary After.
- Beat-to-prose uses focused context: story so far, text before, current beat, relevant Codex, project/style constraints.
- Summarization should create factual future memory, not literary critique.
- Developmental Editor is critic/evaluator-like, not the V0 main revision engine.
- Invalid beats can contaminate prose and later summaries, so beat validation is required before prose.

## Received Sources

The user pasted official prompts for:

- Scene Beat Completion
- Scene Summarization
- Scene Beats from Summary
- Developmental Editor

These are enough to draft the V0 prompt templates for:

- `06_generate_scene_beats.md`
- `08_write_beat_prose.md`
- `09_summarize_chapter.md`
- lightweight validation/evaluator principles

## P0: Needed Before Writing Final Prompt Templates

### 1. Scene Beat Completion: General Purpose Prompt

Status: received.

Questions to answer:

- What role/instruction does it give the model?
- What context blocks are included?
- How are `storySoFar`, `textBefore`, current beat, Codex, style guide, genre, and additional context represented?
- Does it tell the model to output only prose?
- Does it control length, pacing, dialogue/action balance, POV, tense, or style?
- Does it prevent repeating earlier text?
- Does it mention continuing seamlessly from prior prose?

This is the highest-priority source because it maps directly to `08_write_beat_prose.md`.

### 2. Scene Summarization Default Prompt

Status: received.

Questions to answer:

- Does it summarize the whole scene, selected text, or current prose section?
- Does it read `scene.fullText`, chapter text, or a generated completion?
- What does the summary preserve: events, reveals, character state, timeline, unresolved questions?
- What length or format does it request?
- Does it avoid critique/opinion?

This maps directly to `09_summarize_chapter.md`.

### 3. Scene Beats From Summary Prompt

Status: received.

Questions to answer:

- How many beats does it ask for?
- What makes a beat valid?
- Does it require concrete action, character movement, conflict, and reveal?
- Does it ask for JSON, list items, or plain text?
- Does it include Codex or only the summary?

This maps directly to `06_generate_scene_beats.md`.

## P1: Useful For Better V0 Prompts Or V1

### 4. Developmental Editor Prompt

Status: received.

Questions to answer:

- What dimensions does it critique?
- Does it produce recommendations, rewritten text, or both?
- Does it focus on plot, pacing, character, consistency, style, or prose?
- Can its categories inspire V0 beat validation or a future review step?

This is not V0 main-loop material, but useful for future evaluator/revision design.

### 5. Text Replacement / Expand / Shorten Prompts

Need prompts for selected-text editing operations if available.

Questions to answer:

- What context does local editing receive?
- Does replacement preserve surrounding style and continuity?
- Does expand add new events or only enrich existing content?
- Does shorten preserve plot facts?

These should stay out of V0's main workflow, but they inform future local revision.

### 6. Codex Extraction / Classification Prompt

Need any official extraction prompt if NovelCrafter has one.

Questions to answer:

- How does it classify Character, Location, Lore/Rule, Object, etc.?
- What fields are used?
- How does it avoid misclassification?
- Does it ask for Name / Type / Tags / Description?

This matters because the earlier Extract result did not classify elements correctly.

## Macro Expansion Decision

The pasted prompts contain include macros whose resolved contents are not fully public or not necessary to reproduce:

- `Novelcrafter/AdditionalInstructions`
- `Novelcrafter/Personas`
- `Novelcrafter/Codex`
- `Novelcrafter/AdditionalContext`
- `Novelcrafter/Chat/DefaultContext`
- `Novelcrafter/Chat/DefaultInstructions`

V0 should proceed without exact macro contents by using explicit context slots.

See `design_context/14_novelcrafter_macro_mapping.md`.

Useful but non-blocking future source:

1. `Novelcrafter/Codex` include output or example resolved Codex context.
2. `Novelcrafter/Chat/DefaultContext`.
3. `Novelcrafter/Chat/DefaultInstructions`.
4. `AdditionalContext` and `AdditionalInstructions` behavior.
5. Codex extraction/classification prompt, if available.

None of these are blockers for V0.

## P2: Nice To Have

### 7. Plan / Workshop / Chapter Summary Prompt

Useful if there is an official prompt for generating or refining chapter plans.

Questions:

- How does it turn high-level story intent into a chapter summary?
- Does it include previous summaries or Codex?
- Does it distinguish planning summary from after-writing summary?

### 8. Context Macro / Include Syntax Examples

Useful for translating NovelCrafter-specific syntax into our own placeholders.

Questions:

- What macros exist?
- What do they resolve to?
- Are they ordered by priority?
- Does NovelCrafter use relevance retrieval or full inclusion?

## Preferred Paste Order

If the user can paste only a few items first, use this order:

1. Scene Beat Completion General Purpose prompt
2. Scene Summarization default prompt
3. Scene Beats From Summary prompt
4. Developmental Editor prompt
5. Text Replacement / Expand / Shorten prompts
6. Codex extraction prompt
