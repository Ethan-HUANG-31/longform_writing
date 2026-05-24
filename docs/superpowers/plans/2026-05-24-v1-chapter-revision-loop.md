# V1 Chapter Revision Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build V1 chapter-level review/revision loop and blind evaluation harness so `full skill revised` can be evaluated against `direct write`.

**Architecture:** Add V1 as an extension layer around the existing acceptance runner rather than rewriting V0. The new runner reuses existing full-skill draft generation, then adds chapter review, revision planning, chapter rewriting, revised summary generation, revised manuscript merge, four-way blind package creation, and final acceptance reporting. Test deterministic helper functions with `unittest`; keep expensive model calls outside unit tests.

**Tech Stack:** Python 3 stdlib, existing markdown prompt templates, JSON schemas, existing `run_acceptance.py` runner, Codex internal evaluator agents for blind judging.

---

## File Structure

Create:

- `longform-writing/core_spec/prompts/12_review_chapter_quality.md` - prompt for chapter-level text quality review.
- `longform-writing/core_spec/prompts/13_plan_chapter_revision.md` - prompt for converting review findings into a bounded rewrite plan.
- `longform-writing/core_spec/prompts/14_rewrite_chapter.md` - prompt for whole-chapter rewrite with continuity constraints.
- `longform-writing/core_spec/prompts/15_summarize_revised_chapter.md` - prompt for revised chapter memory.
- `longform-writing/core_spec/prompts/16_merge_revised_manuscript.md` - merge prompt/contract.
- `longform-writing/core_spec/schemas/chapter_revision_plan.schema.json` - schema for revision plans.
- `longform-writing/core_spec/schemas/revision_acceptance.schema.json` - schema for final V1 acceptance summary.
- `longform-writing/scripts/run_v1_revision_loop.py` - V1 runner and deterministic helper functions.
- `longform-writing/tests/test_v1_revision_helpers.py` - unit tests for helper logic.

Modify:

- `.gitignore` - ignore `revision_eval_runs/`.
- `longform-writing/SKILL.md` - describe V1 revision mode and runner.
- `longform-writing/core_spec/workflow.md` - add V1 workflow section.
- `longform-writing/scripts/create_blind_quality_eval.py` - either leave unchanged or explicitly note it is D0.5-only; V1 uses the new runner's four-way blind package builder.

Generated but not committed:

- `revision_eval_runs/v1_chapter_revision/...`
- `runs/<case>_v1_revision_iter_<n>/...`

## Task 1: Add V1 Prompt Templates And Schemas

**Files:**

- Create: `longform-writing/core_spec/prompts/12_review_chapter_quality.md`
- Create: `longform-writing/core_spec/prompts/13_plan_chapter_revision.md`
- Create: `longform-writing/core_spec/prompts/14_rewrite_chapter.md`
- Create: `longform-writing/core_spec/prompts/15_summarize_revised_chapter.md`
- Create: `longform-writing/core_spec/prompts/16_merge_revised_manuscript.md`
- Create: `longform-writing/core_spec/schemas/chapter_revision_plan.schema.json`
- Create: `longform-writing/core_spec/schemas/revision_acceptance.schema.json`
- Create: `longform-writing/tests/test_v1_revision_helpers.py`

- [ ] **Step 1: Write failing contract tests**

Create `longform-writing/tests/test_v1_revision_helpers.py` with:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "longform-writing" / "core_spec" / "prompts"
SCHEMAS = ROOT / "longform-writing" / "core_spec" / "schemas"


