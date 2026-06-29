"""ReAct 工具集 — 1:1 复刻原版 agentic_data_api.py 中的工具实现

核心差异 vs 旧版:
- code_interpreter: 前奏注入(json/os/pandas/numpy/PLOT_DIR/FILE_PATH) + 子进程执行 + 图片捕获 + chunks 格式
- execute_analysis: 返回 chunks 格式（code + json + table + chart）
- html_interpreter: 3种模式(inline html / file_path / template_path) + 图片URL修正
- todowrite: 返回 __todos__ 字段供 SSE 管线推送 plan.update
- terminate: 标准终止工具
- load_file: 返回 chunks 格式
- select_skill: 根据用户查询匹配最相关的 skill
- load_skill: 加载 skill 内容（SKILL.md）
- get_skill_resource: 读取 skill 中的参考文档等资源
- execute_skill_script: 执行 skill 内联脚本
- execute_skill_script_file: 执行 skill scripts 目录下的脚本文件
- 所有工具统一返回 JSON 字符串，格式: {"chunks": [{"output_type": "...", "content": "..."}]}
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any, Dict, List, Optional

from app.core import config
from app.core.logger import get_session_logger
from app.services.react_agent.skills import (
    get_skill,
    get_skills_context,
    load_data_analysis_skills,
    load_skill_content,
    match_skill,
    read_skill_resource,
    execute_skill_script_file as _execute_skill_script_file_impl,
)

logger = logging.getLogger(__name__)

# ── 图片扩展名 ────────────────────────────────────────────
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

# ── 静态图片目录 ──────────────────────────────────────────
STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'storage', 'static', 'images')


def _ensure_static_img_dir() -> str:
    """确保静态图片目录存在，返回路径"""
    os.makedirs(STATIC_IMG_DIR, exist_ok=True)
    return STATIC_IMG_DIR


def _try_repair_truncated_code(code: str) -> Optional[str]:
    """尝试修复被截断的代码（LLM 输出超长时常见）

    复刻自原版 agentic_data_api.py 中的 _try_repair_truncated_code
    """
    if not code or not code.strip():
        return None
    repaired = code.rstrip()
    # 尝试补全未闭合的括号
    open_parens = repaired.count("(") - repaired.count(")")
    open_brackets = repaired.count("[") - repaired.count("]")
    open_braces = repaired.count("{") - repaired.count("}")
    if open_parens > 0 or open_brackets > 0 or open_braces > 0:
        repaired += ")" * max(0, open_parens)
        repaired += "]" * max(0, open_brackets)
        repaired += "}" * max(0, open_braces)
    # 尝试补全未闭合的字符串
    if repaired.count('"""') % 2 != 0:
        repaired += '"""'
    elif repaired.count("'''") % 2 != 0:
        repaired += "'''"
    elif repaired.count('"') % 2 != 0:
        repaired += '"'
    elif repaired.count("'") % 2 != 0:
        repaired += "'"
    try:
        compile(repaired, "<repair>", "exec")
        return repaired
    except SyntaxError:
        return None


# ══════════════════════════════════════════════════════════
# 工具实现
# ══════════════════════════════════════════════════════════

