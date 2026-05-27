from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "longform-writing" / "scripts"


def load_module(name: str, filename: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class WorkflowModularizationTests(unittest.TestCase):
    def test_core_exports_context_and_helpers(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")

        self.assertTrue(hasattr(core, "WorkflowContext"))
        self.assertTrue(hasattr(core, "WorkflowState"))
        self.assertTrue(hasattr(core, "WorkflowResult"))
        self.assertTrue(hasattr(core, "ModelClient"))
        self.assertTrue(hasattr(core, "parse_test_case"))
        self.assertTrue(hasattr(core, "render_template"))

    def test_context_records_manifest_and_prompt(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            ctx = core.WorkflowContext(
                skill_path=ROOT / "longform-writing",
                test_case={"name": "unit_case", "request": "写一个三章中文故事。", "markdown": "", "feedback": {}},
                run_dir=run_dir,
                provider="mock",
                mode="full_auto",
                beat_count=4,
                prose_word_count=260,
            )
            ctx.initialize_project()
            ctx.record(
                "unit_step",
                "unit_template",
                "rendered prompt",
                ["00_request.md"],
                ["01_project_brief.md"],
                "success",
                ["Unit Context"],
                {"genre_adapter": "general"},
            )

            manifest = run_dir / "run_records" / "step_manifest.jsonl"
            rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(rows[0]["workflow_step"], "unit_step")
            self.assertEqual(rows[0]["context_sections"], ["Unit Context"])
            prompt_path = run_dir / rows[0]["rendered_prompt"]
            self.assertEqual(prompt_path.read_text(encoding="utf-8"), "rendered prompt")

    def test_acceptance_checker_only_writes_report(self) -> None:
        core = load_module("workflow_core", "workflow_core.py")
        checker_module = load_module("acceptance_checker", "acceptance_checker.py")

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "chapters" / "chapter_01").mkdir(parents=True)
            (run_dir / "manuscript").mkdir()
            (run_dir / "run_records" / "rendered_prompts").mkdir(parents=True)
            files = {
                "00_request.md": "写一个中文故事。\n",
                "01_project_brief.md": "Language: zh\n",
                "02_codex.json": "{\"entries\": []}\n",
                "03_outline.json": "[{\"chapter_id\": 1, \"title\": \"一\", \"summary\": \"开端\"}]\n",
                "chapters/chapter_01/00_summary.md": "第一章摘要。\n",
                "chapters/chapter_01/01_beats.json": "[{\"beat_id\": 1, \"text\": \"小明进入房间并发现信。\"}]\n",
                "chapters/chapter_01/02_draft.md": "小明进入房间。\n",
                "chapters/chapter_01/03_summary_after.md": "小明发现信。\n",
                "manuscript/draft_full.md": "小明进入房间。\n",
                "manuscript/final.md": "小明进入房间。\n",
            }
            for rel, text in files.items():
                path = run_dir / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            prompt = run_dir / "run_records" / "rendered_prompts" / "001_parse_request.md"
            prompt.write_text("prompt\n", encoding="utf-8")
            manifest = {
                "step_id": "001_parse_request",
                "workflow_step": "parse_request",
                "prompt_template": "core_spec/prompts/01_parse_request.md",
                "input_files": ["00_request.md"],
                "context_sections": ["User Request"],
                "rendered_prompt": "run_records/rendered_prompts/001_parse_request.md",
                "output_files": ["00_request.md"],
                "status": "success",
            }
            (run_dir / "run_records" / "step_manifest.jsonl").write_text(
                json.dumps(manifest, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            before = snapshot_tree(run_dir)

            result = core.WorkflowResult(
                success=True,
                failures=[],
                major=[],
                minor=[],
                feedback_applied=[],
                expected_validation_guard=False,
                validation_guard_triggered=False,
                genre_adapter_key="general",
            )
            checker = checker_module.AcceptanceChecker(
                skill_path=ROOT / "longform-writing",
                test_case={"name": "unit_case", "request": "写一个中文故事。", "markdown": "", "feedback": {}},
                run_dir=run_dir,
                mode="full_auto",
                result=result,
            )
            checker.write_report()

            after = snapshot_tree(run_dir)
            report = after.pop("acceptance_report.md", None)
            self.assertIsNotNone(report)
            self.assertEqual(before, after)

    def test_run_acceptance_keeps_compatibility_exports(self) -> None:
        module = load_module("run_acceptance", "run_acceptance.py")

        self.assertTrue(hasattr(module, "AcceptanceRun"))
        self.assertTrue(hasattr(module, "ModelClient"))
        self.assertTrue(hasattr(module, "load_dotenv"))
        self.assertTrue(hasattr(module, "parse_test_case"))
        self.assertTrue(hasattr(module, "read_text"))
        self.assertTrue(hasattr(module, "render_template"))
        self.assertTrue(hasattr(module, "write_text"))