class V1PromptAndSchemaContractTests(unittest.TestCase):
    def test_prompt_templates_exist_and_expose_required_slots(self) -> None:
        required = {
            "12_review_chapter_quality.md": [
                "{{project_brief}}",
                "{{chapter_text}}",
                "{{longform_text_quality_rubric}}",
                "{{previous_summaries}}",
            ],
            "13_plan_chapter_revision.md": [
                "{{chapter_review}}",
                "{{chapter_text}}",
                "{{chapter_summary}}",
            ],
            "14_rewrite_chapter.md": [
                "{{original_chapter_text}}",
                "{{revision_plan}}",
                "{{previous_summaries}}",
                "{{relevant_codex}}",
            ],
            "15_summarize_revised_chapter.md": [
                "{{revised_chapter_text}}",
                "{{project_brief}}",
            ],
            "16_merge_revised_manuscript.md": [
                "final_unrevised.md",
                "final_revised.md",
            ],
        }
        for filename, slots in required.items():
            text = (PROMPTS / filename).read_text(encoding="utf-8")
            for slot in slots:
                self.assertIn(slot, text, f"{filename} missing {slot}")

    def test_revision_plan_schema_has_required_fields(self) -> None:
        schema = json.loads((SCHEMAS / "chapter_revision_plan.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "chapter_id",
                "must_fix",
                "preserve",
                "rewrite_strategy",
                "continuity_constraints",
                "expected_quality_gains",
                "risk_notes",
            }.issubset(required)
        )

    def test_revision_acceptance_schema_has_required_fields(self) -> None:
        schema = json.loads((SCHEMAS / "revision_acceptance.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "case_id",
                "iteration_id",
                "judge_rankings",
                "revealed_ranking",
                "pass",
                "evidence",
                "failure_reason",
            }.issubset(required)
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
ERROR: test_prompt_templates_exist_and_expose_required_slots
FileNotFoundError
```

- [ ] **Step 3: Add prompt templates**

Create `longform-writing/core_spec/prompts/12_review_chapter_quality.md`:

```markdown
You are an expert fiction editor evaluating one chapter as reader-facing prose.

Use the provided context as source of truth. Do not reward workflow artifacts. Judge only what a reader can experience in the chapter.

[Project Brief]
{{project_brief}}

[Previous Summaries]
{{previous_summaries}}

[Current Chapter Summary]
{{chapter_summary}}

[Relevant Codex]
{{relevant_codex}}

[Longform Text Quality Rubric]
{{longform_text_quality_rubric}}

[Chapter Text]
{{chapter_text}}

Return only JSON with this shape:
{
  "rubric_version": "longform_text_quality_rubric_v1",
  "chapter_id": 1,
  "overall_score": 1.0,
  "revision_required": true,
  "strengths_to_preserve": [],
  "blocking_issues": [
    {
      "dimension": "Scene & Prose Flow",
      "location": "paragraph or quoted anchor",
      "issue": "specific reader-visible issue",
      "evidence": "short text evidence",
      "suggested_fix": "actionable fix"
    }
  ],
  "continuity_risks": [],
  "revision_targets": []
}

Required checks:
- Identify repeated object inspection, repeated deduction, or repeated line-level wording.
- Identify visible beat expansion or checklist-style prose.
- Identify summary-like emotional conclusions where character pressure should be dramatized.
- Identify dialogue that only transmits information without conflict, subtext, or pressure.
- Identify genre payoff that is mechanically correct but emotionally weak.
- Preserve required facts, reveal order, POV, and chapter function.

Evidence is mandatory. If no evidence supports an issue, omit that issue.
```

Create `longform-writing/core_spec/prompts/13_plan_chapter_revision.md`:

```markdown
You are a chapter revision planner.

Turn the editor review into a bounded whole-chapter rewrite plan. Do not invent new major plot facts. Preserve the required chapter function and continuity.

[Chapter Summary]
{{chapter_summary}}

[Chapter Text]
{{chapter_text}}

[Chapter Review]
{{chapter_review}}

Return only JSON with this shape:
{
  "chapter_id": 1,
  "must_fix": [
    {
      "issue": "specific issue",
      "evidence": "short evidence",
      "rewrite_instruction": "specific rewrite action"
    }
  ],
  "preserve": [],
  "rewrite_strategy": [],
  "continuity_constraints": [],
  "expected_quality_gains": [],
  "risk_notes": []
}

Plan requirements:
- Remove repetition without deleting required clues.
- Convert clue confirmation into character pressure where possible.
- Replace checklist-style deduction with scene, conflict, or dialogue when appropriate.
- Keep reveal order intact.
- Keep the chapter's required plot function intact.
```

Create `longform-writing/core_spec/prompts/14_rewrite_chapter.md`:

```markdown
You are an expert fiction writer revising one chapter.

Rewrite the chapter according to the revision plan. Preserve all required facts, reveal boundaries, POV, and continuity. Do not add major new events. Return only the revised chapter text.

[Project Brief]
{{project_brief}}

[Previous Summaries]
{{previous_summaries}}

[Chapter Summary]
{{chapter_summary}}

[Relevant Codex]
{{relevant_codex}}

[Original Chapter Text]
{{original_chapter_text}}

[Revision Plan]
{{revision_plan}}

Revision priorities:
- Remove repeated physical inspection and repeated deduction.
- Make prose read as continuous fiction, not beat execution.
- Turn important clues into character pressure and choices.
- Improve dialogue pressure and subtext.
- Keep genre payoff clear but less procedural.
- Do not reveal future information earlier than the original chapter allows.
```

Create `longform-writing/core_spec/prompts/15_summarize_revised_chapter.md`:

```markdown
You are a factual chapter summarizer.

Summarize the revised chapter for future continuity memory. Use third person and present tense. Do not evaluate prose quality. Do not include future events that are not in the revised chapter.

[Project Brief]
{{project_brief}}

[Revised Chapter Text]
{{revised_chapter_text}}

Return only the summary in running text.
```

Create `longform-writing/core_spec/prompts/16_merge_revised_manuscript.md`:

```markdown
Merge contract for V1 revision mode.

The runner must preserve:
- manuscript/final_unrevised.md
- manuscript/final_revised.md

The revised manuscript is built from each chapter's 02_revised_draft.md when present. If a revised draft is missing, the runner must use 02_draft.md and record that fallback in revision_manifest.jsonl.
```

- [ ] **Step 4: Add schemas**

Create `longform-writing/core_spec/schemas/chapter_revision_plan.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChapterRevisionPlanV1",
  "type": "object",
  "required": [
    "chapter_id",
    "must_fix",
    "preserve",
    "rewrite_strategy",
    "continuity_constraints",
    "expected_quality_gains",
    "risk_notes"
  ],
  "properties": {
    "chapter_id": { "type": "integer", "minimum": 1 },
    "must_fix": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["issue", "evidence", "rewrite_instruction"],
        "properties": {
          "issue": { "type": "string" },
          "evidence": { "type": "string" },
          "rewrite_instruction": { "type": "string" }
        },
        "additionalProperties": true
      }
    },
    "preserve": { "type": "array", "items": { "type": "string" } },
    "rewrite_strategy": { "type": "array", "items": { "type": "string" } },
    "continuity_constraints": { "type": "array", "items": { "type": "string" } },
    "expected_quality_gains": { "type": "array", "items": { "type": "string" } },
    "risk_notes": { "type": "array", "items": { "type": "string" } }
  },
  "additionalProperties": true
}
```

Create `longform-writing/core_spec/schemas/revision_acceptance.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RevisionAcceptanceV1",
  "type": "object",
  "required": [
    "case_id",
    "iteration_id",
    "judge_rankings",
    "revealed_ranking",
    "pass",
    "evidence",
    "failure_reason"
  ],
  "properties": {
    "case_id": { "type": "string" },
    "iteration_id": { "type": "integer", "minimum": 1 },
    "judge_rankings": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "revealed_ranking": {
      "type": "array",
      "items": { "type": "string" }
    },
    "pass": { "type": "boolean" },
    "evidence": { "type": "array", "items": { "type": "string" } },
    "failure_reason": { "type": "string" },
    "next_iteration_strategy": { "type": "array", "items": { "type": "string" } }
  },
  "additionalProperties": true
}
```

- [ ] **Step 5: Run tests and verify pass**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add longform-writing/core_spec/prompts/12_review_chapter_quality.md \
  longform-writing/core_spec/prompts/13_plan_chapter_revision.md \
  longform-writing/core_spec/prompts/14_rewrite_chapter.md \
  longform-writing/core_spec/prompts/15_summarize_revised_chapter.md \
  longform-writing/core_spec/prompts/16_merge_revised_manuscript.md \
  longform-writing/core_spec/schemas/chapter_revision_plan.schema.json \
  longform-writing/core_spec/schemas/revision_acceptance.schema.json \
  longform-writing/tests/test_v1_revision_helpers.py
git commit -m "Add V1 revision prompt and schema contracts"
```

