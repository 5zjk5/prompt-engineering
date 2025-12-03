import os
import subprocess
import time
import webbrowser
import sys
import signal

# 前端目录路径
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
# 前端服务地址
FRONTEND_URL = "http://localhost:5173"


def check_npm_installed():
    """检查npm是否已安装"""
    try:
        # 在Windows上尝试使用shell=True来运行npm命令
        if sys.platform == "win32":
            result = subprocess.run(
                "npm --version", check=True, capture_output=True, text=True, shell=True
            )
        else:
            result = subprocess.run(
                ["npm", "--version"], check=True, capture_output=True, text=True
            )
        print(f"npm版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"检查npm时出错: {e}")
        return False


def check_node_installed():
    """检查Node.js是否已安装"""
    try:
        result = subprocess.run(
            ["node", "--version"], check=True, capture_output=True, text=True
        )
        print(f"Node.js版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_dependencies():
    """安装前端依赖"""
    print("正在安装前端依赖...")
    try:
        subprocess.run(["npm", "install"], check=True)
        print("依赖安装完成！")
        return True
    except subprocess.CalledProcessError:
        print("依赖安装失败！")
        return False


def start_frontend():
    """启动前端服务"""
    # 检查Node.js是否已安装
    if not check_node_installed():
        print("错误: Node.js未安装！")
        print("请访问 https://nodejs.org/ 下载并安装Node.js")
        print("安装完成后，请重新运行此脚本")
        return

    # 检查npm是否已安装
    if not check_npm_installed():
        print("错误: npm未安装！")
        print("npm通常随Node.js一起安装，请确保Node.js安装正确")
        print("如果问题仍然存在，请尝试重新安装Node.js")
        return

    # 切换到前端目录
    os.chdir(FRONTEND_DIR)

    # 检查node_modules是否存在
    if not os.path.exists("node_modules"):
        if not install_dependencies():
            return

    print("正在启动前端服务...")
    print("请稍候，服务正在初始化...")

    # 启动npm run dev命令
    try:
        # 在Windows上使用cmd启动npm
        if os.name == "nt":
            process = subprocess.Popen(
                ["cmd", "/c", "npm", "run", "dev"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,  # 创建新的进程组，便于信号处理
            )
    except Exception as e:
        print(f"启动前端服务失败: {e}")
        return

    # 等待服务启动
    print("等待服务启动...")
    time.sleep(5)  # 等待5秒，给服务足够的启动时间

    # 检查进程是否仍在运行
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"服务启动失败！")
        print(f"错误信息: {stderr}")
        return

    # 自动打开浏览器
    print(f"前端服务已启动，正在打开浏览器访问: {FRONTEND_URL}")
    webbrowser.open(FRONTEND_URL)

    print("\n前端服务启动成功！")
    print("========================================")
    print(f"服务地址: {FRONTEND_URL}")
    print("按 Ctrl+C 停止服务")
    print("========================================")

    # 全局变量，用于标记是否应该退出
    global should_exit
    should_exit = False

    def signal_handler(sig, frame):
        global should_exit
        print("\n正在停止前端服务...")
        should_exit = True
        try:
            if os.name == "nt":
                # 在Windows上，先发送CTRL_BREAK_EVENT信号
                process.send_signal(signal.CTRL_BREAK_EVENT)
                # 等待进程终止，最多等待5秒
                try:
                    exit_code = process.wait(timeout=5)
                    print(f"前端服务已停止，退出代码: {exit_code}")
                except subprocess.TimeoutExpired:
                    # 如果5秒后仍未终止，强制终止
                    process.terminate()
                    exit_code = process.wait()
                    print(f"前端服务已强制停止，退出代码: {exit_code}")
            else:
                # 在Unix系统上，向整个进程组发送SIGTERM信号
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                # 等待进程终止，最多等待5秒
                try:
                    exit_code = process.wait(timeout=5)
                    print(f"前端服务已停止，退出代码: {exit_code}")
                except subprocess.TimeoutExpired:
                    # 如果5秒后仍未终止，强制终止整个进程组
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    exit_code = process.wait()
                    print(f"前端服务已强制停止，退出代码: {exit_code}")
        except Exception as e:
            print(f"停止服务时出错: {e}")
        finally:
            # 在Windows上使用sys.exit而不是os._exit
            if os.name == "nt":
                sys.exit(0)
            else:
                os._exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    # 创建一个线程来读取子进程输出，防止缓冲区阻塞
    import threading

    def read_output(pipe, output_type):
        try:
            for line in iter(pipe.readline, ""):
                if line:
                    print(f"[{output_type}] {line.strip()}")
        except:
            pass

    # 启动线程读取输出
    stdout_thread = threading.Thread(target=read_output, args=(process.stdout, "OUT"))
    stderr_thread = threading.Thread(target=read_output, args=(process.stderr, "ERR"))
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()

    try:
        # 保持脚本运行，但定期检查是否应该退出
        while not should_exit:
            # 使用poll()非阻塞检查进程状态
            if process.poll() is not None:
                exit_code = process.returncode
                print(f"前端服务已退出，退出代码: {exit_code}")
                break
            # 短暂休眠，避免CPU占用过高
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    start_frontend()
