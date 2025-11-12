# 默认情况下，` Nodesand` 和`or`Edges是预先定义的，并且操作的是同一个共享状态。
# 但是，有时可能事先不知道确切的边，或者您可能希望同时存在不同版本的 `and`。MapReduce设计State模式就是一个常见的例子。
# 在这种设计模式中，第一个节点可能会生成一个对象列表，而您可能希望将另一个节点应用于所有这些对象。对象的数量可能事先未知（意味着边的数量可能未知），并且下游节点的输入应该不同（每个生成的对象对应一个输入）。StateNode
# 为了支持这种设计模式，LangGraph 支持Send从条件边返回对象。Send它接受两个参数：第一个参数是节点名称，第二个参数是要传递给该节点的状态。
# 意思就是相当于直接 goto 某个节点了

def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state['subjects']]  # 也相当于并行，同一个节点执行多次不同任务

graph.add_conditional_edges("node_a", continue_to_jokes)
