import json
import os
import sys
from typing import Optional
from pydantic import BaseModel


class ProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    enabled: bool = True


def _get_config_dir() -> str:
    """配置文件目录：exe旁边 或 源码目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，放在 exe 所在目录
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(_get_config_dir(), "providers.json")


def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"providers": [], "active_model": None}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"providers": [], "active_model": None}


def _save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_all_providers() -> list[ProviderConfig]:
    config = _load_config()
    return [ProviderConfig(**p) for p in config.get("providers", [])]


def get_active_provider() -> Optional[ProviderConfig]:
    """获取当前启用的供应商"""
    config = _load_config()
    active_model = config.get("active_model")
    providers = get_all_providers()
    if active_model:
        for p in providers:
            if p.model == active_model and p.enabled:
                return p
    # 回退到第一个启用的供应商
    for p in providers:
        if p.enabled:
            return p
    return None


def get_provider_by_model(model: str) -> Optional[ProviderConfig]:
    providers = get_all_providers()
    for p in providers:
        if p.model == model:
            return p
    return None


def set_active_provider(model: str) -> bool:
    """设置当前启用的供应商"""
    config = _load_config()
    providers = config.get("providers", [])
    found = any(p["model"] == model for p in providers)
    if not found:
        return False
    config["active_model"] = model
    _save_config(config)
    return True


def add_provider(provider: ProviderConfig) -> bool:
    config = _load_config()
    for p in config.get("providers", []):
        if p["model"] == provider.model:
            return False
    config.setdefault("providers", []).append(provider.model_dump())
    # 如果是第一个供应商，自动设为活跃
    if len(config["providers"]) == 1:
        config["active_model"] = provider.model
    _save_config(config)
    return True


def update_provider(model: str, provider: ProviderConfig) -> bool:
    config = _load_config()
    providers = config.get("providers", [])
    for i, p in enumerate(providers):
        if p["model"] == model:
            providers[i] = provider.model_dump()
            # 如果更新的是活跃供应商，同步更新 active_model
            if config.get("active_model") == model:
                config["active_model"] = provider.model
            _save_config(config)
            return True
    return False


def delete_provider(model: str) -> bool:
    config = _load_config()
    providers = config.get("providers", [])
    new_providers = [p for p in providers if p["model"] != model]
    if len(new_providers) == len(providers):
        return False
    config["providers"] = new_providers
    # 如果删除的是活跃供应商，切换到第一个
    if config.get("active_model") == model:
        config["active_model"] = new_providers[0]["model"] if new_providers else None
    _save_config(config)
    return True
