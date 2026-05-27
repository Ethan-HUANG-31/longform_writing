"""Shared infrastructure for the longform-writing workflow."""

from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


GENRE_ADAPTERS: dict[str, dict[str, str]] = {
    "locked_room_moral_trial": {
        "label": "locked_room_moral_trial",
        "title": "Psychological Thriller / Locked-Room Moral Trial",
        "body": "\n".join(
            [
                "- Keep the room, trial, or pressure rules visible and internally consistent.",
                "- Make pressure come from choices, evidence, self-justification, and moral cost.",
                "- Do not add gore, bodily harm, or supernatural explanations unless the request asks for them.",
                "- Escalate reveals in order; do not leak protected future evidence early.",
            ]
        ),
    },
    "romance": {
        "label": "romance",
        "title": "Romance",
        "body": "\n".join(
            [
                "- Track both romantic leads as full people with distinct desire, fear, flaw, and non-romantic stakes.",
                "- Progress relationship milestones believably: forced proximity, guarded trust, earned vulnerability, rupture, choice.",
                "- Let obstacles create emotional stakes through professional choices and values, not random coincidence.",
                "- Use subtext, changing intimacy, and what characters avoid saying; do not explain all backstory in dialogue.",
                "- Do not rush the final resolution; make it depend on a mature character choice.",
            ]
        ),
    },
    "fantasy": {
        "label": "fantasy",
        "title": "Fantasy",
        "body": "\n".join(
            [
                "- Put magic, world rules, limitations, and costs into Codex Rules/Lore and keep them consistent.",
                "- Respect the stated magic cost and do not invent additional magic systems.",
                "- Make fantasy elements shape character choices instead of solving conflicts without setup.",
                "- Introduce terminology naturally through action, objects, and social routine.",
                "- Keep worldbuilding in service of the current beat and chapter plan.",
            ]
        ),
    },
    "mystery_clue_fairness": {
        "label": "mystery_clue_fairness",
        "title": "Mystery / Clue Fairness",
        "body": "\n".join(
            [
                "- Plant clues before payoff and keep a running clue state in chapter summaries.",
                "- Red herrings may mislead, but they must not contradict the final truth.",
                "- Deductions must use evidence available to the protagonist before the reveal.",
                "- The final reveal must be fair and must not depend on evidence first introduced in the reveal chapter.",
                "- Preserve suspect timing; do not identify the true mover/culprit before the requested reveal point.",
            ]
        ),
    },
    "general": {
        "label": "general",
        "title": "General Fiction",
        "body": "- Follow the user's requested genre conventions without adding unsupported genre machinery.",
    },
}


BASE_ADAPTER = "\n".join(
    [
        "[Genre Adapter]",
        "Selected adapter: {label}",
        "",
        "## Base Fiction Rules",
        "- Use active, concrete prose with action and dialogue.",
        "- Follow the current beat; do not conclude or advance beyond it.",
        "- Preserve the project language, POV, tone, and hard prohibitions.",
        "- Do not leak future reveals or hidden evidence before its planned chapter.",
        "",
        "## {title} Adapter",
        "{body}",
    ]
)


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
        self.max_retries = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "3"))
        self.retry_base_delay = float(os.environ.get("DEEPSEEK_RETRY_BASE_DELAY", "1.0"))

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
        raw = ""
        for attempt in range(1, self.max_retries + 1):
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
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {408, 409, 429, 500, 502, 503, 504} or attempt >= self.max_retries:
                    raise RuntimeError(f"HTTP {exc.code}: {body[:1000]}") from exc
                time.sleep(self.retry_base_delay * attempt)
            except (
                TimeoutError,
                ConnectionError,
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                urllib.error.URLError,
            ) as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"Model request failed after {self.max_retries} attempts: {exc}") from exc
                time.sleep(self.retry_base_delay * attempt)
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


def sanitize_scene_beats(beats: Any) -> list[dict[str, Any]]:
    if not isinstance(beats, list):
        return []
    sanitized: list[dict[str, Any]] = []
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        text = str(beat.get("text", "")).strip()
        purpose = str(beat.get("purpose", "")).strip()
        if not text and not purpose:
            continue
        copied = dict(beat)
        copied["text"] = text
        if "purpose" in copied:
            copied["purpose"] = purpose
        sanitized.append(copied)
    return sanitized


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


@dataclass
class WorkflowResult:
    success: bool
    failures: list[str] = field(default_factory=list)
    major: list[str] = field(default_factory=list)
    minor: list[str] = field(default_factory=list)
    feedback_applied: list[str] = field(default_factory=list)
    expected_validation_guard: bool = False
    validation_guard_triggered: bool = False
    genre_adapter_key: str = "general"


@dataclass
class WorkflowState:
    parsed_requirement: dict[str, Any] = field(default_factory=dict)
    outline: list[dict[str, Any]] = field(default_factory=list)
    story_so_far: str = ""
    previous_summary_files: list[str] = field(default_factory=list)

    def add_summary(self, chapter_id: int, summary_after: str) -> None:
        self.story_so_far += f"\n\nChapter {chapter_id} summary:\n{summary_after.strip()}\n"
        self.previous_summary_files.append(f"chapters/chapter_{chapter_id:02d}/03_summary_after.md")


