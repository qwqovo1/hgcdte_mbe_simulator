import subprocess
import sys
import os
import time
import signal
import webbrowser
import re
import socket
import json
import urllib.request

# --- 基础配置 ---
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
# 锁定你的 Cpolar 路径
CPOLAR_PATH = r"D:\内网穿透\cpolar.exe"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

processes = []


def get_current_ip():
    """动态获取本机在当前 WiFi 环境下的局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        # 通过探测公共地址来确定本地出网网卡的 IP
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def force_cleanup():
    """清理环境进程，防止端口被占用"""
    print("🧹 正在深度清理旧环境进程...")
    # 彻底结束 cpolar
    subprocess.run('taskkill /F /IM cpolar.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 强制清理端口占用
    for port in [BACKEND_PORT, FRONTEND_PORT]:
        try:
            cmd = f'netstat -ano | findstr :{port}'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            pids = set(re.findall(r'\s+(\d+)\s*$', res.stdout, re.M))
            for pid in pids:
                if pid != '0':
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        except:
            pass


def get_remote_url():
    """扫描 Cpolar API 端口并抓取公网地址 (保留此功能作为备选)"""
    active_api = None
    for port in range(4040, 4046):
        api_url = f"http://127.0.0.1:{port}/api/tunnels"
        try:
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.getcode() == 200:
                    active_api = f"http://127.0.0.1:{port}"
                    data = json.loads(response.read().decode())
                    if 'tunnels' in data and len(data['tunnels']) > 0:
                        for tunnel in data['tunnels']:
                            pub_url = tunnel.get('public_url', '')
                            if pub_url.startswith('https') and 'cpolar' in pub_url:
                                return pub_url, active_api
        except:
            continue
    return None, active_api


def start_services():
    """一键启动前后端及隧道"""
    try:
        # 1. 启动后端
        print(f"🚀 [1/3] 启动后端服务 (Port {BACKEND_PORT})...")
        p_back = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
            cwd=BACKEND_DIR, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        processes.append(p_back)

        # 2. 启动前端
        print(f"🚀 [2/3] 启动前端服务 (Port {FRONTEND_PORT})...")
        p_front = subprocess.Popen(
            "npm run dev -- --host 0.0.0.0",
            cwd=FRONTEND_DIR, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        processes.append(p_front)

        # 3. 启动 Cpolar
        print(f"🚀 [3/3] 开启远程隧道 (Cpolar)...")
        if os.path.exists(CPOLAR_PATH):
            p_cpolar = subprocess.Popen(
                f'"{CPOLAR_PATH}" http {FRONTEND_PORT}',
                shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            processes.append(p_cpolar)
        else:
            print("⚠️ 未找到 Cpolar，仅支持内网访问模式。")

        return True
    except Exception as e:
        print(f"❌ 启动崩溃: {e}")
        return False


def shutdown(signum=None, frame=None):
    """安全退出"""
    print("\n\n🛑 正在执行安全退出并清理进程...")
    for p in processes:
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except:
            pass
    subprocess.run('taskkill /F /IM cpolar.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✨ 环境已清理完毕。")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    print("=" * 65)
    print("      电子束外延数字孪生项目 - 全集成内网/远程版")
    print("=" * 65)

    force_cleanup()
    time.sleep(1)

    if not start_services():
        sys.exit(1)

    print("\n" + "-" * 50)
    print("📡 正在准备网络访问地址...")

    # 尝试获取远程网址 (供参考)
    remote_url, _ = get_remote_url()
    host_ip = get_current_ip()

    print("\n")
    if remote_url:
        print(f"🌍 远程公网: {remote_url}")

    print(f"📍 校园网内网访问: http://{host_ip}:{FRONTEND_PORT}")
    print(f"💡 手机/平板连接同一 WiFi 后，手动输入上方地址即可访问。")
    print("-" * 50)

    print("🌐 正在为您打开本地预览...")
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{FRONTEND_PORT}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()