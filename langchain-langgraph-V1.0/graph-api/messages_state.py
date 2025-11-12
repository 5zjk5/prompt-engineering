"""
由于在状态中存储消息列表非常常见，因此存在一个名为 `message` 的预构建状态MessagesState，它简化了消息的使用。
`message`MessagesState仅使用一个messages键来定义，该键是一个对象列表AnyMessage，并使用add_messagesreducer。
通常，需要跟踪的状态不仅仅是消息，因此我们看到人们会继承这个状态并添加更多字段，例如：
"""

from langgraph.graph import MessagesState

class State(MessagesState):
    documents: list[str]