async def tool_execute_analysis(file_path: str, conv_id: str = "default") -> str:
    """执行初始统计分析 — 1:1 复刻原版 execute_analysis

    返回数据概况: shape/columns/dtypes/head5
    """
    if not file_path or not os.path.exists(file_path):
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": f"Error: File not found: {file_path}"}]},
            ensure_ascii=False,
        )

    analysis_code = f"""
import json
import pandas as pd

file_path = r"{file_path}"
if file_path.lower().endswith((".xls", ".xlsx")):
    df = pd.read_excel(file_path)
else:
    df = pd.read_csv(file_path)
summary = {{
    "shape": list(df.shape),
    "columns": list(df.columns),
    "dtypes": {{col: str(dtype) for col, dtype in df.dtypes.items()}},
    "head": df.head(5).to_dict(orient="records"),
}}
print(json.dumps(summary, ensure_ascii=False, default=str))
"""
    # 使用 code_interpreter 的子进程方式执行
    result = await _run_code_subprocess(analysis_code, conv_id)

    chunks: List[Dict[str, Any]] = [
        {"output_type": "code", "content": analysis_code.strip()},
    ]

    output_text = result.get("stdout", "")
    if output_text.strip():
        try:
            summary = json.loads(output_text.strip())
            chunks.append({"output_type": "json", "content": summary})
            head_rows = summary.get("head")
            columns = summary.get("columns")
            if isinstance(head_rows, list) and isinstance(columns, list):
                chunks.append(
                    {
                        "output_type": "table",
                        "content": {
                            "columns": [
                                {"title": col, "dataIndex": col, "key": col}
                                for col in columns
                            ],
                            "rows": head_rows,
                        },
                    }
                )
            numeric_columns = [
                col
                for col, dtype in (summary.get("dtypes") or {}).items()
                if "int" in dtype or "float" in dtype
            ]
            if numeric_columns and isinstance(head_rows, list):
                series_col = numeric_columns[0]
                data = [
                    {"x": idx + 1, "y": row.get(series_col)}
                    for idx, row in enumerate(head_rows)
                    if row.get(series_col) is not None
                ]
                if data:
                    chunks.append(
                        {
                            "output_type": "chart",
                            "content": {
                                "data": data,
                                "xField": "x",
                                "yField": "y",
                            },
                        }
                    )
        except Exception:
            chunks.append({"output_type": "text", "content": output_text.strip()})
    else:
        error_text = result.get("stderr", "")
        if error_text:
            chunks.append({"output_type": "text", "content": f"Error:\n{error_text}"})
        else:
            chunks.append({"output_type": "text", "content": "(no output)"})

    return json.dumps({"chunks": chunks}, ensure_ascii=False)


