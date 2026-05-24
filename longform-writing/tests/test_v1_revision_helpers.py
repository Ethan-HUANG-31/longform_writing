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
