# Clean Generation Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove testcase-specific output mutation from the `longform-writing` generation path while keeping read-only acceptance checks available.

**Architecture:** Keep the existing runner structure for this pass. Make `AcceptanceRun.run()` produce Codex, outline, beats, chapter drafts, summaries, and manuscripts only from user request, prompts, model output, feedback, and generic sanitization. Leave acceptance checks in place as readers of generated artifacts, but do not let them write or patch story content.

**Tech Stack:** Python stdlib runner, existing Markdown prompt templates, existing `unittest` tests.

---

### Task 1: Remove Fixed Reveal Redaction From Generation

**Files:**
- Modify: `/Users/yuhuang/vibe-coding/longform_writing/longform-writing/scripts/run_acceptance.py`
- Test: `python3 -m py_compile longform-writing/scripts/run_acceptance.py`

- [x] **Step 1: Replace testcase-specific redaction helpers with generic pass-through helpers**

```python
def redact_protected_reveals_text(text: str, chapter_id: int) -> str:
    return text


def redact_protected_reveals_obj(value: Any, chapter_id: int) -> Any:
    return value
```

- [x] **Step 2: Keep call sites unchanged for compatibility**

The final implementation removed the helpers and call sites entirely, because keeping no-op redaction hooks made the generation path harder to audit.

- [x] **Step 3: Compile**

Run:

```bash
python3 -m py_compile longform-writing/scripts/run_acceptance.py
```

Expected: command exits `0`.

### Task 2: Remove Generation-Time Testcase Patches

**Files:**
- Modify: `/Users/yuhuang/vibe-coding/longform_writing/longform-writing/scripts/run_acceptance.py`
- Test: `python3 -m py_compile longform-writing/scripts/run_acceptance.py`

- [x] **Step 1: Make output patch helpers no-op or remove their calls**

Use pass-through implementations for:

```python
def ensure_phase_c_codex(self, codex: dict[str, Any]) -> dict[str, Any]:
    return codex if isinstance(codex, dict) else {"version": "0.1", "entries": []}

def ensure_phase_c_outline(self, outline: Any, target_chapters: int) -> list[dict[str, Any]]:
    return outline if isinstance(outline, list) else []

def ensure_phase_c_beats(self, chapter_id: int, beats: Any) -> list[dict[str, Any]]:
    return beats if isinstance(beats, list) else []

def clue_state_for_chapter(self, chapter_id: int) -> str:
    return ""

def finalize_chapter_draft(self, chapter_id: int) -> None:
    return None

def normalize_summary_after(self, chapter_id: int, summary_after: str) -> str:
    return summary_after

def ensure_required_reveal_beats(self, chapter_id: int, chapter: dict[str, Any], beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return beats
```

- [x] **Step 2: Keep acceptance-only checks intact**

Do not remove `phase_b_trace_checks`, `phase_b_content_checks`, `content_checks`, or report writing in this pass. They are allowed to fail after cleanup because they only read generated outputs.

- [x] **Step 3: Compile**

Run:

```bash
python3 -m py_compile longform-writing/scripts/run_acceptance.py
```

Expected: command exits `0`.

### Task 3: Generalize Request Fallback And Codex Selection

**Files:**
- Modify: `/Users/yuhuang/vibe-coding/longform_writing/longform-writing/scripts/run_acceptance.py`
- Test: `python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'`

- [x] **Step 1: Replace concrete fallback parse fields**

Use this fallback when parse JSON fails:

```python
parsed = {
    "version": "0.1",
    "language": "zh",
    "genre": None,
    "target_chapters": 3,
    "target_length": "short_draft",
    "protagonist": None,
    "key_supporting_characters": [],
    "premise": raw,
    "setting": None,
    "tone": [],
    "pov": "third_person_limited",
    "style_constraints": [],
    "prohibited_elements": [],
    "must_include": [],
    "must_not_reveal_early": [],
    "final_reveal": None,
    "automation_mode": self.mode,
}
```

- [x] **Step 2: Remove testcase-name Codex routing override**

Delete the special branch that always includes `小美 / 阿强 / 老周 / 林姐` for `06_supporting_cast_codex_routing`. Generic routing should only use global entries, required Codex ids/names, aliases, and text matches.

- [x] **Step 3: Run helper tests**

Run:

```bash
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected: existing helper tests pass. These tests may contain sample story strings, but should not require generation-time patching.

### Task 4: Verify No Remaining Generation-Path Case Patches

**Files:**
- Modify only if grep exposes another generation-time mutation in `/Users/yuhuang/vibe-coding/longform_writing/longform-writing/scripts/run_acceptance.py`
- Test: grep checks below

- [x] **Step 1: Search high-risk generation helpers**

Run:

```bash
rg -n "ensure_phase_c|finalize_chapter_draft|normalize_summary_after|ensure_required_reveal_beats|redact_protected_reveals|clue_state_for_chapter|self\\.test_case\\[\"name\"\\]" longform-writing/scripts/run_acceptance.py
```

Expected: remaining `self.test_case["name"]` references are limited to validation guard handling and read-only acceptance/report checks, not writing Codex, outline, beats, drafts, or summaries.

- [x] **Step 2: Search fixed story content in the runner**

Run:

```bash
rg -n "小帅|小美|阿强|老周|林姐|旧录音装置|蓝色钥匙|缺失封面|旧借书卡|高风险，不建议上线" longform-writing/scripts/run_acceptance.py
```

Expected: matches may remain in read-only checks, test validation fixtures, or prompt-trace assertions, but not in generation-time patch functions.

- [x] **Step 3: Final verification**

Run:

```bash
python3 -m py_compile longform-writing/scripts/run_acceptance.py longform-writing/scripts/run_v1_revision_loop.py
python3 -m unittest discover -s longform-writing/tests -p 'test_v1_*.py'
```

Expected: commands exit `0`. Old full acceptance content checks may fail if run separately; that is an accepted consequence of this cleanup.

---

## Self-Review

- Spec coverage: The plan removes generation-time testcase patches, keeps read-only evaluation logic, generalizes parse fallback, and explicitly handles fixed-string reveal redaction.
- Placeholder scan: No placeholders remain.
- Type consistency: Pass-through helper signatures match existing call sites.
