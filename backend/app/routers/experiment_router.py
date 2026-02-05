from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List
from fastapi.responses import FileResponse

router = APIRouter()


def get_data_dir():
    current_file_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(current_file_path)
    while os.path.basename(root_dir) != 'backend' and root_dir != os.path.dirname(root_dir):
        root_dir = os.path.dirname(root_dir)
    project_root = os.path.dirname(root_dir)
    data_dir = os.path.join(project_root, "Data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


class ExperimentData(BaseModel):
    name: str
    startTime: str
    duration: str
    parameters: Dict[str, float]
    thickness: str


@router.post("/export")
async def export_experiment(data: ExperimentData):
    data_dir = get_data_dir()
    files = os.listdir(data_dir)
    max_index = 0
    pattern = re.compile(r"分子束外延实验报告单_(\d+)\.txt")
    for f in files:
        match = pattern.search(f)
        if match: max_index = max(max_index, int(match.group(1)))

    next_index = max_index + 1
    file_name = f"分子束外延实验报告单_{next_index}.txt"
    file_path = os.path.join(data_dir, file_name)

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
    data_dir = get_data_dir()
    files = []
    for name in os.listdir(data_dir):
        path = os.path.join(data_dir, name)
        stats = os.stat(path)
        files.append({
            "name": name,
            "size": f"{round(stats.st_size / 1024, 2)} KB",
            "time": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    return files


@router.get("/files/{name}")
async def get_file_content(name: str):
    path = os.path.join(get_data_dir(), name)
    if not os.path.exists(path): raise HTTPException(status_code=404)
    if name.endswith('.txt'):
        with open(path, "r", encoding="utf-8") as f: return {"content": f.read()}
    return {"content": "二进制文件，请直接下载查看"}


@router.get("/download/{name}")
async def download_file(name: str):
    path = os.path.join(get_data_dir(), name)
    return FileResponse(path, filename=name)


@router.delete("/files/{name}")
async def delete_file(name: str):
    path = os.path.join(get_data_dir(), name)
    os.remove(path)
    return {"message": "deleted"}


@router.put("/files/{old_name}")
async def rename_file(old_name: str, new_name: Dict[str, str]):
    old_path = os.path.join(get_data_dir(), old_name)
    new_path = os.path.join(get_data_dir(), new_name['newName'])
    os.rename(old_path, new_path)
    return {"message": "renamed"}


@router.post("/files/copy/{name}")
async def copy_file(name: str):
    path = os.path.join(get_data_dir(), name)
    new_name = f"副本_{name}"
    shutil.copy(path, os.path.join(get_data_dir(), new_name))
    return {"message": "copied"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    path = os.path.join(get_data_dir(), file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}