async def tool_code_interpreter(code: str, file_path: str = "", conv_id: str = "default") -> str:
    """执行 Python 代码 — 1:1 复刻原版 code_interpreter

    核心逻辑:
    1. 前奏注入: import json, os, pandas, numpy; PLOT_DIR; FILE_PATH
    2. 语法检查 + 自动修复截断代码
    3. 子进程执行 (cwd=会话工作目录)
    4. 输出截断 (2000字符)
    5. 图片捕获 (扫描工作目录新图片 → 拷贝到静态目录)
    6. 返回 chunks 格式
    """
    t_logger = get_session_logger(conv_id, "react_agent")
    t_logger.info("【code_interpreter】执行代码: conv_id=%s, 代码长度=%d, file_path=%s",
                  conv_id, len(code or ""), file_path)
    t_logger.debug("【code_interpreter代码】\n%s", (code or "")[:1000])

    if not code or not code.strip():
        t_logger.warning("code_interpreter 未收到代码")
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": "No code provided"}]},
            ensure_ascii=False,
        )

    # 会话持久工作目录
    work_dir = os.path.join(config.UPLOAD_DIR, "..", "tmp", conv_id)
    work_dir = os.path.abspath(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    # 收集执行前已有的图片
    pre_existing_images: set = set()
    for root, _dirs, files in os.walk(work_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTS:
                pre_existing_images.add(os.path.join(root, f))

    # 前奏注入 — 1:1 复刻原版
    preamble_lines = [
        "import json",
        "import os",
        "import sys",
        "try:",
        "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')",
        "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')",
        "except Exception:",
        "    pass",
        "import pandas as pd",
        "import numpy as np",
        f'PLOT_DIR = r"{work_dir}"',
        "os.makedirs(PLOT_DIR, exist_ok=True)",
    ]
    if file_path:
        preamble_lines.append(f'FILE_PATH = r"{file_path}"')
    preamble = "\n".join(preamble_lines) + "\n"
    full_code = preamble + code

    # 语法检查 + 自动修复
    try:
        compile(full_code, "<code_interpreter>", "exec")
    except SyntaxError as se:
        repaired = _try_repair_truncated_code(full_code)
        if repaired is not None:
            logger.warning(f"code_interpreter: auto-repaired truncated code (SyntaxError: {se.msg} line {se.lineno})")
            full_code = repaired
            code = full_code[len(preamble):]
        else:
            error_msg = (
                f"SyntaxError before execution: {se.msg} (line {se.lineno})\n"
                "Please regenerate complete, syntactically valid Python code. "
                "Keep code under 80 lines and split long tasks into multiple code_interpreter calls."
            )
            return json.dumps(
                {"chunks": [
                    {"output_type": "code", "content": code.strip()},
                    {"output_type": "text", "content": error_msg},
                ]},
                ensure_ascii=False,
            )

    # 子进程执行
    result = await _run_code_subprocess(full_code, conv_id, cwd=work_dir)

    output_text = result.get("stdout", "")
    error_text = result.get("stderr", "")
    return_code = result.get("returncode", 0)
    t_logger.info("【code_interpreter结果】return_code=%d, stdout_len=%d, stderr_len=%d",
                  return_code, len(output_text or ""), len(error_text or ""))
    if error_text:
        t_logger.warning("【code_interpreter错误】\n%s", error_text[:1000])
    if return_code != 0 and error_text:
        output_text = (output_text + "\n[ERROR]\n" + error_text) if output_text else error_text

    # 构建输出 chunks
    chunks: List[Dict[str, Any]] = [
        {"output_type": "code", "content": code.strip()},
    ]

    if output_text.strip():
        clean_output = output_text.strip()
        max_out_len = 2000
        if len(clean_output) > max_out_len:
            truncation_notice = (
                f"\n\n... [Output truncated, length: {len(clean_output)} chars."
                f" Only showing first {max_out_len} chars."
                f" If you generated HTML, the file is saved.]"
            )
            clean_output = clean_output[:max_out_len] + truncation_notice
        chunks.append({"output_type": "text", "content": clean_output})
    else:
        chunks.append({"output_type": "text", "content": "(no output — add print() to see results)"})

    # 扫描工作目录中新生成的图片 → 拷贝到静态目录
    generated_images: List[str] = []
    try:
        static_dir = _ensure_static_img_dir()
        for root, _dirs, files in os.walk(work_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                full_path = os.path.join(root, fname)
                if ext in IMAGE_EXTS and full_path not in pre_existing_images:
                    unique_name = f"{uuid.uuid4().hex[:8]}_{fname}"
                    dest = os.path.join(static_dir, unique_name)
                    shutil.copy2(full_path, dest)
                    img_url = f"/images/{unique_name}"
                    chunks.append({"output_type": "image", "content": img_url})
                    generated_images.append(img_url)
    except Exception as e:
        logger.warning(f"code_interpreter: image capture failed: {e}")

    # 追加已生成图片的汇总提示，供 LLM 后续生成 HTML 时引用
    if generated_images:
        img_summary = "已生成的图片URL（在生成HTML时请使用这些URL）:\n" + "\n".join(
            f"  - {url}" for url in generated_images
        )
        chunks.append({"output_type": "text", "content": img_summary})

    return json.dumps({"chunks": chunks}, ensure_ascii=False)


async def tool_html_interpreter(
    html: str = "",
    title: str = "Report",
    file_path: str = "",
    template_path: str = "",
    data: Any = None,
    generated_images: List[str] = None,
) -> str:
    """渲染 HTML 报告 — 1:1 复刻原版 html_interpreter

    三种模式:
    1. template_path + data: 模板替换 (暂不实现，复刻项目无 skills)
    2. file_path: 从磁盘读取 HTML 文件
    3. html (默认): 直接使用 LLM 生成的 HTML 字符串
    """
    # Mode 2: file_path — 从文件读取
    if file_path and file_path.strip():
        fp = file_path.strip()
        if not os.path.isfile(fp):
            # 尝试在工作目录中查找
            return json.dumps(
                {"chunks": [{"output_type": "text", "content": f"File not found: {file_path}"}]},
                ensure_ascii=False,
            )
        try:
            with open(fp, "r", encoding="utf-8") as f:
                html = f.read()
            if not title or title == "Report":
                title = os.path.splitext(os.path.basename(fp))[0]
        except Exception as e:
            return json.dumps(
                {"chunks": [{"output_type": "text", "content": f"Error reading file: {e}"}]},
                ensure_ascii=False,
            )

    # Mode 3: inline html — 反转义 LLM 可能产生的 \n \t
    if html and isinstance(html, str) and not template_path and not file_path:
        if "\\n" in html:
            html = html.replace("\\n", "\n")
        if "\\t" in html:
            html = html.replace("\\t", "\t")

    if not html or not html.strip():
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": "No HTML content provided"}]},
            ensure_ascii=False,
        )

    # 修正图片 URL: LLM 可能猜测了错误的图片路径
    fixed_html = html.strip()
    try:
        static_dir = STATIC_IMG_DIR
        if os.path.isdir(static_dir):
            # 构建 文件名(无uuid前缀) -> 服务路径 的映射
            name_to_served: Dict[str, str] = {}
            for fname in os.listdir(static_dir):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in IMAGE_EXTS:
                    continue
                # 去掉 uuid8_ 前缀得到原始文件名
                parts = fname.split("_", 1)
                orig_name = parts[1] if len(parts) > 1 else fname
                name_to_served[orig_name.lower()] = f"/images/{fname}"
                name_to_served[fname.lower()] = f"/images/{fname}"

            # 替换 HTML 中的图片引用
            for orig_lower, served_url in name_to_served.items():
                # 替换 src="orig_name" 或 src="/images/orig_name" 等
                patterns = [
                    f'src="{orig_lower}"',
                    f"src='{orig_lower}'",
                    f'src="/images/{orig_lower}"',
                    f"src='/images/{orig_lower}'",
                ]
                for pat in patterns:
                    if pat.lower() in fixed_html.lower():
                        fixed_html = re.sub(
                            re.escape(pat),
                            f'src="{served_url}"',
                            fixed_html,
                            flags=re.IGNORECASE,
                        )
    except Exception as e:
        logger.warning(f"html_interpreter: image URL fix failed: {e}")

    return json.dumps(
        {"chunks": [{"output_type": "html", "content": fixed_html, "title": title or "Report"}]},
        ensure_ascii=False,
    )


async def tool_load_file(file_path: str = "") -> str:
    """读取上传文件信息 — 1:1 复刻原版 load_file"""
    if not file_path:
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": "No file uploaded"}]},
            ensure_ascii=False,
        )
    chunks = [
        {"output_type": "text", "content": file_path},
        {"output_type": "text", "content": "File path provided by user upload"},
    ]
    return json.dumps({"chunks": chunks}, ensure_ascii=False)


async def tool_todowrite(todos: Any, todo_list_ref: list) -> str:
    """更新任务列表 — 1:1 复刻原版 todowrite

    参数:
        todos: 字符串或列表格式的任务列表
        todo_list_ref: 外部可变列表引用，用于跨调用保持状态

    返回 JSON 含 __todos__ 字段，供 SSE 管线推送 plan.update
    """
    parsed: List[Dict[str, str]] = []
    try:
        raw = json.loads(todos) if isinstance(todos, str) else todos
        items = raw if isinstance(raw, list) else raw.get("todos", raw)
        if isinstance(items, list):
            for item in items:
                parsed.append(
                    {
                        "content": str(item.get("content", "")),
                        "status": str(item.get("status", "pending")),
                        "priority": str(item.get("priority", "medium")),
                    }
                )
    except Exception:
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": "Error: invalid todos JSON"}]},
            ensure_ascii=False,
        )

    # 更新外部引用
    todo_list_ref.clear()
    todo_list_ref.extend(parsed)

    total = len(parsed)
    done = sum(1 for t in parsed if t["status"] == "completed")
    return json.dumps(
        {
            "chunks": [
                {"output_type": "text", "content": f"Todo list updated: {done}/{total} completed"},
            ],
            "__todos__": parsed,
        },
        ensure_ascii=False,
    )


