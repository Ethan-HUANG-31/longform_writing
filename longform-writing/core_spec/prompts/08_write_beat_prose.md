# Prompt: write_beat_prose

## Purpose

Write prose that continues the chapter from the current beat.

## Inputs

- project brief
- story so far
- current chapter summary
- global Codex
- relevant Codex
- text before
- current beat
- optional additional context

## Output

Markdown prose only.

## Constraints

- Continue the story, do not summarize.
- Follow the current beat closely.
- Never conclude the scene on your own.
- Never end with foreshadowing.
- Never write further than the current beat requires.
- Stop early if the continuation satisfies the beat.
- Use active, concrete prose and dialogue that advances action.
- Do not include markdown headings unless the beat requires it.

## Prompt Template

[Role Prompt]
You are an expert fiction writer.

[Style Rules]
- Write in the project language.
- Write in active voice.
- Show through concrete action, dialogue, objects, and spatial pressure.
- Avoid cliches, filler, and abstract pressure words when concrete detail can carry the tension.
- Dialogue should continue the action, not stall.

[Project Brief]
{{project_brief}}

[Story So Far]
{{story_so_far}}

[Current Chapter Summary]
{{chapter_summary}}

[Global Codex]
{{global_codex}}

[Relevant Codex]
{{relevant_codex}}

[Genre Adapter]
{{genre_adapter}}

[Text Before]
{{text_before}}

[Current Beat]
{{current_beat}}

[Additional Context]
{{additional_context}}

Write {{word_count}} words or fewer that continue the story from Text Before and fulfill only Current Beat.

## Failure Cases

- Writes beyond the beat.
- Reveals future information early.
- Repeats text_before.
- Ignores relevant Codex.
