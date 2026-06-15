"""
AI 分析模块 - DeepSeek API 集成
功能：工艺参数推荐 / 生长诊断 / 数据解读报告 / 对话式分析
"""

import os
import json
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx

router = APIRouter(prefix="/api/ai-analysis", tags=["AI分析-高级"])

# ── 配置 ──────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

SYSTEM_PROMPT_BASE = """你是 HgCdTe MBE（分子束外延）数字孪生系统的 AI 分析助手。
你精通以下领域：
- HgCdTe 红外探测器材料的 MBE 外延生长工艺
- 基板温度、Hg/Te/Cd 束流比、生长速率等关键工艺参数
- CdZnTe 基板表面处理与晶格匹配
- 组分均匀性、缺陷密度（空位迁移：V_Hg 1.320eV, V_Cd 0.938eV, V_Te 0.684eV）
- RHEED 振荡分析与表面重构
- X 射线衍射(XRD)、光致发光(PL)谱等表征手段

回答时请结合 MBE 生长的物理机理，给出可操作的建议。
对于数值型建议，请给出合理范围和推荐值。
"""


# ── 请求/响应模型 ─────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False
    mode: str = Field(
        default="chat",
        description="分析模式: chat/recommend/diagnose/report",
    )


class GrowthParams(BaseModel):
    """当前生长参数"""
    substrate_temp: Optional[float] = Field(None, description="基板温度 (°C)")
    hg_flux: Optional[float] = Field(None, description="Hg 束流 BEP (Torr)")
    te_flux: Optional[float] = Field(None, description="Te 束流 BEP (Torr)")
    cd_flux: Optional[float] = Field(None, description="Cd 束流 BEP (Torr)")
    growth_rate: Optional[float] = Field(None, description="生长速率 (μm/h)")
    target_x: Optional[float] = Field(None, description="目标 Cd 组分 x")
    thickness: Optional[float] = Field(None, description="目标厚度 (μm)")
    substrate: str = Field(default="CdZnTe(211)B", description="基板类型")


class RecommendRequest(BaseModel):
    params: GrowthParams
    target: str = Field(
        default="optimize_composition",
        description="优化目标",
    )


class DiagnoseRequest(BaseModel):
    params: GrowthParams
    symptoms: list[str] = Field(default_factory=list, description="观察到的异常现象")
    rheed_pattern: Optional[str] = Field(None, description="RHEED 图样描述")
    time_series: Optional[dict] = Field(None, description="时间序列数据")


class ReportRequest(BaseModel):
    simulation_data: dict = Field(..., description="模拟结果数据")
    report_type: str = Field(default="growth_summary", description="报告类型")


# ── DeepSeek API 调用 ─────────────────────────────────

async def call_deepseek(messages: list[dict], stream: bool = False):
    """调用 DeepSeek API"""
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
            ) as response:
                if response.status_code != 200:
                    detail = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"DeepSeek API 调用失败: {detail.decode()}",
                    )
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        yield data
        else:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"DeepSeek API 错误: {resp.text}",
                )
            result = resp.json()
            yield result["choices"][0]["message"]["content"]


def build_messages(
    system_extra: str,
    user_content: str,
    history: list[dict] = None,
) -> list[dict]:
    """构建消息列表"""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT_BASE + "\n" + system_extra}]
    if history:
        msgs.extend(history)
    msgs.append({"role": "user", "content": user_content})
    return msgs


# ── API 端点 ──────────────────────────────────────────

@router.post("/chat")
async def ai_chat(req: ChatRequest):
    """通用对话式分析"""
    mode_prompts = {
        "chat": "以对话方式帮助用户理解 MBE 生长过程和模拟结果。",
        "recommend": "重点关注工艺参数优化建议，给出具体数值范围。",
        "diagnose": "重点分析可能的问题原因，按可能性排序并给出解决方案。",
        "report": "生成结构化的分析报告，包含数据解读和结论。",
    }
    system_extra = mode_prompts.get(req.mode, mode_prompts["chat"])
    messages = [{"role": "system", "content": SYSTEM_PROMPT_BASE + "\n" + system_extra}]
    messages.extend([m.model_dump() for m in req.messages])

    if req.stream:
        async def event_stream():
            async for chunk in call_deepseek(messages, stream=True):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        result = ""
        async for content in call_deepseek(messages, stream=False):
            result = content
        return {"response": result, "mode": req.mode}


