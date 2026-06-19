"""轻量级 Skill 支持：只服务 ReAct Excel/CSV 数据分析场景。"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core import config

DATA_ANALYSIS_KEYWORDS = {
    "csv",
    "excel",
    "xlsx",
    "xls",
    "spreadsheet",
    "data analysis",
    "data visualization",
    "数据分析",
    "数据可视化",
    "分析excel",
    "分析csv",
    "销售",
    "walmart",
}


@dataclass
class SkillInfo:
    name: str
    description: str
    root_dir: str
    instructions: str
    tags: List[str]


def _parse_skill_md(path: Path) -> Optional[SkillInfo]:
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception:
        return None

    frontmatter: Dict[str, Any] = {}
    body = raw
    if raw.strip().startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            meta_text = parts[1]
            body = parts[2].strip()
            for line in meta_text.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                value = value.strip().strip('"').strip("'")
                frontmatter[key.strip()] = value

    name = str(frontmatter.get("name") or path.parent.name)
    description = str(frontmatter.get("description") or "")
    tags_raw = frontmatter.get("tags") or ""
    tags = [item.strip() for item in re.split(r"[,;]", str(tags_raw)) if item.strip()]
    return SkillInfo(
        name=name,
        description=description,
        root_dir=str(path.parent),
        instructions=body,
        tags=tags,
    )


def _is_data_analysis_skill(skill: SkillInfo) -> bool:
    text = " ".join([skill.name, skill.description, " ".join(skill.tags)]).lower()
    return any(keyword.lower() in text for keyword in DATA_ANALYSIS_KEYWORDS)


def load_data_analysis_skills() -> List[SkillInfo]:
    skills_dir = Path(config.SKILLS_DIR)
    if not skills_dir.exists():
        return []
    skills: List[SkillInfo] = []
    for skill_md in skills_dir.glob("*/SKILL.md"):
        skill = _parse_skill_md(skill_md)
        if skill and _is_data_analysis_skill(skill):
            skills.append(skill)
    return sorted(skills, key=lambda item: item.name)


def get_skill(skill_name: str) -> Optional[SkillInfo]:
    target = (skill_name or "").lower()
    for skill in load_data_analysis_skills():
        if skill.name.lower() == target:
            return skill
    return None


def match_skill(query: str, has_file: bool = False) -> Optional[SkillInfo]:
    skills = load_data_analysis_skills()
    lowered = (query or "").lower()
    if has_file and any(skill.name == "csv-data-analysis" for skill in skills):
        if not any(token in lowered for token in ["walmart", "沃尔玛"]):
            return get_skill("csv-data-analysis")
    best_score = 0
    best: Optional[SkillInfo] = None
    for skill in skills:
        haystack = " ".join([skill.name, skill.description, " ".join(skill.tags)]).lower()
        score = 0
        for token in re.findall(r"[\w\u4e00-\u9fff]+", lowered):
            if len(token) > 1 and token in haystack:
                score += 1
        if skill.name in lowered:
            score += 5
        if score > best_score:
            best_score = score
            best = skill
    return best if best_score > 0 else None


def get_skills_context() -> str:
    skills = load_data_analysis_skills()
    if not skills:
        return "No data-analysis skills available."
    return "\n".join(f"- {skill.name}: {skill.description}" for skill in skills)


def load_skill_content(skill_name: str) -> str:
    skill = get_skill(skill_name)
    if not skill:
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": f"Skill '{skill_name}' not found"}]},
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "chunks": [
                {"output_type": "text", "content": f"Skill: {skill.name}"},
                {"output_type": "markdown", "content": skill.instructions},
            ]
        },
        ensure_ascii=False,
    )


def read_skill_resource(skill_name: str, resource_path: str, args: Optional[dict] = None) -> str:
    skill = get_skill(skill_name)
    if not skill:
        return json.dumps({"error": True, "message": f"Skill '{skill_name}' not found"}, ensure_ascii=False)
    target = (Path(skill.root_dir) / resource_path).resolve()
    root = Path(skill.root_dir).resolve()
    try:
        target.relative_to(root)
    except Exception:
        return json.dumps({"error": True, "message": "Invalid resource path"}, ensure_ascii=False)
    if not target.is_file():
        return json.dumps({"error": True, "message": f"Resource not found: {resource_path}"}, ensure_ascii=False)
    return target.read_text(encoding="utf-8")


def _copy_generated_images(output_dir: Path) -> List[Dict[str, str]]:
    static_dir = Path(__file__).resolve().parents[3] / "storage" / "static" / "images"
    static_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    for img in output_dir.rglob("*"):
        if img.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            continue
        dest = static_dir / f"{img.stem}_{os.urandom(4).hex()}{img.suffix}"
        dest.write_bytes(img.read_bytes())
        chunks.append({"output_type": "image", "content": f"/images/{dest.name}"})
    return chunks


def execute_skill_script_file(skill_name: str, script_file_name: str, args: Optional[dict], conv_id: str) -> str:
    skill = get_skill(skill_name)
    if not skill:
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": f"Skill '{skill_name}' not found"}]},
            ensure_ascii=False,
        )
    script_path = (Path(skill.root_dir) / "scripts" / script_file_name).resolve()
    root = Path(skill.root_dir).resolve()
    try:
        script_path.relative_to(root)
    except Exception:
        return json.dumps({"chunks": [{"output_type": "text", "content": "Invalid script path"}]}, ensure_ascii=False)
    if not script_path.is_file():
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": f"Script not found: {script_file_name}"}]},
            ensure_ascii=False,
        )

    work_dir = Path(config.UPLOAD_DIR).resolve().parent / "tmp" / conv_id
    work_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(args or {})
    payload.setdefault("output_dir", str(work_dir))
    env = os.environ.copy()
    env["OUTPUT_DIR"] = str(work_dir)
    proc = subprocess.run(
        [sys.executable, str(script_path), json.dumps(payload, ensure_ascii=False)],
        cwd=str(script_path.parent),
        env=env,
        capture_output=True,
        text=True,
        timeout=config.SANDBOX_TIMEOUT,
        encoding="utf-8",
        errors="replace",
    )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    parsed: Dict[str, Any]
    try:
        parsed = json.loads(stdout) if stdout else {"chunks": []}
    except Exception:
        parsed = {"chunks": [{"output_type": "text", "content": stdout}]}
    chunks = parsed.get("chunks") if isinstance(parsed.get("chunks"), list) else []
    normalized_chunks: List[Dict[str, Any]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        content = chunk.get("content")
        if chunk.get("output_type") == "image" and isinstance(content, str) and os.path.isabs(content):
            img_path = Path(content)
            if img_path.exists():
                normalized_chunks.extend(_copy_generated_images(img_path.parent))
                continue
        normalized_chunks.append(chunk)
    if stderr:
        normalized_chunks.append({"output_type": "text", "content": stderr[:2000]})
    if proc.returncode != 0:
        normalized_chunks.append({"output_type": "text", "content": f"Script exited with code {proc.returncode}"})
    parsed["chunks"] = normalized_chunks
    return json.dumps(parsed, ensure_ascii=False)
