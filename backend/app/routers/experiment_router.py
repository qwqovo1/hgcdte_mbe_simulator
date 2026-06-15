"""
实验报告管理路由
功能：导出报告 / 文件列表 / 查看 / 下载 / 删除 / 重命名 / 复制 / 上传
"""

import os
import re
import shutil
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()


# ── 工具函数 ──────────────────────────────────────────

def get_data_dir() -> str:
    """获取 Data/ 目录的绝对路径，如果不存在则自动创建"""
    current_file_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(current_file_path)
    # 向上查找到 backend/ 目录
    while os.path.basename(root_dir) != "backend" and root_dir != os.path.dirname(root_dir):
        root_dir = os.path.dirname(root_dir)
    project_root = os.path.dirname(root_dir)
    data_dir = os.path.join(project_root, "Data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


# ── 请求模型 ──────────────────────────────────────────

class ExperimentData(BaseModel):
    """实验导出数据模型"""
    name: str
    startTime: str
    duration: str
    parameters: Dict[str, float]
    thickness: str


class RenamePayload(BaseModel):
    """重命名载荷"""
    newName: str


# ── API 端点 ──────────────────────────────────────────

@router.post("/export")
async def export_experiment(data: ExperimentData):
    """导出实验报告为 .txt 文件"""
    data_dir = get_data_dir()

    # 查找当前最大编号
    files = os.listdir(data_dir)
    max_index = 0
    pattern = re.compile(r"分子束外延实验报告单_(\d+)\.txt")
    for f in files:
        match = pattern.search(f)
        if match:
            max_index = max(max_index, int(match.group(1)))

    next_index = max_index + 1
    file_name = f"分子束外延实验报告单_{next_index}.txt"
    file_path = os.path.join(data_dir, file_name)

    # 构建报告内容
    content = (
        "================================================\n"
        "      HgCdTe (碲镉汞) MBE 外延生长报告单       \n"
        "================================================\n\n"
        f"报告编号: #{next_index}\n"
        f"实验项目: {data.name}\n"
        f"开始时间: {data.startTime}\n"
        f"生长历时: {data.duration}\n"
        f"预测膜厚: {data.thickness} nm\n\n"
        "------------------------------------------------\n"
        "【HgCdTe 特色物理模型说明】\n"
        "1. 材料体系: Hg-Cd-Te 三元半导体。\n"
        "2. 生长控制: 生长速率受 Te2 和 CdTe 通量共同决定。\n"
        "3. 核心机制: 引入了 Hg 粘附系数修正。Hg 通量必须覆盖\n"
        "   碲原子占据位点，否则会导致组分偏差和生长速率损失。\n"
        "4. 温度敏感度: 严格执行 180°C 窗口模型，偏离值将直接\n"
        "   通过 Arrhenius 关系影响最终沉积膜厚。\n"
        "------------------------------------------------\n\n"
        "【实验环境工艺参数明细】\n"
    )
    for key, value in data.parameters.items():
        content += f" - {key}: {value}\n"

    content += (
        "\n------------------------------------------------\n"
        f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "================================================\n"
    )

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "file": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_files():
    """列出 Data/ 目录下的所有文件"""
    data_dir = get_data_dir()
    files = []
    try:
        for name in sorted(os.listdir(data_dir)):
            path = os.path.join(data_dir, name)
            if not os.path.isfile(path):
                continue
            stats = os.stat(path)
            files.append({
                "name": name,
                "size": f"{round(stats.st_size / 1024, 2)} KB",
                "time": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return files


@router.get("/files/{name}")
async def get_file_content(name: str):
    """读取指定文件的文本内容"""
    path = os.path.join(get_data_dir(), name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"文件 {name} 不存在")
    if name.endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": "二进制文件，请直接下载查看"}


@router.get("/download/{name}")
async def download_file(name: str):
    """下载指定文件"""
    path = os.path.join(get_data_dir(), name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"文件 {name} 不存在")
    return FileResponse(path, filename=name)


@router.delete("/files/{name}")
async def delete_file(name: str):
    """删除指定文件"""
    path = os.path.join(get_data_dir(), name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"文件 {name} 不存在")
    try:
        os.remove(path)
        return {"message": f"文件 {name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/{old_name}")
async def rename_file(old_name: str, payload: RenamePayload):
    """重命名文件"""
    data_dir = get_data_dir()
    old_path = os.path.join(data_dir, old_name)
    new_path = os.path.join(data_dir, payload.newName)
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail=f"文件 {old_name} 不存在")
    if os.path.exists(new_path):
        raise HTTPException(status_code=409, detail=f"文件 {payload.newName} 已存在")
    try:
        os.rename(old_path, new_path)
        return {"message": f"已重命名为 {payload.newName}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/copy/{name}")
async def copy_file(name: str):
    """复制文件"""
    data_dir = get_data_dir()
    src_path = os.path.join(data_dir, name)
    if not os.path.exists(src_path):
        raise HTTPException(status_code=404, detail=f"文件 {name} 不存在")
    new_name = f"副本_{name}"
    dst_path = os.path.join(data_dir, new_name)
    try:
        shutil.copy(src_path, dst_path)
        return {"message": f"已复制为 {new_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    path = os.path.join(get_data_dir(), file.filename)
    try:
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))