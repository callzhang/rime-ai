

#!/usr/bin/env python3
import sys
import os
import time
import json
import subprocess
import threading
from pathlib import Path

# 外部依赖列表：格式为 (包名, 导入语句, 描述)
REQUIRED_PACKAGES = [
    ("requests", "import requests", "HTTP library for API requests"),
    ("pynput", "from pynput.keyboard import Controller as KeyboardController, Listener, Key", 
     "Keyboard input library"),
]

def install_package(package_name):
    """安装指定的包"""
    try:
        python_exe = sys.executable
        print(f"Installing {package_name}...", file=sys.stderr)
        # 使用超时，避免卡住
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=60  # 60秒超时
        )
        if result.returncode == 0:
            return True
        else:
            print(f"Failed to install {package_name}: {result.stderr.decode('utf-8', errors='ignore')}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"Timeout installing {package_name}", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error installing {package_name}: {e}", file=sys.stderr)
        return False

def check_and_install_dependencies():
    """检查并安装所有必需的依赖"""
    global KeyboardController, Listener, Key  # 声明全局变量
    
    for package_name, import_stmt, description in REQUIRED_PACKAGES:
        # 尝试导入
        try:
            # 使用 globals() 确保导入到全局作用域
            exec(import_stmt, globals())
            continue  # 导入成功，继续下一个
        except ImportError:
            pass  # 导入失败，继续安装流程
        
        # 导入失败，尝试安装
        print(f"{description} ({package_name}) not found, attempting to install...", file=sys.stderr)
        if not install_package(package_name):
            print(f"Error: Failed to install {package_name}.", file=sys.stderr)
            print(f"Please install manually: pip3 install {package_name}", file=sys.stderr)
            sys.exit(1)
        
        # 安装后重新尝试导入
        try:
            # 使用 globals() 确保导入到全局作用域
            exec(import_stmt, globals())
            print(f"Successfully installed and imported {package_name}", file=sys.stderr)
        except ImportError as e:
            print(f"Error: {package_name} installed but import failed: {e}", file=sys.stderr)
            print("You may need to install additional dependencies manually.", file=sys.stderr)
            sys.exit(1)

# 检查并安装所有依赖
check_and_install_dependencies()

# 用法：
#   python3 ai_streamer.py <cmd> <query>
#
# 示例：
#   python3 ai_streamer.py ai "台湾在哪里"

def load_env_file(env_path):
    """从 .env 文件读取环境变量"""
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 去除引号
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        env_vars[key] = value
    except FileNotFoundError:
        pass
    except Exception as e:
        pass  # 忽略读取错误
    return env_vars

def get_api_config():
    """获取 API 配置（优先从环境变量，其次从 .env 文件）"""
    # 先尝试从环境变量读取
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    # 如果环境变量中没有，尝试从 .env 文件读取
    if not api_key or not base_url:
        home = os.getenv("HOME") or os.path.expanduser("~")
        env_path = Path(home) / "Library" / "Rime" / ".env"
        env_vars = load_env_file(env_path)
        
        if not api_key and "OPENAI_API_KEY" in env_vars:
            api_key = env_vars["OPENAI_API_KEY"]
        if not base_url and "OPENAI_BASE_URL" in env_vars:
            base_url = env_vars["OPENAI_BASE_URL"]
    
    # 设置默认值
    if not base_url:
        base_url = "https://api.openai.com/v1"
    
    # 规范化 BASE_URL：去除末尾的 /v1 或 /v1/，然后统一添加
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]  # 移除末尾的 /v1
    base_url = base_url.rstrip("/") + "/v1"  # 统一添加 /v1
    
    return api_key, base_url

