# https://docs.langchain.com/oss/python/langchain/test#mocking-chat-model

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolCall


model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[ToolCall(name="foo", args={"bar": "baz"}, id="call_1")]),  # 模拟 ai 回复的第一条消息，工具调用
    "bar"  # 模拟 ai 回复的第二条消息，普通文本
]))

res1 = model.invoke("hello")
print(res1)
# AIMessage(content='', ..., tool_calls=[{'name': 'foo', 'args': {'bar': 'baz'}, 'id': 'call_1', 'type': 'tool_call'}])

res2 = model.invoke("hello bar")
print(res2)
# AIMessage(content='bar', ...)
