# Prompt: merge_manuscript

## Purpose

Assemble chapter drafts into a complete manuscript.

## Inputs

- all chapter drafts

## Output

- `manuscript/draft_full.md`
- `manuscript/final.md`

## Constraints

- Do not rewrite in V0.
- Preserve chapter order.
- V0 final may equal draft_full.

## Prompt Template

[Role Prompt]
You are a manuscript assembler.

Concatenate chapter drafts in order. Do not revise content.

## Failure Cases

- Chapters out of order.
- Missing chapter draft.
- Final manuscript generated directly from request instead of chapter drafts.

