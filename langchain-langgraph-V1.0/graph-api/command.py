# 将控制流（边）和状态更新（节点）结合起来可能很有用。
# 例如，你可能希望在同一个节点中同时执行状态更新并决定下一步要跳转到哪个节点。
# LangGraph 提供了一种方法，即通过Command节点函数返回一个对象来实现这一点：
# 在节点函数中返回时Command，必须添加返回类型注解，其中包含节点路由到的节点名称列表，例如Command[Literal["my_other_node"]]

from langgraph.types import Command
from typing_extensions import Literal



def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # state update
        update={"foo": "bar"},
        # control flow
        goto="my_other_node"
    )


# 导航到父图中的节点
# 如果您正在使用子图，您可能希望从子图中的一个节点导航到另一个子图（即父图中的另一个节点）。为此，您可以graph=Command.PARENT在以下位置指定Command：
def my_node(state: State) -> Command[Literal["other_subgraph"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",  # where `other_subgraph` is a node in the parent graph
        graph=Command.PARENT
    )


# Command是人机交互工作流程的重要组成部分：当使用它interrupt()来收集用户输入时，Command然后通过提供输入并恢复执行Command(resume="User input")
