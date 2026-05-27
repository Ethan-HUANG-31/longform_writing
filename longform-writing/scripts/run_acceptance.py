#!/usr/bin/env python3
"""Run longform-writing acceptance tests."""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.request
from pathlib import Path

from acceptance_checker import AcceptanceChecker
from workflow_core import (  # noqa: F401
    ModelClient,
    WorkflowContext,
    WorkflowResult,
    append_text,
    load_dotenv,
    parse_test_case,
    read_text,
    render_template,
    sanitize_scene_beats,
    slugify,
    write_text,
)
from workflow_runner import WorkflowRunner


class AcceptanceRun(WorkflowContext):
    def __init__(
        self,
        skill_path: Path,
        test_case: dict,
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ) -> None:
        super().__init__(skill_path, test_case, run_dir, provider, mode, beat_count, prose_word_count)
        self.result: WorkflowResult | None = None

    def run(self) -> None:
        runner = WorkflowRunner(context=self)
        self.result = runner.run()
        self.write_report()

    def workflow_result(self) -> WorkflowResult:
        return self.result or WorkflowResult(
            success=not self.failures,
            failures=list(self.failures),
            major=list(self.major),
            minor=list(self.minor),
            feedback_applied=list(self.feedback_applied),
            expected_validation_guard=self.expected_validation_guard,
            validation_guard_triggered=self.validation_guard_triggered,
            genre_adapter_key=self.genre_adapter_key,
        )

    def write_report(self) -> None:
        AcceptanceChecker(
            self.skill_path,
            self.test_case,
            self.run_dir,
            self.mode,
            self.workflow_result(),
        ).write_report()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--test-case", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--provider", choices=["deepseek", "mock"], default=os.environ.get("LONGFORM_MODEL_PROVIDER", "deepseek"))
    parser.add_argument("--mode", choices=["full_auto", "milestone_review"], default="full_auto")
    parser.add_argument("--beat-count", type=int, default=int(os.environ.get("LONGFORM_BEAT_COUNT", "4")))
    parser.add_argument("--prose-word-count", type=int, default=int(os.environ.get("LONGFORM_PROSE_WORD_COUNT", "260")))
    args = parser.parse_args()

    repo_root = args.skill_path.resolve().parents[0]
    load_dotenv(repo_root / ".env")
    load_dotenv(Path.cwd() / ".env")

    test_case = parse_test_case(args.test_case)
    output_dir = args.output_dir or (Path.cwd() / "runs" / slugify(test_case["name"]))
    runner = AcceptanceRun(
        args.skill_path.resolve(),
        test_case,
        output_dir.resolve(),
        args.provider,
        args.mode,
        args.beat_count,
        args.prose_word_count,
    )
    start = time.monotonic()
    try:
        runner.run()
    except Exception as exc:
        runner.failures.append(f"Runner exception: {exc}")
        runner.result = runner.workflow_result()
        try:
            runner.write_report()
        except Exception:
            pass
        print(f"Acceptance run failed: {exc}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - start
    print(f"Acceptance run complete: {output_dir.resolve()}")
    print(f"elapsed_sec={elapsed:.2f}")
    report = output_dir.resolve() / "acceptance_report.md"
    if report.exists():
        print(read_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