async def tool_terminate(result: str = "") -> str:
    """终止 ReAct 循环 — 1:1 复刻原版 Terminate"""
    return json.dumps(
        {"chunks": [{"output_type": "text", "content": result or "Task completed"}]},
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════
# Skill 相关工具 — 1:1 复刻原版
# ══════════════════════════════════════════════════════════

def _is_excel_skill_meta(skill) -> bool:
    """判断 skill 是否为 Excel/数据分析类型"""
    name = (skill.name or "").lower()
    desc = (skill.description or "").lower()
    tags = [tag.lower() for tag in (skill.tags or [])]
    return any(
        token in name or token in desc or token in tags
        for token in ["excel", "xlsx", "xls", "spreadsheet", "csv", "data analysis", "数据分析"]
    )


def _mentions_excel(text: str) -> bool:
    """判断文本是否提及 Excel 相关关键词"""
    lowered = text.lower()
    keywords = [
        "excel", "xlsx", "xls", "spreadsheet", "workbook", "sheet",
        "工作表", "表格", "电子表格", "csv", "数据分析",
    ]
    return any(keyword in lowered for keyword in keywords)


async def tool_select_skill(query: str, file_path: str = "") -> str:
    """选择最相关的 skill — 1:1 复刻原版 select_skill

    根据用户查询和文件上下文匹配最相关的数据分析 skill。
    如果有文件上传，自动在匹配输入中追加 Excel 相关关键词。
    """
    match_input = query or ""
    if file_path:
        match_input = f"{match_input} excel xlsx spreadsheet file"

    matched = match_skill(match_input, has_file=bool(file_path))

    # 如果匹配到的 skill 是 Excel 类型但用户查询和文件都不涉及 Excel，则不匹配
    if (
        matched
        and _is_excel_skill_meta(matched)
        and not (_mentions_excel(query) or file_path)
    ):
        matched = None

    if matched:
        detail = f"Matched: {matched.name} - {matched.description}"
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": detail}]},
            ensure_ascii=False,
        )
    return json.dumps(
        {"chunks": [{"output_type": "text", "content": "No skill matched; proceed without skill"}]},
        ensure_ascii=False,
    )


