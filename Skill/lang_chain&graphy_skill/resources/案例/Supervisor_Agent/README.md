# Supervisor Agent 示例

## 概述

Supervisor Agent 是一个基于 LangChain 和 LangGraph 的多智能体系统，实现了智能协调模式。该系统包含一个主智能体（supervisor）作为协调中心，通过调用子智能体来完成复杂的复合任务。

## 系统架构

### 核心组件

1. **Supervisor Agent** (`supervisor_agent.py`) - 主协调智能体
2. **Calendar Agent** (`sub_agent.py`) - 日程管理子智能体  
3. **Email Agent** (`sub_agent.py`) - 邮件处理子智能体

### 智能体职责

#### Supervisor Agent
- 接收用户自然语言请求
- 分析任务并分解为子任务
- 调用相应的子智能体
- 协调和整合结果
- 处理人机交互中断

#### Calendar Agent  
- 解析自然语言时间描述
- 检查参与者可用性
- 创建日历事件
- 提供人工审批机制

#### Email Agent
- 提取收件人信息
- 生成邮件主题和正文
- 发送电子邮件
- 提供人工审批机制

