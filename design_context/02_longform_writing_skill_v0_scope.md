# Longform Writing Skill V0 Scope

## Goal

Build a minimal workflow skill that can run one complete longform fiction drafting task from user request to full manuscript.

The skill should not ask the model to write the whole story directly. It must generate and maintain intermediate files so the writing process is traceable and context controlled.

## V0 Does

1. Receive a natural-language writing request.
2. Initialize a new writing project directory.
3. Save the original request.
4. Generate a project brief.
5. Generate a minimal Codex.
6. Generate a chapter outline.
7. Initialize chapter folders.
8. Generate each chapter summary from the outline.
9. Generate concrete scene beats for each chapter.
10. Validate scene beats before prose generation.
11. Write chapter prose beat by beat.
12. Summarize each completed chapter.
13. Merge chapter drafts into a complete manuscript.

## V0 Does Not Do

- complex revision workflows
- SFT data construction
- preference pair generation
- multi-agent orchestration
- complex subplot tracking
- full evaluator/scoring framework
- automatic global literary polish
- multiple scenes per chapter as a required structure
- platform-specific packaging as the first step

## Current Priority

The first implementation should prove that the workflow can run end to end:

```text
User Request -> Project Brief -> Codex -> Outline -> Chapter Summary -> Scene Beats -> Beat Prose -> Summary After -> Full Manuscript
```

Quality optimization comes after this minimum loop is runnable.