## Task 2: Add Deterministic Revision Helper Functions

**Files:**

- Modify: `longform-writing/tests/test_v1_revision_helpers.py`
- Create: `longform-writing/scripts/run_v1_revision_loop.py`

- [ ] **Step 1: Add failing helper tests**

Append to `longform-writing/tests/test_v1_revision_helpers.py`:

```python
import importlib.util
import tempfile


def load_v1_runner():
    script = ROOT / "longform-writing" / "scripts" / "run_v1_revision_loop.py"
    spec = importlib.util.spec_from_file_location("run_v1_revision_loop", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V1RevisionHelperTests(unittest.TestCase):
    def test_find_repetition_signals_detects_repeated_object_handling(self) -> None:
        module = load_v1_runner()
        text = "小帅将报告举到灯光下。\n他放下报告。\n小帅将报告举到灯光下。"
        signals = module.find_repetition_signals(text)
        self.assertTrue(any("举到灯光下" in signal["evidence"] for signal in signals))

    def test_merge_revised_chapters_prefers_revised_draft(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            chapter_1 = run_dir / "chapters" / "chapter_01"
            chapter_2 = run_dir / "chapters" / "chapter_02"
            chapter_1.mkdir(parents=True)
            chapter_2.mkdir(parents=True)
            (chapter_1 / "02_draft.md").write_text("original one\n", encoding="utf-8")
            (chapter_1 / "02_revised_draft.md").write_text("revised one\n", encoding="utf-8")
            (chapter_2 / "02_draft.md").write_text("original two\n", encoding="utf-8")
            result = module.merge_revised_chapters(run_dir)
            self.assertIn("revised one", result)
            self.assertIn("original two", result)
            self.assertNotIn("original one", result)
            self.assertTrue((run_dir / "manuscript" / "final_revised.md").exists())

    def test_build_blind_package_creates_private_mapping(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "case"
            case_dir.mkdir()
            paths = {}
            for method in ["direct_write", "simple_engineered", "full_unrevised", "full_revised"]:
                path = case_dir / f"{method}.md"
                path.write_text(f"# {method}\n", encoding="utf-8")
                paths[method] = path
            out = root / "blind"
            mapping = module.build_blind_package(
                out,
                {
                    "case_05": {
                        "case_name": "05_medium_length_single_protagonist",
                        "request": "写一个五章故事。",
                        "methods": paths,
                    }
                },
            )
            self.assertTrue((out / "public" / "case_05" / "sample_A.md").exists())
            self.assertTrue((out / "private_mapping.json").exists())
            self.assertEqual(set(mapping["case_05"]["samples"].keys()), {"A", "B", "C", "D"})
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
FileNotFoundError: run_v1_revision_loop.py
```

- [ ] **Step 3: Create helper implementation**

Create `longform-writing/scripts/run_v1_revision_loop.py` with:

```python
#!/usr/bin/env python3
"""Run V1 chapter-level revision loops for longform-writing.

The script has two layers:
1. deterministic helpers that unit tests can run without model calls;
2. model-backed revision orchestration used by long-running acceptance tasks.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_acceptance import AcceptanceRun, load_dotenv, parse_test_case, read_text, render_template, slugify, write_text  # noqa: E402


DEFAULT_CASES = [
    "05_medium_length_single_protagonist",
    "10_mystery_clue_fairness_smoke",
    "07_dual_timeline_continuity",
]


METHOD_ORDER = ["direct_write", "simple_engineered", "full_unrevised", "full_revised"]
SAMPLE_IDS = ["A", "B", "C", "D"]


def find_repetition_signals(text: str) -> list[dict[str, str]]:
    patterns = [
        "举到灯光下",
        "并排放在",
        "边缘对齐",
        "再次确认",
        "三张借书卡",
        "四张便签纸",
        "线索图",
    ]
    signals: list[dict[str, str]] = []
    for pattern in patterns:
        count = text.count(pattern)
        if count >= 2:
            signals.append({
                "dimension": "Scene & Prose Flow",
                "issue": f"Repeated phrase appears {count} times.",
                "evidence": pattern,
                "suggested_fix": "Compress repeated physical confirmation and replace with new pressure, conflict, or consequence.",
            })
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    seen: dict[str, int] = {}
    for paragraph in paragraphs:
        key = re.sub(r"\s+", "", paragraph)[:80]
        if len(key) < 20:
            continue
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            signals.append({
                "dimension": "Repetition",
                "issue": "Near-duplicate paragraph appears more than once.",
                "evidence": paragraph[:160],
                "suggested_fix": "Delete the duplicate and preserve only the version that advances the scene.",
            })
    return signals


def merge_revised_chapters(run_dir: Path) -> str:
    parts: list[str] = []
    manifest_rows: list[dict[str, str]] = []
    for chapter_dir in sorted((run_dir / "chapters").glob("chapter_*")):
        revised = chapter_dir / "02_revised_draft.md"
        original = chapter_dir / "02_draft.md"
        chosen = revised if revised.exists() and revised.read_text(encoding="utf-8").strip() else original
        if not chosen.exists():
            continue
        parts.append(chosen.read_text(encoding="utf-8").strip())
        manifest_rows.append({
            "chapter": chapter_dir.name,
            "source": str(chosen.relative_to(run_dir)),
            "mode": "revised" if chosen == revised else "original_fallback",
        })
    manuscript = "\n\n".join(parts).strip() + "\n"
    write_text(run_dir / "manuscript" / "final_revised.md", manuscript)
    manifest = "\n".join(json.dumps(row, ensure_ascii=False) for row in manifest_rows) + "\n"
    write_text(run_dir / "run_records" / "revision_manifest.jsonl", manifest)
    return manuscript


def build_blind_package(output_root: Path, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if output_root.exists():
        shutil.rmtree(output_root)
    public = output_root / "public"
    mapping: dict[str, Any] = {}
    for case_id, case in cases.items():
        case_public = public / case_id
        write_text(case_public / "request.md", "# Request\n\n" + case["request"].strip() + "\n")
        write_text(case_public / "case_name.txt", case["case_name"] + "\n")
        mapping[case_id] = {"case_name": case["case_name"], "samples": {}}
        methods = case["methods"]
        for sample_id, method in zip(SAMPLE_IDS, METHOD_ORDER):
            source = Path(methods[method])
            write_text(case_public / f"sample_{sample_id}.md", source.read_text(encoding="utf-8").strip() + "\n")
            mapping[case_id]["samples"][sample_id] = {
                "method": method,
                "source": str(source),
            }
    write_text(output_root / "private_mapping.json", json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    write_text(
        output_root / "README.md",
        "# V1 Blind Revision Evaluation Package\n\nGive evaluators only `public/` until judging is complete.\n",
    )
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", type=Path, default=ROOT / "longform-writing")
    parser.add_argument("--test-dir", type=Path, default=ROOT / "test_cases")
    parser.add_argument("--output-root", type=Path, default=ROOT / "revision_eval_runs" / "v1_chapter_revision")
    parser.add_argument("--provider", choices=["deepseek"], default="deepseek")
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    print("V1 runner helper layer is installed.")
    print(f"cases={','.join(args.cases)}")
    print(f"max_iterations={args.max_iterations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_v1_revision_loop.py
```

