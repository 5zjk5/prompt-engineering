#!/usr/bin/env python3
"""FastAPI 后端目录脚手架生成脚本

按照标准分层架构生成完整的后端目录结构：
  backend/
  ├── main.py                      # FastAPI 入口（从模板复制）
  ├── requirements.txt             # Python 依赖
  ├── .env.example                 # 环境变量示例
  ├── app/
  │   ├── __init__.py
  │   ├── core/
  │   │   ├── __init__.py
  │   │   ├── config.py            # 全局配置（从模板复制）
  │   │   └── logger.py            # 会话级日志（从模板复制）
  │   ├── llm/                     # LLM 客户端（直接照抄，不修改）
  │   │   ├── __init__.py
  │   │   ├── client.py
  │   │   └── llm_config.py
  │   ├── dal/
  │   │   ├── __init__.py
  │   │   └── database.py          # SQLite 连接与初始化（从模板复制）
  │   ├── api/
  │   │   ├── __init__.py
  │   │   └── example.py           # SSE 流式 API 示例（从模板复制）
  │   ├── services/
  │   │   └── __init__.py
  │   └── prompts/
  │       └── __init__.py
  ├── logs/                        # 日志目录（运行时自动创建子目录）
  ├── skills/                      # 技能目录
  └── storage/                     # 存储目录（按需存放项目文件，结构由实际需求决定）

注意：不生成 .gitignore 和 .gitkeep 文件。
storage/ 仅创建顶层目录，不预生成子目录结构，由运行时代码按需创建。

用法：
    python scaffold.py <目标目录> [--project-name <名称>]

示例：
    python scaffold.py ./my-backend
    python scaffold.py ./my-backend --project-name "My API"
"""

import argparse
import shutil
import sys
from pathlib import Path

# Windows 控制台默认 GBK 编码，强制 stdout 使用 UTF-8 避免中文/符号输出失败
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# 脚本所在目录（即技能根目录）
SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_LLM = SKILL_ROOT / "assets" / "llm"
ASSETS_TEMPLATES = SKILL_ROOT / "assets" / "templates"


def write_file(path: Path, content: str) -> None:
    """写入文件，自动创建父目录"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    """复制文件，自动创建父目录"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    """递归复制目录"""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            copy_dir(item, dst / item.name)


def create_empty_init(dir_path: Path) -> None:
    """创建空的 __init__.py"""
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")


def generate_scaffold(target_dir: str, project_name: str = "FastAPI Backend") -> None:
    """生成完整的后端目录结构

    Args:
        target_dir: 目标根目录路径（即 backend/ 目录）
        project_name: 项目名称，写入 main.py 的 FastAPI title
    """
    root = Path(target_dir).resolve()

    if root.exists() and any(root.iterdir()):
        print(f"⚠️  目标目录已存在且非空: {root}")
        confirm = input("是否继续？已存在的文件将被覆盖 [y/N]: ").strip().lower()
        if confirm != "y":
            print("已取消。")
            return

    print(f"🚀 生成后端脚手架到: {root}")
    root.mkdir(parents=True, exist_ok=True)

    # ── 1. 复制 LLM 模块（直接照抄，不做任何修改） ──────────
    print("  [1/7] 复制 LLM 模块 (app/llm/)...")
    llm_dst = root / "app" / "llm"
    copy_dir(ASSETS_LLM, llm_dst)

    # ── 2. 复制 core 模块模板 ────────────────────────────────
    print("  [2/7] 生成 core 模块 (app/core/)...")
    core_dst = root / "app" / "core"
    create_empty_init(core_dst)
    copy_file(ASSETS_TEMPLATES / "config.py", core_dst / "config.py")
    copy_file(ASSETS_TEMPLATES / "logger.py", core_dst / "logger.py")

    # ── 3. 复制 dal 模块模板 ─────────────────────────────────
    print("  [3/7] 生成 dal 模块 (app/dal/)...")
    dal_dst = root / "app" / "dal"
    create_empty_init(dal_dst)
    copy_file(ASSETS_TEMPLATES / "database.py", dal_dst / "database.py")

    # ── 4. 生成 api 模块（含示例） ───────────────────────────
    print("  [4/7] 生成 api 模块 (app/api/)...")
    api_dst = root / "app" / "api"
    create_empty_init(api_dst)
    copy_file(ASSETS_TEMPLATES / "api_example.py", api_dst / "example.py")

    # ── 5. 生成 services 和 prompts 空模块 ──────────────────
    print("  [5/7] 生成 services 和 prompts 模块...")
    create_empty_init(root / "app" / "services")
    create_empty_init(root / "app" / "prompts")
    create_empty_init(root / "app")

    # ── 6. 复制入口文件和配置 ────────────────────────────────
    print("  [6/7] 生成入口文件和依赖...")
    # 读取模板 main.py，替换项目名称
    main_content = (ASSETS_TEMPLATES / "main.py").read_text(encoding="utf-8")
    main_content = main_content.replace('FastAPI Backend', project_name)
    write_file(root / "main.py", main_content)
    copy_file(ASSETS_TEMPLATES / "requirements.txt", root / "requirements.txt")
    copy_file(ASSETS_TEMPLATES / ".env.example", root / ".env.example")

    # ── 7. 创建运行时目录（logs / skills / storage） ────────
    print("  [7/7] 创建运行时目录 (logs/ skills/ storage/)...")
    # 仅创建顶层目录，不预生成子目录结构，也不生成 .gitignore / .gitkeep。
    # storage/ 用于存放项目运行时所需的文件（数据库、上传文件、临时文件等），
    # 具体子目录结构由实际业务需求决定，运行时代码会按需自动创建。
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "skills").mkdir(parents=True, exist_ok=True)
    (root / "storage").mkdir(parents=True, exist_ok=True)

    print()
    print("✅ 后端脚手架生成完成！")
    print()
    print("目录结构：")
    print(f"  {root.name}/")
    print(f"  ├── main.py              # FastAPI 入口")
    print(f"  ├── requirements.txt     # Python 依赖")
    print(f"  ├── .env.example         # 环境变量示例")
    print(f"  ├── app/")
    print(f"  │   ├── core/            # 配置、日志")
    print(f"  │   ├── llm/             # LLM 客户端（多模型、重试、流式）")
    print(f"  │   ├── dal/             # 数据访问层（SQLite）")
    print(f"  │   ├── api/             # API 路由（含 SSE 流式示例）")
    print(f"  │   ├── services/        # 业务逻辑层")
    print(f"  │   └── prompts/         # 提示词管理")
    print(f"  ├── logs/                # 日志目录")
    print(f"  ├── skills/              # 技能目录")
    print(f"  └── storage/             # 存储目录（按需存放项目文件）")
    print()
    print("后续步骤：")
    print(f"  1. cd {root}")
    print(f"  2. python -m venv venv && source venv/bin/activate  # Windows: venv\\Scripts\\activate")
    print(f"  3. pip install -r requirements.txt")
    print(f"  4. cp .env.example .env  # 并修改配置")
    print(f"  5. 修改 app/llm/llm_config.py 填入实际模型配置")
    print(f"  6. python main.py")


def main():
    parser = argparse.ArgumentParser(
        description="生成标准 FastAPI 后端目录脚手架"
    )
    parser.add_argument(
        "target_dir",
        help="目标目录路径（即 backend/ 目录）",
    )
    parser.add_argument(
        "--project-name",
        default="FastAPI Backend",
        help="项目名称，写入 FastAPI title（默认: FastAPI Backend）",
    )
    args = parser.parse_args()

    generate_scaffold(args.target_dir, args.project_name)


if __name__ == "__main__":
    main()