class WorkflowContext:
    def __init__(
        self,
        skill_path: Path,
        test_case: dict[str, Any],
        run_dir: Path,
        provider: str,
        mode: str,
        beat_count: int,
        prose_word_count: int,
    ) -> None:
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
        self.genre_adapter_key = "general"
        self.genre_adapter_text = self.render_genre_adapter("general")

    @property
    def manifest(self) -> Path:
        return self.run_dir / "run_records" / "step_manifest.jsonl"

    @property
    def prompts_dir(self) -> Path:
        return self.run_dir / "run_records" / "rendered_prompts"

    def template(self, name: str) -> str:
        return read_text(self.skill_path / "core_spec" / "prompts" / name)

    def detect_genre_adapter(self, parsed: dict[str, Any] | None = None) -> str:
        text = "\n".join(
            [
                self.test_case.get("request", ""),
                json.dumps(parsed or {}, ensure_ascii=False),
            ]
        ).lower()
        if any(token in text for token in ["奇幻", "魔法", "fantasy", "low-magic", "低魔"]):
            return "fantasy"
        if any(token in text for token in ["本格", "mystery", "clue", "线索", "推理", "red herring"]):
            if not any(token in text for token in ["审判", "道德选择", "moral trial", "locked-room moral trial"]):
                return "mystery_clue_fairness"
        romance_blocked = any(token in text for token in ["不要写成恋爱", "不要恋爱", "不要写成 romance", "not romance"])
        if not romance_blocked and any(token in text for token in ["爱情", "恋爱", "romance", "relationship-focused", "关系推进", "黑暗时刻"]):
            return "romance"
        if any(token in text for token in ["密室", "审判", "心理惊悚", "moral trial", "locked-room"]):
            return "locked_room_moral_trial"
        return "general"

    def render_genre_adapter(self, key: str) -> str:
        spec = GENRE_ADAPTERS.get(key, GENRE_ADAPTERS["general"])
        return BASE_ADAPTER.format(label=spec["label"], title=spec["title"], body=spec["body"])

    def genre_extra(self) -> dict[str, Any]:
        if not self.genre_adapter_key:
            return {}
        return {"genre_adapter": self.genre_adapter_key}

    def genre_context(self) -> list[str]:
        return ["Genre Adapter"]

    def initialize_project(self) -> None:
        template_dir = self.skill_path / "templates" / "writing_project_v0"
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        shutil.copytree(template_dir, self.run_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        write_text(self.manifest, "")
        write_text(self.run_dir / "00_request.md", self.test_case["request"].strip() + "\n")
        append_text(self.run_dir / "writing_log.md", f"\n- Initialized run from {self.test_case['name']}.\n")

    def initialize(self) -> None:
        self.initialize_project()

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
        extra: dict[str, Any] | None = None,
    ) -> str:
        rendered = render_template(self.template(prompt_file), values)
        output = self.client.complete(rendered, max_tokens=max_tokens, temperature=temperature)
        self.record(workflow_step, f"core_spec/prompts/{prompt_file}", rendered, input_files, output_files, "success", context_sections, extra)
        return output

    def parse_or_retry_json(
        self,
        output: str,
        *,
        workflow_step: str,
        input_files: list[str],
        output_files: list[str],
        expected_shape: str,
    ) -> Any:
        try:
            return extract_json(output)
        except Exception as exc:
            retry_prompt = (
                "下面内容本应是合法 JSON，但解析失败。请只输出修复后的合法 JSON，不要解释，不要 markdown fences。\n"
                f"期望形状：{expected_shape}\n"
                f"解析错误：{exc}\n\n"
                "[Invalid Output]\n"
                f"{output}"
            )
            repaired = self.client.complete(retry_prompt, max_tokens=2200, temperature=0)
            self.record(
                f"{workflow_step}_retry_json",
                "json_repair",
                retry_prompt,
                input_files,
                output_files,
                "success",
                ["JSON Repair"],
                self.genre_extra(),
            )
            return extract_json(repaired)

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

    def normalize_codex(self, codex: Any) -> dict[str, Any]:
        if not isinstance(codex, dict):
            codex = {"version": "0.1", "entries": []}
        entries = codex.setdefault("entries", [])
        if not isinstance(entries, list):
            codex["entries"] = []
        return codex

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

    def apply_brief_feedback(self, brief: str, feedback: str) -> str:
        lines = brief.splitlines()
        lines.extend(["", "## User Feedback Applied", feedback])
        return "\n".join(lines).strip() + "\n"

    def cjk_ratio(self, text: str) -> float:
        chars = [ch for ch in text if not ch.isspace()]
        if not chars:
            return 0
        cjk = sum(1 for ch in chars if "\u4e00" <= ch <= "\u9fff")
        return cjk / len(chars)

    def current_chapter_draft_path(self, chapter_id: int) -> Path:
        return self.run_dir / "chapters" / f"chapter_{chapter_id:02d}" / "02_draft.md"
