# Prompt: user_checkpoint

## Purpose

Present a milestone artifact summary to the user simulator and record the user's acceptance or feedback.

## Inputs

- checkpoint name
- current artifact summary
- simulated user feedback

## Output

Checkpoint record only. Do not generate story prose.

## Prompt Template

[Role Prompt]
You are the writing workflow executor asking for milestone review.

[Checkpoint]
{{checkpoint_name}}

[Artifacts Presented To User]
{{artifact_summary}}

[Instruction]
Ask the user simulator to confirm whether the current artifact should be accepted or revised. If feedback is provided, record it exactly and mark downstream steps that must be regenerated.

[Simulated User Feedback]
{{simulated_user_feedback}}
