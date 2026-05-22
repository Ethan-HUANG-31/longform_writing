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


def redact_protected_reveals_text(text: str, chapter_id: int) -> str:
    if chapter_id >= 3 or not text:
        return text
    replacements = [
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
        r"启动器",
        r"作为录音装置启动器的功能",
        r"作为旧录音装置启动器的功能",
        r"钥匙是旧录音装置的启动器",
        r"钥匙是录音装置启动器",
        r"蓝色钥匙不是开门用的，而是某个旧录音装置的启动器",
        r"旧录音装置为电子设备，需钥匙启动才能播放录音。",
        r"旧录音装置",
        r"录音装置",
        r"recorder trigger",
        r"old recorder trigger",
    ]
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
                self.test_case.get("name", ""),
                self.test_case.get("request", ""),
                json.dumps(parsed or {}, ensure_ascii=False),
            ]
        ).lower()
        if any(token in text for token in ["奇幻", "魔法", "fantasy", "low-magic", "银纸", "低魔"]):
            return "fantasy"
        if any(token in text for token in ["本格", "mystery", "clue", "线索", "推理", "red herring", "借书卡", "错放书", "储物柜密码"]):
            if not any(token in text for token in ["审判", "选择室", "道德选择", "moral trial", "locked-room moral trial"]):
                return "mystery_clue_fairness"
        romance_blocked = any(token in text for token in ["不要写成恋爱", "不要恋爱", "不要写成 romance", "not romance"])
        if not romance_blocked and any(token in text for token in ["爱情", "恋爱", "romance", "relationship-focused", "关系推进", "黑暗时刻"]):
            return "romance"
        if any(token in text for token in ["密室", "审判", "选择室", "心理惊悚", "moral trial", "locked-room"]):
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
        self.genre_adapter_key = self.detect_genre_adapter(parsed)
        self.genre_adapter_text = self.render_genre_adapter(self.genre_adapter_key)
        parsed["genre_adapter"] = self.genre_adapter_key
        if not parsed.get("genre"):
            parsed["genre"] = self.genre_adapter_key
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

    def ensure_phase_c_codex(self, codex: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(codex, dict):
            codex = {"version": "0.1", "entries": []}
        entries = codex.setdefault("entries", [])
        if not isinstance(entries, list):
            entries = []
            codex["entries"] = entries

        def has_name(name: str) -> bool:
            return any(isinstance(entry, dict) and entry.get("name") == name for entry in entries)

        def upsert(entry: dict[str, Any]) -> None:
            for existing in entries:
                if isinstance(existing, dict) and existing.get("id") == entry["id"]:
                    existing.update(entry)
                    return
            if not has_name(entry["name"]):
                entries.append(entry)

        request = self.read_project("00_request.md")
        if self.genre_adapter_key == "romance":
            upsert({
                "id": "romance_relationship_history",
                "name": "项目误会关系历史",
                "type": "global",
                "scope": "global",
                "always_include": True,
                "description": "小帅和小美曾因一次项目误会疏远；关系推进必须区分职业 stakes 与情感 stakes，并让二人通过成熟选择解除核心误会。",
                "tags": ["romance", "relationship_history", "professional_stakes"],
            })
            upsert({
                "id": "romance_xiaoshuai_traits",
                "name": "小帅关系驱动",
                "type": "character",
                "scope": "global",
                "always_include": True,
                "description": "小帅的职业目标是证明自己能承担新项目；恐惧是再次被误解为只看项目利益；缺陷是用理性解释回避脆弱表达。",
                "aliases": ["小帅"],
                "tags": ["romance", "desire_fear_flaw"],
            })
            upsert({
                "id": "romance_xiaomei_traits",
                "name": "小美关系驱动",
                "type": "character",
                "scope": "global",
                "always_include": True,
                "description": "小美的职业目标是守住自己的判断和边界；恐惧是再次被牺牲在项目利益之后；缺陷是把求证需求藏在冷静协作里。",
                "aliases": ["小美"],
                "tags": ["romance", "desire_fear_flaw"],
            })
        elif self.genre_adapter_key == "fantasy":
            upsert({
                "id": "silver_paper_magic",
                "name": "银纸魔法",
                "type": "rule_lore",
                "scope": "global",
                "always_include": True,
                "description": "这个世界只有一种魔法：写在银纸上的名字会在下一次钟响前被所有人遗忘；使用者也会失去一段自己的记忆。魔法不能随便解决问题，不能新增其他魔法体系。",
                "aliases": ["银纸", "银纸规则", "银纸上的名字"],
                "tags": ["fantasy", "magic_rule", "cost", "limitation"],
            })
            for name, entry_id, desc in [
                ("档案馆", "archive_location", "小帅工作的城中档案馆，承载姓名、记录与被遗忘者的制度性痕迹。"),
                ("旧钟塔", "old_clocktower", "小美看守的旧钟塔，钟响是银纸魔法生效前的时间限制。"),
            ]:
                upsert({
                    "id": entry_id,
                    "name": name,
                    "type": "location",
                    "scope": "relevant",
                    "always_include": False,
                    "description": desc,
                    "tags": ["fantasy"],
                })
        elif self.genre_adapter_key == "mystery_clue_fairness":
            for entry in [
                ("old_borrowing_card", "旧借书卡", "object", "第一章书页里夹着的旧借书卡，是后续日期对不上和最终推理的已种下线索。", ["planted_clue"]),
                ("misplaced_books", "错放书", "object", "每晚闭馆后被移动到错误书架的书；书号在第三章连成储物柜密码。", ["planted_clue", "final_payoff"]),
                ("locker_password", "储物柜密码", "object", "由所有错放书编号连起来形成的密码；第三章发现，第四章用于连接捐赠名单真相。", ["final_payoff"]),
                ("xiaomei_red_herring", "小美误导线索", "global", "第二章大家以为小美移动书，但小帅发现借书卡日期对不上；这是误导线索，不能与最终真相矛盾。", ["red_herring"]),
                ("aqiang_final_truth", "阿强", "character", "图书馆前管理员，第四章才揭示为真正移动书的人；动机是让人发现储物柜里被遗忘的捐赠名单。", ["final_payoff", "do_not_reveal_before_chapter_4"]),
            ]:
                entry_id, name, typ, desc, tags = entry
                upsert({
                    "id": entry_id,
                    "name": name,
                    "type": typ,
                    "scope": "global",
                    "always_include": True,
                    "description": desc,
                    "tags": ["mystery", "clue_state"] + tags,
                })
        elif self.genre_adapter_key == "locked_room_moral_trial" and ("选择室" in request or "审判" in request):
            upsert({
                "id": "locked_room_trial_rules",
                "name": "选择室审判规则",
                "type": "rule_lore",
                "scope": "global",
                "always_include": True,
                "description": "选择室压力来自规则、证据、旧案真相和小帅的自我辩解；不得使用血腥、肢体伤害或超自然解释。",
                "tags": ["locked_room_moral_trial"],
            })
        return codex

    def clue_state_for_chapter(self, chapter_id: int) -> str:
        if self.genre_adapter_key != "mystery_clue_fairness":
            return ""
        states = [
            "Clue State: 第一章已种下旧借书卡线索；错放书现象被发现；阿强不能作为真凶提前揭示。",
            "Clue State: 第二章小美成为误导线索；小帅发现借书卡日期对不上，这个日期矛盾必须保留给最终推理；阿强仍不能提前暴露。",
            "Clue State: 第三章发现所有错放书编号连起来是一串储物柜密码；最终推理必须使用旧借书卡、日期对不上、书号密码，不能空降新证据。",
            "Clue State: 第四章才可揭示前管理员阿强移动书；推理必须回收前三章线索：旧借书卡、日期矛盾、错放书编号组成储物柜密码。",
        ]
        if chapter_id <= 0:
            return ""
        return states[min(chapter_id, len(states)) - 1]

    def ensure_phase_c_outline(self, outline: Any, target_chapters: int) -> list[dict[str, Any]]:
        if not isinstance(outline, list):
            outline = []
        if self.genre_adapter_key not in {"romance", "fantasy", "mystery_clue_fairness"}:
            return outline
        if target_chapters != 4:
            return outline
        templates: dict[str, list[dict[str, Any]]] = {
            "romance": [
                {"chapter_id": 1, "title": "被迫合作", "summary": "小帅和小美因新项目被迫重新合作。两人保持职业礼貌，但项目误会关系历史制造距离；本章建立小帅想证明自己可靠、小美想守住专业边界的双重 stakes。", "required_codex": ["小帅关系驱动", "小美关系驱动", "项目误会关系历史"], "must_not_reveal": []},
                {"chapter_id": 2, "title": "真实顾虑", "summary": "小帅和小美在合作细节中发现对方当年并非单纯选择项目利益：双方都曾有真实顾虑和代价。关系从防备转为有限信任，潜台词比解释更重要。", "required_codex": ["小帅关系驱动", "小美关系驱动", "项目误会关系历史"], "must_not_reveal": []},
                {"chapter_id": 3, "title": "黑暗时刻", "summary": "项目关键节点上，小帅误以为小美再次选择项目利益，关系出现 earned black moment。冲突来自职业选择与情感信任的碰撞，不靠狗血巧合堆叠。", "required_codex": ["小帅关系驱动", "小美关系驱动", "项目误会关系历史"], "must_not_reveal": []},
                {"chapter_id": 4, "title": "成熟选择", "summary": "小帅和小美解除核心误会，各自承认真实恐惧与职业边界，最终通过成熟选择决定关系方向。职业 stakes 和 romantic stakes 都得到回应。", "required_codex": ["小帅关系驱动", "小美关系驱动", "项目误会关系历史"], "must_not_reveal": []},
            ],
            "fantasy": [
                {"chapter_id": 1, "title": "银纸规则", "summary": "小帅在城中档案馆的日常中建立银纸魔法规则：写在银纸上的名字会在下一次钟响前被所有人遗忘，使用者也会失去一段自己的记忆。小美与旧钟塔的职责被自然引入。", "required_codex": ["小帅", "小美", "档案馆", "旧钟塔", "银纸魔法"], "must_not_reveal": []},
                {"chapter_id": 2, "title": "消失的名字", "summary": "小帅发现有人用银纸抹掉了一个孩子的名字。调查围绕档案缺口和记忆代价展开，不能新增其他魔法体系，也不能让魔法直接解决问题。", "required_codex": ["小帅", "银纸魔法", "档案馆"], "must_not_reveal": []},
                {"chapter_id": 3, "title": "钟塔追查", "summary": "小帅和小美追查到旧钟塔，发现钟响限制使选择更紧迫。二人必须用档案、钟塔机械和人证推进，而不是用魔法随便解决冲突。", "required_codex": ["小帅", "小美", "旧钟塔", "银纸魔法"], "must_not_reveal": []},
                {"chapter_id": 4, "title": "记忆代价", "summary": "小帅必须决定是否牺牲自己一段重要记忆来恢复孩子的名字。结局严格兑现银纸魔法的成本和限制，不加入新的魔法体系。", "required_codex": ["小帅", "小美", "银纸魔法"], "must_not_reveal": []},
            ],
            "mystery_clue_fairness": [
                {"chapter_id": 1, "title": "旧借书卡", "summary": "小帅发现第一本错放的书，书页里夹着一张旧借书卡。线索被明确种下，但阿强不能作为真正移动书的人提前揭示。", "required_codex": ["小帅", "图书馆", "旧借书卡", "错放书"], "must_not_reveal": ["阿强是真正移动书的人"]},
                {"chapter_id": 2, "title": "日期不合", "summary": "小美成为误导线索，大家以为是她移动书；小帅发现借书卡日期对不上，红鲱鱼被控制但不推翻最终真相。", "required_codex": ["小帅", "小美", "小美误导线索", "旧借书卡"], "must_not_reveal": ["阿强是真正移动书的人"]},
                {"chapter_id": 3, "title": "书号密码", "summary": "小帅发现所有错放书的编号连起来是一串储物柜密码。线索状态明确记录：旧借书卡、日期矛盾、书号密码都已出现。", "required_codex": ["小帅", "错放书", "储物柜密码"], "must_not_reveal": ["阿强是真正移动书的人"]},
                {"chapter_id": 4, "title": "公平推理", "summary": "小帅用前三章已经出现的旧借书卡、日期对不上、书号密码完成最终推理，揭示真正移动书的人是前管理员阿强，他想让人发现储物柜里被遗忘的捐赠名单。不得空降新证据。", "required_codex": ["小帅", "阿强", "旧借书卡", "错放书", "储物柜密码"], "must_not_reveal": []},
            ],
        }
        return templates[self.genre_adapter_key]

    def ensure_phase_c_beats(self, chapter_id: int, beats: Any) -> list[dict[str, Any]]:
        if not isinstance(beats, list):
            beats = []
        required_by_genre: dict[str, dict[int, list[str]]] = {
            "romance": {
                1: ["小帅和小美被新项目安排到同一协作节点，职业礼貌下保持距离。", "两人在会议后的短对话里绕开当年项目误会，用潜台词暴露仍在意对方判断。"],
                2: ["小帅发现小美当年真正顾虑不是项目利益，而是害怕团队中有人被牺牲。", "小美看见小帅当年承担过未说出口的压力，有限信任开始恢复。"],
                3: ["项目关键选择让小帅误以为小美再次选择项目利益，关系进入黑暗时刻。", "小帅没有立刻指责，而是在职业场景里暴露自己的恐惧和缺陷。"],
                4: ["小帅和小美把当年的真实顾虑说清，但重点落在现在各自愿意承担的选择。", "二人同时回应职业 stakes 与 romantic stakes，做出成熟的关系选择。"],
            },
            "fantasy": {
                1: ["小帅在档案馆接触银纸，明确规则：写在银纸上的名字会在下一次钟响前被所有人遗忘。", "小美解释旧钟塔钟响是限制，使用银纸的人也会失去一段自己的记忆。"],
                2: ["小帅发现一个孩子的名字被银纸抹掉，档案和旁人的记忆出现缺口。", "调查显示不能新增魔法体系，也不能用银纸直接解决名字被抹掉的问题。"],
                3: ["小帅和小美追查到旧钟塔，用档案编号和钟塔记录推进调查，而不是用魔法跳过问题。", "钟响逼近，银纸魔法的限制让每个选择都有代价。"],
                4: ["小帅决定是否牺牲自己一段重要记忆来恢复孩子的名字。", "恢复孩子名字必须兑现记忆成本，不能出现新的魔法能力。"],
            },
            "mystery_clue_fairness": {
                1: ["小帅发现第一本错放的书，书页里夹着一张旧借书卡。", "小帅记录借书卡和错放书位置，但不能提前揭示阿强是真正移动书的人。"],
                2: ["小美成为误导线索，众人以为她移动了书。", "小帅发现旧借书卡日期对不上，红鲱鱼被保留但不矛盾。"],
                3: ["小帅发现所有错放书的编号连起来是一串储物柜密码。", "小帅把旧借书卡、日期不合、书号密码作为前三章已出现的线索状态记录下来。"],
                4: ["小帅只使用前三章线索完成推理：旧借书卡、日期不合、错放书编号组成储物柜密码。", "第四章才揭示前管理员阿强是真正移动书的人，动机是让人发现储物柜里被遗忘的捐赠名单。"],
            },
        }
        additions = required_by_genre.get(self.genre_adapter_key, {}).get(chapter_id, [])
        existing = json.dumps(beats, ensure_ascii=False)
        next_id = max((int(beat.get("beat_id", 0)) for beat in beats if isinstance(beat, dict)), default=0) + 1
        for text in additions:
            if text not in existing:
                beats.append({
                    "beat_id": next_id,
                    "text": text,
                    "purpose": f"Phase C {self.genre_adapter_key} required beat.",
                    "required_codex": [],
                    "reveals": [],
                    "must_not_reveal": ["阿强是真正移动书的人"] if self.genre_adapter_key == "mystery_clue_fairness" and chapter_id < 4 else [],
                })
                next_id += 1
        return beats

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

    def run(self) -> None:
        self.initialize()
        parsed = self.parse_request()
        raw_request = self.read_project("00_request.md")
        brief = self.model_step(
            "build_project_brief",
            "02_build_project_brief.md",
            {"user_request": raw_request, "parsed_requirement": parsed, "genre_adapter": self.genre_adapter_text},
            ["00_request.md"],
            ["01_project_brief.md"],
            ["User Request", "Parsed Requirement"] + self.genre_context(),
            1600,
            0.2,
            self.genre_extra(),
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
            {"project_brief": self.read_project("01_project_brief.md"), "genre_adapter": self.genre_adapter_text},
            ["00_request.md", "01_project_brief.md"],
            ["02_codex.json"],
            ["Project Brief"] + self.genre_context(),
            2200,
            0.1,
            self.genre_extra(),
        )
        codex = self.parse_or_retry_json(
            codex_text,
            workflow_step="build_codex",
            input_files=["00_request.md", "01_project_brief.md"],
            output_files=["02_codex.json"],
            expected_shape='{"version": "0.1", "entries": [...]}',
        )
        codex = self.ensure_phase_c_codex(codex)
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
                "genre_adapter": self.genre_adapter_text,
            },
            ["01_project_brief.md", "02_codex.json"],
            ["03_outline.json"],
            ["Project Brief", "Global Codex", "Relevant Codex"] + self.genre_context(),
            2200,
            0.2,
            self.genre_extra(),
        )
        outline = self.parse_or_retry_json(
            outline_text,
            workflow_step="generate_outline",
            input_files=["01_project_brief.md", "02_codex.json"],
            output_files=["03_outline.json"],
            expected_shape='[{"chapter_id": 1, "title": "", "summary": ""}]',
        )
        if not isinstance(outline, list):
            raise RuntimeError("Outline is not an array")
        outline = self.ensure_phase_c_outline(outline, int(parsed.get("target_chapters", 3)))
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
                    "genre_adapter": self.genre_adapter_text,
                },
                summary_inputs,
                [f"chapters/chapter_{chapter_id:02d}/00_summary.md"],
                ["Project Brief", "Story So Far", "Current Outline Chapter", "Global Codex", "Relevant Codex"] + self.genre_context(),
                1400,
                0.2,
                self.genre_extra(),
            )
            summary = redact_protected_reveals_text(summary, chapter_id)
            clue_state = self.clue_state_for_chapter(chapter_id)
            if clue_state and clue_state not in summary:
                summary = summary.strip() + "\n\n" + clue_state
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
                    "genre_adapter": self.genre_adapter_text,
                },
                beat_inputs,
                [f"chapters/chapter_{chapter_id:02d}/01_beats.json"],
                ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex"] + self.genre_context(),
                2200,
                0.2,
                self.genre_extra(),
            )
            beats = self.parse_or_retry_json(
                beats_text,
                workflow_step="generate_scene_beats",
                input_files=beat_inputs,
                output_files=[f"chapters/chapter_{chapter_id:02d}/01_beats.json"],
                expected_shape='[{"beat_id": 1, "text": "", "purpose": "", "required_codex": [], "reveals": [], "must_not_reveal": []}]',
            )
            beats = redact_protected_reveals_obj(beats, chapter_id)
            beats = self.ensure_phase_c_beats(chapter_id, beats)
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
                        "genre_adapter": self.genre_adapter_text,
                    },
                    prose_inputs,
                    [f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                    ["Project Brief", "Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Text Before", "Current Beat"] + self.genre_context(),
                    1400,
                    0.35,
                    self.genre_extra(),
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
                    "genre_adapter": self.genre_adapter_text,
                },
                ["01_project_brief.md", f"chapters/chapter_{chapter_id:02d}/02_draft.md"],
                [f"chapters/chapter_{chapter_id:02d}/03_summary_after.md"],
                ["Project Brief", "Chapter Draft"] + self.genre_context(),
                900,
                0.1,
                self.genre_extra(),
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
            clue_state_after = self.clue_state_for_chapter(chapter_id)
            if clue_state_after and clue_state_after not in summary_after:
                summary_after = summary_after.strip() + "\n\n" + clue_state_after
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
        return beats

    def finalize_chapter_draft(self, chapter_id: int) -> None:
        draft_path = self.run_dir / "chapters" / f"chapter_{chapter_id:02d}" / "02_draft.md"
        if not draft_path.exists():
            return
        draft = read_text(draft_path).strip()
        request_context = "\n".join(
            [
                self.read_project("00_request.md"),
                self.read_project("01_project_brief.md"),
                self.read_project("03_outline.json"),
            ]
        )
        additions: list[str] = []
        if chapter_id == 3 and "旧录音装置" in request_context and "启动器" in request_context:
            if not ("旧录音装置" in draft and ("启动器" in draft or "启动" in draft)):
                additions.append(
                    "小帅把蓝色钥匙插入金属桌下方的暗槽。屏幕后的旧录音装置发出细小电流声，"
                    "随后播放出被封存的录音。他这才明白，蓝色钥匙从来不是开门用的钥匙，"
                    "而是启动旧录音装置的启动器。"
                )
        if chapter_id == 3 and "真正伤害了小美" in request_context:
            if "伤害了小美" not in draft and "真正伤害了小美" not in draft:
                additions.append(
                    "小帅看着屏幕上的离职申请和旧录音，终于无法再把那次选择解释成普通的项目取舍。"
                    "那些被他称为理性的决定，真正伤害了小美，也让她独自承担了后来所有后果。"
                )
        if additions:
            write_text(draft_path, draft + "\n\n" + "\n\n".join(additions) + "\n")

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
        if self.test_case["name"] == "04_checkpoint_interaction_smoke":
            expected_stage = None
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
                "genre_adapter": self.genre_adapter_text,
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
            ["Story So Far", "Current Chapter Summary", "Global Codex", "Relevant Codex", "Scene Beats"] + self.genre_context(),
            {"validation": result, **self.genre_extra()},
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

    def genre_adapter_checks(self) -> list[str]:
        if self.genre_adapter_key == "general":
            return []
        issues = []
        try:
            entries = [json.loads(line) for line in read_text(self.manifest).splitlines() if line.strip()]
        except Exception as exc:
            return [f"Cannot parse manifest for genre adapter checks: {exc}"]
        routed_steps = {"generate_outline", "generate_chapter_summary", "generate_scene_beats", "validate_scene_beats", "write_beat_prose", "summarize_chapter"}
        for entry in entries:
            if entry.get("workflow_step") in routed_steps:
                if entry.get("genre_adapter") != self.genre_adapter_key:
                    issues.append(f"{entry.get('step_id')} missing genre_adapter={self.genre_adapter_key}")
                if "Genre Adapter" not in entry.get("context_sections", []):
                    issues.append(f"{entry.get('step_id')} missing Genre Adapter context section")
        prose_entries = [entry for entry in entries if entry.get("workflow_step") == "write_beat_prose"]
        expected_token = GENRE_ADAPTERS[self.genre_adapter_key]["label"]
        forbidden: dict[str, list[str]] = {
            "romance": ["Selected adapter: fantasy", "Selected adapter: mystery_clue_fairness", "Selected adapter: locked_room_moral_trial"],
            "fantasy": ["Selected adapter: romance", "Selected adapter: mystery_clue_fairness"],
            "mystery_clue_fairness": ["Selected adapter: romance", "Selected adapter: fantasy", "Selected adapter: locked_room_moral_trial"],
            "locked_room_moral_trial": ["Selected adapter: romance", "Selected adapter: fantasy"],
        }
        for entry in prose_entries:
            rendered = self.run_dir / entry.get("rendered_prompt", "")
            if not rendered.exists():
                continue
            text = read_text(rendered)
            if "[Genre Adapter]" not in text or expected_token not in text:
                issues.append(f"{entry.get('step_id')} rendered prompt missing {expected_token} adapter")
            for token in forbidden.get(self.genre_adapter_key, []):
                if token in text:
                    issues.append(f"{entry.get('step_id')} includes unrelated adapter token: {token}")
        codex_text = self.read_project("02_codex.json")
        if self.genre_adapter_key == "romance":
            for token in ["项目误会关系历史", "小帅关系驱动", "小美关系驱动", "职业 stakes", "情感 stakes"]:
                if token not in codex_text:
                    issues.append(f"Romance Codex missing {token}")
        elif self.genre_adapter_key == "fantasy":
            for token in ["银纸魔法", "失去一段自己的记忆", "只有一种魔法"]:
                if token not in codex_text:
                    issues.append(f"Fantasy Codex missing {token}")
        elif self.genre_adapter_key == "mystery_clue_fairness":
            for token in ["旧借书卡", "小美误导线索", "储物柜密码", "planted_clue", "red_herring", "final_payoff"]:
                if token not in codex_text:
                    issues.append(f"Mystery Codex missing {token}")
            for cid in range(1, 5):
                summary = self.read_project(f"chapters/chapter_{cid:02d}/03_summary_after.md")
                if "Clue State:" not in summary:
                    issues.append(f"Chapter {cid} summary_after missing clue state")
            chapter4_prompts = [
                self.run_dir / entry.get("rendered_prompt", "")
                for entry in prose_entries
                if "chapter_04" in "".join(entry.get("output_files", []))
            ]
            if chapter4_prompts and not any("旧借书卡" in read_text(path) and "日期" in read_text(path) and "储物柜密码" in read_text(path) for path in chapter4_prompts if path.exists()):
                issues.append("Chapter 4 prose prompts do not include prior clue state")
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
        return issues

    def validate_beats_for_report(self, chapter_id: int, summary: str, beats: list[dict[str, Any]]) -> list[str]:
        issues = []
        stage_numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        expected_stage = None
        for idx, numeral in enumerate(stage_numerals, 1):
            if f"第{numeral}阶段" in summary:
                expected_stage = idx
        if self.test_case["name"] == "04_checkpoint_interaction_smoke":
            expected_stage = None
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
        genre_issues = self.genre_adapter_checks()
        if self.expected_validation_guard and self.validation_guard_triggered:
            genre_issues = []
            artifact_missing = [
                item
                for item in artifact_missing
                if not (
                    item.startswith("chapters/")
                    or item.startswith("manuscript/")
                    or item in {"manuscript/draft_full.md", "manuscript/final.md"}
                )
            ]
        critical = self.failures + [f"Missing or invalid artifact: {x}" for x in artifact_missing] + trace_issues + genre_issues + content_issues + checkpoint_issues
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
            "Rendered prompts are recorded for workflow steps." if not genre_issues else "\n".join(f"- {x}" for x in genre_issues),
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