async def tool_load_skill(skill_name: str, file_path: str = "") -> str:
    """加载 skill 内容 — 1:1 复刻原版 load_skill

    根据 skill 名称加载 SKILL.md 内容，返回 markdown 格式。
    """
    return load_skill_content(skill_name)


async def tool_get_skill_resource(skill_name: str, resource_path: str, args: Optional[dict] = None) -> str:
    """读取 skill 资源文件 — 1:1 复刻原版 get_skill_resource

    根据路径读取 skill 中的参考文档、配置文件等非脚本资源。
    """
    return read_skill_resource(skill_name, resource_path, args)


async def tool_execute_skill_script(skill_name: str, script_name: str, args: Optional[dict] = None, conv_id: str = "default") -> str:
    """执行 skill 内联脚本 — 1:1 复刻原版 execute_skill_script

    执行 skill 中定义的内联脚本（非 scripts/ 目录下的文件）。
    """
    # 当前轻量实现中，内联脚本和脚本文件使用同一执行路径
    return _execute_skill_script_file_impl(skill_name, script_name, args, conv_id)


async def tool_execute_skill_script_file(
    skill_name: str,
    script_file_name: str,
    args: Optional[dict] = None,
    conv_id: str = "default",
    file_path: str = "",
) -> str:
    """执行 skill scripts 目录下的脚本文件 — 1:1 复刻原版 execute_skill_script_file

    核心逻辑:
    1. 自动注入 react_state 中的 file_path 到 args（防止 LLM 篡改路径）
    2. 执行脚本
    3. 后处理：将绝对路径图片替换为 /images/ URL
    4. 读取脚本源码作为 code chunk 前置显示
    5. 追加已生成图片的汇总提示
    """
    # 自动注入正确的 file_path 到 args（1:1 复刻原版逻辑）
    real_file_path = file_path
    if real_file_path and args:
        _FILE_PATH_KEYS = {
            "input_file", "file_path", "data_path", "csv_path",
            "excel_path", "data_file",
        }
        for key in list(args.keys()):
            if key in _FILE_PATH_KEYS:
                args[key] = real_file_path

    result_str = _execute_skill_script_file_impl(skill_name, script_file_name, args, conv_id)

    # 读取脚本源码作为 code chunk 前置显示 — 1:1 复刻原版
    script_source = None
    try:
        skill = get_skill(skill_name)
        if skill:
            from pathlib import Path
            sf = script_file_name.lstrip("/\\")
            if sf.startswith("scripts/") or sf.startswith("scripts\\"):
                sf = sf[8:]
            script_abs = Path(skill.root_dir) / "scripts" / sf
            if script_abs.is_file():
                script_source = script_abs.read_text(encoding="utf-8")
    except Exception:
        pass

    # 后处理：替换绝对路径图片为 /images/ URL
    try:
        result_obj = json.loads(result_str) if isinstance(result_str, str) else result_str
        chunks = result_obj.get("chunks", [])

        # 前置脚本源码
        if script_source:
            chunks.insert(0, {"output_type": "code", "content": script_source})

        # 替换绝对路径图片
        static_dir = _ensure_static_img_dir()
        for chunk in chunks:
            if chunk.get("output_type") == "image":
                content = chunk.get("content", "")
                if isinstance(content, str) and os.path.isabs(content) and os.path.isfile(content):
                    ext = os.path.splitext(content)[1].lower()
                    if ext in IMAGE_EXTS:
                        unique_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(content)}"
                        dest = os.path.join(static_dir, unique_name)
                        shutil.copy2(content, dest)
                        img_url = f"/images/{unique_name}"
                        chunk["content"] = img_url

        result_obj["chunks"] = chunks
        return json.dumps(result_obj, ensure_ascii=False)
    except (json.JSONDecodeError, KeyError):
        return result_str


