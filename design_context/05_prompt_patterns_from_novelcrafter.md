# Prompt Patterns From NovelCrafter

Do not copy NovelCrafter prompts verbatim. Preserve the mechanisms and rewrite prompts in our own workflow language.

## Pattern 1: Scene Beat Completion

NovelCrafter-style beat completion uses focused context:

- story so far
- current chapter or scene summary
- current beat
- current chapter text before the beat
- relevant Codex entries
- global genre and style constraints
- optional user additional context

Our equivalent placeholders:

```text
[Project Brief]
{{project_brief}}

[Story So Far]
{{previous_chapter_summaries}}

[Current Chapter Summary]
{{chapter_summary}}

[Relevant Codex]
{{relevant_codex}}

[Text Before]
{{current_chapter_text_before}}

[Current Beat]
{{current_beat}}
```

Important rule: do not inject all Codex by default when writing prose. Use relevant Codex.

Additional prompt design details from the official Scene Beat Completion prompt:

- Start with a fiction-writer role.
- Keep global style rules close to the top of the prompt.
- Force the prose to continue the story, not summarize or plan.
- Tell the model to follow the beat closely and not conclude the scene on its own.
- Tell the model not to foreshadow, not to imagine endings, and not to write beyond the requested beat.
- Allow early stopping when the beat requirement is satisfied; do not force the model to fill the maximum word budget.
- Include previous scene tail only when the current text is empty and the previous scene has the same POV character.
- Always include recent `textBefore` from the current scene/chapter before asking for continuation.
- Put the current POV and beat instruction inside an explicit instruction block.
- Put additional user context after the main instruction block so it can specialize the current generation.

Portable V0 equivalent:

```text
[Writer Role]
[Project / Style Constraints]
[Relevant Codex]
[Story So Far]
[Previous Same-POV Tail, optional]
[Text Before]
[Current POV, if any]
[Current Beat]
[Additional Context, optional]
```

## Pattern 2: Scene Beats Should Be Concrete

Beats should not be abstract mood statements. They should contain:

- named characters
- concrete actions
- specific location or object references
- information revealed or withheld
- emotional or relationship state change

Weak beat:

```text
The atmosphere becomes more tense.
```

Better beat:

```text
小帅 notices the monitor light blink twice as the countdown starts, then hides his recognition of the displayed date from 小美.
```

Additional prompt design details from the official Scene Beats from Summary prompt:

- Ask for a specific number of beats.
- Require highly detailed beats.
- Require logical and temporal coherence.
- Require precise wording and ambiguity resolution.
- Do not allow beats to deviate from the summary.
- Do not allow beats to continue the story outside the summary.
- Output as a numbered list in NovelCrafter, but V0 should use JSON for machine validation.

Portable V0 equivalent:

```json
[
  {
    "beat_id": 1,
    "text": "Concrete beat description",
    "purpose": "what this beat accomplishes",
    "required_codex": ["小帅", "选择室"]
  }
]
```

## Pattern 3: Summarization Is Factual Memory

Chapter summarization should not review literary quality. It should compress what actually happened into future context.

It should preserve:

- events that occurred
- revealed information
- decisions made
- character state changes
- unresolved questions needed later
- timeline facts

Additional prompt design details from the official Scene Summarization prompt:

- Output running text, not bullets.
- Do not start with meta phrases like "In this scene".
- Mention characters by name, not by role.
- Assume the reader already knows profiles, so do not explain who everyone is.
- Use third person even if the source prose uses first person.
- Use present tense.
- Prefer nouns and names over pronouns.
- Start a new paragraph when time or location shifts.
- Do not re-summarize backstory already covered by previous summaries.
- Remove mundane actions unless they matter to plot development.
- Remove sensory detail, description, and dialogue unless they carry key plot information.

Portable V0 implication: `03_summary_after.md` should be a compact factual memory artifact, not a prose critique and not a literary rewrite.

## Pattern 4: Developmental Editor as Critic

Developmental Editor maps to a critic/evaluator role. It can identify issues but should not be part of the V0 main drafting loop.

V0 can include beat validation, but should not include complex automatic revision.

Useful future evaluator dimensions from the official Developmental Editor prompt:

- concept clarity
- premise conflict strength
- central dramatic question
- theme through plot and character choices
- beginning/middle/end structure
- escalating stakes
- subplot relevance
- climax and resolution
- pacing and momentum
- scene purpose and meaningful change
- POV consistency
- dialogue advancing conflict, character, and plot
- characterization through desire, fear, flaw, and pressure choices

V0 should only borrow lightweight checks where they support workflow correctness, especially scene purpose, chronology, premature reveal, and whether a beat advances the chapter summary.

## Pattern 5: Validate Before Prose

Because Beat Completion faithfully expands the beat, invalid beats pollute prose and later summaries.

Beat validation should detect:

- timeline contradictions
- mismatch with chapter summary
- premature reveal of future truth
- missing key character/location/rule references
- overly abstract beats
- contradiction with previous chapter summaries
