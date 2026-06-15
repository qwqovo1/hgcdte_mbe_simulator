"""
AI 分析路由 - DeepSeek API + 论文佐证（增强版）
放置位置: backend/app/routers/ai_router.py
"""

import os
import json
import time
import re
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from ..services.paper_search import paper_service

router = APIRouter()

# ── 配置 ──────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ── System Prompt ─────────────────────────────────────
SYSTEM_PROMPT = """你是 HgCdTe MBE（分子束外延）数字孪生系统的 AI 分析引擎。

【知识背景】
- HgCdTe (MCT) 红外探测器材料的 MBE 外延生长全流程
- CdZnTe(211)B 基板，晶格常数 a≈6.48Å
- 工艺窗口：基板温度 170-190°C，Hg/Te BEP 比 ≈100-200
- RHEED (2×1) 重构 → Te-rich 表面，条纹→点状 = 二维→三维转变
- 组分 x(Cd) 与截止波长关系：λc ≈ 1.24/Eg

【课题组 DFT 计算数据】
- V_Hg 空位迁移势垒: 1.320 eV (CI-NEB, VASP 6.4.2)
- V_Cd 空位迁移势垒: 0.938 eV
- V_Te 空位迁移势垒: 0.684 eV
- 192原子 CZT(211) slab: Cd₉₂Zn₄Te₉₆
- NEP v4.5 ML势: 能量RMSE ~10.8 meV/atom

【要求】
- 回答要结合 MBE 物理机理，给出可操作的建议
- 数值建议必须给出范围和推荐值
- 引用课题组数据时标注"DFT计算结果"
- 不确定的内容要明确说明
- 回答使用中文，适当使用 Markdown 格式
- ⚠️ 重要：当系统提供了【论文佐证】信息时，你必须在正文中显式引用这些论文。引用格式为 [作者, 年份]。"""


# ── 论文佐证注入模板 ──────────────────────────────────
EVIDENCE_INJECTION_TEMPLATE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【系统指令 - 论文佐证（必须引用）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

以下是根据你回答内容检索到的相关学术论文。你 **必须** 做到以下两点：

1. **在正文分析中**，至少引用其中 2-3 篇论文来佐证你的观点。
   引用格式：[作者姓氏, 年份] 或 [第一作者 et al., 年份]
   示例：研究表明 Hg 粘附系数随温度升高呈指数下降 [Smith et al., 2018]。

2. **在回答末尾**，添加一个 "📚 参考文献" 部分，列出所有被引用的论文，格式为：
   [序号] 作者, "标题", 年份. 来源. 链接

检索到的论文列表：
{papers_text}

如果某篇论文与你当前分析的关联不够紧密，你可以标注"（间接相关）"。
但至少引用 2 篇。现在请重新组织你的回答，确保包含论文引用。
"""

# ── 无论文时的回退说明 ────────────────────────────────
NO_PAPER_NOTICE = """

---
> ⚠️ **论文佐证说明**：系统已尝试检索 arXiv、Semantic Scholar 等学术数据库，
> 但未找到与当前分析高度相关的论文。以上分析基于 AI 模型知识和课题组 DFT 数据。
> 建议用户可手动搜索以下关键词获取更多文献支持：
> `{keywords}`
"""


# ── 请求/响应模型 ─────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False


class ChatWithEvidenceRequest(BaseModel):
    messages: List[ChatMessage]
    enable_evidence: bool = True
    max_papers: int = 5


class PaperSearchRequest(BaseModel):
    query: str
    max_results: int = 5
    sources: List[str] = ["arxiv", "semantic_scholar"]


# ── DeepSeek API 调用 ─────────────────────────────────

async def call_deepseek(messages: list, stream: bool = False):
    """
    调用 DeepSeek API
    使用 async generator 模式，stream 和非 stream 统一接口
    """
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": stream,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        if stream:
            async with client.stream(
                "POST",
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    detail = await resp.aread()
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=detail.decode(),
                    )
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk.strip() == "[DONE]":
                            break
                        yield chunk
        else:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=resp.text,
                )
            data = resp.json()
            yield data["choices"][0]["message"]["content"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 端点
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/chat")
async def ai_chat(req: ChatRequest):
    """基础对话接口（不带论文佐证）"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend([m.model_dump() for m in req.messages])

    if req.stream:
        async def sse():
            async for chunk in call_deepseek(messages, stream=True):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(sse(), media_type="text/event-stream")

    result = ""
    async for content in call_deepseek(messages, stream=False):
        result = content
    return {"response": result}


