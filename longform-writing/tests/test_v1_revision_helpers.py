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

    def test_merge_revised_chapters_rejects_missing_chapter_source(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            chapter_1 = run_dir / "chapters" / "chapter_01"
            chapter_2 = run_dir / "chapters" / "chapter_02"
            chapter_1.mkdir(parents=True)
            chapter_2.mkdir(parents=True)
            (chapter_1 / "02_draft.md").write_text("original one\n", encoding="utf-8")

            with self.assertRaises(FileNotFoundError):
                module.merge_revised_chapters(run_dir)

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

    def test_build_blind_package_preserves_unknown_output_children(self) -> None:
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
            (out / "public" / "old_case").mkdir(parents=True)
            (out / "private_mapping.json").write_text("{}\n", encoding="utf-8")
            (out / "README.md").write_text("old readme\n", encoding="utf-8")
            keep = out / "keep.txt"
            keep.write_text("do not remove\n", encoding="utf-8")

            module.build_blind_package(
                out,
                {
                    "case_05": {
                        "case_name": "05_medium_length_single_protagonist",
                        "request": "写一个五章故事。",
                        "methods": paths,
                    }
                },
            )

            self.assertTrue(keep.exists())
            self.assertFalse((out / "public" / "old_case").exists())
            self.assertTrue((out / "public" / "case_05" / "sample_A.md").exists())

    def test_build_blind_package_rejects_repo_root_output(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            fake_repo_root = Path(tmp) / "repo"
            fake_repo_root.mkdir()
            module.ROOT = fake_repo_root

            with self.assertRaises(ValueError):
                module.build_blind_package(fake_repo_root, {})


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


if __name__ == "__main__":
    unittest.main()
