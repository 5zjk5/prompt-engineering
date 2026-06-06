# PandasAI 项目梳理

## 一句话总结

> **`df.chat(自然语言)` → 框架把表结构+前 5 行样本拼进 prompt → LLM 输出一段 Python 代码（里面嵌一条 SQL 字符串）→ 框架用 `exec()` 跑这段 Python，跑到 `execute_sql_query(sql)` 时把所有 DataFrame 临时注册进 DuckDB 执行 SQL，再把结果包成 Response 返回。**

---

## 单轮对话完整流程（以 `df.chat("统计各类别商品的销售总金额")` 为例）

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 1. 读数据                                                              │
│    pai.read_csv("sales_orders.csv")                                  │
│    └─ pandas 把 CSV 读到内存，包成 pandasai 的 DataFrame               │
│       （数据只在 Python 对象里，不入任何数据库）                          │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. df.chat(query) → Agent._process_query                              │
│    （清空 Memory，启动新一轮对话）                                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. 拼 Prompt（jinja2 渲染 generate_python_code_with_sql.tmpl）         │
│                                                                       │
│    <tables>                                                           │
│      <table table_name="table_sales_orders"                           │
│             columns='[{"name":"销售金额","type":"integer"},...]'        │
│             dimensions="20x8">                                        │
│         订单编号,客户编号,商品名称,销售金额,销售省份                       │
│         DD2024001,C001,小米手机,5998,广东      ← 只取 head(5)           │
│         ...                                                           │
│      </table>                                                         │
│    </tables>                                                          │
│                                                                       │
│    <function>def execute_sql_query(sql) -> pd.DataFrame</function>    │
│    ### QUERY  统计各类别商品的销售总金额                                  │
│    Note: 聚合/排序/join/groupby 必须用 SQL                              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. LLM 生成 Python 代码（一次调用，不是 CoT）                            │
│                                                                       │
│    import pandas as pd                                                │
│    sql_query = """                                                    │
│      SELECT 商品类别, SUM(销售金额) AS total                            │
│      FROM table_sales_orders                                          │
│      GROUP BY 商品类别 ORDER BY total DESC                              │
│    """                                                                │
│    df = execute_sql_query(sql_query)   ← SQL 嵌在 Python 字符串里        │
│    result = {"type": "dataframe", "value": df}                        │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. CodeCleaner 清洗：AST 扫描 → 表名白名单校验、剥危险代码                │
│    CodeRequirementValidator：必须调用 execute_sql_query，否则重试        │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 6. exec(code, env)  在受控 env 里跑这段 Python                          │
│    env = { pd, np, plt, execute_sql_query: Agent._execute_sql_query } │
└──────────────────────────────────────────────────────────────────────┘
                              │
              代码跑到 execute_sql_query(sql) 这一行
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 7. Agent._execute_sql_query —— 真正"入库 + 查询"发生在这一刻             │
│                                                                       │
│    for df in self._state.dfs:                                         │
│        duckdb.register(df.schema.name, df)  ← 零拷贝挂载，不是复制       │
│    return duckdb.sql(sql).df()              ← DuckDB 内存执行           │
│                                                                       │
│    返回 pd.DataFrame 给 Python 代码继续用                                │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 8. Python 代码组装 result = {"type": ..., "value": ...}                │
│    ResponseParser 按 type 包成 Response：                               │
│      number    → NumberResponse                                       │
│      string    → StringResponse                                       │
│      dataframe → DataFrameResponse                                    │
│      plot      → ChartResponse                                        │
│                                                                       │
│    返回给用户                                                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 关键认知点

### 1. 数据存哪？

| 阶段 | 数据位置 |
|---|---|
| `pai.read_csv()` 之后 | 只在 Python 内存里（pandas DataFrame 对象） |
| `df.chat()` 之前 | DuckDB 还不知道这张表 |
| 执行 `execute_sql_query` 时 | 临时把所有 df `duckdb.register(name, df)` 挂载（零拷贝），SQL 跑完结果以 pd.DataFrame 返回 |
| 进程结束 | DuckDB 内存表自动消失，没有持久化 |

### 2. LLM 输出的是什么？

**一段完整的 Python 代码，里面有一个 SQL 字符串字面量**。
不是 CoT，不是先 pandas 后 SQL，就是一次 LLM 调用出最终代码。

- Python 部分：负责调度、组装 `result = {type, value}` 字典
- SQL 字符串：作为 `execute_sql_query("...")` 的参数，由 DuckDB 实际执行
- 强约束：prompt 末尾 `Note: 聚合/排序/join/groupby 必须用 SQL`，所以重活都在 SQL 里

### 3. 多表是怎么 join 的？

```python
orders_df    = pai.read_csv("sales_orders.csv")
customers_df = pai.read_csv("customers.csv")
pai.chat("VIP 客户的总销售额", orders_df, customers_df)
```

- Prompt 里渲染**两个** `<table>` 标签，各自带表名、列类型、head(5)
- LLM 看到两表都有 `客户编号` → 自己写出 `JOIN ... ON o.客户编号 = c.客户编号`
- 执行时 `Agent._execute_sql_query` 把**两张表都** register 到同一个 DuckDB 连接，SQL 一次跑完

兼容性限制：要么全是本地 CSV/Parquet，要么全是同一个远程数据库，混搭会抛 `ValueError`。

---

## 多轮对话怎么实现

代码很简单：

