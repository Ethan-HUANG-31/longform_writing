# Prompt: summarize_chapter

## Purpose

Compress the written chapter into factual memory for future chapters.

## Inputs

- project brief
- chapter draft

## Output

Markdown running text summary.

## Constraints

- Do not use bullets.
- Write in the project language.
- Do not start with "In this chapter" or "Here is".
- Use third person and present tense.
- Mention characters by name.
- Avoid pronouns when names are clearer.
- Preserve key events, decisions, reveals, timeline facts, location changes, and state changes.
- Omit sensory detail and mundane action unless plot-relevant.
- Do not critique.

## Prompt Template

[Role Prompt]
You are an expert novel summarizer.

[Default Instructions]
Summarize only what actually happens in the text. Produce compact future memory.

[Project Brief]
{{project_brief}}

[Chapter Draft]
{{chapter_draft}}

Write a concise factual summary in running text. Use the same language as the project brief.

## Failure Cases

- Summary critiques instead of summarizes.
- Summary omits key reveal or state change.
- Summary adds events not in the draft.
