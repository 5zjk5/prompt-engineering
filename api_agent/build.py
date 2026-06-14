"""PyInstaller 打包脚本 - 将 API Agent 打包为单个 exe"""
import PyInstaller.__main__
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

args = [
    os.path.join(ROOT, "main.py"),
    "--name=API_Agent",
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    f"--add-data={os.path.join(ROOT, 'server.py')};.",
    f"--add-data={os.path.join(ROOT, 'config.py')};.",
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols",
    "--hidden-import=uvicorn.protocols.http",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.protocols.websockets",
    "--hidden-import=uvicorn.protocols.websockets.auto",
    "--hidden-import=uvicorn.lifespan",
    "--hidden-import=uvicorn.lifespan.on",
    "--hidden-import=webview",
    "--hidden-import=webview.platforms",
    "--hidden-import=webview.platforms.winforms",
    "--hidden-import=openai",
    "--hidden-import=httpx",
    "--hidden-import=httpcore",
    "--hidden-import=anyio",
    "--hidden-import=sniffio",
    "--hidden-import=h11",
    "--hidden-import=starlette",
    "--hidden-import=starlette.responses",
    "--hidden-import=starlette.routing",
    "--hidden-import=starlette.middleware",
    "--hidden-import=fastapi",
    "--hidden-import=pydantic",
    "--hidden-import=pydantic_core",
    "--hidden-import=jiter",
]

# 图标：如果根目录有 icon.ico 则使用
icon_path = os.path.join(ROOT, "icon.ico")
if os.path.exists(icon_path):
    args.append(f"--icon={icon_path}")
    args.append(f"--add-data={icon_path};.")
    print(f"[打包] 使用图标: {icon_path}")
else:
    print("[打包] 未找到 icon.ico，使用默认图标")

PyInstaller.__main__.run(args)