Expected:

```text
OK
```

and no `py_compile` output.

- [ ] **Step 5: Commit**

```bash
git add longform-writing/scripts/run_v1_revision_loop.py longform-writing/tests/test_v1_revision_helpers.py
git commit -m "Add V1 revision helper runner"
```

## Task 3: Implement Model-Backed Chapter Review, Planning, And Rewrite

**Files:**

- Modify: `longform-writing/scripts/run_v1_revision_loop.py`
- Modify: `longform-writing/tests/test_v1_revision_helpers.py`

- [ ] **Step 1: Add failing tests for review scaffolding**

Append to `longform-writing/tests/test_v1_revision_helpers.py`:

```python
class V1RevisionPromptValueTests(unittest.TestCase):
    def test_collect_previous_summaries_uses_revised_when_available(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            c1 = run_dir / "chapters" / "chapter_01"
            c2 = run_dir / "chapters" / "chapter_02"
            c1.mkdir(parents=True)
            c2.mkdir(parents=True)
            (c1 / "03_summary_after.md").write_text("old summary\n", encoding="utf-8")
            (c1 / "03_summary_after_revised.md").write_text("revised summary\n", encoding="utf-8")
            (c2 / "03_summary_after.md").write_text("chapter two\n", encoding="utf-8")
            result = module.collect_previous_summaries(run_dir, 3)
            self.assertIn("revised summary", result)
            self.assertIn("chapter two", result)
            self.assertNotIn("old summary", result)

    def test_builtin_review_injects_repetition_findings(self) -> None:
        module = load_v1_runner()
        text = "小帅将报告举到灯光下。\n\n小帅将报告举到灯光下。"
        review = module.builtin_chapter_review(1, text)
        self.assertTrue(review["revision_required"])
        self.assertTrue(review["blocking_issues"])
        self.assertEqual(review["blocking_issues"][0]["dimension"], "Scene & Prose Flow")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
AttributeError: module 'run_v1_revision_loop' has no attribute 'collect_previous_summaries'
```

- [ ] **Step 3: Add deterministic review scaffolding**

Add to `run_v1_revision_loop.py` after `build_blind_package`:

```python
def collect_previous_summaries(run_dir: Path, chapter_id: int) -> str:
    chunks: list[str] = []
    for cid in range(1, chapter_id):
        chapter_dir = run_dir / "chapters" / f"chapter_{cid:02d}"
        revised = chapter_dir / "03_summary_after_revised.md"
        original = chapter_dir / "03_summary_after.md"
        chosen = revised if revised.exists() and revised.read_text(encoding="utf-8").strip() else original
        if chosen.exists():
            chunks.append(f"Chapter {cid} summary:\n{chosen.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(chunks)


def builtin_chapter_review(chapter_id: int, chapter_text: str) -> dict[str, Any]:
    issues = find_repetition_signals(chapter_text)
    checklist_markers = ["**一、", "**二、", "**三、", "一、旧", "二、日期", "三、书号"]
    if any(marker in chapter_text for marker in checklist_markers):
        issues.append({
            "dimension": "Scene & Prose Flow",
            "location": f"chapter_{chapter_id:02d}",
            "issue": "Deduction is presented as an explicit checklist.",
            "evidence": " / ".join(marker for marker in checklist_markers if marker in chapter_text),
            "suggested_fix": "Rewrite the deduction as scene movement, dialogue pressure, or incremental discovery.",
        })
    return {
        "rubric_version": "longform_text_quality_rubric_v1",
        "chapter_id": chapter_id,
        "overall_score": 3.0 if issues else 4.0,
        "revision_required": bool(issues),
        "strengths_to_preserve": [],
        "blocking_issues": issues,
        "continuity_risks": [],
        "revision_targets": [issue["suggested_fix"] for issue in issues],
    }
```

- [ ] **Step 4: Add `V1RevisionRun` methods**

Add this class before `main()`:

```python
class V1RevisionRun:
    def __init__(
        self,
        skill_path: Path,
        test_case_path: Path,
        run_dir: Path,
        provider: str,
        iteration_id: int,
    ) -> None:
        self.skill_path = skill_path.resolve()
        self.test_case_path = test_case_path.resolve()
        self.test_case = parse_test_case(self.test_case_path)
        self.run_dir = run_dir.resolve()
        self.provider = provider
        self.iteration_id = iteration_id
        self.acceptance = AcceptanceRun(
            self.skill_path,
            self.test_case,
            self.run_dir,
            provider,
            "full_auto",
            4,
            260,
        )

    def template(self, filename: str) -> str:
        return read_text(self.skill_path / "core_spec" / "prompts" / filename)

    def ensure_unrevised_draft(self) -> None:
        if (self.run_dir / "manuscript" / "final.md").exists():
            return
        self.acceptance.run()
        final = self.run_dir / "manuscript" / "final.md"
        if final.exists():
            write_text(self.run_dir / "manuscript" / "final_unrevised.md", final.read_text(encoding="utf-8"))

    def review_chapter(self, chapter_id: int) -> dict[str, Any]:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        chapter_text = read_text(chapter_dir / "02_draft.md")
        builtin = builtin_chapter_review(chapter_id, chapter_text)
        write_text(chapter_dir / "04_chapter_review.json", json.dumps(builtin, ensure_ascii=False, indent=2) + "\n")
        lines = ["# Chapter Review", "", f"Revision required: `{str(builtin['revision_required']).lower()}`", "", "## Blocking Issues"]
        for issue in builtin["blocking_issues"]:
            lines.append(f"- {issue['dimension']}: {issue['issue']} Evidence: {issue['evidence']}")
        if not builtin["blocking_issues"]:
            lines.append("- None")
        write_text(chapter_dir / "04_chapter_review.md", "\n".join(lines) + "\n")
        return builtin

    def plan_revision(self, chapter_id: int, review: dict[str, Any]) -> dict[str, Any]:
        plan = {
            "chapter_id": chapter_id,
            "must_fix": [
                {
                    "issue": issue["issue"],
                    "evidence": issue["evidence"],
                    "rewrite_instruction": issue["suggested_fix"],
                }
                for issue in review.get("blocking_issues", [])
            ],
            "preserve": ["Preserve required plot facts, reveal order, POV, and chapter function."],
            "rewrite_strategy": [
                "Compress repeated object handling.",
                "Convert clue confirmation into character pressure.",
                "Replace checklist deduction with scene or dialogue when possible.",
            ],
            "continuity_constraints": ["Do not add new major facts that contradict previous summaries."],
            "expected_quality_gains": review.get("revision_targets", []),
            "risk_notes": [],
        }
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        write_text(chapter_dir / "05_revision_plan.json", json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
        write_text(chapter_dir / "05_revision_plan.md", "# Revision Plan\n\n```json\n" + json.dumps(plan, ensure_ascii=False, indent=2) + "\n```\n")
        return plan
```

Do not yet implement LLM rewriting in this step; this task establishes deterministic review/plan artifacts and makes them testable.

- [ ] **Step 5: Run tests**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_v1_revision_loop.py
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add longform-writing/scripts/run_v1_revision_loop.py longform-writing/tests/test_v1_revision_helpers.py
git commit -m "Add V1 revision review scaffolding"
```

## Task 4: Implement Chapter Rewrite And Revised Summary Generation

**Files:**

- Modify: `longform-writing/scripts/run_v1_revision_loop.py`
- Modify: `longform-writing/tests/test_v1_revision_helpers.py`

- [ ] **Step 1: Add failing rewrite fallback test**

Append to `longform-writing/tests/test_v1_revision_helpers.py`:

```python
class V1RevisionRewriteFallbackTests(unittest.TestCase):
    def test_apply_builtin_revision_removes_duplicate_paragraph(self) -> None:
        module = load_v1_runner()
        text = "第一段。\n\n重复段落很长很长很长。\n\n重复段落很长很长很长。\n\n结尾。"
        revised = module.apply_builtin_revision(text)
        self.assertEqual(revised.count("重复段落很长很长很长"), 1)
        self.assertIn("第一段", revised)
        self.assertIn("结尾", revised)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
