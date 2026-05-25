from __future__ import annotations

import json
import http.client
import os
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
                "{{previous_revised_tail}}",
                "{{manuscript_revision_context}}",
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


def load_acceptance_runner():
    script = ROOT / "longform-writing" / "scripts" / "run_acceptance.py"
    spec = importlib.util.spec_from_file_location("run_acceptance", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V1RevisionHelperTests(unittest.TestCase):
    def test_require_external_model_export_approval_rejects_deepseek_without_flag(self) -> None:
        module = load_v1_runner()

        with self.assertRaises(RuntimeError) as ctx:
            module.require_external_model_export_approval("deepseek", False)

        self.assertIn("--allow-external-model-export", str(ctx.exception))

    def test_require_external_model_export_approval_accepts_deepseek_with_flag(self) -> None:
        module = load_v1_runner()

        module.require_external_model_export_approval("deepseek", True)

    def test_model_client_retries_incomplete_read(self) -> None:
        module = load_acceptance_runner()
        calls = {"count": 0}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps({
                    "choices": [{"message": {"content": "retry ok"}}],
                }).encode("utf-8")

        def fake_urlopen(request, timeout):
            calls["count"] += 1
            if calls["count"] == 1:
                raise http.client.IncompleteRead(b"")
            return FakeResponse()

        old_urlopen = module.urllib.request.urlopen
        old_env = {key: os.environ.get(key) for key in ["DEEPSEEK_API_KEY", "DEEPSEEK_MAX_RETRIES", "DEEPSEEK_RETRY_BASE_DELAY"]}
        try:
            os.environ["DEEPSEEK_API_KEY"] = "test-key"
            os.environ["DEEPSEEK_MAX_RETRIES"] = "2"
            os.environ["DEEPSEEK_RETRY_BASE_DELAY"] = "0"
            module.urllib.request.urlopen = fake_urlopen
            client = module.ModelClient("deepseek")

            self.assertEqual(client.complete("hello"), "retry ok")
            self.assertEqual(calls["count"], 2)
        finally:
            module.urllib.request.urlopen = old_urlopen
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

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

    def test_sanitize_scene_beats_drops_empty_placeholder(self) -> None:
        module = load_acceptance_runner()
        beats = [
            {"beat_id": 1, "text": "小帅按下第三段录像的播放键。", "purpose": "present action"},
            {"beat_id": 2, "text": "", "purpose": "", "required_codex": []},
            {"beat_id": 3, "text": "录像揭示小帅删掉风险提示。", "purpose": "past reveal"},
        ]
        sanitized = module.sanitize_scene_beats(beats)
        self.assertEqual([beat["text"] for beat in sanitized], [
            "小帅按下第三段录像的播放键。",
            "录像揭示小帅删掉风险提示。",
        ])

    def test_ensure_unrevised_draft_rejects_incomplete_v0_run(self) -> None:
        module = load_v1_runner()

        class IncompleteAcceptance:
            def run(self) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            runner = module.V1RevisionRun.__new__(module.V1RevisionRun)
            runner.run_dir = run_dir
            runner.acceptance = IncompleteAcceptance()

            with self.assertRaises(RuntimeError) as ctx:
                runner.ensure_unrevised_draft()

            self.assertIn("final.md", str(ctx.exception))


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

    def test_acceptance_fails_without_required_judges(self) -> None:
        module = load_v1_runner()
        result = module.decide_acceptance("case_05", 1, {})
        self.assertFalse(result["pass"])
        self.assertIn("rubric ranking missing", result["failure_reason"])
        self.assertIn("reader ranking missing", result["failure_reason"])

    def test_acceptance_rejects_invalid_rankings(self) -> None:
        module = load_v1_runner()
        rankings = {
            "rubric": ["full_revised", "direct_write", "direct_write", "unknown_method"],
            "reader": ["full_revised", "direct_write", "full_unrevised", "simple_engineered"],
        }
        result = module.decide_acceptance("case_05", 1, rankings)
        self.assertFalse(result["pass"])
        self.assertIn("unknown methods", result["failure_reason"])
        self.assertIn("missing required methods", result["failure_reason"])
        self.assertIn("duplicate methods", result["failure_reason"])

    def test_iteration_root_uses_task_7_contract(self) -> None:
        module = load_v1_runner()
        self.assertEqual(
            module.iteration_root(Path("revision_eval_runs/v1_chapter_revision"), 1),
            Path("revision_eval_runs/v1_chapter_revision/iter_01"),
        )

    def test_cli_accepts_start_iteration_without_changing_default(self) -> None:
        module = load_v1_runner()
        parser = module.build_argument_parser()

        default_args = parser.parse_args([])
        self.assertEqual(default_args.start_iteration, 1)

        args = parser.parse_args(["--start-iteration", "2", "--max-iterations", "3"])
        self.assertEqual(args.start_iteration, 2)
        self.assertEqual(args.max_iterations, 3)
        self.assertEqual(module.iteration_root(Path("out"), args.start_iteration), Path("out/iter_02"))


class V1RevisionPromptValueTests(unittest.TestCase):
    def test_collect_previous_summaries_uses_revised_when_available(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            c1 = run_dir / "chapters" / "chapter_01"
            c2 = run_dir / "chapters" / "chapter_02"
            c3 = run_dir / "chapters" / "chapter_03"
            c4 = run_dir / "chapters" / "chapter_04"
            c1.mkdir(parents=True)
            c2.mkdir(parents=True)
            c3.mkdir(parents=True)
            c4.mkdir(parents=True)
            (c1 / "03_summary_after.md").write_text("old summary\n", encoding="utf-8")
            (c1 / "03_summary_after_revised.md").write_text("revised summary\n", encoding="utf-8")
            (c2 / "03_summary_after.md").write_text("chapter two\n", encoding="utf-8")
            (c3 / "03_summary_after.md").write_text("current chapter\n", encoding="utf-8")
            (c4 / "03_summary_after.md").write_text("future chapter\n", encoding="utf-8")
            result = module.collect_previous_summaries(run_dir, 3)
            self.assertIn("revised summary", result)
            self.assertIn("chapter two", result)
            self.assertNotIn("old summary", result)
            self.assertNotIn("current chapter", result)
            self.assertNotIn("future chapter", result)

    def test_collect_previous_revised_tail_uses_revised_draft_only_from_previous_chapter(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            c1 = run_dir / "chapters" / "chapter_01"
            c2 = run_dir / "chapters" / "chapter_02"
            c3 = run_dir / "chapters" / "chapter_03"
            c1.mkdir(parents=True)
            c2.mkdir(parents=True)
            c3.mkdir(parents=True)
            (c1 / "02_revised_draft.md").write_text("第一章修订尾部。", encoding="utf-8")
            (c2 / "02_revised_draft.md").write_text("第二章修订尾部。", encoding="utf-8")
            (c3 / "02_revised_draft.md").write_text("第三章不应进入。", encoding="utf-8")

            result = module.collect_previous_revised_tail(run_dir, 3, max_chars=20)

            self.assertIn("第二章修订尾部", result)
            self.assertNotIn("第一章修订尾部", result)
            self.assertNotIn("第三章不应进入", result)

    def test_build_manuscript_revision_context_flags_overused_procedural_terms(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            c1 = run_dir / "chapters" / "chapter_01"
            c2 = run_dir / "chapters" / "chapter_02"
            c1.mkdir(parents=True)
            c2.mkdir(parents=True)
            repeated = "第一，他确认纸纤维。第二，他再次确认纸纤维。第三，他排除其他可能。"
            (c1 / "02_draft.md").write_text(repeated, encoding="utf-8")
            (c2 / "02_draft.md").write_text(repeated, encoding="utf-8")

            result = module.build_manuscript_revision_context(run_dir, 1)

            self.assertIn("Manuscript-Level Revision Context", result)
            self.assertIn("纸纤维", result)
            self.assertIn("numbered or list-like deduction", result)

    def test_builtin_review_injects_repetition_findings(self) -> None:
        module = load_v1_runner()
        text = "小帅将报告举到灯光下。\n\n小帅将报告举到灯光下。"
        review = module.builtin_chapter_review(1, text)
        self.assertTrue(review["revision_required"])
        self.assertTrue(review["blocking_issues"])
        self.assertEqual(review["blocking_issues"][0]["dimension"], "Scene & Prose Flow")

    def test_builtin_review_flags_obvious_procedural_prose(self) -> None:
        module = load_v1_runner()
        text = (
            "第一步，他先核对借书卡上的日期。\n"
            "第二步，他再确认书号和便签纸能对应。\n"
            "第三步，他最后排除其他可能。"
        )
        review = module.builtin_chapter_review(5, text)
        issues = review["blocking_issues"]
        self.assertTrue(any("procedural" in issue["issue"].lower() for issue in issues))

    def test_ensure_unrevised_draft_copies_existing_final(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            manuscript = run_dir / "manuscript"
            manuscript.mkdir()
            (manuscript / "final.md").write_text("existing full draft\n", encoding="utf-8")
            runner = module.V1RevisionRun.__new__(module.V1RevisionRun)
            runner.run_dir = run_dir

            runner.ensure_unrevised_draft()

            self.assertEqual(
                (manuscript / "final_unrevised.md").read_text(encoding="utf-8"),
                "existing full draft\n",
            )

    def test_plan_revision_includes_default_quality_targets_without_blocking_issues(self) -> None:
        module = load_v1_runner()
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "chapters" / "chapter_01").mkdir(parents=True)
            runner = module.V1RevisionRun.__new__(module.V1RevisionRun)
            runner.run_dir = run_dir

            plan = runner.plan_revision(1, {"blocking_issues": [], "revision_targets": []})

            self.assertEqual(plan["must_fix"], [])
            self.assertTrue(plan["quality_targets"])
            self.assertTrue(any("reveal order" in item for item in plan["quality_targets"]))
            self.assertTrue(any("whole chapter" in item for item in plan["rewrite_strategy"]))


class V1RevisionRewriteFallbackTests(unittest.TestCase):
    def test_apply_builtin_revision_removes_duplicate_paragraphs(self) -> None:
        module = load_v1_runner()
        text = "第一段。\n\n重复段落很长很长很长。\n\n重复段落很长很长很长。\n\n结尾。"
        revised = module.apply_builtin_revision(text)
        self.assertEqual(revised.count("重复段落很长很长很长。"), 1)
        self.assertTrue(revised.startswith("第一段。"))
        self.assertTrue(revised.strip().endswith("结尾。"))

    def test_rewrite_chapter_calls_model_when_must_fix_is_empty(self) -> None:
        module = load_v1_runner()

        class FakeClient:
            def __init__(self) -> None:
                self.prompts: list[str] = []

            def complete(self, prompt: str, *, max_tokens: int, temperature: float) -> str:
                self.prompts.append(prompt)
                return "模型重写后的章节。"

        class FakeAcceptance:
            def __init__(self) -> None:
                self.client = FakeClient()
                self.records: list[tuple] = []

            def read_project(self, path: str) -> str:
                values = {
                    "01_project_brief.md": "项目简报",
                    "chapters/chapter_01/00_summary.md": "章节摘要",
                }
                return values.get(path, "")

            def select_codex(self, text: str) -> tuple[list[str], str]:
                return [], "相关设定"

            def record(self, *args) -> None:
                self.records.append(args)

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            chapter_dir = run_dir / "chapters" / "chapter_01"
            chapter_dir.mkdir(parents=True)
            (chapter_dir / "02_draft.md").write_text("原始章节。", encoding="utf-8")
            runner = module.V1RevisionRun.__new__(module.V1RevisionRun)
            runner.run_dir = run_dir
            runner.acceptance = FakeAcceptance()
            runner.template = lambda filename: (
                "Original={{original_chapter_text}}\n"
                "Plan={{revision_plan}}\n"
                "Codex={{relevant_codex}}\n"
                "Tail={{previous_revised_tail}}\n"
                "Manuscript={{manuscript_revision_context}}"
            )

            revised = runner.rewrite_chapter(1, {"must_fix": [], "quality_targets": ["改善文本质感"]})

            self.assertEqual(revised, "模型重写后的章节。\n")
            self.assertEqual(len(runner.acceptance.client.prompts), 1)
            self.assertIn("Original=原始章节。", runner.acceptance.client.prompts[0])
            self.assertIn('"must_fix": []', runner.acceptance.client.prompts[0])
            self.assertIn('"改善文本质感"', runner.acceptance.client.prompts[0])
            self.assertIn("Manuscript=## Manuscript-Level Revision Context", runner.acceptance.client.prompts[0])
            self.assertIn("model rewrite", (chapter_dir / "06_revision_notes.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
