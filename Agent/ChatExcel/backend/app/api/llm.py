"""大模型配置查询接口 — 返回可选模型列表。"""

from fastapi import APIRouter

from app.llm.llm_config import get_llm_providers

router = APIRouter()


@router.get("/llm/models")
async def list_llm_models():
    """返回代码中配置的大模型列表，供前端展示和选择。"""
    providers = get_llm_providers()
    return [
        {"name": p.name, "model": p.model}
        for p in providers
    ]
