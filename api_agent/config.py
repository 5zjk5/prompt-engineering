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
    active_name = config.get("active_name")
    providers = get_all_providers()
    if active_name:
        for p in providers:
            if p.name == active_name and p.enabled:
                return p
    # 回退到第一个启用的供应商
    for p in providers:
        if p.enabled:
            return p
    return None


def get_provider_by_name(name: str) -> Optional[ProviderConfig]:
    providers = get_all_providers()
    for p in providers:
        if p.name == name:
            return p
    return None


def get_provider_by_model(model: str) -> Optional[ProviderConfig]:
    """根据 model 查找 provider，优先返回活跃的"""
    config = _load_config()
    active_name = config.get("active_name")
    providers = get_all_providers()
    
    # 优先返回活跃的 provider（如果 model 匹配）
    if active_name:
        for p in providers:
            if p.name == active_name and p.model == model and p.enabled:
                return p
    
    # 否则返回第一个匹配的
    for p in providers:
        if p.model == model and p.enabled:
            return p
    return None


def set_active_provider(name: str) -> bool:
    """设置当前启用的供应商"""
    config = _load_config()
    providers = config.get("providers", [])
    found = any(p["name"] == name for p in providers)
    if not found:
        return False
    config["active_name"] = name
    _save_config(config)
    return True


def add_provider(provider: ProviderConfig) -> bool:
    config = _load_config()
    for p in config.get("providers", []):
        if p["name"] == provider.name:
            return False
    config.setdefault("providers", []).append(provider.model_dump())
    # 如果是第一个供应商，自动设为活跃
    if len(config["providers"]) == 1:
        config["active_name"] = provider.name
    _save_config(config)
    return True


def update_provider(name: str, provider: ProviderConfig) -> bool:
    config = _load_config()
    providers = config.get("providers", [])
    for i, p in enumerate(providers):
        if p["name"] == name:
            providers[i] = provider.model_dump()
            # 如果更新的是活跃供应商，同步更新 active_name
            if config.get("active_name") == name:
                config["active_name"] = provider.name
            _save_config(config)
            return True
    return False


def delete_provider(name: str) -> bool:
    config = _load_config()
    providers = config.get("providers", [])
    new_providers = [p for p in providers if p["name"] != name]
    if len(new_providers) == len(providers):
        return False
    config["providers"] = new_providers
    # 如果删除的是活跃供应商，切换到第一个
    if config.get("active_name") == name:
        config["active_name"] = new_providers[0]["name"] if new_providers else None
    _save_config(config)
    return True
