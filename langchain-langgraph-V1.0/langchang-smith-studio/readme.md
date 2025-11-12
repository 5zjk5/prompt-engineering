# LangGraph Studio Demo with Custom Chat Model

本项目演示了如何使用 LangGraph 和 LangSmith Studio 构建一个带有自定义聊天模型的智能代理。

## 📋 项目概述

该项目实现了一个基于 LangChain 的智能代理，具有以下特性：

- 使用自定义的 `ChatOpenAIModel` 类，兼容 OpenAI API 接口
- 支持多种大语言模型（包括 OpenAI、Azure OpenAI 和 Google Gemini）
- 集成工具调用功能（如发送邮件）
- 可视化调试界面（LangSmith Studio）

## 🚀 快速开始

### 启动服务

在项目根目录下运行以下命令启动开发服务器：

```bash
langgraph dev
```

启动后，您可以通过以下 URL 访问 LangSmith Studio 进行可视化调试：

[http://127.0.0.1:2024/studio](http://127.0.0.1:2024/studio)

或者直接访问官方 Studio：

[https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

## 🧠 核心组件

### 自定义聊天模型 (`ChatOpenAIModel_LangChian.py`)

实现了兼容 OpenAI API 的自定义聊天模型，支持：

- OpenAI 和 Azure OpenAI 接口
- Google Gemini 模型
- 流式响应处理
- 工具绑定功能
- 思考过程内容处理

### 示例代理 (`demo.py`)

演示了如何创建一个具备工具调用能力的智能代理：

- 集成了 `send_email` 工具
- 使用自定义聊天模型
- 设置系统提示词

### sdk 示例

- `sync_sdk.py`: 同步 SDK 示例
- `async_sdk.py`: 异步 SDK 示例

## ⚙️ 配置说明

- `.env`: 包含 LangSmith API 密钥等敏感信息
- LANGSMITH_TRACING=true 可将跟踪信息记录到 LangSmith
- `langgraph.json`: LangGraph 项目配置文件，指定入口点和依赖关系

## 📚 文档资源

- [LangChain 官方文档](https://docs.langchain.com/oss/python/langchain/studio)
- [LangGraph 教程1](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangGraph 教程2](https://docs.langchain.com/oss/python/langgraph/local-server#7-test-the-api)