@router.post("/recommend")
async def recommend_params(req: RecommendRequest):
    """工艺参数智能推荐"""
    system_extra = """你现在作为工艺参数优化专家。
请根据用户提供的当前参数和目标，给出优化建议。
回复格式要求（JSON）：
{
  "current_assessment": "对当前参数的评估",
  "recommendations": [
    {
      "parameter": "参数名",
      "current": "当前值",
      "suggested": "建议值/范围",
      "reason": "调整原因",
      "priority": "high/medium/low"
    }
  ],
  "expected_outcome": "预期改善效果",
  "warnings": ["注意事项"]
}
请确保输出合法 JSON，不要包含 markdown 代码块标记。"""

    params_str = json.dumps(
        req.params.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=2,
    )
    user_content = f"当前生长参数：\n{params_str}\n\n优化目标：{req.target}\n\n请给出参数优化建议。"

    messages = build_messages(system_extra, user_content)
    result = ""
    async for content in call_deepseek(messages, stream=False):
        result = content

    # 尝试解析 JSON
    try:
        cleaned = result.strip()
        # 移除可能的 markdown 代码块标记
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
        return {"recommendations": parsed, "raw": result}
    except json.JSONDecodeError:
        return {"recommendations": None, "raw": result}


@router.post("/diagnose")
async def diagnose_growth(req: DiagnoseRequest):
    """生长过程诊断"""
    system_extra = """你现在作为 MBE 生长故障诊断专家。
根据用户描述的异常现象和工艺参数，分析可能的原因并给出解决方案。
回复格式要求（JSON）：
{
  "diagnosis": [
    {
      "issue": "问题描述",
      "probability": "high/medium/low",
      "root_cause": "根本原因分析",
      "evidence": "判断依据",
      "solution": "解决方案",
      "param_adjustments": {"参数名": "建议值"}
    }
  ],
  "overall_status": "critical/warning/normal",
  "immediate_actions": ["需要立即采取的措施"]
}
请确保输出合法 JSON，不要包含 markdown 代码块标记。"""

    params_str = json.dumps(
        req.params.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=2,
    )
    symptoms_str = (
        "\n".join(f"- {s}" for s in req.symptoms)
        if req.symptoms
        else "无明确症状描述"
    )
    rheed_str = f"\nRHEED 图样: {req.rheed_pattern}" if req.rheed_pattern else ""

    user_content = f"""当前生长参数：
{params_str}

观察到的异常现象：
{symptoms_str}
{rheed_str}

请进行诊断分析。"""

    messages = build_messages(system_extra, user_content)
    result = ""
    async for content in call_deepseek(messages, stream=False):
        result = content

    try:
        cleaned = result.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
        return {"diagnosis": parsed, "raw": result}
    except json.JSONDecodeError:
        return {"diagnosis": None, "raw": result}


@router.post("/report")
async def generate_report(req: ReportRequest):
    """模拟数据 AI 解读与报告生成"""
    system_extra = f"""你现在作为材料科学分析报告撰写专家。
报告类型：{req.report_type}
请根据提供的模拟数据生成专业的分析报告。
报告应包含：
1. 数据概述与关键指标
2. 趋势分析与物理解读
3. 与理论预期的对比
4. 结论与建议
使用 Markdown 格式输出。"""

    data_str = json.dumps(req.simulation_data, ensure_ascii=False, indent=2)
    user_content = f"模拟数据:\n{data_str}\n\n请生成分析报告。"

    messages = build_messages(system_extra, user_content)
    result = ""
    async for content in call_deepseek(messages, stream=False):
        result = content

    return {
        "report": result,
        "report_type": req.report_type,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/health")
async def health_check():
    """检查 AI 分析服务状态"""
    if not DEEPSEEK_API_KEY:
        return {"status": "no_key", "detail": "DEEPSEEK_API_KEY 未配置"}
    try:
        messages = [{"role": "user", "content": "ping"}]
        async for _ in call_deepseek(messages, stream=False):
            pass
        return {
            "status": "ok",
            "model": DEEPSEEK_MODEL,
            "api_base": DEEPSEEK_BASE_URL,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}