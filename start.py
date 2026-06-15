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

# ── 加载 .env 配置文件 ──────────────────────────────
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# --- 基础配置（优先读 .env，否则用默认值） ---
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5173"))
FRPC_PATH = os.getenv("FRPC_PATH", r"D:\内网穿透\frpc.exe")
FRPC_CONFIG = os.getenv("FRPC_CONFIG", r"D:\内网穿透\frpc.ini")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

processes = []


def get_current_ip():
    """动态获取本机在当前 WiFi 环境下的局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def generate_qrcode(url, save_path):
    """
    生成二维码图片，保存到指定路径
    微信扫码后会跳转到默认浏览器打开该 URL
    """
    try:
        import qrcode
        from PIL import Image
    except ImportError:
        print("📦 正在安装二维码依赖: qrcode[pil]...")
        subprocess.run([sys.executable, "-m", "pip", "install", "qrcode[pil]"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import qrcode
        from PIL import Image

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # 添加标题文字提示
    try:
        from PIL import ImageDraw, ImageFont
        # 创建带标题的画布
        qr_width, qr_height = img.size
        canvas_height = qr_height + 80
        canvas = Image.new('RGB', (qr_width, canvas_height), 'white')
        canvas.paste(img, (0, 60))

        draw = ImageDraw.Draw(canvas)
        # 尝试加载中文字体
        try:
            font = ImageFont.truetype("msyh.ttc", 20)  # 微软雅黑
        except:
            try:
                font = ImageFont.truetype("simhei.ttf", 20)
            except:
                font = ImageFont.load_default()

        title = "微信扫码 → 浏览器打开"
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        x = (qr_width - text_width) // 2
        draw.text((x, 15), title, fill="black", font=font)

        # 底部显示URL
        url_short = url if len(url) < 40 else url[:40] + "..."
        try:
            font_small = ImageFont.truetype("msyh.ttc", 14)
        except:
            font_small = font
        bbox2 = draw.textbbox((0, 0), url_short, font=font_small)
        url_width = bbox2[2] - bbox2[0]
        draw.text(((qr_width - url_width) // 2, canvas_height - 25),
                  url_short, fill="gray", font=font_small)

        canvas.save(save_path)
    except Exception:
        img.save(save_path)

    return save_path


def print_qrcode_terminal(url):
    """在终端中直接打印二维码（备用方案）"""
    try:
        import qrcode
    except ImportError:
        return

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def generate_mobile_qr_page(url, qr_image_path):
    """
    生成一个 HTML 引导页，用于微信扫码后提示用浏览器打开
    解决微信内置浏览器兼容性问题
    """
    html_path = os.path.join(ROOT_DIR, "scan_redirect.html")
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MBE数字孪生 - 移动端访问</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 32px 24px;
            max-width: 360px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}
        .icon {{ font-size: 48px; margin-bottom: 16px; }}
        h1 {{ font-size: 20px; color: #333; margin-bottom: 8px; }}
        p {{ color: #666; font-size: 14px; line-height: 1.6; margin-bottom: 20px; }}
        .btn {{
            display: block;
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            margin-bottom: 12px;
        }}
        .btn:active {{ transform: scale(0.98); }}
        .tip {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            color: #856404;
            margin-top: 16px;
        }}
        .url {{ 
            word-break: break-all; 
            font-family: monospace; 
            font-size: 12px;
            color: #999;
            margin-top: 12px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🔬</div>
        <h1>MBE 数字孪生系统</h1>
        <p>电子束外延实验数据分析与AI智能诊断平台</p>

        <a class="btn" href="{url}" id="openBtn">
            🚀 点击进入系统
        </a>

        <div class="tip" id="wechatTip" style="display:none;">
            💡 <strong>微信用户提示：</strong><br>
            请点击右上角 ⋯ 选择「在浏览器中打开」<br>
            以获得最佳体验
        </div>

        <div class="url">{url}</div>
    </div>

    <script>
        // 检测微信环境
        if (/MicroMessenger/i.test(navigator.userAgent)) {{
            document.getElementById('wechatTip').style.display = 'block';
        }}

        // 自动跳转（非微信环境）
        if (!/MicroMessenger/i.test(navigator.userAgent)) {{
            window.location.href = "{url}";
        }}
    </script>
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_path


def force_cleanup():
    """清理环境进程，防止端口被占用"""
    print("🧹 正在深度清理旧环境进程...")
    subprocess.run('taskkill /F /IM frpc.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run('taskkill /F /IM cpolar.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

        # 3. 启动 frpc
        print(f"🚀 [3/3] 开启远程隧道 (frpc)...")
        if os.path.exists(FRPC_PATH) and os.path.exists(FRPC_CONFIG):
            p_frpc = subprocess.Popen(
                f'"{FRPC_PATH}" -c "{FRPC_CONFIG}"',
                shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            processes.append(p_frpc)
            print("✅ frpc 隧道已启动")
        else:
            print("⚠️ 未找到 frpc 或配置文件，仅支持内网访问模式。")
            print(f"   frpc路径: {FRPC_PATH}")
            print(f"   配置文件: {FRPC_CONFIG}")

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
    subprocess.run('taskkill /F /IM frpc.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

    host_ip = get_current_ip()
    access_url = f"http://{host_ip}:{FRONTEND_PORT}"

    # 显示 AI 模块状态
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    model = os.getenv("DEEPSEEK_MODEL", "未指定")
    if api_key and not api_key.startswith("sk-在这里"):
        print(f"\n🤖 AI 分析模块: ✅ 已配置 (模型: {model})")
    else:
        print(f"\n🤖 AI 分析模块: ❌ 请在 .env 文件中填入 DEEPSEEK_API_KEY")

    print(f"🌍 远程访问: 请查看 frpc 日志获取公网地址")
    print(f"📍 校园网内网访问: {access_url}")
    print(f"💡 手机/平板连接同一 WiFi 后，扫描下方二维码即可访问。")
    print("-" * 50)

    # ── 生成二维码 ──────────────────────────────────
    print("\n📱 正在生成手机扫码二维码...")

    # 生成微信引导跳转页面（解决微信内置浏览器问题）
    # 如果有公网地址，用公网；否则用局域网
    qr_target_url = access_url  # 默认局域网地址

    # 生成二维码图片
    qr_save_dir = os.path.join(ROOT_DIR, "qrcode_output")
    os.makedirs(qr_save_dir, exist_ok=True)
    qr_image_path = os.path.join(qr_save_dir, "access_qrcode.png")

    generate_qrcode(qr_target_url, qr_image_path)

    # 同时生成引导HTML（微信扫码友好）
    redirect_html = generate_mobile_qr_page(qr_target_url, qr_image_path)

    print(f"\n{'=' * 50}")
    print(f"📱 手机扫码访问二维码:")
    print(f"{'=' * 50}")

    # 终端内打印二维码
    print_qrcode_terminal(qr_target_url)

    print(f"\n{'=' * 50}")
    print(f"📁 二维码图片已保存: {qr_image_path}")
    print(f"📄 微信引导页已生成: {redirect_html}")
    print(f"{'=' * 50}")
    print(f"\n💡 使用说明:")
    print(f"   1. 手机连接同一WiFi网络")
    print(f"   2. 微信扫描上方二维码 或 打开二维码图片扫描")
    print(f"   3. 微信中点击右上角 ⋯ → 在浏览器中打开")
    print(f"   4. 系统已自动适配手机端显示比例")
    print(f"-" * 50)

    # 打开本地预览 + 打开二维码图片
    print("🌐 正在为您打开本地预览...")
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{FRONTEND_PORT}")

    # 同时打开二维码图片方便展示给他人扫码
    time.sleep(0.5)
    os.startfile(qr_image_path)  # Windows 下直接打开图片

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()