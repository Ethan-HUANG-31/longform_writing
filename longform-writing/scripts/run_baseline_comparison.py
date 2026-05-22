#!/usr/bin/env python3
"""Run direct-write and simple-engineered baseline controls.

The output is intentionally simple and inspectable. Generated baseline outputs
live under baseline_runs/ and are ignored by git.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_CASES = [
    "05_medium_length_single_protagonist",
    "07_dual_timeline_continuity",
    "10_mystery_clue_fairness_smoke",
]

FULL_RUN_DEFAULTS = {
    "05_medium_length_single_protagonist": "runs/integrated_05_v2",
    "07_dual_timeline_continuity": "runs/integrated_07_v4",
    "10_mystery_clue_fairness_smoke": "runs/integrated_10",
}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def section(md: str, names: list[str]) -> str:
    for name in names:
        pattern = rf"^##\s+{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
        match = re.search(pattern, md, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def endpoint_from_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


class ModelClient:
    def __init__(self, provider: str):
        if provider != "deepseek":
            raise ValueError(f"Unsupported provider: {provider}")
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        self.endpoint = endpoint_from_base_url(os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    def complete(self, prompt: str, *, max_tokens: int, temperature: float) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body[:1000]}") from exc
        data = json.loads(raw)
        return data["choices"][0]["message"]["content"]


def split_chapters(manuscript: str) -> list[str]:
    pattern = re.compile(r"(?m)^(?:#{1,3}\s*)?(?:第[一二三四五六七八九十\d]+章|Chapter\s+\d+|章节\s*\d+)[^\n]*$")
    matches = list(pattern.finditer(manuscript))
    if not matches:
        return [manuscript.strip()] if manuscript.strip() else []
    chapters = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(manuscript)
        chapters.append(manuscript[match.start() : end].strip())
    return [chapter for chapter in chapters if chapter]


def contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def add_failure(failures: list[dict[str, str]], dimension: str, issue: str, evidence: str) -> None:
    failures.append({"dimension": dimension, "issue": issue, "evidence": evidence[:240]})


def evaluate_case(case_name: str, manuscript: str, *, method: str, has_outline: bool, full_pass: bool | None = None) -> dict[str, Any]:
    chapters = split_chapters(manuscript)
    full = manuscript
    failures: list[dict[str, str]] = []
    strengths: list[str] = []

    if case_name == "05_medium_length_single_protagonist":
        if len(chapters) < 5:
            add_failure(failures, "Requirement Fulfillment", "Expected about five chapters.", f"Detected {len(chapters)} chapter section(s).")
        required_groups = [
            ["项目评估报告", "报告"],
            ["缺失封面", "封面"],
            ["高风险，不建议上线", "高风险"],
            ["责任", "回避", "承担", "面对"],
        ]
        for group in required_groups:
            if not contains_any(full, group):
                add_failure(failures, "Requirement Fulfillment", f"Missing marker group: {'/'.join(group)}", full[:240])
        early = "\n\n".join(chapters[:4]) if len(chapters) >= 5 else full[: len(full) // 2]
        if "高风险，不建议上线" in early or "高风险" in early and "不建议上线" in early:
            add_failure(failures, "Reveal Control", "Missing-cover warning appears before the final chapter window.", early[-240:])

    elif case_name == "07_dual_timeline_continuity":
        required_groups = [
            ["旧会议室"],
            ["第一段录像", "第一段"],
            ["第二段录像", "第二段"],
            ["小美"],
            ["反对", "不同意"],
            ["第三段录像", "第三段"],
            ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"],
            ["第四段录像", "第四段"],
            ["承担责任", "担责"],
            ["离职", "离开"],
        ]
        for group in required_groups:
            if not contains_any(full, group):
                add_failure(failures, "Continuity", f"Missing dual-timeline marker: {'/'.join(group)}", full[:240])
        early = "\n\n".join(chapters[:2]) if len(chapters) >= 3 else full[: len(full) // 2]
        if contains_any(early, ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"]):
            add_failure(failures, "Reveal Control", "Risk-warning deletion appears before chapter 3.", early[-240:])
        if "现在" not in full or not contains_any(full, ["录像", "三年前", "过去"]):
            add_failure(failures, "Structural Coherence", "Timeline is not explicitly separated into present action and past evidence.", full[:240])

    elif case_name == "10_mystery_clue_fairness_smoke":
        required_groups = [
            ["旧借书卡"],
            ["日期", "对不上"],
            ["错放书"],
            ["储物柜密码"],
            ["阿强"],
            ["捐赠名单"],
        ]
        for group in required_groups:
            if not contains_any(full, group):
                add_failure(failures, "Clue Fairness", f"Missing clue/payoff marker: {'/'.join(group)}", full[:240])
        first_half = full[: len(full) // 2]
        if "阿强" in first_half and "真正" in first_half:
            add_failure(failures, "Reveal Control", "Possible early culprit reveal in first half.", first_half[-240:])

    if method == "direct_write":
        add_failure(failures, "Traceability", "Direct write has only one prompt and no localized planning trace.", "No outline, Codex, beat, summary, or manifest artifacts.")
    elif has_outline:
        strengths.append("Produces an outline and manuscript artifacts, so failures are partially localizable.")

    if full_pass:
        strengths.append("Full skill passed this case in integrated acceptance.")
    if not failures:
        strengths.append("Heuristic content checks found no baseline-specific failures.")

    return {
        "pass": not failures,
        "strengths": strengths,
        "failures": failures,
        "chapter_sections_detected": len(chapters),
    }


def read_full_skill_pass(full_run: Path) -> bool | None:
    report = full_run / "acceptance_report.md"
    if not report.exists():
        return None
    text = read_text(report)
    return bool(re.search(r"## Pass / Fail\s+Pass", text))


def method_report(case_name: str, method: str, evaluation: dict[str, Any]) -> str:
    lines = [
        f"# Baseline Report: {method}",
        "",
        f"Case: `{case_name}`",
        "",
        f"Pass: `{str(evaluation['pass']).lower()}`",
        f"Detected chapter sections: `{evaluation['chapter_sections_detected']}`",
        "",
        "## Strengths",
    ]
    lines.extend([f"- {item}" for item in evaluation["strengths"]] or ["- None recorded."])
    lines.extend(["", "## Failures"])
    if evaluation["failures"]:
        for failure in evaluation["failures"]:
            lines.append(f"- {failure['dimension']}: {failure['issue']} Evidence: {failure['evidence']}")
    else:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def conclusion_for(case_name: str, direct_eval: dict[str, Any], simple_eval: dict[str, Any], full_pass: bool | None) -> tuple[str, list[str]]:
    signals: list[str] = []
    if full_pass and (not direct_eval["pass"] or not simple_eval["pass"]):
        signals.append("Workflow Rule Improvement: Preserve the mechanisms that helped the full skill pass: explicit memory, reveal checks, Codex/clue state, and prompt trace.")
    if any(f["dimension"] == "Traceability" for f in direct_eval["failures"]):
        signals.append("Evaluator Rule Improvement: Keep traceability as a separate process-quality dimension, not just final prose quality.")
    if simple_eval["pass"] and full_pass:
        signals.append("Writer Rule Improvement: Compare prose flow against the simple baseline; if simple prose is smoother, reduce mechanical beat-boundary artifacts.")
    if not full_pass:
        signals.append("Workflow Rule Improvement: Full skill did not have a passing integrated report for this case; inspect acceptance output before claiming advantage.")
    if not signals:
        signals.append("Evaluator Rule Improvement: Add stronger semantic checks if all methods appear to pass by keyword heuristics.")

    if full_pass and (not direct_eval["pass"] or not simple_eval["pass"]):
        conclusion = "The full skill is justified on this case because it passed integrated acceptance while at least one simpler baseline exposed control or traceability gaps."
    elif full_pass:
        conclusion = "The full skill passed, but simpler baselines also looked competitive under these heuristic checks; this case should be strengthened or prose quality should be compared by an LLM judge."
    else:
        conclusion = "The comparison is inconclusive because the full skill did not have a confirmed passing integrated run."
    return conclusion, signals


def run_direct(client: ModelClient, case_name: str, request: str, out_dir: Path) -> dict[str, Any]:
    prompt = (
        "请根据下面的用户需求，直接写出完整小说。不要先输出大纲，不要解释过程，只输出正文。\n\n"
        "<user_request>\n"
        f"{request}\n"
        "</user_request>\n"
    )
    write_text(out_dir / "request.md", request + "\n")
    write_text(out_dir / "prompt.md", prompt)
    manuscript = client.complete(prompt, max_tokens=5200, temperature=0.35)
    write_text(out_dir / "manuscript.md", manuscript.strip() + "\n")
    return {"manuscript": manuscript}


def run_simple(client: ModelClient, case_name: str, request: str, out_dir: Path) -> dict[str, Any]:
    outline_prompt = (
        "请根据用户需求生成章节大纲。只输出每章标题、目标、关键事件和不能提前揭示的信息。\n\n"
        "<user_request>\n"
        f"{request}\n"
        "</user_request>\n"
    )
    write_text(out_dir / "request.md", request + "\n")
    write_text(out_dir / "outline_prompt.md", outline_prompt)
    outline = client.complete(outline_prompt, max_tokens=1800, temperature=0.2)
    write_text(out_dir / "outline.md", outline.strip() + "\n")

    prose_prompt = (
        "请根据用户需求和章节大纲，按章节写完整正文。\n"
        "请保持连续性，不要提前揭示大纲中标注为后续章节的信息。只输出正文。\n\n"
        "<user_request>\n"
        f"{request}\n"
        "</user_request>\n\n"
        "<outline>\n"
        f"{outline}\n"
        "</outline>\n"
    )
    write_text(out_dir / "prose_prompt.md", prose_prompt)
    manuscript = client.complete(prose_prompt, max_tokens=5600, temperature=0.35)
    write_text(out_dir / "manuscript.md", manuscript.strip() + "\n")
    for idx, chapter in enumerate(split_chapters(manuscript), 1):
        write_text(out_dir / f"chapter_{idx:02d}.md", chapter.strip() + "\n")
    return {"outline": outline, "manuscript": manuscript}


def run_case(client: ModelClient, test_case: Path, output_root: Path, full_run_root: Path) -> dict[str, Any]:
    md = read_text(test_case)
    request = section(md, ["User Request", "Initial User Request", "Base Request"])
    case_name = test_case.stem
    full_run_rel = FULL_RUN_DEFAULTS.get(case_name, f"runs/integrated_{case_name[:2]}")
    full_run = full_run_root / full_run_rel
    full_pass = read_full_skill_pass(full_run)

    direct_dir = output_root / "direct_write" / case_name
    simple_dir = output_root / "simple_engineered" / case_name
    for path in [direct_dir, simple_dir]:
        if path.exists():
            shutil.rmtree(path)

    direct = run_direct(client, case_name, request, direct_dir)
    direct_eval = evaluate_case(case_name, direct["manuscript"], method="direct_write", has_outline=False, full_pass=full_pass)
    write_text(direct_dir / "baseline_report.md", method_report(case_name, "direct_write", direct_eval))

    simple = run_simple(client, case_name, request, simple_dir)
    simple_eval = evaluate_case(case_name, simple["manuscript"], method="simple_engineered", has_outline=True, full_pass=full_pass)
    write_text(simple_dir / "baseline_report.md", method_report(case_name, "simple_engineered", simple_eval))

    conclusion, signals = conclusion_for(case_name, direct_eval, simple_eval, full_pass)
    return {
        "test_case": case_name,
        "full_run": full_run_rel,
        "methods": {
            "direct_write": direct_eval,
            "simple_engineered": simple_eval,
            "full_skill": {
                "pass": full_pass,
                "strengths": ["Integrated acceptance report passed."] if full_pass else [],
                "failures": [] if full_pass else [{"dimension": "Acceptance", "issue": "No confirmed passing full-skill report.", "evidence": full_run_rel}],
            },
        },
        "conclusion": conclusion,
        "improvement_signals": signals,
    }


def write_aggregate(output_root: Path, results: list[dict[str, Any]], elapsed: float) -> None:
    write_text(output_root / "comparison_report.json", json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Baseline Comparison Report",
        "",
        f"Elapsed seconds: `{elapsed:.2f}`",
        "",
        "## Summary",
    ]
    for result in results:
        direct_pass = result["methods"]["direct_write"]["pass"]
        simple_pass = result["methods"]["simple_engineered"]["pass"]
        full_pass = result["methods"]["full_skill"]["pass"]
        lines.append(f"- `{result['test_case']}`: direct={direct_pass}, simple={simple_pass}, full={full_pass}")
    lines.extend(["", "## Case Findings"])
    for result in results:
        lines.extend(["", f"### {result['test_case']}", result["conclusion"], "", "Improvement signals:"])
        lines.extend([f"- {signal}" for signal in result["improvement_signals"]])
    write_text(output_root / "comparison_report.md", "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="deepseek")
    parser.add_argument("--test-dir", type=Path, default=Path("test_cases"))
    parser.add_argument("--output-root", type=Path, default=Path("baseline_runs"))
    parser.add_argument("--full-run-root", type=Path, default=Path("."))
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    client = ModelClient(args.provider)
    start = time.time()
    results = []
    for case in args.cases:
        test_case = args.test_dir / f"{case}.md"
        if not test_case.exists():
            raise FileNotFoundError(test_case)
        results.append(run_case(client, test_case, args.output_root, args.full_run_root))
    elapsed = time.time() - start
    write_aggregate(args.output_root, results, elapsed)
    print(f"Baseline comparison complete: {args.output_root}")
    print(read_text(args.output_root / "comparison_report.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
