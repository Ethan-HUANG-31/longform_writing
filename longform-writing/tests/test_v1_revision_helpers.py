from __future__ import annotations

import json
import unittest
import importlib.util
import tempfile
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


if __name__ == "__main__":
    unittest.main()