# ══════════════════════════════════════════════════════════
# 统一工具执行入口
# ══════════════════════════════════════════════════════════

async def execute_tool(
    action: str,
    action_input: Dict[str, Any],
    file_path: str = "",
    conv_id: str = "default",
    todo_list_ref: list = None,
    generated_images: List[str] = None,
) -> str:
    """统一工具执行入口 — 返回工具的原始输出字符串

    所有工具返回 JSON 字符串，格式: {"chunks": [...]}
    engine 层负责解析 chunks 并推送 SSE 事件。
    """
    todo_list_ref = todo_list_ref if todo_list_ref is not None else []

    if action == "execute_analysis":
        # 模型误把 code 参数传给 execute_analysis 时，提示使用 code_interpreter
        if "code" in action_input and "input_file" not in action_input:
            return json.dumps({
                "chunks": [{
                    "type": "text",
                    "content": "execute_analysis 仅用于获取文件概览（参数: input_file）。你传入的 code 参数已被忽略。如需执行 Python 代码，请使用 code_interpreter 工具。",
                }]
            }, ensure_ascii=False)
        input_file = action_input.get("input_file", file_path)
        return await tool_execute_analysis(input_file, conv_id)
    elif action == "code_interpreter":
        code = action_input.get("code", "")
        return await tool_code_interpreter(code, file_path, conv_id)
    elif action == "html_interpreter":
        return await tool_html_interpreter(
            html=action_input.get("html", ""),
            title=action_input.get("title", "Report"),
            file_path=action_input.get("file_path", ""),
            template_path=action_input.get("template_path", ""),
            data=action_input.get("data"),
            generated_images=generated_images,
        )
    elif action == "load_file":
        return await tool_load_file(action_input.get("file_path", file_path))
    elif action == "todowrite":
        return await tool_todowrite(action_input.get("todos", action_input), todo_list_ref)
    elif action == "terminate":
        result = action_input.get("result", "")
        if not result and isinstance(action_input, dict):
            result = str(action_input)
        return await tool_terminate(result)
    elif action == "select_skill":
        return await tool_select_skill(
            query=action_input.get("query", ""),
            file_path=file_path,
        )
    elif action == "load_skill":
        return await tool_load_skill(
            skill_name=action_input.get("skill_name", ""),
            file_path=action_input.get("file_path", ""),
        )
    elif action == "get_skill_resource":
        return await tool_get_skill_resource(
            skill_name=action_input.get("skill_name", ""),
            resource_path=action_input.get("resource_path", ""),
            args=action_input.get("args"),
        )
    elif action == "execute_skill_script":
        return await tool_execute_skill_script(
            skill_name=action_input.get("skill_name", ""),
            script_name=action_input.get("script_name", ""),
            args=action_input.get("args"),
            conv_id=conv_id,
        )
    elif action == "execute_skill_script_file":
        return await tool_execute_skill_script_file(
            skill_name=action_input.get("skill_name", ""),
            script_file_name=action_input.get("script_file_name", ""),
            args=action_input.get("args"),
            conv_id=conv_id,
            file_path=file_path,
        )
    else:
        return json.dumps(
            {"chunks": [{"output_type": "text", "content": f"Unknown tool: {action}"}]},
            ensure_ascii=False,
        )


# ══════════════════════════════════════════════════════════
# 子进程执行器
# ══════════════════════════════════════════════════════════

async def _run_code_subprocess(code: str, conv_id: str = "default", cwd: str = None) -> Dict[str, Any]:
    """在子进程中执行 Python 代码 — 1:1 复刻原版 code_interpreter 的执行方式

    返回: {"returncode": int, "stdout": str, "stderr": str}
    """
    if not cwd:
        cwd = os.path.join(config.UPLOAD_DIR, "..", "tmp", conv_id)
        cwd = os.path.abspath(cwd)
    os.makedirs(cwd, exist_ok=True)

    tmp_path = os.path.join(cwd, "_run.py")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        def _run_sync() -> subprocess.CompletedProcess:
            """在线程中同步执行 Python，并强制使用 UTF-8 处理中文输出。"""
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            return subprocess.run(
                [sys.executable, "-X", "utf8", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                timeout=60,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )

        try:
            proc = await asyncio.to_thread(_run_sync)
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            return {
                "returncode": proc.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Execution timed out (60s limit)",
            }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Execution error: {e}",
        }
    finally:
        # 清理临时脚本文件，保留工作目录中的其他文件
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