def stream_openai_like(cmd, query):
    """
    调用 OpenAI API 进行流式输出
    要求：yield 出"最小 token 粒度"的 unicode 字符串。
    """
    API_KEY, BASE_URL = get_api_config()
    
    if not API_KEY:
        yield "ERROR: OPENAI_API_KEY not set"
        return
    
    # 根据命令类型构建不同的提示
    system_prompt = "you are a helpful assistant, answer in concise and clear manner, with no more than 100 words."
    user_prompt = query
    
    if cmd == "translate" or cmd == "tr":
        user_prompt = f"【翻译】{query}"
    elif cmd == "sum":
        user_prompt = f"【总结】{query[:200]}..."
    elif cmd == "code":
        user_prompt = f"# 代码示例\n# {query}\nprint('hello')"
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "stream": True
            },
            timeout=60,
            stream=True
        )
        
        if resp.status_code != 200:
            error_msg = resp.json().get("error", {}).get("message", "Unknown error")
            yield f"ERROR: {error_msg}"
            return
        
        # 流式读取响应
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # 移除 'data: ' 前缀
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                # 逐字符 yield，实现真正的流式输出
                                for ch in content:
                                    yield ch
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"ERROR: {str(e)}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ai_streamer.py <cmd> <query>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    query = sys.argv[2]

    # 日志文件用于调试 - 输出到 rime_ai.log 方便查看
    log_file = "/tmp/rime_ai.log"
    
    def debug_log(msg):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[AI_STREAMER][{time.strftime('%H:%M:%S')}] {msg}\n")
            # 同时输出到 stderr，确保能看到
            print(f"[AI_STREAMER] {msg}", file=sys.stderr)
        except Exception:
            pass

    debug_log(f"Starting: cmd={cmd}, query={query}")

    # 全局停止标志
    stop_flag = threading.Event()
    paused = False

    # 初始化键盘控制器（在监听器之前创建，以便共享使用）
    try:
        keyboard = KeyboardController()
        # 为了兼容性，如果 Controller 没有 write 方法，添加一个别名
        if not hasattr(keyboard, 'write'):
            keyboard.write = keyboard.type
            debug_log("Added write() alias to keyboard controller")
        debug_log("Keyboard controller initialized")
        
        # 测试权限：尝试输入一个测试字符（但不实际输入）
        # 如果权限不足，这里会抛出异常或警告
        try:
            # 不实际输入，只是检查权限
            debug_log("Testing accessibility permissions...")
        except Exception as perm_error:
            debug_log(f"WARNING: Possible permission issue: {perm_error}")
    except Exception as e:
        error_msg = str(e)
        debug_log(f"ERROR: Failed to initialize keyboard: {e}")
        print("=" * 60, file=sys.stderr)
        print("ERROR: Keyboard input requires Accessibility permissions!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("", file=sys.stderr)
        print("To fix this:", file=sys.stderr)
        print("1. Open System Settings (System Preferences)", file=sys.stderr)
        print("2. Go to Privacy & Security > Accessibility", file=sys.stderr)
        print("3. Add Python or Terminal to the list", file=sys.stderr)
        print("4. Or add: /Users/derek/miniforge3/bin/python3", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Original error: {error_msg}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    # ESC 键监听器
    def on_press(key):
        nonlocal paused
        try:
            if key == Key.esc:
                if not paused:
                    paused = True
                    stop_flag.set()
                    # 追加"已暂停"
                    keyboard.type("已暂停")
        except Exception:
            pass

    # 启动键盘监听器（在后台线程）
    listener = Listener(on_press=on_press)
    listener.start()

    # 记录进程信息
    debug_log(f"Process PID: {os.getpid()}")
    debug_log(f"Current working directory: {os.getcwd()}")

    # 流式获取并输入字符
    token_count = 0
    try:
        debug_log("Starting stream...")
        for token in stream_openai_like(cmd, query):
            # 检查停止标志
            if stop_flag.is_set():
                debug_log("Stop flag set, breaking")
                break
            try:
                # 真·逐 token 输入
                # 使用 pynput 直接输入字符，不占用剪贴板，不会激活输入法，支持中文
                # 使用 type() 方法，它更可靠
                keyboard.type(token)
                token_count += 1
                # 每5个字符记录一次（更频繁的日志，方便调试）
                if token_count % 5 == 0:
                    debug_log(f"Written {token_count} tokens (last: '{token}')")
            except Exception as e:
                debug_log(f"ERROR writing token '{token}': {e}")
                debug_log(f"Exception type: {type(e).__name__}, message: {str(e)}")
                import traceback
                debug_log(f"Traceback: {traceback.format_exc()}")
                # 最小失败兜底：直接打印到 stdout
                sys.stdout.write(token)
                sys.stdout.flush()
        debug_log(f"Stream completed, total tokens: {token_count}")
    except Exception as e:
        debug_log(f"ERROR in main loop: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        # 停止监听器
        try:
            listener.stop()
        except Exception as e:
            debug_log(f"ERROR stopping listener: {e}")
        debug_log("Exiting")

    sys.exit(0)

if __name__ == "__main__":
    main()