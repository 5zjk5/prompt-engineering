# 🔬 Open Deep Research
深度研究已成为最受欢迎的智能体应用之一。这是一款简单、可配置、完全开源的深度研究智能体，可在多个模型供应商、搜索工具和MCP服务器上运行。它的性能与许多流行的深度研究智能体相当。
项目来自 langchain 官方的开源实现，使用了 langgraph，具体链接：

[官方 github](https://github.com/langchain-ai/open_deep_research)

详细介绍看官方介绍就可以，这里拿过来作为学习 langgraph，改了些东西进行了适配 langgraph-v1.0，langchang-v1.0 版本。

加了自定义日志，适配了某些参数更新问题，把所有子图都模块化，注释都改成中文了，使用自定义 langchian 兼容 openai 的模型，可以 debug 调试，不依赖 langsmith 可视化。

架构图如下：

<img width="817" height="666" alt="Screenshot 2025-07-13 at 11 21 12 PM" src="https://github.com/user-attachments/assets/052f2ed3-c664-4a4f-8ec2-074349dcaa3f" />


# 使用
包适配版本，在 langchain-langgraph-V1.0/requirements.txt 中。安装即可。

.env 需要填入 TAVILY 搜索 api，langsmith api。都去对应官网可以直接拿到，TAVILY 免费  1000 次。

大模型 api 在 src/llm.py 中，ChatOpenAIModel_LangChian.py 为自定义的 langchain 模型，适配了 openai 的 api，加了返回更多内容（token，请求参数，块统计）

deep_researcher.py 为主文件入口