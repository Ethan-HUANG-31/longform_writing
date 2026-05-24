Merge contract for V1 revision mode.

The runner must preserve:
- manuscript/final_unrevised.md
- manuscript/final_revised.md

The revised manuscript is built from each chapter's 02_revised_draft.md when present. If a revised draft is missing, the runner must use 02_draft.md and record that fallback in revision_manifest.jsonl.