```python
df.chat(q)         # ① 调用 start_new_conversation()，清空 memory，新会话
df.follow_up(q2)   # ② 不清空，复用 memory；prompt 里会带上轮代码做上下文
```

### Memory 是什么

[pandasai/helpers/memory.py](file:///d:/code/pandas-ai/pandasai/helpers/memory.py)：一个 list，按顺序存 `{message, is_user}`。

```python
self._messages = [
    {"message": "各省份销售额？",  "is_user": True},
    {"message": "广东 14893,...",  "is_user": False},   # 上一轮 LLM 答案（会被截到 100 字符）
    {"message": "哪三个最高？",    "is_user": True},   # 当前轮
]
```

### 多轮 prompt 区别

主模板 [generate_python_code_with_sql.tmpl](file:///d:/code/pandas-ai/pandasai/core/prompts/templates/generate_python_code_with_sql.tmpl) 有个分支：

```jinja
{% if last_code_generated and context.memory.count() > 0 %}
Last code generated:
{{ last_code_generated }}        ← 把上一轮 LLM 写的代码塞进来作为上下文
{% else %}
Update this initial code:
import pandas as pd
# Write code here                ← 首轮：只给空脚手架
{% endif %}
```

所以 `follow_up` 时 LLM 能"看到"自己上一轮写的 SQL，便于在同一份上下文里继续：

```python
df.chat("各省份销售额")
#   → LLM 写：SELECT 销售省份, SUM(销售金额) ... GROUP BY 销售省份

df.follow_up("哪三个最高？")
#   → Prompt 含 "Last code generated: SELECT 销售省份, SUM(销售金额)..."
#   → LLM 直接在上轮基础上加 ORDER BY total DESC LIMIT 3
```

### 手动重置

```python
df.start_new_conversation()    # 等价于 clear_memory()
df.add_message("...", is_user=False)   # 手动塞历史消息
```

---

## 生成图表（plot 类型）

调用方式跟普通 chat 完全一样，只是问题让 LLM 决定生成 plot：

```python
df.chat("用柱状图展示各商品类别的销售额")
```

### 跟普通查询的差别

LLM 生成的代码会变成（Python 里直接画图，画完保存路径）：

```python
import pandas as pd
import matplotlib.pyplot as plt

sql_query = "SELECT 商品类别, SUM(销售金额) AS total FROM table_sales_orders GROUP BY 商品类别"
df = execute_sql_query(sql_query)

plt.figure(figsize=(10, 6))
plt.bar(df['商品类别'], df['total'], color=['red','blue','green'])
plt.xlabel('商品类别')
plt.ylabel('销售金额')
plt.title('各类别销售额')
plt.savefig('exports/charts/my_chart.png')   # ← 关键：保存图片

result = {"type": "plot", "value": "exports/charts/my_chart.png"}
```

### CodeCleaner 在图表上做了两件事

[code_cleaning.py](file:///d:/code/pandas-ai/pandasai/core/code_generation/code_cleaning.py)：

1. `_replace_output_filenames_with_temp_chart`：把代码里所有 `*.png` 路径强制改成 `exports/charts/temp_chart_<uuid>.png`，防止覆盖别的文件
2. `re.sub(r"plt\.show\(\)", "", code)`：去掉 `plt.show()`（在脚本里弹窗会阻塞）

### 返回的是什么

`ResponseParser` 看到 `type == "plot"` → 返回 `ChartResponse`：

```python
resp = df.chat("用柱状图展示各类别销售额")
print(resp)              # 图片路径字符串
resp.save("output.png")  # 复制到指定位置
# 在 Jupyter 里会自动渲染图片
```

---

## 想看实际效果

`test/run.py` 4 个场景：

| 场景 | 函数 | 演示 |
|---|---|---|
| 单表查询 | `demo_单表查询()` | 最基础流程 |
| 多表 JOIN | `demo_多表联合查询()` | DuckDB 自动 join |
| 图表 | `demo_图表()` | plot 类型输出 |
| 多轮追问 | `demo_追问()` | `chat()` + `follow_up()` 复用 Memory |

调试断点推荐：

| 看什么 | 文件 |
|---|---|
| 入口 | [pandasai/agent/base.py:271 `_process_query`](file:///d:/code/pandas-ai/pandasai/agent/base.py#L271) |
| 拼 prompt | [pandasai/agent/base.py:117 `get_chat_prompt_for_sql`](file:///d:/code/pandas-ai/pandasai/agent/base.py#L117) |
| 看渲染后 prompt | [pandasai/core/prompts/base.py:51 `prompt.render`](file:///d:/code/pandas-ai/pandasai/core/prompts/base.py#L51) |
| LLM 出来的原始代码 | [pandasai/core/code_generation/base.py](file:///d:/code/pandas-ai/pandasai/core/code_generation/base.py) |
| 执行 Python | [pandasai/agent/base.py:197 `execute_with_retries`](file:///d:/code/pandas-ai/pandasai/agent/base.py#L197) |
| 真正跑 SQL | [pandasai/agent/base.py:137 `_execute_sql_query`](file:///d:/code/pandas-ai/pandasai/agent/base.py#L137) |
| DuckDB 注册 | [pandasai/data_loader/duck_db_connection_manager.py](file:///d:/code/pandas-ai/pandasai/data_loader/duck_db_connection_manager.py) |
| 结果包装 | [pandasai/core/response/parser.py](file:///d:/code/pandas-ai/pandasai/core/response/parser.py) |