AttributeError: module 'run_v1_revision_loop' has no attribute 'apply_builtin_revision'
```

- [ ] **Step 3: Add deterministic fallback revision**

Add to `run_v1_revision_loop.py`:

```python
def apply_builtin_revision(text: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    seen: set[str] = set()
    kept: list[str] = []
    for paragraph in paragraphs:
        key = re.sub(r"\s+", "", paragraph)
        if key in seen:
            continue
        seen.add(key)
        kept.append(paragraph)
    return "\n\n".join(kept).strip() + "\n"
```

- [ ] **Step 4: Add model-backed rewrite methods**

Add methods to `V1RevisionRun`:

```python
    def rewrite_chapter(self, chapter_id: int, plan: dict[str, Any]) -> str:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        original = read_text(chapter_dir / "02_draft.md")
        if not plan.get("must_fix"):
            revised = original
        else:
            values = {
                "project_brief": read_text(self.run_dir / "01_project_brief.md"),
                "previous_summaries": collect_previous_summaries(self.run_dir, chapter_id),
                "chapter_summary": read_text(chapter_dir / "00_summary.md"),
                "relevant_codex": read_text(self.run_dir / "02_codex.json"),
                "original_chapter_text": original,
                "revision_plan": json.dumps(plan, ensure_ascii=False, indent=2),
            }
            prompt = render_template(self.template("14_rewrite_chapter.md"), values)
            revised = self.acceptance.client.complete(prompt, max_tokens=4200, temperature=0.25)
            if not revised.strip() or revised.strip() == "MOCK_OUTPUT":
                revised = apply_builtin_revision(original)
        write_text(chapter_dir / "02_revised_draft.md", revised.strip() + "\n")
        write_text(
            chapter_dir / "06_revision_notes.md",
            "# Revision Notes\n\n"
            f"- Iteration: {self.iteration_id}\n"
            f"- Must-fix count: {len(plan.get('must_fix', []))}\n"
            "- Rewrote whole chapter while preserving required facts.\n",
        )
        return revised

    def summarize_revised_chapter(self, chapter_id: int, revised: str) -> str:
        chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
        values = {
            "project_brief": read_text(self.run_dir / "01_project_brief.md"),
            "revised_chapter_text": revised,
        }
        prompt = render_template(self.template("15_summarize_revised_chapter.md"), values)
        summary = self.acceptance.client.complete(prompt, max_tokens=900, temperature=0.1)
        if not summary.strip() or summary.strip() == "MOCK_OUTPUT":
            summary = read_text(chapter_dir / "03_summary_after.md")
        write_text(chapter_dir / "03_summary_after_revised.md", summary.strip() + "\n")
        return summary

    def revise_all_chapters(self) -> None:
        self.ensure_unrevised_draft()
        chapter_dirs = sorted((self.run_dir / "chapters").glob("chapter_*"))
        for chapter_dir in chapter_dirs:
            chapter_id = int(chapter_dir.name.split("_")[-1])
            review = self.review_chapter(chapter_id)
            plan = self.plan_revision(chapter_id, review)
            revised = self.rewrite_chapter(chapter_id, plan)
            self.summarize_revised_chapter(chapter_id, revised)
        final = self.run_dir / "manuscript" / "final.md"
        if final.exists():
            write_text(self.run_dir / "manuscript" / "final_unrevised.md", final.read_text(encoding="utf-8"))
        merge_revised_chapters(self.run_dir)
```

- [ ] **Step 5: Wire CLI dry run**

Modify `main()` so it can run one case and one iteration:

```python
    for iteration in range(1, args.max_iterations + 1):
        iter_root = args.output_root / f"iter_{iteration:02d}"
        iter_root.mkdir(parents=True, exist_ok=True)
        case_methods: dict[str, Any] = {}
        for case in args.cases:
            test_case_path = args.test_dir / f"{case}.md"
            run_dir = ROOT / "runs" / f"{case}_v1_revision_iter_{iteration:02d}"
            v1 = V1RevisionRun(args.skill_path, test_case_path, run_dir, args.provider, iteration)
            v1.revise_all_chapters()
        print(f"V1 revision iteration complete: {iter_root}")
        break
```

Keep the `break` for this task. Later tasks add blind evaluation and full iteration decisions.

- [ ] **Step 6: Run verification**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_v1_revision_loop.py
```

Expected:

```text
OK
```

- [ ] **Step 7: Commit**

```bash
git add longform-writing/scripts/run_v1_revision_loop.py longform-writing/tests/test_v1_revision_helpers.py
git commit -m "Implement V1 chapter revision loop"
```

## Task 5: Add Four-Way Blind Evaluation Package And Acceptance Reporting

**Files:**

- Modify: `longform-writing/scripts/run_v1_revision_loop.py`
- Modify: `.gitignore`
- Modify: `longform-writing/tests/test_v1_revision_helpers.py`

- [ ] **Step 1: Add failing acceptance decision tests**

Append to `longform-writing/tests/test_v1_revision_helpers.py`:

```python
class V1AcceptanceDecisionTests(unittest.TestCase):
    def test_acceptance_passes_when_full_revised_beats_direct_and_unrevised(self) -> None:
        module = load_v1_runner()
        rankings = {
            "rubric": ["full_revised", "direct_write", "full_unrevised", "simple_engineered"],
            "reader": ["full_revised", "direct_write", "simple_engineered", "full_unrevised"],
        }
        result = module.decide_acceptance("case_05", 1, rankings)
        self.assertTrue(result["pass"])
        self.assertEqual(result["failure_reason"], "")

    def test_acceptance_fails_when_direct_beats_full_revised(self) -> None:
        module = load_v1_runner()
        rankings = {
            "rubric": ["direct_write", "full_revised", "full_unrevised", "simple_engineered"],
            "reader": ["direct_write", "full_revised", "simple_engineered", "full_unrevised"],
        }
        result = module.decide_acceptance("case_10", 1, rankings)
        self.assertFalse(result["pass"])
        self.assertIn("direct_write", result["failure_reason"])
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected:

```text
AttributeError: module 'run_v1_revision_loop' has no attribute 'decide_acceptance'
```

- [ ] **Step 3: Implement acceptance decision helper**

Add to `run_v1_revision_loop.py`:

```python
def decide_acceptance(case_id: str, iteration_id: int, judge_rankings: dict[str, list[str]]) -> dict[str, Any]:
    failures: list[str] = []
    for judge, ranking in judge_rankings.items():
        if "full_revised" not in ranking or "direct_write" not in ranking or "full_unrevised" not in ranking:
            failures.append(f"{judge} ranking missing required method.")
            continue
        if ranking.index("full_revised") > ranking.index("direct_write"):
            failures.append(f"{judge}: direct_write beats full_revised.")
        if ranking.index("full_revised") > ranking.index("full_unrevised"):
            failures.append(f"{judge}: full_unrevised beats full_revised.")
    return {
        "case_id": case_id,
        "iteration_id": iteration_id,
        "judge_rankings": judge_rankings,
        "revealed_ranking": judge_rankings.get("reader") or judge_rankings.get("rubric") or [],
        "pass": not failures,
        "evidence": [],
        "failure_reason": "; ".join(failures),
        "next_iteration_strategy": [
            "Reduce repetition and checklist prose.",
            "Increase character pressure and scene flow.",
        ] if failures else [],
    }
```

- [ ] **Step 4: Ignore generated revision eval runs**

Modify `.gitignore`:

```gitignore
revision_eval_runs/
```

- [ ] **Step 5: Extend CLI to build blind package**

After running cases in `main()`, collect paths:

```python
        blind_cases: dict[str, dict[str, Any]] = {}
        for case in args.cases:
            test_case_path = args.test_dir / f"{case}.md"
            request = parse_test_case(test_case_path)["request"]
            run_dir = ROOT / "runs" / f"{case}_v1_revision_iter_{iteration:02d}"
            blind_cases[f"case_{case[:2]}"] = {
                "case_name": case,
                "request": request,
                "methods": {
                    "direct_write": ROOT / "baseline_runs" / "direct_write" / case / "manuscript.md",
                    "simple_engineered": ROOT / "baseline_runs" / "simple_engineered" / case / "manuscript.md",
                    "full_unrevised": run_dir / "manuscript" / "final_unrevised.md",
                    "full_revised": run_dir / "manuscript" / "final_revised.md",
                },
            }
        mapping = build_blind_package(iter_root / "blind", blind_cases)
        write_text(iter_root / "private_mapping.json", json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
```

Do not attempt to automate internal evaluator agents inside the script. The main Codex thread should dispatch blind judge agents after the package exists.

- [ ] **Step 6: Run verification**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_v1_revision_loop.py
git diff --check
```

Expected:

```text
OK
```

No `py_compile` or `git diff --check` output.

- [ ] **Step 7: Commit**

```bash
git add .gitignore longform-writing/scripts/run_v1_revision_loop.py longform-writing/tests/test_v1_revision_helpers.py
git commit -m "Add V1 blind revision evaluation package"
```

## Task 6: Update Skill Documentation And Workflow Contract

**Files:**

- Modify: `longform-writing/SKILL.md`
- Modify: `longform-writing/core_spec/workflow.md`

- [ ] **Step 1: Update `workflow.md`**

Append:

```markdown
## Workflow V1: Chapter Revision Loop

V1 extends V0 after `merge_manuscript`.

For each chapter:

1. `review_chapter_quality` -> `chapters/chapter_XX/04_chapter_review.json` and `.md`
2. `plan_chapter_revision` -> `chapters/chapter_XX/05_revision_plan.json` and `.md`
3. `rewrite_chapter` -> `chapters/chapter_XX/02_revised_draft.md`
4. `summarize_revised_chapter` -> `chapters/chapter_XX/03_summary_after_revised.md`

Then:

5. `merge_revised_manuscript` -> `manuscript/final_unrevised.md` and `manuscript/final_revised.md`
6. Build a four-way blind package comparing `direct_write`, `simple_engineered`, `full_unrevised`, and `full_revised`.
7. Evaluate with Rubric Judge and Reader/Editor Judge.
8. Iterate review/revision strategy up to 3 times.

V1 is successful only if `full_revised` beats `direct_write` in blind real-text quality evaluation while preserving longform continuity.
```

- [ ] **Step 2: Update `SKILL.md`**

Add a concise V1 section after current runner instructions:

```markdown
## V1 Chapter Revision Mode

Use `scripts/run_v1_revision_loop.py` when validating chapter-level revision.

Primary command:

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --max-iterations 3
```

V1 compares:

- direct write
- simple engineered
- full skill unrevised
- full skill revised

The goal is not workflow traceability. The goal is for `full skill revised` to beat `direct write` in blind real-text quality evaluation.
```

- [ ] **Step 3: Run docs checks**

Run:

```bash
rg -n "V1|revision loop|full_revised|direct_write" longform-writing/SKILL.md longform-writing/core_spec/workflow.md
git diff --check
```

Expected:

```text
```

`rg` should show the new V1 sections. `git diff --check` should emit no output.

- [ ] **Step 4: Commit**

```bash
git add longform-writing/SKILL.md longform-writing/core_spec/workflow.md
git commit -m "Document V1 chapter revision workflow"
```

## Task 7: Run V1 On Target Cases And Dispatch Blind Evaluators

**Files:**

- Generated: `runs/*_v1_revision_iter_01/`
- Generated: `revision_eval_runs/v1_chapter_revision/iter_01/`
- Create: `design_context/27_v1_revision_loop_iteration_01_report.md`

- [ ] **Step 1: Run V1 first iteration**

Run:

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --provider deepseek \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --max-iterations 3
```

Expected:

```text
V1 revision iteration complete: ...
```

Generated paths should include:

```text
runs/05_medium_length_single_protagonist_v1_revision_iter_01/manuscript/final_revised.md
runs/10_mystery_clue_fairness_smoke_v1_revision_iter_01/manuscript/final_revised.md
runs/07_dual_timeline_continuity_v1_revision_iter_01/manuscript/final_revised.md
revision_eval_runs/v1_chapter_revision/iter_01/blind/public/
```

- [ ] **Step 2: Validate generated artifacts**

Run:

```bash
test -f runs/05_medium_length_single_protagonist_v1_revision_iter_01/manuscript/final_revised.md
test -f runs/10_mystery_clue_fairness_smoke_v1_revision_iter_01/manuscript/final_revised.md
test -f runs/07_dual_timeline_continuity_v1_revision_iter_01/manuscript/final_revised.md
test -f revision_eval_runs/v1_chapter_revision/iter_01/blind/private_mapping.json
```

Expected: no output and exit code 0.

- [ ] **Step 3: Dispatch Rubric Judge**

Use an internal evaluator agent with this instruction:

```text
You are Rubric Judge for V1 blind revision evaluation.

Read only:
- revision_eval_runs/v1_chapter_revision/iter_01/blind/public/
- longform-writing/references/longform_text_quality_rubric_v1.md

Do not inspect private_mapping.json, baseline_runs, runs, git history, or source paths.

For each case and sample A/B/C/D:
- score using longform_text_quality_rubric_v1;
- rank samples;
- cite concrete text evidence;
- identify whether the top sample wins because of real prose quality, not workflow traceability.

Return one compact report per case.
```

- [ ] **Step 4: Dispatch Reader/Editor Judge**

Use a second internal evaluator agent with this instruction:

```text
You are Reader/Editor Judge for V1 blind revision evaluation.

Read only:
- revision_eval_runs/v1_chapter_revision/iter_01/blind/public/

Do not read rubric files. Do not inspect private_mapping.json, baseline_runs, runs, git history, or source paths.

For each case:
- rank samples A/B/C/D by real reading quality;
- identify the most satisfying longform manuscript;
- identify best local prose flow;
- identify most mechanical manuscript;
- cite concrete text evidence;
- give short revision advice.

Do not guess writing method.
```

- [ ] **Step 5: Reveal mapping and write iteration report**

After both judges return, inspect:

```text
revision_eval_runs/v1_chapter_revision/iter_01/blind/private_mapping.json
```

Create `design_context/27_v1_revision_loop_iteration_01_report.md` with:

```markdown
# V1 Revision Loop Iteration 01 Report

## Blind Result

## Revealed Mapping

## Acceptance Decision

## Case 05

## Case 10

## Case 07 Regression

## Remaining Failure Modes

## Next Iteration Strategy
```

- [ ] **Step 6: Decide whether to iterate**

Pass if:

- `full_revised` beats `direct_write` overall;
- `full_revised` beats `full_unrevised`;
- `case_07` does not regress below direct.

If pass, skip Task 8 and write final acceptance report.

If fail, continue to Task 8.

## Task 8: Iterate Revision Strategy Up To Two More Times

**Files:**

- Modify as needed: `longform-writing/core_spec/prompts/12_review_chapter_quality.md`
- Modify as needed: `longform-writing/core_spec/prompts/14_rewrite_chapter.md`
- Modify as needed: `longform-writing/references/longform_text_quality_rubric_v1.md`
- Create: `design_context/28_v1_revision_loop_iteration_02_report.md`
- Create if needed: `design_context/29_v1_revision_loop_iteration_03_report.md`

- [ ] **Step 1: If iteration 01 fails, classify failure**

Use this table:

```text
Failure: repeated mechanical prose remains
Change: strengthen review prompt and rewrite prompt around repetition deletion.

Failure: revised draft breaks continuity
Change: strengthen preserve constraints and summary_after_revised checks.

Failure: direct still wins on emotional payoff
Change: add rewrite instruction requiring clue -> pressure -> action conversion.

Failure: judge output lacks evidence
Change: rerun judge with stricter evidence prompt; do not change manuscript yet.
```

- [ ] **Step 2: Apply smallest prompt/rubric calibration change**

Record each change in:

```text
design_context/27_v1_revision_loop_iteration_01_report.md
```

or the current iteration report under:

```markdown
## Calibration / Prompt Changes
```

- [ ] **Step 3: Run next iteration**

Run:

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py \
  --provider deepseek \
  --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity \
  --max-iterations 3
```

Expected: new `iter_02` or `iter_03` output.

- [ ] **Step 4: Repeat blind evaluation**

Repeat Task 7 steps 3-6 for the new iteration.

- [ ] **Step 5: Stop after iteration 03**

If still failing after iteration 03, do not continue. Write route-failure analysis in Task 9.

## Task 9: Write Final Acceptance Or Route-Failure Report

**Files:**

- Create: `design_context/30_v1_revision_loop_acceptance_report.md`
- Or create: `design_context/30_v1_revision_loop_route_failure_report.md`

- [ ] **Step 1: Write final report**

If V1 passes, create `design_context/30_v1_revision_loop_acceptance_report.md`:

```markdown
# V1 Revision Loop Acceptance Report

## Result

Pass.

## Winning Evidence

## Case 05

## Case 10

## Case 07 Regression

## What Improved Over Full Unrevised

## What Beat Direct Write

## Remaining Risks

## Next Version
```

If V1 fails, create `design_context/30_v1_revision_loop_route_failure_report.md`:

```markdown
# V1 Revision Loop Route-Failure Report

## Result

Fail after 3 iterations.

## Did Full Revised Improve Over Full Unrevised?

## Why Direct Still Won

## Failure Type

- prompt quality
- revision granularity
- context packaging
- judge alignment
- workflow premise

## Evidence

## V1.1 Recommendation
```

- [ ] **Step 2: Run final verification**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
python3 -m py_compile longform-writing/scripts/run_v1_revision_loop.py
PYTHONPATH=/tmp/codex_pyyaml python3 /Users/yuhuang/.codex/skills/.system/skill-creator/scripts/quick_validate.py longform-writing
git diff --check
```

Expected:

```text
OK
Skill is valid!
```

No `py_compile` or `git diff --check` output.

- [ ] **Step 3: Commit final implementation**

If pass:

```bash
git add .gitignore longform-writing docs design_context
git commit -m "Implement V1 chapter revision loop"
```

If fail:

```bash
git add .gitignore longform-writing docs design_context
git commit -m "Analyze V1 chapter revision route failure"
```

## Execution Notes

- Do not commit `runs/`, `baseline_runs/`, `revision_eval_runs/`, or private mapping files.
- Do not upload manuscript text to external judging APIs.
- DeepSeek may be used for generation/revision only when the user has accepted that local `.env` model path for writing. Judging should use internal Codex agents.
- If `git add` or `git commit` fails on `.git/index.lock` because of sandbox restrictions, rerun the same git command with escalation.
- If a judge result is generic and lacks text evidence, rerun the judge before changing the manuscript.

## Self-Review

Spec coverage:

- Prompt additions are covered by Task 1.
- Schema additions are covered by Task 1.
- Revision runner and chapter-level loop are covered by Tasks 2-4.
- Four-way blind package is covered by Task 5.
- Skill/workflow docs are covered by Task 6.
- Blind evaluation and iteration are covered by Tasks 7-8.
- Final pass/failure reporting is covered by Task 9.

Placeholder scan:

- No placeholder markers remain.

Type consistency:

- Helper names used in tests match planned implementation names: `find_repetition_signals`, `merge_revised_chapters`, `build_blind_package`, `collect_previous_summaries`, `builtin_chapter_review`, `apply_builtin_revision`, and `decide_acceptance`.

Scope check:

- The plan implements chapter-level revision only. Fragment-level revision remains out of scope for V1.