@router.post("/chat-with-evidence")
async def ai_chat_with_evidence(req: ChatWithEvidenceRequest):
    """
    增强对话接口 - 带论文佐证

    流程：
    1. 先调用 DeepSeek 生成初步分析
    2. 从分析结果中提取英文关键词
    3. 搜索 arXiv + Semantic Scholar 相关论文
    4. 将论文信息注入上下文，让 AI 重新生成带引用的回答
    5. 如果没找到论文，附加说明提示
    """
    messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_for_api.extend([m.model_dump() for m in req.messages])

    # ── Step 1: 获取初步 AI 分析 ──
    initial_response = ""
    async for content in call_deepseek(messages_for_api, stream=False):
        initial_response = content

    if not req.enable_evidence:
        return {
            "response": initial_response,
            "papers": [],
            "evidence_enabled": False,
            "evidence_status": "disabled",
        }

    # ── Step 2: 提取搜索关键词 ──
    user_query = ""
    for m in reversed(req.messages):
        if m.role == "user":
            user_query = m.content
            break

    search_keywords = paper_service.extract_search_keywords(initial_response, user_query)
    print(f"[Evidence] 提取的搜索关键词: {search_keywords}")

    # ── Step 3: 并行搜索论文 ──
    all_papers = []
    for kw in search_keywords:
        try:
            papers = await paper_service.search(kw, max_results=3)
            all_papers.extend(papers)
        except Exception as e:
            print(f"[Evidence] 搜索 '{kw}' 失败: {e}")
            continue

    # 去重 & 限制数量
    seen_titles = set()
    unique_papers = []
    for p in all_papers:
        title_key = p["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(p)
    unique_papers = unique_papers[: req.max_papers]

    print(f"[Evidence] 检索到 {len(unique_papers)} 篇论文")

    # ── Step 4: 根据是否有论文，选择不同策略 ──
    if not unique_papers:
        # 没找到论文：在初步回答末尾附加说明
        keywords_str = " / ".join(search_keywords)
        notice = NO_PAPER_NOTICE.format(keywords=keywords_str)
        final_response = initial_response + notice

        return {
            "response": final_response,
            "papers": [],
            "evidence_enabled": True,
            "evidence_status": "no_papers_found",
            "search_keywords": search_keywords,
            "note": "未检索到高度相关论文，建议手动搜索上述关键词",
        }

    # ── Step 5: 有论文 → 注入上下文让 AI 重新生成带引用的回答 ──
    papers_text = ""
    for i, p in enumerate(unique_papers, 1):
        papers_text += f"\n[{i}] {p['authors']} ({p['year']})\n"
        papers_text += f"    标题: {p['title']}\n"
        if p.get("abstract"):
            papers_text += f"    摘要: {p['abstract'][:250]}...\n"
        papers_text += f"    来源: {p['source']} | 链接: {p['url']}\n"
        if p.get("citation_count", 0) > 0:
            papers_text += f"    被引: {p['citation_count']} 次\n"
        if p.get("doi"):
            papers_text += f"    DOI: {p['doi']}\n"

    evidence_prompt = EVIDENCE_INJECTION_TEMPLATE.format(papers_text=papers_text)

    # 重建消息：原始消息 + 初步回答 + 论文佐证指令
    enhanced_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    enhanced_messages.extend([m.model_dump() for m in req.messages])
    enhanced_messages.append({"role": "assistant", "content": initial_response})
    enhanced_messages.append({
        "role": "user",
        "content": evidence_prompt + "\n\n请基于以上论文，重新组织你的回答，在正文中引用这些文献。",
    })

    # 重新生成回答
    enhanced_response = ""
    async for content in call_deepseek(enhanced_messages, stream=False):
        enhanced_response = content

    # 为每篇论文生成 relevance 说明
    for p in unique_papers:
        if not p.get("relevance"):
            title_lower = p["title"].lower()
            if "hgcdte" in title_lower or "hg" in title_lower:
                p["relevance"] = "直接相关：HgCdTe 材料研究"
            elif "mbe" in title_lower or "epitax" in title_lower:
                p["relevance"] = "工艺相关：MBE 外延生长技术"
            elif "infrared" in title_lower or "detector" in title_lower:
                p["relevance"] = "应用相关：红外探测器"
            elif "temperature" in title_lower or "growth" in title_lower:
                p["relevance"] = "参数相关：生长条件优化"
            else:
                p["relevance"] = "领域参考文献"

    return {
        "response": enhanced_response,
        "papers": unique_papers,
        "evidence_enabled": True,
        "evidence_status": "success",
        "search_keywords": search_keywords,
        "initial_response_length": len(initial_response),
    }


@router.post("/search-papers")
async def search_papers(req: PaperSearchRequest):
    """独立论文搜索端点"""
    try:
        results = await paper_service.search(
            query=req.query,
            max_results=req.max_results,
            sources=req.sources,
        )
        return {
            "papers": results,
            "query": req.query,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_health():
    """AI 服务健康检查"""
    if not DEEPSEEK_API_KEY:
        return {"status": "no_key", "message": "DEEPSEEK_API_KEY 未设置"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code == 200:
                return {"status": "ok", "model": DEEPSEEK_MODEL}
            return {"status": "error", "message": f"API 返回 {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 报告文件端点
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_data_dir() -> str:
    """获取 Data/ 目录路径"""
    current = os.path.abspath(__file__)
    root = os.path.dirname(current)
    while os.path.basename(root) != "backend" and root != os.path.dirname(root):
        root = os.path.dirname(root)
    project_root = os.path.dirname(root)
    data_dir = os.path.join(project_root, "Data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


@router.get("/reports")
async def list_reports():
    """返回 Data/ 目录下所有实验报告文件列表"""
    data_dir = _get_data_dir()
    reports = []
    try:
        for name in sorted(os.listdir(data_dir)):
            filepath = os.path.join(data_dir, name)
            if not os.path.isfile(filepath):
                continue
            stat = os.stat(filepath)
            match = re.search(r"_(\d+)", name)
            index = int(match.group(1)) if match else 0
            reports.append({
                "name": name,
                "index": index,
                "size": f"{round(stat.st_size / 1024, 2)} KB",
                "time": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)
                ),
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return reports


@router.get("/reports/{filename}")
async def get_report_content(filename: str):
    """读取指定报告文件的完整文本内容"""
    data_dir = _get_data_dir()
    filepath = os.path.join(data_dir, filename)

    # 路径安全检查
    if not os.path.abspath(filepath).startswith(os.path.abspath(data_dir)):
        raise HTTPException(status_code=403, detail="非法路径")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))