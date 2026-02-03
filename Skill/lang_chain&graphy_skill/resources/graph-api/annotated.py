# https://docs.langchain.com/oss/python/langgraph/graph-api#default-reducer

from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]

# 第二个键Annotated指定了一个 reducer 函数。
# 注意，第一个键保持不变。假设图的输入是。假设第一个返回。这被视为对状态的更新。
# 注意，不需要返回整个schema，只需要更新即可。应用此更新后，将变为。如果第二个节点返回，则将变为。
# 注意，这里的键是通过将两个列表相加来更新的。