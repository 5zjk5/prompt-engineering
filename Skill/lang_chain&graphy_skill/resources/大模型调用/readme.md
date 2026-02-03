# 大模型调用

本目录包含了各种大语言模型的调用实现，基于LangChain框架，支持多种主流大模型API。

## 文件说明

### ChatOpenAIModel_LangChian.py
自定义的OpenAI兼容模型实现，继承自LangChain的BaseChatModel类。该实现支持：

- **多种模型接口**：兼容OpenAI API格式的所有模型，包括智谱、ModelScope、Gemini、微软Azure等
- **多种调用方式**：
  - 同步调用（invoke），普通支持三种方式 message，agent 方式也支持三种方式 message
  - 异步调用（ainvoke）
  - 流式调用（stream）
  - 异步流式调用（astream）
  - 批次调用（batch）
- **Agent工具调用**：支持在LangChain Agent中使用
- **思考功能**：支持模型的思考内容处理（如Gemini的thinking功能）
- **Azure支持**：专门支持Azure OpenAI服务

### Azure.py
微软Azure OpenAI服务的调用示例，展示了：
- 使用`init_chat_model`和`AzureChatOpenAI`两种初始化方式
- 三种消息传递方法：字典格式、LangChain消息格式、简单字符串
- 流式调用和批次调用的实现
- Token使用统计

### Gemini.py
Google Gemini模型的调用示例，展示了如何通过OpenAI兼容接口调用Gemini模型。

### OpanAI.py
OpenAI官方API的调用示例，提供了两种基本的模型初始化和调用方法。

## 特性对比

| 特性 | init_chat_model | ChatOpenAIModel_LangChian |
|------|----------------|--------------------------|
| 支持模型 | OpenAI、Anthropic、Azure、Google、Gemini、AWS Bedrock | 所有OpenAI兼容接口 |
| 思考功能 | 支持 | 支持 |
| 异步调用 | 支持 | 支持 |
| 流式调用 | 支持 | 支持 |
| 批次调用 | 支持 | 支持 |
| Agent工具调用 | 支持 | 支持 |
| 自定义配置 | 有限 | 完全自定义 |
