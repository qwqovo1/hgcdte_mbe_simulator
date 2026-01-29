import subprocess
import os
import sys
import time

def run_service():
    # 1. 下载 Cloudflare 穿透工具 (如果没有)
    # 放在项目根目录
    cf_tool = os.path.join(os.path.dirname(os.getcwd()), "cloudflared")
    if not os.path.exists(cf_tool):
        print("首次运行，正在下载公网穿透工具...")
        subprocess.run(["wget", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", "-O", cf_tool])
        subprocess.run(["chmod", "+x", cf_tool])

    # 2. 开启公网穿透
    print("正在开启公网访问通道，请在下方日志中寻找以 .trycloudflare.com 结尾的链接...")
    tunnel_process = subprocess.Popen(
        [cf_tool, "tunnel", "--url", "http://127.0.0.1:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # 3. 启动 FastAPI 后端
    print("正在启动 FastAPI 服务 (端口 8000)...")
    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    try:
        # 同时监控穿透日志并启动服务器
        # 打印前 20 行穿透日志以便用户寻找链接
        for _ in range(20):
            line = tunnel_process.stdout.readline()
            if "trycloudflare.com" in line:
                print("\n" + "="*50)
                print("访问地址: " + line.strip().split(" ")[-1])
                print("="*50 + "\n")
            if not line: break
            
        subprocess.run(uvicorn_cmd)
    except KeyboardInterrupt:
        print("正在停止服务...")
        tunnel_process.terminate()

if __name__ == "__main__":
    run_service()
