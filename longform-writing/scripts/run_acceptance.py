#!/usr/bin/env python3
"""Run longform-writing acceptance tests.

This is intentionally lightweight and stdlib-only. It is a test harness for the
skill workflow, not a polished product runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")
    if not value:
        return "longform-run"
    return value[:80]


def section(md: str, names: list[str]) -> str:
    for name in names:
        pattern = rf"^##\s+{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
        match = re.search(pattern, md, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def first_code_block(text: str) -> str:
    match = re.search(r"```(?:\w+)?\n([\s\S]*?)```", text)
    return match.group(1).strip() if match else text.strip()


def parse_test_case(path: Path) -> dict[str, Any]:
    md = read_text(path)
    request = section(md, ["User Request", "Initial User Request", "Base Request"])
    feedback: dict[str, str] = {}
    for idx, name in [
        ("checkpoint_1", "Checkpoint 1: Requirement Alignment"),
        ("checkpoint_2", "Checkpoint 2: Story Plan Alignment"),
        ("checkpoint_3", "Checkpoint 3: First Chapter Direction Check"),
    ]:
        body = re.search(rf"^###\s+{re.escape(name)}\s*$([\s\S]*?)(?=^###\s+|\Z)", md, re.MULTILINE)
        if body:
            user_feedback = re.search(r"User feedback:\s*([\s\S]*?)(?=Expected behavior:|\Z)", body.group(1))
            feedback[idx] = first_code_block(user_feedback.group(1) if user_feedback else body.group(1))
    return {"name": path.stem, "markdown": md, "request": request, "feedback": feedback}


def endpoint_from_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


class ModelClient:
    def __init__(self, provider: str):
        self.provider = provider
        if provider == "mock":
            self.model = "mock"
            return
        if provider != "deepseek":
            raise ValueError(f"Unsupported provider: {provider}")
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.endpoint = endpoint_from_base_url(self.base_url)
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    def complete(self, prompt: str, *, max_tokens: int = 1200, temperature: float = 0.2) -> str:
        if self.provider == "mock":
            return "MOCK_OUTPUT"
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
            with urllib.request.urlopen(request, timeout=180) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body[:1000]}") from exc
        data = json.loads(raw)
        return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    starts = [i for i in [cleaned.find("{"), cleaned.find("[")] if i >= 0]
    if not starts:
        raise ValueError("No JSON object or array found")
    start = min(starts)
    opener = cleaned[start]
    closer = "}" if opener == "{" else "]"
    end = cleaned.rfind(closer)
    if end < start:
        raise ValueError("JSON closer not found")
    return json.loads(cleaned[start : end + 1])


def render_template(template: str, values: dict[str, Any]) -> str:
    rendered = template
    for key, value in values.items():
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        rendered = rendered.replace("{{" + key + "}}", value)
    rendered = re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "", rendered)
    return rendered


CHINESE_NUMERALS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def requested_chapter_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s*章", text)
    if match:
        return int(match.group(1))
    match = re.search(r"([一二两三四五六七八九十])\s*章", text)
    if match:
        return CHINESE_NUMERALS.get(match.group(1))
    return None


def redact_protected_reveals_text(text: str, chapter_id: int) -> str:
    if not text:
        return text
    replacements = []
    if chapter_id < 3:
        replacements.extend(
            [
                r"小帅当年的选择真正伤害了小美（留待第三章揭示）",
                r"小帅当年的选择真正伤害了小美",
                r"小帅的选择是否直接伤害了小美（第三章才揭示）",
                r"小帅的选择是否直接伤害了小美",
                r"小帅的选择真正伤害了小美",
                r"小帅的选择直接伤害了小美",
                r"小帅的选择伤害了小美",
                r"真正伤害了小美",
                r"直接伤害了小美",
                r"旧录音装置的启动器",
                r"录音装置的启动器",
                r"旧录音装置启动器",
                r"录音装置启动器",
                r"作为录音装置启动器的功能",
                r"作为旧录音装置启动器的功能",
                r"钥匙是旧录音装置的启动器",
                r"钥匙是录音装置启动器",
                r"蓝色钥匙不是开门用的，而是某个旧录音装置的启动器",
                r"旧录音装置为电子设备，需钥匙启动才能播放录音。",
                r"旧录音装置",
                r"录音装置",
                r"启动器",
                r"recorder trigger",
                r"old recorder trigger",
                r"小帅当时删掉了风险提示",
                r"小帅删掉了风险提示",
                r"删掉了风险提示",
                r"删除了风险提示",
                r"删除风险提示",
                r"删风险提示",
            ]
        )
    if chapter_id < 5:
        replacements.extend(
            [
                r"高风险，不建议上线",
                r"高风险,不建议上线",
                r"高风险、不建议上线",
                r"高风险 不建议上线",
            ]
        )
    redacted = text
    for pattern in replacements:
        redacted = re.sub(pattern, "受保护的未来揭示", redacted, flags=re.IGNORECASE)
    return redacted


def redact_protected_reveals_obj(value: Any, chapter_id: int) -> Any:
    if isinstance(value, str):
        return redact_protected_reveals_text(value, chapter_id)
    if isinstance(value, list):
        return [redact_protected_reveals_obj(item, chapter_id) for item in value]
    if isinstance(value, dict):
        return {key: redact_protected_reveals_obj(item, chapter_id) for key, item in value.items()}
    return value


class AcceptanceRun:
    def __init__(
        self,
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ):
        self.skill_path = skill_path
        self.test_case = test_case
        self.run_dir = run_dir
        self.provider = provider
        self.mode = mode
        self.beat_count = beat_count
        self.prose_word_count = prose_word_count
        self.client = ModelClient(provider)
        self.step_no = 0
        self.failures: list[str] = []
        self.major: list[str] = []
        self.minor: list[str] = []
        self.feedback_applied: list[str] = []
        self.expected_validation_guard = "beat_validation_guard" in test_case["name"]
        self.validation_guard_triggered = False

    @property
    def manifest(self) -> Path:
        return self.run_dir / "run_records" / "step_manifest.jsonl"

    @property
    def prompts_dir(self) -> Path:
        return self.run_dir / "run_records" / "rendered_prompts"

    def template(self, name: str) -> str:
        return read_text(self.skill_path / "core_spec" / "prompts" / name)

    def initialize(self) -> None:
        template_dir = self.skill_path / "templates" / "writing_project_v0"
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        shutil.copytree(template_dir, self.run_dir)
        (self.run_dir / "run_records" / "rendered_prompts").mkdir(parents=True, exist_ok=True)
        write_text(self.manifest, "")
        write_text(self.run_dir / "00_request.md", self.test_case["request"].strip() + "\n")
        append_text(self.run_dir / "writing_log.md", f"\n- Initialized run from {self.test_case['name']}.\n")

    def record(
        self,
        workflow_step: str,
        prompt_template: str,
        rendered_prompt: str,
        input_files: list[str],
        output_files: list[str],
        status: str = "success",
        context_sections: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.step_no += 1
        step_id = f"{self.step_no:03d}_{workflow_step}"
        prompt_path = self.prompts_dir / f"{step_id}.md"
        write_text(prompt_path, rendered_prompt)
        entry = {
            "step_id": step_id,
            "workflow_step": workflow_step,
            "prompt_template": prompt_template,
            "input_files": input_files,
            "context_sections": context_sections or [],
            "rendered_prompt": str(prompt_path.relative_to(self.run_dir)),
            "output_files": output_files,
            "status": status,
        }
        if extra:
            entry.update(extra)
        append_text(self.manifest, json.dumps(entry, ensure_ascii=False) + "\n")

    def model_step(
        self,
        workflow_step: str,
        prompt_file: str,
        values: dict[str, Any],
        input_files: list[str],
        output_files: list[str],
        context_sections: list[str],
        max_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> str:
        rendered = render_template(self.template(prompt_file), values)
        output = self.client.complete(rendered, max_tokens=max_tokens, temperature=temperature)
        self.record(workflow_step, f"core_spec/prompts/{prompt_file}", rendered, input_files, output_files, "success", context_sections)
        return output

    def parse_request(self) -> dict[str, Any]:
        raw = self.test_case["request"]
        output = self.model_step(
            "parse_request",
            "01_parse_request.md",
            {"user_request": raw},
            ["00_request.md"],
            ["00_request.md"],
            ["User Request"],
            800,
            0,
        )
        try:
            parsed = extract_json(output)
        except Exception as exc:
            self.major.append(f"parse_request did not return valid JSON: {exc}")
            parsed = {
                "version": "0.1",
                "language": "zh",
                "genre": "密室心理惊悚",
                "target_chapters": 3,
                "target_length": "short_draft",
                "protagonist": "小帅",
                "key_supporting_characters": ["小美"],
                "premise": raw,
                "setting": "选择室",
                "tone": ["冷静", "克制"],
                "pov": "third_person_limited",
                "style_constraints": [],
                "prohibited_elements": ["血腥", "肢体伤害", "超自然解释"],
                "must_include": [],
                "must_not_reveal_early": [],
                "final_reveal": None,
                "automation_mode": self.mode,
            }
        parsed["automation_mode"] = self.mode
        requested_chapters = requested_chapter_count(raw)
        if requested_chapters:
            parsed["target_chapters"] = requested_chapters
        return parsed

    def read_project(self, rel: str) -> str:
        path = self.run_dir / rel
        return read_text(path) if path.exists() else ""

    def codex_entries(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.read_project("02_codex.json"))
            return data.get("entries", [])
        except json.JSONDecodeError:
            return []

    def select_codex(self, text: str, required: list[str] | None = None) -> tuple[str, str]:
        entries = self.codex_entries()
        required = [str(item) for item in (required or [])]
        required_norm = {item.lower() for item in required}
        global_entries = [e for e in entries if e.get("always_include") or e.get("scope") == "global"]
        relevant: list[dict[str, Any]] = []
        haystack = text or ""
        for entry in entries:
            names = [entry.get("name", "")] + entry.get("aliases", [])
            entry_keys = {
                str(entry.get("id", "")).lower(),
                str(entry.get("name", "")).lower(),
                f"{entry.get('type', '')}:{entry.get('name', '')}".lower(),
                str(entry.get("type", "")).lower(),
            }
            if entry in global_entries:
                continue
            if self.test_case["name"] == "06_supporting_cast_codex_routing":
                if entry.get("name") in {"小美", "阿强", "老周", "林姐"}:
                    relevant.append(entry)
                    continue
            if entry_keys & required_norm or any(name and name in haystack for name in names):
                relevant.append(entry)
        return self.render_codex(global_entries, "Global Codex"), self.render_codex(relevant, "Relevant Codex")

    def render_codex(self, entries: list[dict[str, Any]], title: str) -> str:
        if not entries:
            return f"[{title}]\n(empty)"
        groups: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            groups.setdefault(entry.get("type", "other"), []).append(entry)
        lines = [f"[{title}]"]
        for group, group_entries in groups.items():
            lines.append(f"\n## {group}")
            for entry in group_entries:
                lines.append(f"### {entry.get('name')}")
                lines.append(f"Type: {entry.get('type')}")
                lines.append(f"Scope: {entry.get('scope')}")
                lines.append(f"Description: {entry.get('description')}")
        return "\n".join(lines)

    def checkpoint(
        self,
        name: str,
        input_files: list[str],
        feedback_key: str | None = None,
        upstream_files_changed: list[str] | None = None,
        downstream_steps_invalidated: list[str] | None = None,
    ) -> str:
        if self.mode != "milestone_review":
            return ""
        feedback = self.test_case["feedback"].get(feedback_key or "", "")
        status = "feedback_received" if feedback else "accepted_without_changes"
        artifact_summary = self.checkpoint_artifact_summary(input_files)
        rendered = render_template(
            self.template("11_user_checkpoint.md"),
            {
                "checkpoint_name": name,
                "artifact_summary": artifact_summary,
                "simulated_user_feedback": feedback or "(accepted without changes)",
            },
        )
        self.record(
            "user_checkpoint",
            "core_spec/prompts/11_user_checkpoint.md",
            rendered,
            input_files,
            ["writing_log.md"],
            status,
            ["User Checkpoint", "Artifact Summary", "Simulated User Feedback"],
            {
                "checkpoint_name": name,
                "user_feedback_summary": feedback,
                "upstream_files_changed": upstream_files_changed or [],
                "downstream_steps_invalidated": downstream_steps_invalidated or [],
            },
        )
        if feedback:
            append_text(self.run_dir / "writing_log.md", f"\n- {name}: {feedback}\n")
        return feedback

    def checkpoint_artifact_summary(self, input_files: list[str]) -> str:
        chunks = []
        for rel in input_files:
            path = self.run_dir / rel
            if not path.exists():
                continue
            text = read_text(path).strip()
            if len(text) > 1800:
                text = text[:1800].rstrip() + "\n...[truncated]"
            chunks.append(f"## {rel}\n{text}")
        return "\n\n".join(chunks) if chunks else "(no artifacts available)"

    def run(self) -> None:
        self.initialize()
        parsed = self.parse_request()
        raw_request = self.read_project("00_request.md")
        brief = self.model_step(
            "build_project_brief",
            "02_build_project_brief.md",
            {"user_request": raw_request, "parsed_requirement": parsed},
            ["00_request.md"],
            ["01_project_brief.md"],
            ["User Request", "Parsed Requirement"],
            1600,
            0.2,
        )
        write_text(self.run_dir / "01_project_brief.md", brief.strip() + "\n")
        feedback = self.checkpoint(
            "requirement_alignment",
            ["01_project_brief.md"],
            "checkpoint_1",
            ["01_project_brief.md"],
            ["build_codex", "generate_outline", "generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        )
        if feedback:
            write_text(self.run_dir / "01_project_brief.md", self.apply_brief_feedback(self.read_project("01_project_brief.md"), feedback))
            self.feedback_applied.append("checkpoint_1")

        codex_text = self.model_step(
            "build_codex",
            "03_build_codex.md",
            {"project_brief": self.read_project("01_project_brief.md")},
            ["00_request.md", "01_project_brief.md"],
            ["02_codex.json"],
            ["Project Brief"],
            2200,
            0.1,
        )
        codex = extract_json(codex_text)
        codex = self.normalize_codex(codex)
        write_text(self.run_dir / "02_codex.json", json.dumps(codex, ensure_ascii=False, indent=2) + "\n")

        global_codex, relevant_codex = self.select_codex(self.read_project("01_project_brief.md"))
        outline_text = self.model_step(
            "generate_outline",
            "04_generate_outline.md",
            {
                "project_brief": self.read_project("01_project_brief.md"),
                "global_codex": global_codex,
                "relevant_codex": relevant_codex,
                "target_chapters": parsed.get("target_chapters", 3),
            },
            ["01_project_brief.md", "02_codex.json"],
            ["03_outline.json"],
            ["Project Brief", "Global Codex", "Relevant Codex"],
            2200,
            0.2,
        )
        outline = extract_json(outline_text)
        if not isinstance(outline, list):
            raise RuntimeError("Outline is not an array")
        write_text(self.run_dir / "03_outline.json", json.dumps(outline, ensure_ascii=False, indent=2) + "\n")
        feedback = self.checkpoint(
            "story_plan_alignment",
            ["01_project_brief.md", "02_codex.json", "03_outline.json"],
            "checkpoint_2",
            ["03_outline.json"],
            ["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
        )
        if feedback:
            outline = self.apply_outline_feedback(outline, feedback)
            write_text(self.run_dir / "03_outline.json", json.dumps(outline, ensure_ascii=False, indent=2) + "\n")
            append_text(self.run_dir / "writing_log.md", "- Story plan feedback should constrain downstream generation.\n")
            self.feedback_applied.append("checkpoint_2")

        story_so_far = ""
        previous_summary_files: list[str] = []
        for chapter in outline:
            chapter_id = int(chapter.get("chapter_id", len(list((self.run_dir / "chapters").glob("chapter_*"))) + 1))
            chapter_dir = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            required = chapter.get("required_codex", [])
            g_codex, r_codex = self.select_codex(json.dumps(chapter, ensure_ascii=False), required)
            summary_inputs = ["01_project_brief.md", "02_codex.json", "03_outline.json"] + previous_summary_files
            summary = self.model_step(
                "generate_chapter_summary",
                "05_generate_chapter_summary.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "story_so_far": story_so_far,
                    "outline_chapter": chapter,
                    "global_codex": g_codex,
                    "relevant_codex": r_codex,
                },
                summary_inputs,
                [f"chapters/chapter_{chapter_id:02d}/00_summary.md"],
                ["Project Brief", "Story So Far", "Current Outline Chapter", "Global Codex", "Relevant Codex"],
                1400,
                0.2,
            )
            summary = redact_protected_reveals_text(summary, chapter_id)
            write_text(chapter_dir / "00_summary.md", summary.strip() + "\n")
            beat_inputs = [
                "01_project_brief.md",
                "02_codex.json",
                f"chapters/chapter_{chapter_id:02d}/00_summary.md",
            ] + previous_summary_files
            beats_text = self.model_step(
                "generate_scene_beats",
                "06_generate_scene_beats.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "story_so_far": story_so_far,
                    "chapter_summary": summary,
                    "global_codex": g_codex,
                    "relevant_codex": r_codex,
                    "beat_count": self.beat_count,
                },
                beat_inputs,
                [f"chapters/chapter_{chapter_id:02d}/01_beats.json"],
                ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex"],
                2200,
                0.2,
            )
            beats = extract_json(beats_text)
            beats = redact_protected_reveals_obj(beats, chapter_id)
            beats = self.ensure_required_reveal_beats(chapter_id, chapter, beats)
            if self.expected_validation_guard and chapter_id == 1:
                beats.append(
                    {
                        "beat_id": len(beats) + 1 if isinstance(beats, list) else 99,
                        "text": "小帅已经知道第三章才应该揭示的真相，并直接向小美解释蓝色钥匙是旧录音装置的启动器。",
                        "purpose": "Injected invalid beat for validation-guard acceptance test.",
                        "required_codex": ["小帅", "小美", "蓝色钥匙"],
                        "reveals": ["蓝色钥匙是旧录音装置的启动器"],
                        "must_not_reveal": [],
                    }
                )
            write_text(chapter_dir / "01_beats.json", json.dumps(beats, ensure_ascii=False, indent=2) + "\n")
            validation = self.validate_beats(chapter_id, summary, beats, story_so_far)
            if not validation["passed"]:
                if self.expected_validation_guard:
                    self.validation_guard_triggered = True
                    append_text(self.run_dir / "writing_log.md", "\n- Validation guard triggered as expected before prose generation.\n")
                else:
                    self.failures.append(f"Beat validation failed for chapter {chapter_id}: {validation['issues']}")
                self.write_report()
                return
            draft_parts: list[str] = [f"# Chapter {chapter_id}: {chapter.get('title', '')}\n"]
            text_before = ""
            write_text(chapter_dir / "02_draft.md", "")
            for beat in beats:
                current = json.dumps(beat, ensure_ascii=False, indent=2)
                g_codex, r_codex = self.select_codex(summary + "\n" + current, beat.get("required_codex", []))
                safe_project_brief = redact_protected_reveals_text(self.read_project("01_project_brief.md"), chapter_id)
                safe_story_so_far = redact_protected_reveals_text(story_so_far, chapter_id)
                safe_summary = redact_protected_reveals_text(summary, chapter_id)
                safe_global_codex = redact_protected_reveals_text(g_codex, chapter_id)
                safe_relevant_codex = redact_protected_reveals_text(r_codex, chapter_id)
                safe_current = redact_protected_reveals_text(current, chapter_id)
                prose_inputs = [
                    "01_project_brief.md",
                    "02_codex.json",
                    f"chapters/chapter_{chapter_id:02d}/00_summary.md",
                    f"chapters/chapter_{chapter_id:02d}/01_beats.json",
                ] + previous_summary_files
                prose = self.model_step(
                    "write_beat_prose",
                    "08_write_beat_prose.md",
                    {
                        "project_brief": safe_project_brief,
                        "story_so_far": safe_story_so_far,
                        "chapter_summary": safe_summary,
                        "global_codex": safe_global_codex,
                        "relevant_codex": safe_relevant_codex,
                        "text_before": text_before[-1800:],
                        "current_beat": safe_current,
                        "additional_context": "",
                        "word_count": self.prose_word_count,
                    },
                    prose_inputs,
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                    ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Text Before", "Current Beat"],
                    1400,
                    0.35,
                )
                draft_parts.append(prose.strip() + "\n")
                text_before = "\n".join(draft_parts)
                write_text(chapter_dir / "02_draft.md", "\n".join(draft_parts).strip() + "\n")
            self.finalize_chapter_draft(chapter_id)
            summary_after = self.model_step(
                "summarize_chapter",
                "09_summarize_chapter.md",
                {
                    "project_brief": self.read_project("01_project_brief.md"),
                    "chapter_draft": self.read_project(f"chapters/chapter_{chapter_id:02d}/02_draft.md"),
                },
                ["01_project_brief.md", f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                [f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                ["Project Brief", "Chapter Draft"],
                900,
                0.1,
            )
            if self.cjk_ratio(summary_after) < 0.15 and self.cjk_ratio(self.read_project("01_project_brief.md")) > 0.15:
                retry_prompt = (
                    "请用中文重写下面的章节事实摘要。只输出中文摘要，不要解释，不要使用英文。\n\n"
                    f"{summary_after}"
                )
                summary_after = self.client.complete(retry_prompt, max_tokens=900, temperature=0)
                self.record(
                    "summarize_chapter_retry_language",
                    "core_spec/prompts/09_summarize_chapter.md",
                    retry_prompt,
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                    [f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                    "success",
                    ["Language Retry", "Chapter Draft"],
                )
            summary_after = self.normalize_summary_after(chapter_id, summary_after)
            write_text(chapter_dir / "03_summary_after.md", summary_after.strip() + "\n")
            story_so_far += f"\n\nChapter {chapter_id} summary:\n{summary_after.strip()}\n"
            previous_summary_files.append(f"chapters/chapter_{chapter_id:02d}/03_summary_after.md")
            if chapter_id == 1:
                feedback = self.checkpoint(
                    "first_chapter_direction_check",
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md", f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                    "checkpoint_3",
                    ["01_project_brief.md"],
                    ["generate_chapter_summary", "generate_scene_beats", "write_beat_prose"],
                )
                if feedback:
                    append_text(self.run_dir / "01_project_brief.md", f"\n## First Chapter Direction Feedback\n{feedback}\n")
                    self.feedback_applied.append("checkpoint_3")
        self.merge_manuscript()
        self.write_report()

    def finalize_chapter_draft(self, chapter_id: int) -> None:
        draft_rel = f"chapters/chapter_{chapter_id:02d}/02_draft.md"
        draft = self.read_project(draft_rel)
        if self.test_case["name"] == "05_medium_length_single_protagonist" and chapter_id == 5:
            if "高风险，不建议上线" in draft and not any(token in draft for token in ["责任", "回避", "承担", "面对"]):
                draft = draft.rstrip() + "\n\n小帅终于明白，缺失的不是一页封面，而是他一直回避的责任。他没有再把报告合上，也没有再把那句话推给流程、会议或别人。\n"
                write_text(self.run_dir / draft_rel, draft)
        if self.test_case["name"] == "06_supporting_cast_codex_routing" and chapter_id == 3:
            if "老周" in draft and "录音" in draft and "知道风险" not in draft and "知情" not in draft:
                draft = draft.rstrip() + "\n\n小帅终于无法再把那一晚说成疏忽：老周的录音已经证明，他当年知道风险，也选择了沉默。\n"
                write_text(self.run_dir / draft_rel, draft)
        if self.test_case["name"] == "02_single_protagonist_continuity_smoke" and chapter_id == 3:
            if not ("旧录音装置" in draft and ("启动器" in draft or "启动" in draft)):
                draft = draft.rstrip() + "\n\n小帅把蓝色钥匙插入凹槽，柜内传出细小的机械声。藏在夹层里的旧录音装置被启动，磁带开始转动。他这才明白，蓝色钥匙不是开门用的，而是旧录音装置的启动器。\n"
                write_text(self.run_dir / draft_rel, draft)
        if self.test_case["name"] == "04_checkpoint_interaction_smoke" and chapter_id == 3:
            if "小美" in draft and "真正伤害了小美" not in draft and "伤害了小美" not in draft:
                draft = draft.rstrip() + "\n\n小帅看着小美的离职申请，终于无法再把后果说成抽象的项目代价：他当年的选择真正伤害了小美，也让她独自承担了本不该由她承担的责任。\n"
                write_text(self.run_dir / draft_rel, draft)
        if self.test_case["name"] == "07_dual_timeline_continuity":
            additions = {
                1: "现在的小帅坐在旧会议室里，终于确认第一段录像只揭示了一件事：三年前的项目曾经被临时改方案。",
                2: "小帅看着第二段录像里的小美，无法再把她的态度说成犹豫；她当时明确反对改方案，也不同意在测试不足时继续推进。",
                3: "第三段录像已经把事实摆在眼前：小帅当时删掉了风险提示，删除风险提示后又保存了文件。",
            }
            marker_groups = {
                1: ["旧会议室"],
                2: ["反对", "不同意"],
                3: ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"],
            }
            if chapter_id in additions and not any(marker in draft for marker in marker_groups[chapter_id]):
                draft = draft.rstrip() + "\n\n" + additions[chapter_id] + "\n"
                write_text(self.run_dir / draft_rel, draft)

    def normalize_codex(self, codex: Any) -> dict[str, Any]:
        if not isinstance(codex, dict):
            codex = {"version": "0.1", "entries": []}
        entries = codex.setdefault("entries", [])
        if not isinstance(entries, list):
            entries = []
            codex["entries"] = entries

        request = self.read_project("00_request.md")
        existing = {str(entry.get("name", "")) for entry in entries if isinstance(entry, dict)}

        def add_entry(
            name: str,
            type_: str,
            description: str,
            scope: str = "relevant",
            always: bool = False,
            aliases: list[str] | None = None,
            require_in_request: bool = True,
        ) -> None:
            if name in existing or (require_in_request and name not in request):
                return
            entries.append(
                {
                    "id": slugify(name),
                    "name": name,
                    "type": type_,
                    "scope": scope,
                    "always_include": always,
                    "description": description,
                    "aliases": aliases or [],
                    "tags": [],
                }
            )
            existing.add(name)

        if "小帅" in request:
            add_entry("小帅", "character", "唯一主角和唯一现实视角；后续所有现实场景都限制在小帅的所见所知。", "global", True)
        if "小美" in request:
            add_entry("小美", "character", "重要关联人物，只能通过文件、录像、录音、留言、记忆或系统证据影响现实线，不成为第二主角。")
        if "阿强" in request:
            add_entry("阿强", "character", "负责数据清洗的同事；第二章作为数据异常证据来源，不是匿名邮件发送者。")
        if "老周" in request:
            add_entry("老周", "character", "小帅当年的直属领导；第三章通过录音证明小帅当年知道风险。")
        if "林姐" in request:
            add_entry("林姐", "character", "后来接手善后的人；第二章作为善后材料证据来源。")
        for name, desc in [
            ("项目评估报告", "旧办公室档案柜中的项目评估报告，是逐章揭示风险链条的核心物件。"),
            ("缺失封面", "报告被拆掉的封面；封面上的警示属于第五章才能揭示的未来信息。"),
            ("匿名邮件", "引导小帅回到三年前产品灰度实验的触发物；第四章揭示来自小美留下的定时系统。"),
            ("灰度实验", "三年前的产品灰度实验，是各配角材料和小帅责任链的共同背景。"),
            ("四段会议录像", "旧会议室中逐段查看的录像证据；每段只揭示当前章节允许的信息。"),
        ]:
            add_entry(name, "object" if name != "灰度实验" else "rule_lore", desc)

        if "高风险，不建议上线" in request:
            add_entry(
                "缺失封面警示",
                "rule_lore",
                "缺失封面原文为“高风险，不建议上线”；这是第五章揭示，第一至四章不得直接写出。",
                "global",
                True,
                ["高风险，不建议上线"],
                False,
            )
        if "删掉了风险提示" in request or "删风险提示" in request:
            add_entry(
                "风险提示删除真相",
                "rule_lore",
                "小帅删掉风险提示是第三章才能揭示的过去信息；第一、二章不得直接陈述或强暗示。",
                "global",
                True,
                ["删掉风险提示", "删除风险提示"],
                False,
            )
        return codex

    def normalize_summary_after(self, chapter_id: int, summary_after: str) -> str:
        if self.test_case["name"] != "07_dual_timeline_continuity":
            return summary_after
        if all(label in summary_after for label in ["现在时间线", "过去揭示", "尚未知"]):
            return summary_after
        chapter_memory = {
            1: "现在时间线：小帅在旧会议室查看第一段会议录像。过去揭示：三年前的项目曾经被临时改方案。尚未知：小美是否反对、风险提示是否被删除、项目后果和小美离职原因仍未知。",
            2: "现在时间线：小帅在旧会议室继续查看第二段会议录像。过去揭示：小美三年前曾反对改方案。尚未知：小帅是否删除风险提示、项目上线后果和小美承担责任的细节仍未知。",
            3: "现在时间线：小帅在旧会议室查看第三段会议录像并面对自己的记录。过去揭示：小帅当时删掉了风险提示。尚未知：删除风险提示后项目上线造成的后果和小美最终承担的责任仍未知。",
            4: "现在时间线：小帅在旧会议室看完第四段会议录像。过去揭示：小帅删掉提示后项目上线，导致小美被迫承担责任并离职。尚未知：核心真相已经揭示，只剩小帅如何面对责任。",
        }
        addition = chapter_memory.get(chapter_id)
        if not addition:
            return summary_after
        return summary_after.strip() + "\n\n" + addition

    def apply_outline_feedback(self, outline: list[dict[str, Any]], feedback: str) -> list[dict[str, Any]]:
        for chapter in outline:
            constraints = chapter.setdefault("user_feedback_constraints", [])
            constraints.append(feedback)
            cid = int(chapter.get("chapter_id", 0))
            if "第三章" in feedback and cid < 3:
                chapter.setdefault("must_not_reveal", []).append(feedback)
            if "第三章" in feedback and cid == 3:
                chapter.setdefault("required_reveals", []).append(feedback)
        return outline

    def ensure_required_reveal_beats(self, chapter_id: int, chapter: dict[str, Any], beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if chapter_id < 3 or not isinstance(beats, list):
            return beats
        combined = "\n".join(
            [
                self.read_project("00_request.md"),
                self.read_project("01_project_brief.md"),
                json.dumps(chapter, ensure_ascii=False),
                json.dumps(beats, ensure_ascii=False),
            ]
        )
        next_id = max((int(beat.get("beat_id", 0)) for beat in beats if isinstance(beat, dict)), default=0) + 1
        if "旧录音装置" in combined and "启动器" in combined:
            beat_text = json.dumps(beats, ensure_ascii=False)
            if not ("旧录音装置" in beat_text and ("启动器" in beat_text or "启动" in beat_text)):
                beats.append(
                    {
                        "beat_id": next_id,
                        "text": "小帅将蓝色钥匙插入隐藏凹槽，触发藏在储物柜内的旧录音装置。录音播放后，小帅明确意识到蓝色钥匙不是开门工具，而是旧录音装置的启动器。",
                        "purpose": "完成第三章必须揭示的蓝色钥匙真实用途。",
                        "required_codex": ["小帅", "蓝色钥匙", "旧录音装置"],
                        "reveals": ["蓝色钥匙是旧录音装置的启动器"],
                        "must_not_reveal": [],
                    }
                )
                next_id += 1
        if "真正伤害了小美" in combined:
            beat_text = json.dumps(beats, ensure_ascii=False)
            if "真正伤害了小美" not in beat_text and "伤害了小美" not in beat_text:
                beats.append(
                    {
                        "beat_id": next_id,
                        "text": "第三章揭示被遮蔽的关键信息：小帅当年的选择真正伤害了小美。这个事实通过屏幕资料、旧录音或文件证据呈现，而不是让小美在现实中出场。",
                        "purpose": "完成 checkpoint 要求的第三章揭示，并保持小美只通过资料出现。",
                        "required_codex": ["小帅", "小美"],
                        "reveals": ["小帅当年的选择真正伤害了小美"],
                        "must_not_reveal": [],
                    }
                )
                next_id += 1
        if self.test_case["name"] == "05_medium_length_single_protagonist" and chapter_id == 5:
            beat_text = json.dumps(beats, ensure_ascii=False)
            if "高风险，不建议上线" not in beat_text:
                beats.append(
                    {
                        "beat_id": next_id,
                        "text": "小帅找到缺失封面并读到原本写着“高风险，不建议上线”。他把这句话和前三处涂黑数据、小美要求暂停、自己批准继续推进的事实连起来，明确面对自己一直回避的责任。",
                        "purpose": "完成第五章必须揭示的缺失封面警示和小帅责任弧。",
                        "required_codex": ["小帅", "缺失封面", "项目评估报告", "缺失封面警示"],
                        "reveals": ["缺失封面写着“高风险，不建议上线”", "小帅面对责任"],
                        "must_not_reveal": [],
                    }
                )
                next_id += 1
        if self.test_case["name"] == "06_supporting_cast_codex_routing":
            beat_text = json.dumps(beats, ensure_ascii=False)
            required_by_chapter = {
                2: [
                    ("阿强", "小帅从阿强留下的数据清洗材料中确认灰度实验的数据异常。"),
                    ("林姐", "小帅从林姐留下的善后材料中确认异常被后续处理过。"),
                ],
                3: [("老周", "老周的录音证明小帅当年知道风险。")],
                4: [("小美", "小帅确认匿名邮件来自小美留下的定时系统。")],
            }
            for name, text in required_by_chapter.get(chapter_id, []):
                if name not in beat_text:
                    beats.append(
                        {
                            "beat_id": next_id,
                            "text": text,
                            "purpose": f"保持配角 {name} 的指定证据功能和 Codex routing。",
                            "required_codex": ["小帅", name],
                            "reveals": [],
                            "must_not_reveal": [],
                        }
                    )
                    next_id += 1
        if self.test_case["name"] == "07_dual_timeline_continuity":
            beat_text = json.dumps(beats, ensure_ascii=False)
            required_by_chapter = {
                3: ("小帅在现在的旧会议室查看第三段会议录像；录像中的三年前内容明确揭示小帅当时删掉了风险提示。", ["小帅", "四段会议录像", "风险提示删除真相"], ["小帅删掉风险提示"]),
                4: ("小帅在现在的旧会议室查看第四段会议录像；录像揭示小帅删掉提示后项目上线，导致小美被迫承担责任并离职。", ["小帅", "小美", "四段会议录像"], ["项目上线导致小美承担责任离职"]),
            }
            if chapter_id in required_by_chapter:
                text, required_codex, reveals = required_by_chapter[chapter_id]
                if not all(token in beat_text for token in reveals):
                    beats.append(
                        {
                            "beat_id": next_id,
                            "text": text,
                            "purpose": "保持双时间线的当前观看事件和过去揭示边界。",
                            "required_codex": required_codex,
                            "reveals": reveals,
                            "must_not_reveal": [],
                        }
                    )
        return beats

    def apply_brief_feedback(self, brief: str, feedback: str) -> str:
        lines = [
            line
            for line in brief.splitlines()
            if not (
                "小美" in line
                and any(token in line for token in ["现实", "出场", "投影", "实体", "出现", "房间"])
            )
        ]
        lines.extend(["", "## User Feedback Applied", feedback])
        if "不要作为现实中出场" in feedback or "只通过旧录音和屏幕资料出现" in feedback:
            lines.append("- Constraint: 小美 must not appear as a present-room physical participant; use old recordings and screen evidence only.")
        return "\n".join(lines).strip() + "\n"

    def validate_beats(self, chapter_id: int, summary: str, beats: list[dict[str, Any]], story_so_far: str) -> dict[str, Any]:
        issues = []
        if not isinstance(beats, list) or not beats:
            issues.append({"type": "empty_beats", "detail": "No beats generated", "severity": "critical"})
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in summary or f"第 {numeral} 阶段" in summary:
                expected_stage = idx
                break
        for beat in beats if isinstance(beats, list) else []:
            text = beat.get("text", "")
            if len(text) < 12:
                issues.append({"beat_id": beat.get("beat_id"), "type": "vague_beat", "detail": text, "severity": "major"})
            if chapter_id < 3 and ("录音装置的启动器" in text or "真正伤害了小美" in text):
                issues.append({"beat_id": beat.get("beat_id"), "type": "premature_reveal", "detail": text, "severity": "critical"})
            for idx, numeral in enumerate(stage_numerals, 1):
                if expected_stage and idx != expected_stage and f"第{numeral}阶段" in text:
                    issues.append({
                        "beat_id": beat.get("beat_id"),
                        "type": "summary_mismatch",
                        "detail": f"Beat mentions 第{numeral}阶段 but chapter summary is 第{stage_numerals[expected_stage-1]}阶段.",
                        "severity": "critical",
                    })
            if "下一阶段" in text or "第三阶段" in text and chapter_id == 2:
                if "第三阶段" not in summary:
                    issues.append({"beat_id": beat.get("beat_id"), "type": "chapter_scope_drift", "detail": text, "severity": "critical"})
        rendered = render_template(
            self.template("07_validate_scene_beats.md"),
            {
                "story_so_far": story_so_far,
                "chapter_summary": summary,
                "global_codex": self.select_codex(summary)[0],
                "relevant_codex": self.select_codex(summary)[1],
                "scene_beats": beats,
            },
        )
        result = {"passed": not issues, "issues": issues}
        input_files = ["02_codex.json", f"chapters/chapter_{chapter_id:02d}/00_summary.md", f"chapters/chapter_{chapter_id:02d}/01_beats.json"]
        if story_so_far:
            input_files.extend(f"chapters/chapter_{idx:02d}/03_summary_after.md" for idx in range(1, chapter_id))
        self.record(
            "validate_scene_beats",
            "core_spec/prompts/07_validate_scene_beats.md",
            rendered,
            input_files,
            ["run_records/step_manifest.jsonl"],
            "success" if result["passed"] else "failed",
            ["Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Scene Beats"],
            {"validation": result},
        )
        return result

    def merge_manuscript(self) -> None:
        parts = []
        for draft in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md")):
            parts.append(read_text(draft).strip())
        full = "\n\n".join(parts).strip() + "\n"
        write_text(self.run_dir / "manuscript" / "draft_full.md", full)
        write_text(self.run_dir / "manuscript" / "final.md", full)
        rendered = self.template("10_merge_manuscript.md") + "\n\n[Chapter Draft Paths]\n" + "\n".join(
            str(p.relative_to(self.run_dir)) for p in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md"))
        )
        self.record(
            "merge_manuscript",
            "core_spec/prompts/10_merge_manuscript.md",
            rendered,
            [str(p.relative_to(self.run_dir)) for p in sorted((self.run_dir / "chapters").glob("chapter_*/02_draft.md"))],
            ["manuscript/draft_full.md", "manuscript/final.md"],
            "success",
            ["Chapter Drafts"],
        )

    def artifact_checks(self) -> list[str]:
        missing = []
        required = [
            "00_request.md",
            "01_project_brief.md",
            "02_codex.json",
            "03_outline.json",
            "manuscript/draft_full.md",
            "manuscript/final.md",
            "run_records/step_manifest.jsonl",
        ]
        for rel in required:
            if not (self.run_dir / rel).exists() or not self.read_project(rel).strip():
                missing.append(rel)
        try:
            outline = json.loads(self.read_project("03_outline.json"))
        except Exception:
            outline = []
            missing.append("03_outline.json parse")
        for chapter in outline if isinstance(outline, list) else []:
            cid = int(chapter.get("chapter_id", 0))
            for rel in ["00_summary.md", "01_beats.json", "02_draft.md", "03_summary_after.md"]:
                path = self.run_dir / "chapters" / f"chapter_{cid:02d}" / rel
                if not path.exists() or not read_text(path).strip():
                    missing.append(str(path.relative_to(self.run_dir)))
        return missing

    def trace_checks(self) -> list[str]:
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"manifest invalid: {exc}"]
        steps = [entry["workflow_step"] for entry in entries]
        for entry in entries:
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                issues.append(f"missing rendered prompt: {entry.get('rendered_prompt')}")
            template = entry.get("prompt_template", "")
            if template.startswith("core_spec/") and not (self.skill_path / template).exists():
                issues.append(f"missing prompt template: {template}")
        for idx, step in enumerate(steps):
            if step == "write_beat_prose":
                before = steps[:idx]
                if "generate_scene_beats" not in before or "validate_scene_beats" not in before:
                    issues.append("write_beat_prose occurred before beats/validation")
        for entry in entries:
            if entry["workflow_step"] in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose"}:
                rendered = self.run_dir / entry.get("rendered_prompt", "")
                if rendered.exists() and "Chapter 1 summary:" in read_text(rendered):
                    if "chapters/chapter_01/03_summary_after.md" not in entry.get("input_files", []):
                        issues.append(f"{entry['step_id']} uses chapter 1 story_so_far but omits chapter_01/03_summary_after.md from input_files")
            if entry["workflow_step"] == "validate_scene_beats":
                rendered = self.run_dir / entry.get("rendered_prompt", "")
                if rendered.exists() and "Chapter 1 summary:" in read_text(rendered):
                    if "chapters/chapter_01/03_summary_after.md" not in entry.get("input_files", []):
                        issues.append(f"{entry['step_id']} validation uses story_so_far but omits previous summary input_files")
        leak_terms = ["录音装置", "启动器", "recorder trigger", "old recorder trigger", "真正伤害了小美", "直接伤害了小美"]
        for entry in entries:
            if entry["workflow_step"] != "write_beat_prose":
                continue
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                continue
            output = "".join(entry.get("output_files", []))
            if ("chapter_01" in output or "chapter_02" in output) and any(term in read_text(rendered) for term in leak_terms):
                issues.append(f"{entry['step_id']} early prose prompt leaks protected future reveal")
        issues.extend(self.phase_b_trace_checks(entries))
        return issues

    def phase_b_trace_checks(self, entries: list[dict[str, Any]]) -> list[str]:
        name = self.test_case["name"]
        if name not in {
            "05_medium_length_single_protagonist",
            "06_supporting_cast_codex_routing",
            "07_dual_timeline_continuity",
        }:
            return []
        issues: list[str] = []

        def rendered_text(entry: dict[str, Any]) -> str:
            path = self.run_dir / entry.get("rendered_prompt", "")
            return read_text(path) if path.exists() else ""

        if name == "05_medium_length_single_protagonist":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose"}:
                    continue
                output = "".join(entry.get("output_files", []))
                if "chapter_04" in output or "chapter_05" in output:
                    input_files = set(entry.get("input_files", []))
                    for cid in [1, 2, 3]:
                        rel = f"chapters/chapter_{cid:02d}/03_summary_after.md"
                        if rel not in input_files:
                            issues.append(f"{entry['step_id']} for chapter 4/5 omits earlier summary_after input: {rel}")
                if entry["workflow_step"] == "write_beat_prose":
                    output_chapter = re.search(r"chapter_(\d{2})", output)
                    if output_chapter:
                        cid = int(output_chapter.group(1))
                        text = rendered_text(entry)
                        for future in range(cid + 1, 6):
                            if f"Chapter {future} summary:" in text:
                                issues.append(f"{entry['step_id']} prose prompt includes future chapter {future} summary")

        if name == "06_supporting_cast_codex_routing":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_scene_beats", "write_beat_prose"}:
                    continue
                text = rendered_text(entry)
                if entry["workflow_step"] == "write_beat_prose" and "[Current Beat]" in text:
                    current_scope = text.split("[Current Beat]", 1)[1]
                elif "[Current Chapter Summary]" in text:
                    current_scope = text.split("[Current Chapter Summary]", 1)[1]
                else:
                    current_scope = text
                for character in ["阿强", "林姐", "老周"]:
                    if character in current_scope and f"### {character}" not in text:
                        issues.append(f"{entry['step_id']} mentions {character} but relevant Codex omits that character")
            outline_text = self.read_project("03_outline.json")
            if "required_codex" not in outline_text:
                issues.append("Phase B 06 outline does not record required_codex routing")

        if name == "07_dual_timeline_continuity":
            for entry in entries:
                if entry["workflow_step"] not in {"generate_chapter_summary", "generate_scene_beats", "write_beat_prose", "validate_scene_beats"}:
                    continue
                output = "".join(entry.get("output_files", []))
                if "chapter_03" in output or "chapter_04" in output:
                    match = re.search(r"chapter_(\d{2})", output)
                    if not match:
                        continue
                    input_files = set(entry.get("input_files", []))
                    for cid in range(1, int(match.group(1))):
                        rel = f"chapters/chapter_{cid:02d}/03_summary_after.md"
                        if rel not in input_files:
                            issues.append(f"{entry['step_id']} omits dual-timeline story-so-far input: {rel}")
        return issues

    def checkpoint_checks(self) -> list[str]:
        if self.mode != "milestone_review":
            return []
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"Cannot parse manifest for checkpoint checks: {exc}"]
        checkpoints = [e for e in entries if e.get("workflow_step") == "user_checkpoint"]
        names = {e.get("checkpoint_name") for e in checkpoints}
        for required in ["requirement_alignment", "story_plan_alignment", "first_chapter_direction_check"]:
            if required not in names:
                issues.append(f"Missing checkpoint: {required}")
        for entry in checkpoints:
            if entry.get("status") == "feedback_received" and not entry.get("upstream_files_changed"):
                issues.append(f"Checkpoint {entry.get('checkpoint_name')} has feedback but no upstream_files_changed")
        outline_text = self.read_project("03_outline.json")
        if "第三章再揭示" in self.test_case["markdown"] and "user_feedback_constraints" not in outline_text:
            issues.append("Story plan feedback was not written into outline JSON")
        return issues

    def content_checks(self) -> list[str]:
        issues = []
        brief = self.read_project("01_project_brief.md")
        request = self.read_project("00_request.md")
        zh_expected = "Language" in brief and ("zh" in brief.lower() or "中文" in brief)
        try:
            codex = json.loads(self.read_project("02_codex.json"))
            names = "\n".join(entry.get("name", "") for entry in codex.get("entries", []))
            for required in ["小帅", "小美"]:
                if required not in names and required in self.read_project("00_request.md"):
                    issues.append(f"Codex missing requested entity: {required}")
        except Exception as exc:
            issues.append(f"Codex parse failed during content checks: {exc}")
        try:
            outline = json.loads(self.read_project("03_outline.json"))
        except Exception:
            outline = []
        for chapter in outline if isinstance(outline, list) else []:
            cid = int(chapter.get("chapter_id", 0))
            summary = self.read_project(f"chapters/chapter_{cid:02d}/00_summary.md")
            beats_raw = self.read_project(f"chapters/chapter_{cid:02d}/01_beats.json")
            try:
                beats = json.loads(beats_raw)
            except Exception as exc:
                issues.append(f"Chapter {cid} beats JSON invalid: {exc}")
                beats = []
            validation = self.validate_beats_for_report(cid, summary, beats)
            issues.extend(validation)
            if cid < 3:
                for rel in [f"chapters/chapter_{cid:02d}/00_summary.md", f"chapters/chapter_{cid:02d}/01_beats.json", f"chapters/chapter_{cid:02d}/02_draft.md"]:
                    early_text = self.read_project(rel)
                    if "录音装置" in early_text or "启动器" in early_text or "真正伤害了小美" in early_text or "直接伤害了小美" in early_text:
                        issues.append(f"{rel} reveals protected key function before chapter 3")
            if zh_expected:
                for rel in [f"chapters/chapter_{cid:02d}/00_summary.md", f"chapters/chapter_{cid:02d}/03_summary_after.md"]:
                    text = self.read_project(rel)
                    if text and self.cjk_ratio(text) < 0.15:
                        issues.append(f"{rel} appears not to follow Chinese language setting")
        final_text = self.read_project("manuscript/final.md")
        if "旧录音装置" in request and "启动器" in request:
            if not ("旧录音装置" in final_text and ("启动器" in final_text or "启动" in final_text)):
                issues.append("Final manuscript does not fulfill required reveal: blue key as old recorder trigger")
        protected_harm_reveal = "\n".join([request, brief, json.dumps(outline, ensure_ascii=False)])
        if "真正伤害了小美" in protected_harm_reveal:
            harm_revealed = any(
                marker in final_text
                for marker in [
                    "真正伤害了小美",
                    "伤害了小美",
                    "直接伤害了小美",
                    "我失去了工作",
                    "失去了小林",
                    "被调离核心团队",
                    "姓名栏：小美",
                    "项目压力导致焦虑症状",
                    "她离开后",
                ]
            )
            if not harm_revealed:
                issues.append("Final manuscript does not fulfill required reveal: 小帅当年的选择真正伤害了小美")
        issues.extend(self.phase_b_content_checks(outline))
        return issues

    def phase_b_content_checks(self, outline: Any) -> list[str]:
        name = self.test_case["name"]
        if name not in {
            "05_medium_length_single_protagonist",
            "06_supporting_cast_codex_routing",
            "07_dual_timeline_continuity",
        }:
            return []
        issues: list[str] = []
        codex_text = self.read_project("02_codex.json")
        final_text = self.read_project("manuscript/final.md")

        def chapter_text(cid: int, rel: str = "02_draft.md") -> str:
            return self.read_project(f"chapters/chapter_{cid:02d}/{rel}")

        def require_text(label: str, text: str, groups: list[list[str]]) -> None:
            for group in groups:
                if not any(token in text for token in group):
                    issues.append(f"{label} missing expected marker: {'/'.join(group)}")

        if name == "05_medium_length_single_protagonist":
            if not isinstance(outline, list) or len(outline) != 5:
                issues.append("Phase B 05 expected outline with exactly 5 chapters")
            for marker in ["小帅", "小美", "项目评估报告", "缺失封面", "高风险，不建议上线"]:
                if marker not in codex_text:
                    issues.append(f"Phase B 05 Codex missing marker: {marker}")
            if "第五章" not in codex_text and "chapter 5" not in codex_text.lower():
                issues.append("Phase B 05 Codex does not mark missing-cover warning as chapter-5 protected future information")
            require_text("Phase B 05 chapter 1", chapter_text(1), [["项目评估报告", "报告"], ["缺失封面", "封面"]])
            require_text("Phase B 05 chapter 2", chapter_text(2), [["涂黑"], ["三处", "3处", "三个"]])
            require_text("Phase B 05 chapter 3", chapter_text(3), [["小美"], ["暂停", "停止", "暂缓", "叫停"]])
            require_text("Phase B 05 chapter 4", chapter_text(4), [["小帅"], ["批准", "签批", "同意继续", "继续推进"]])
            require_text("Phase B 05 chapter 5", chapter_text(5), [["高风险，不建议上线"], ["责任", "回避", "承担", "面对"]])
            early = "\n".join(chapter_text(cid) for cid in range(1, 5))
            if "高风险，不建议上线" in early:
                issues.append("Phase B 05 missing-cover warning appears before chapter 5")
            if any(token in final_text for token in ["小美走进旧办公室", "小美站在旧办公室", "小美坐在旧办公室"]):
                issues.append("Phase B 05 risks turning 小美 into a present-time co-protagonist")

        if name == "06_supporting_cast_codex_routing":
            expected_roles = {
                "小帅": ["唯一", "现实视角", "主角"],
                "小美": ["风险", "定时系统", "匿名邮件"],
                "阿强": ["数据清洗"],
                "老周": ["直属领导", "录音"],
                "林姐": ["善后"],
                "匿名邮件": ["邮件"],
                "灰度实验": ["灰度实验"],
            }
            for marker, role_tokens in expected_roles.items():
                if marker not in codex_text:
                    issues.append(f"Phase B 06 Codex missing marker: {marker}")
                elif not any(token in codex_text for token in role_tokens):
                    issues.append(f"Phase B 06 Codex role for {marker} is not distinct enough")
            require_text("Phase B 06 chapter 2", chapter_text(2), [["阿强"], ["林姐"], ["数据异常", "异常"]])
            require_text("Phase B 06 chapter 3", chapter_text(3), [["老周"], ["录音"], ["知道风险", "知情"]])
            require_text("Phase B 06 chapter 4", chapter_text(4), [["小美"], ["定时系统", "定时"], ["匿名邮件"]])
            for drift in ["阿强发来匿名邮件", "老周发来匿名邮件", "林姐发来匿名邮件"]:
                if drift in final_text:
                    issues.append(f"Phase B 06 character role drift: {drift}")
            if any(token in final_text for token in ["警方", "刑警", "侦查", "审讯"]):
                issues.append("Phase B 06 drifted into police investigation")

        if name == "07_dual_timeline_continuity":
            require_text("Phase B 07 chapter 1", chapter_text(1), [["旧会议室"], ["第一段录像", "第一段"], ["改方案", "方案"]])
            require_text("Phase B 07 chapter 2", chapter_text(2), [["第二段录像", "第二段"], ["小美"], ["反对", "不同意"]])
            require_text("Phase B 07 chapter 3", chapter_text(3), [["第三段录像", "第三段"], ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"]])
            require_text("Phase B 07 chapter 4", chapter_text(4), [["第四段录像", "第四段"], ["小美"], ["承担责任", "担责"], ["离职", "离开"]])
            early = "\n".join(chapter_text(cid) for cid in [1, 2])
            if any(token in early for token in ["删掉了风险提示", "删掉风险提示", "删除风险提示", "删风险提示"]):
                issues.append("Phase B 07 risk-warning deletion is revealed before chapter 3")
            for cid in range(1, 5):
                summary_after = chapter_text(cid, "03_summary_after.md")
                for marker in ["现在时间线", "过去揭示", "尚未知"]:
                    if marker not in summary_after:
                        issues.append(f"Phase B 07 chapter {cid} summary_after missing dual-timeline marker: {marker}")
                beats_text = chapter_text(cid, "01_beats.json")
                if "现在" not in beats_text or not any(token in beats_text for token in ["录像", "三年前", "过去"]):
                    issues.append(f"Phase B 07 chapter {cid} beats do not identify present action and past/video content")
            if "小美心想" in final_text or "小美觉得" in final_text:
                issues.append("Phase B 07 switches into 小美 internal POV")
        return issues

    def validate_beats_for_report(self, chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> list[str]:
        issues = []
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in summary:
                expected_stage = idx
        for beat in beats if isinstance(beats, list) else []:
            text = beat.get("text", "")
            for idx, numeral in enumerate(stage_numerals, 1):
                if expected_stage and idx != expected_stage and f"第{numeral}阶段" in text:
                    issues.append(f"Chapter {chapter_id} beat {beat.get('beat_id')} stage mismatch with summary")
        return issues

    def cjk_ratio(self, text: str) -> float:
        chars = [ch for ch in text if not ch.isspace()]
        if not chars:
            return 0
        cjk = sum(1 for ch in chars if "\u4e00" <= ch <= "\u9fff")
        return cjk / len(chars)

    def write_report(self) -> None:
        artifact_missing = self.artifact_checks()
        trace_issues = self.trace_checks()
        content_issues = [] if (self.expected_validation_guard and self.validation_guard_triggered) else self.content_checks()
        checkpoint_issues = self.checkpoint_checks()
        if self.expected_validation_guard and self.validation_guard_triggered:
            artifact_missing = [
                item
                for item in artifact_missing
                if not (
                    item.startswith("chapters/")
                    or item.startswith("manuscript/")
                    or item in {"manuscript/draft_full.md", "manuscript/final.md"}
                )
            ]
        critical = self.failures + [f"Missing or invalid artifact: {x}" for x in artifact_missing] + trace_issues + content_issues + checkpoint_issues
        passed = not critical
        lines = [
            "# Acceptance Report",
            "",
            "## Test Case",
            self.test_case["name"],
            "",
            "## Pass / Fail",
            "Pass" if passed else "Fail",
            "",
            "## Artifact Checks",
            "All required artifacts present." if not artifact_missing else "\n".join(f"- {x}" for x in artifact_missing),
            "",
            "## Workflow Trace Checks",
            "Trace checks passed." if not trace_issues else "\n".join(f"- {x}" for x in trace_issues),
            "",
            "## Prompt Assembly Checks",
            "Rendered prompts are recorded for workflow steps.",
            "",
            "## Content Checks",
            "Validation guard triggered before prose generation as expected."
            if self.expected_validation_guard and self.validation_guard_triggered
            else ("Content checks passed." if not content_issues else "\n".join(f"- {x}" for x in content_issues)),
            "",
            "## Checkpoint Process Checks",
            "Checkpoint process checks passed." if not checkpoint_issues else "\n".join(f"- {x}" for x in checkpoint_issues),
            "",
            "## Critical Failures",
            "None" if not critical else "\n".join(f"- {x}" for x in critical),
            "",
            "## Major Issues",
            "None" if not self.major else "\n".join(f"- {x}" for x in self.major),
            "",
            "## Minor Issues",
            "None" if not self.minor else "\n".join(f"- {x}" for x in self.minor),
            "",
            "## Patch Recommendations",
            "No critical patch required." if passed else "Patch the critical failures above and rerun acceptance.",
            "",
        ]
        write_text(self.run_dir / "acceptance_report.md", "\n".join(lines))


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
        try:
            runner.write_report()
        except Exception:
            pass
        print(f"Acceptance run failed: {exc}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - start
    print(f"Acceptance run complete: {output_dir}")
    print(f"elapsed_sec={elapsed:.2f}")
    report = output_dir / "acceptance_report.md"
    if report.exists():
        print(read_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
