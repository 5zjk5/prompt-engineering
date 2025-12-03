import os
import yaml
from typing import Dict, Any


class Config:
    """配置管理类"""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        # 获取配置文件路径
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'config.yaml'
        )

        # 默认配置
        default_config = {
            "app": {
                "title": "LangGraph Agent API",
                "description": "A FastAPI backend for LangGraph Agent chat application",
                "version": "1.0.0",
            },
            "cors": {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
            "database": {"url": "sqlite:///./langgraph.db"},
        }

        # 如果配置文件存在，读取并合并
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                try:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        # 递归合并配置
                        return self._merge_configs(default_config, user_config)
                    return default_config
                except yaml.YAMLError as e:
                    print(f"Warning: Failed to load config.yaml: {e}")
                    return default_config
        else:
            # 创建默认配置文件
            self._create_default_config(config_path, default_config)
            return default_config

    def _merge_configs(
        self, default: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """递归合并配置"""
        merged = default.copy()
        for key, value in user.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _create_default_config(self, config_path: str, config: Dict[str, Any]) -> None:
        """创建默认配置文件"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print(f"Created default config.yaml at {config_path}")
        except IOError as e:
            print(f"Warning: Failed to create config.yaml: {e}")

    def __getitem__(self, key: str) -> Any:
        """支持通过字典方式访问配置"""
        return self._config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """通过get方法访问配置"""
        return self._config.get(key, default)

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config


# 创建全局配置实例
config = Config()
