# semantic-query 项目梳理

## 1. 项目一句话定位

【说明这个仓库是干什么的，介绍一下】


## 2. 这个代码仓解决什么问题

宽表查询常见痛点：

【痛点】

这个项目的处理思路：

【整体大概流程，让人读了能知道是做了什么】


## 3. 技术架构

【根据项目情况梳理介绍架构，例如什么关键接口等等，前端用了啥，后端用了啥，比如有没有用 langchain，fastapi 等等框架之类的】

### 3.1 怎么启动服务

【有前后端，分别说明前后端怎么启动】

【对于后端，需要说明怎么安装虚拟环境，虚拟环境需要安装到当前项目根目录；说明怎么安装环境包；用纯命令的话怎么启动；用代码的话怎么启动；想单独在 vscode 中 debug 后端接口代码的话，要怎么配置 .vscode 中的配置文件，写出来让用户知道，如果可以的直接班用户生成】

### 3.2 配置项

【大模型，embedding 模型 api，url，model 的 .env 或者 config 怎么配置，在哪里配置】

【其他配置项，如果有多项的话，需要说明每个配置项的作用，以及配置项的默认值，以及怎么使用】

## 4. 端到端业务流程

【必要的话你可以画流程图，如果流程图跟有利于展示的话，你自己评估】

### 接口先后顺序

【如果后端接口有先后顺序，保留此目录，开始以下步骤介绍】

#### 第一步：xxx

【什么接口，做了什么】

#### 第二步：xxx

【什么接口，做了什么】

#### 第三步：xxx

......

### 接口简介

【如果后端接口没有先后顺序的，都是独立或者存在部分独立接口，保留此目录】

【依次介绍这些接口】


## 5. 后端接口详细流程

本节逐个详细梳理每个后端接口的定义、入参、返回值以及代码执行的每一步细节。

【以下是一个示例，这个示例，是比较理想的，在对应代码流程上都能对应每一步细节，调用了什么函数，具体规则，做了什么，你根据情况可进行调整哈，如果接口不复杂，逻辑很简单你也可以不用分步骤写那么详细】

### 5.1 `POST /api/query/parse`

**定义位置**：`src/backend/app/api/routes/query.py` → `parse_query()`

**服务层**：`src/backend/app/services/query_service.py` → `QueryService.parse()`

**作用**：这是系统最核心的接口。接收用户的自然语言问题和字段语义配置，执行歧义检查、规则识别、LLM 解析，最终返回结构化的查询意图（指标、过滤条件、分组、对比分析）以及 SQL 口径草案。

**请求类型**：`application/json`

**入参**：`ParseQueryRequest`

```json
{
  "question": "华东地区今年订单金额的同比增长率是多少",
  "project_id": "demo-project",
  "table_name": "测试宽表",
  "fields": [
    {
      "field_name": "省份",
      "field_standard_name": "销售省份",
      "field_type": "dimension",
      "data_type": "string",
      "is_enable_enum": true,
      "field_alias": ["省份区域"],
      "field_desc": "订单所属省份区域",
      "enum_values": [
        {"raw_value": "华东", "value_alias": ["华东区"], "field_limit_word": null, "parent_value": null},
        {"raw_value": "华南", "value_alias": ["华南区"], "field_limit_word": null, "parent_value": null}
      ]
    },
    {
      "field_name": "订单金额",
      "field_standard_name": "订单金额",
      "field_type": "metric",
      "data_type": "float",
      "is_enable_enum": false,
      "field_alias": ["成交额", "销售额"],
      "field_desc": "订单总金额",
      "enum_values": []
    }
  ],
  "confirmed_items": []
}
```

**入参字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `question` | str | 是 | 用户自然语言问题 |
| `project_id` | str | 是 | 项目 ID |
| `table_name` | str | 是 | 表名 |
| `fields` | list[FieldSemanticPayload] | 否 | 字段语义配置列表，默认空 |
| `confirmed_items` | list[ConfirmedFieldSelection] | 否 | 用户已确认的歧义选择，默认空 |

**`ConfirmedFieldSelection` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `ambiguous_value` | str | 歧义词（如"上海"） |
| `selected_field_name` | str | 用户选择的字段名（如"省份"） |

**返回类型**：`ParseQueryResponse`

```json
{
  "original_question": "华东地区今年订单金额的同比增长率是多少",
  "parse_status": "success",
  "final_query": {
    "metrics": [
      {"field_name": "订单金额", "standard_name": "订单金额", "operator": null, "value": null, "value_type": null, "value_display": null}
    ],
    "filters": [
      {"field_name": "省份", "standard_name": "销售省份", "operator": "=", "value": "华东", "value_type": "enum", "value_display": "华东"}
    ],
    "group_by": [],
    "comparison": {
      "raw_expression": "同比增长",
      "comparison_type": "yoy",
      "analysis_intent": "compare_rate",
      "baseline_type": "same_period_last_year",
      "time_granularity": "year",
      "current_period": {"expr_type": "natural_period", "raw_text": "今年", "normalized_code": "current_year", "period_unit": "year", "rolling_count": null, "start_date": null, "end_date": null, "start_text": null, "end_text": null, "anchor_text": null, "display_text": "今年"},
      "baseline_period": {"expr_type": "same_period", "raw_text": "去年同期", "normalized_code": "same_period_last_year", "period_unit": "year", "rolling_count": null, "start_date": null, "end_date": null, "start_text": null, "end_text": null, "anchor_text": null, "display_text": "去年同期"},
      "display_text": "今年同比去年同期"
    },
    "comparisons": [],
    "sql_draft": {
      "table_name": "测试宽表",
      "grain": null,
      "metric_definitions": [{"field_name": "订单金额", "standard_name": "订单金额", "aggregation": "sum", "expression": "SUM(`订单金额`)"}],
      "where_clauses": [{"field_name": "省份", "standard_name": "销售省份", "operator": "=", "value_display": "华东", "sql_expression": "`省份` = '华东'"}],
      "group_by_fields": [],
      "comparison_plans": [{"comparison_type": "今年同比去年同期", "current_period": "今年", "baseline_period": "去年同期", "output_columns": ["当前期值", "同比基准值", "同比差值", "同比变化率"]}],
      "output_columns": ["订单金额", "当前期值", "同比基准值", "同比差值", "同比变化率"],
      "pseudo_sql": "SELECT\n  SUM(`订单金额`) AS `订单金额`\nFROM `测试宽表`\nWHERE\n  `省份` = '华东'\n\n-- 对比分析草案\n-- 使用 `下单日期` 取"今年"与"去年同期"两段数据，分别聚合后输出：当前期值, 同比基准值, 同比差值, 同比变化率",
      "notes": ["这是一版 SQL 口径草案...", "指标默认聚合方式按字段名自动推断...", "对比分析默认优先使用时间字段..."]
    }
  },
  "need_confirm_list": [],
  "need_confirm_items": [],
  "unhandled_item": [],
  "reasoning": "模型原始 JSON 输出..."
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `original_question` | str | 原始用户问题 |
| `parse_status` | str | 解析状态：`"success"` 成功、`"need_confirm"` 需要用户确认歧义、`"fail"` 失败 |
| `final_query` | FinalQuery | 结构化查询结果 |
| `need_confirm_list` | list[str] | 人类可读的歧义追问文案列表 |
| `need_confirm_items` | list[NeedConfirmItem] | 结构化的歧义候选项列表 |
| `unhandled_item` | list[str] | 未能处理的片段列表 |
| `reasoning` | str | 模型原始输出内容 |

**`FinalQuery` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `metrics` | list[QueryFieldRef] | 指标字段列表 |
| `filters` | list[QueryFieldRef] | 过滤条件列表 |
| `group_by` | list[QueryFieldRef] | 分组字段列表 |
| `comparison` | ComparisonSpec\|null | 主要对比分析项（取 comparisons 的第一个） |
| `comparisons` | list[ComparisonSpec] | 所有对比分析项列表 |
| `sql_draft` | SqlDraftSpec\|null | SQL 口径草案 |

**`QueryFieldRef` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `field_name` | str | 字段名 |
| `standard_name` | str | 标准名称 |
| `operator` | str\|null | 运算符：`=`、`!=`、`>`、`>=`、`<`、`<=`、`BETWEEN`、`IN`、`LIKE` 等 |
| `value` | any\|null | 过滤值 |
| `value_type` | str\|null | 值类型：`enum`、`number`、`number_range`、`date`、`date_range`、`relative_time`、`text` |
| `value_display` | str\|null | 值的展示文本 |

**`ComparisonSpec` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `raw_expression` | str | 原始对比表达文本 |
| `comparison_type` | str\|null | 对比类型：`yoy`（同比）、`mom`（环比）、`wow`（周环比）、`dod`（日环比）、`qoq`（季环比）、`period_compare`（期间对比）、`trend`（趋势） |
| `analysis_intent` | str\|null | 分析意图：`value_only`（仅值）、`compare_value`（对比值）、`compare_rate`（对比率）、`change_amount`（变化额）、`trend`（趋势） |
| `baseline_type` | str\|null | 基准类型：`previous_period`、`same_period_last_year`、`same_period_last_month`、`same_period_last_week`、`same_period_last_quarter`、`same_fiscal_period_last_year`、`custom_period` |
| `time_granularity` | str\|null | 时间粒度：`day`、`week`、`month`、`quarter`、`year` |
| `current_period` | TimeExpression\|null | 当前期时间表达 |
| `baseline_period` | TimeExpression\|null | 基准期时间表达 |
| `display_text` | str\|null | 展示文本 |

**`TimeExpression` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `expr_type` | str | 表达类型：`relative_range`、`natural_period`、`absolute_range`、`same_period`、`to_date`、`fiscal_period`、`custom` |
| `raw_text` | str | 原始文本 |
| `normalized_code` | str\|null | 标准化编码，如 `same_period_last_year`、`last_30_days` 等 |
| `period_unit` | str\|null | 周期单位：`day`、`week`、`month`、`quarter`、`year` |
| `rolling_count` | int\|null | 滚动周期数，如近 30 天的 30 |
| `start_date` | str\|null | 开始日期 |
| `end_date` | str\|null | 结束日期 |
| `start_text` | str\|null | 开始日期文本 |
| `end_text` | str\|null | 结束日期文本 |
| `anchor_text` | str\|null | 锚点文本 |
| `display_text` | str\|null | 展示文本 |

**`SqlDraftSpec` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `table_name` | str | 表名 |
| `grain` | str\|null | 粒度说明 |
| `metric_definitions` | list[SqlDraftMetric] | 指标定义列表 |
| `where_clauses` | list[SqlDraftCondition] | 筛选条件列表 |
| `group_by_fields` | list[str] | 分组字段列表 |
| `comparison_plans` | list[SqlDraftComparison] | 对比口径说明列表 |
| `output_columns` | list[str] | 输出列列表 |
| `pseudo_sql` | str | 伪 SQL 文本 |
| `notes` | list[str] | 补充说明 |

**`SqlDraftMetric` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `field_name` | str | 字段名 |
| `standard_name` | str | 标准名称 |
| `aggregation` | str | 聚合方式：`sum`、`avg`、`count`、`max`、`min` |
| `expression` | str | SQL 表达式，如 `SUM(\`订单金额\`)`、`COUNT(*)` |

**`SqlDraftCondition` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `field_name` | str | 字段名 |
| `standard_name` | str | 标准名称 |
| `operator` | str | 运算符 |
| `value_display` | str | 值的展示文本 |
| `sql_expression` | str | 伪 SQL 条件表达式 |

**`SqlDraftComparison` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `comparison_type` | str | 对比类型展示文本 |
| `current_period` | str | 当前期展示文本 |
| `baseline_period` | str | 基准期展示文本 |
| `output_columns` | list[str] | 对比分析输出列名 |

**`NeedConfirmItem` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `ambiguous_value` | str | 歧义词 |
| `question_fragment` | str | 歧义词在问题中的位置描述 |
| `candidates` | list[NeedConfirmCandidate] | 候选字段列表 |

**`NeedConfirmCandidate` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `field_name` | str | 候选字段名 |
| `standard_name` | str | 候选字段标准名 |
| `matched_value` | str | 匹配到的值 |
| `enum_value` | str | 命中的枚举原值 |
| `value_alias` | list[str] | 枚举值别名列表 |

---

**代码逐行执行流程（核心流程，最复杂）**：

#### 步骤一：前置校验

1. 检查 `payload.fields` 是否为空列表：
   - 为空则直接返回 `ParseQueryResponse(parse_status="fail", ...)`，reasoning 为 `"缺少字段配置，无法执行语义解析"`。

#### 步骤二：歧义检查

2. 调用 `_find_ambiguous_enum_items(payload)` 检查枚举值歧义：
   - 将 `payload.question` 转为小写。
   - 构建 `confirmed_map`（用户已确认的歧义选择映射：歧义词 → 字段名）。
   - 遍历所有 `is_enable_enum=True` 的字段：
     - 遍历每个枚举值的 `raw_value` 和 `value_alias`：
       - 调用 `_normalize_match_term(term)` 清洗待匹配词（`str.strip()`）。
       - 调用 `_should_match_enum_term(question, field, matched_term)` 判断是否匹配：
         - 如果匹配词为空或不在问题文本中，不匹配。
         - 如果匹配词长度 ≥ 2，匹配。
         - 如果匹配词长度为 1，只有在字段是"是否..."类布尔语义字段且问题中包含字段触发词时才匹配（避免单字值误命中普通问句）。
       - 如果匹配，记录到 `matched_candidates[matched_term][field.field_name] = NeedConfirmCandidate(...)`。
   - 对每个匹配词，如果它命中了 **2 个或以上** 不同字段，且不在 `confirmed_map` 中已被确认：
     - 构造 `NeedConfirmItem`，按 `standard_name` 排序候选项。
   - 返回歧义列表，按 `ambiguous_value` 排序。

3. **如果存在歧义项**（`ambiguity_items` 非空）：
   - 调用 `_build_need_confirm_messages(ambiguity_items)` 生成人类可读的追问文案（如 `"上海"可能对应字段：省份、城市，请确认具体要按哪个字段理解`）。
   - 直接返回 `ParseQueryResponse(parse_status="need_confirm", ...)`，不进入 LLM 解析。
   - 前端会展示歧义候选，用户选择后再次请求。

#### 步骤三：规则识别对比分析

4. 调用 `_extract_comparisons_from_question(payload.question)` 从问题中提取对比分析语义：

   **4a. 提取时间表达** `_extract_time_expressions(question)`：
   - 遍历 `TIME_EXPRESSION_RULES`（共 37 条规则），按关键词匹配：
     - `same_period`（同期类）：去年同期、上年同期、上月同期、上周同期、上季度同期、财年同期等。
     - `to_date`（累计类）：年初至今、本年累计、季初至今、月初至今等。
     - `relative_range`（相对区间类）：近 7 天、近 30 天、近 90 天、近一周、近一个月、近三个月、近半年、近一年等。
     - `natural_period`（自然周期类）：今天、昨天、本周、上周、上上周、本月、上月、上上月、本季度、上季度、今年、去年、前年等。
     - `fiscal_period`（财年类）：本财年、上财年、上上财年等。
   - 遍历正则模式匹配绝对时间区间：
     - `FULL_DATE_RANGE_PATTERNS`：`2024-01-01到2024-12-31`、`2024/01/01至2024/12/31`。
     - `YEAR_MONTH_RANGE_PATTERNS`：`2024年1月到2024年12月`、`2024年1月到12月`。
     - `MONTH_RANGE_PATTERNS`：`1月到3月`。
     - `YEAR_RANGE_PATTERNS`：`2023年到2024年`。
     - `QUARTER_RANGE_PATTERNS`：`2024年一季度到三季度`（支持中文数字一二三四）。
   - 对所有匹配结果按位置去重（`_dedupe_time_expressions`）：如果一个时间片段被更大片段包含则丢弃小片段。
   - 返回 `list[tuple[int, TimeExpression]]`，按出现位置排序。

   **4b. 匹配比较关键词** `_match_comparison_rules(question)`：
   - 遍历 `COMPARISON_RULES`（共 7 条规则）：
     - `yoy`（同比）：同比增长、同比变化、同比、较去年同期、与去年同期比等。
     - `qoq`（季环比）：季环比、较上季度等。
     - `wow`（周环比）：周环比、较上周等。
     - `dod`（日环比）：日环比、较昨日等。
     - `mom`（环比）：月环比、环比增长、环比变化、环比、较上期等。
     - `trend`（趋势）：变化趋势、趋势、走势、波动情况、波动。
     - `period_compare`（期间对比）：对比、比较、相比、相较。
   - 对每条规则，找第一个匹配的关键词，记录位置。
   - 按出现位置排序，去重（同一 `comparison_type + keyword` 只保留第一个）。

   **4c. 提取分析意图** `_extract_analysis_intent(question, has_comparison)`：
   - 问题包含"趋势"、"走势"、"波动" → `"trend"`。
   - 问题包含增长率、增幅、降幅、同比增速等 → `"compare_rate"`。
   - 问题包含增加多少、减少多少、变化多少等 → `"change_amount"`。
   - 有对比关键词或包含对比语境词 → `"compare_value"`。
   - 其他 → `"value_only"`。

   **4d. 构造 ComparisonSpec**：
   - 如果命中比较关键词：
     - 对每条规则调用 `_build_comparison_from_rule()`：
       - 调用 `_resolve_comparison_periods()` 从时间表达中推断当前期和基准期：
         - `period_compare` 且 ≥2 个时间表达 → 第一个作当前期，第二个作基准期。
         - 有"同期"表达 → 同期表达作基准期，其他表达作当前期。
         - ≥2 个时间表达 → 第一个作当前期，第二个作基准期。
         - 只有 1 个时间表达 → 作当前期，基准期为 None。
       - 调用 `_adjust_fiscal_baseline()`：如果当前期是财年表达，自动把同比基准升级为财年同期。
       - 如果基准期为空但有 `baseline_type`，调用 `_infer_baseline_period()` 补全默认基准期：
         - `same_period_last_year` → 构造"去年同期"。
         - `same_period_last_month` → 构造"上月同期"。
         - `previous_period` → 根据当前期推断更前一周期（如"本月"→"上月"，"今年"→"去年"等）。
       - 调用 `_infer_time_granularity()` 推断时间粒度（优先级：规则配置 > 当前期 > 基准期 > 比较类型默认值）。
       - 构造 `ComparisonSpec`，调用 `_build_comparison_display()` 生成展示文本（如"今年同比去年同期"）。
   - 如果未命中比较关键词：
     - 调用 `_build_fallback_comparison()` 尝试用时间表达和上下文推断对比：
       - 如果包含"同期"表达且 ≥2 个时间表达 → 构造同比或期间对比。
       - 如果 ≥2 个时间表达且包含比较语境 → 构造期间对比。
       - 如果意图是趋势且有时间表达 → 构造趋势分析。
   - 调用 `_dedupe_comparisons()` 按 `(comparison_type, current_period, baseline_period, raw_expression)` 去重。

#### 步骤四：构造提示词

5. 调用 `_build_prompt(payload, derived_comparisons)` 构造 LLM 提示词：

   **5a. 构建确认映射** `_build_confirmed_map(payload.confirmed_items)`：
   - 把 `confirmed_items` 转为 `{歧义词: 字段名}` 映射。

   **5b. 构建字段提示对象**：
   - 对每个字段调用 `_build_prompt_field_payload(field, question, confirmed_map)`：
     - 基础信息：`field_name`、`standard_name`、`field_type`、`data_type`、`is_enable_enum`。
     - 如果有 `field_alias`，最多取前 6 个（`PROMPT_ALIAS_LIMIT`）。
     - 如果有 `field_desc`，截取前 80 个字符。
     - 如果 `is_enable_enum` 且有枚举值，调用 `_should_include_enum_values_in_prompt()` 判断是否展开枚举：
       - 字段名/标准名/别名出现在问题中 → 展开。
       - 字段已被确认映射选中 → 展开。
       - 枚举值的原值或别名出现在问题中 → 展开。
       - 其他情况不展开（减少 prompt 噪音）。
     - 如果展开，每个枚举值调用 `_build_prompt_enum_payload()`：
       - 包含 `raw_value`、最多 6 个 `value_alias`、`field_limit_word`、`parent_value`。
       - 最多取前 12 个枚举值（`PROMPT_ENUM_VALUE_LIMIT`），超出部分标记 `enum_truncated`。
     - 每个字段转为 JSON 字符串。

   **5c. 构建确认说明** `_build_confirmed_lines(payload)`：
   - 对每个已确认项，生成如 `"问题中的"上海"按字段"销售省份（省份）"理解"` 的说明。

   **5d. 拼接最终提示词**：
   - 系统指令：`"你是宽表语义解析引擎，只输出 JSON，不要解释、不要 markdown。"`
   - 解析目标：metrics、filters、group_by、comparison、comparisons。
   - 字段引用格式说明：`field_name`、`standard_name`、`operator`、`value`、`value_type`、`value_display`。
   - 时间表达格式说明：`expr_type`、`raw_text`、`normalized_code`、`period_unit`、`rolling_count`、`start_date`、`end_date`、`display_text`。
   - 用户问题。
   - 已确认歧义说明（无则显示"已确认歧义：无"）。
   - 已识别对比线索（JSON 格式，无则显示"已识别对比线索：无"）。
   - 字段配置列表（每行一个 JSON 对象）。
   - 输出格式模板。

#### 步骤五：调用 LLM

6. 调用 `self.ai_gateway.chat(ChatCompletionRequest(messages=[ChatMessage(role="user", content=prompt)]))`：

   **`AIGatewayService.chat()` 执行流程**：
   - 调用 `_resolve_authorization_header()` 校验 API Key：
     - 如果 `ai_api_key` 为空，不加 Authorization 头。
     - 如果包含 `"替换为你的真实密钥"` 或非 ASCII 字符，抛出 `ValueError`。
     - 否则返回 `"Bearer {api_key}"`。
   - 构建请求体：
     ```json
     {
       "model": "MiniMax-M2.5",
       "messages": [{"role": "user", "content": [{"type": "text", "text": "..."}]}],
       "temperature": 0.1,
       "stream": false
     }
     ```
   - 使用 `httpx.AsyncClient(timeout=60.0)` 发送 POST 请求到 `llm_api_url`。
   - 解析响应：取 `data.choices[0].message.content`。
     - 如果 content 是字符串，直接使用。
     - 如果 content 是列表，拼接所有 text 项。
   - 记录耗时日志。
   - 返回 `ChatCompletionResponse(content=content, raw=data)`。

#### 步骤六：解析 LLM 输出

7. 调用 `_safe_parse_json(completion.content)` 从模型原始输出中提取 JSON：
   - 调用 `_extract_json_candidate_strings(content)` 提取所有可能的 JSON 片段：
     - 从 `"parse_status"` 位置向前找 `{`、向后找 `}`，提取候选。
     - 提取 ```json ... ``` 围栏中的内容。
     - 提取 ``` ... ``` 围栏中的内容。
     - 从第一个 `{` 到最后一个 `}` 提取候选。
     - 去重。
   - 对每个候选尝试 `json.loads()`：
     - 解析成功则调用 `_score_parsed_json_candidate()` 打分：
       - `parse_status == "success"` 加 20 分，`"need_confirm"` 加 10 分。
       - 有 metrics 每个加 4 分，filters 每个 6 分，group_by 每个 3 分，comparisons 每个 3 分。
       - 有 need_confirm_items 每个 2 分，unhandled_item 每个 1 分。
     - 如果候选的 `reasoning` 字段是字符串，递归从中提取更多 JSON 候选。
   - 选择得分最高的候选返回。
   - 如果所有候选都解析失败，返回默认兜底结构（`parse_status="need_confirm"`，`need_confirm_list=["模型输出未能成功解析为 JSON"]`）。

#### 步骤七：转换模型输出为 Pydantic 结构

8. 从提取的 JSON 中取出 `final_query` 字段（如果不是 dict 则用空字典）。
9. 调用 `_parse_comparison_specs(final_query)` 解析对比分析：
   - 兼容 `comparisons` 数组和单个 `comparison` 对象。
   - 对每个 comparison 调用 `_parse_single_comparison_spec()`：
     - 尝试用 `ComparisonSpec(**data)` 构造 Pydantic 对象。
     - 失败则忽略（ValidationError 静默处理）。
   - 去重。
10. 调用 `_merge_comparison_spec_lists(parsed_comparisons, derived_comparisons)` 合并模型输出和规则识别结果：
    - 对每个 parsed_comparison，查找是否有相同主题的 derived_comparison（`_is_same_comparison_topic()`）：
      - 同一 `comparison_type` 或相同 `raw_expression` 视为同主题。
      - 合并时优先保留两方的非空字段。
    - 未被匹配的 derived_comparison 直接追加到结果。
    - 最终去重。

11. 取合并后的第一个 comparison 作为 `primary_comparison`。
12. 调用 `_parse_field_refs()` 解析 metrics、filters、group_by：
    - 对每个字段引用调用 `_normalize_field_ref_item()` 归一化：
      - 运算符归一化：`equal`→`=`、`gt`→`>`、`gte`→`>=`、`lt`→`<`、`lte`→`<=` 等。
      - 值类型归一化：`string`→`text`、`numeric`→`number`、`datetime`→`date` 等。
    - 尝试用 `QueryFieldRef(**item)` 构造。
    - 如果是纯字符串，构造 `QueryFieldRef(field_name=item, standard_name=item)`。

#### 步骤八：生成 SQL 口径草案

13. 调用 `_build_sql_draft(payload, metrics, filters, group_by, comparisons)` 生成 SQL 口径草案：
    - 如果 metrics、filters、group_by、comparisons 全为空，返回 `None`。
    - 调用 `_select_time_field(payload.fields)` 选择时间字段：
      - 优先选 data_type 为 `datetime` 的字段。
      - 优先级关键词：下单日期、日期、时间、支付时间、发货日期、签收日期。
      - 都没有则取第一个 datetime 字段。
    - 对每个 metric 调用 `_build_sql_draft_metric()`：
      - 调用 `_infer_metric_aggregation(metric)` 推断聚合方式：
        - 包含订单数、客户数、人数等 → `count`（表达式 `COUNT(*)`）。
        - 包含率、均、平均、客单价 → `avg`。
        - 包含最大、最高 → `max`。
        - 包含最小、最低 → `min`。
        - 其他 → `sum`。
    - 对每个 filter 调用 `_build_sql_draft_condition()`：
      - 生成伪 SQL 条件表达式（支持 `BETWEEN`、`IN`、普通运算符）。
    - 收集 group_by 字段名列表。
    - 对每个 comparison 调用 `_build_sql_draft_comparison()`：
      - 生成对比口径说明和输出列（当前期值、基准值、差值、变化率）。
      - 趋势类型输出列为：趋势值、趋势变化率。
    - 构建输出列列表 `output_columns`。
    - 生成补充说明 `notes`。
    - 调用 `_build_sql_draft_pseudo_sql()` 生成伪 SQL：
      - `SELECT ... FROM table WHERE ... GROUP BY ...`。
      - 对比分析部分以注释形式附加。

14. 构造并返回 `ParseQueryResponse`。

**异常处理**：

| 异常类型 | HTTP 状态码 | 说明 |
|---|---|---|
| `ValueError` | 400 | 参数校验失败 |
| `httpx.ReadTimeout` | 502 | LLM 接口超时 |
| `httpx.HTTPStatusError` | 502 | LLM 接口返回异常状态码 |
| `httpx.HTTPError` | 502 | LLM 接口调用失败 |

---

### 5.1 `POST /api/llm/chat`

**定义位置**：`src/backend/app/api/routes/llm.py` → `chat()`

**服务层**：`src/backend/app/services/ai_gateway.py` → `AIGatewayService.chat()`

**作用**：通用 LLM 聊天补全接口，直接透传到外部 AI 模型。可用于自由对话或调试。

**请求类型**：`application/json`

**入参**：`ChatCompletionRequest`

```json
{
  "messages": [
    {"role": "user", "content": "你好，请介绍一下自己"}
  ],
  "temperature": 0.1,
  "stream": false
}
```

**入参字段说明**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `messages` | list[ChatMessage] | 是 | 无 | 消息列表 |
| `temperature` | float | 否 | `0.1` | 生成温度（0.0~2.0），越低越确定 |
| `stream` | bool | 否 | `false` | 是否流式输出（当前未实现流式） |

**`ChatMessage` 字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `role` | str | 角色：`user`、`assistant`、`system` |
| `content` | str 或 list[ChatContentBlock] | 消息内容，可以是纯文本或多模态内容块列表 |

**`ChatContentBlock`（多模态内容块）**：

| 类型 | 字段 | 说明 |
|---|---|---|
| `TextContentBlock` | `type: "text"`, `text: str` | 文本内容块 |
| `ImageContentBlock` | `type: "image_url"`, `image_url: {url: str}` | 图片 URL 内容块 |

**返回类型**：`ChatCompletionResponse`

```json
{
  "content": "你好！我是AI助手...",
  "raw": {
    "id": "chatcmpl-xxx",
    "choices": [...],
    "usage": {...}
  }
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `content` | str | 模型生成的文本内容 |
| `raw` | dict | 模型原始响应（完整 JSON） |

**代码执行流程**：

1. 路由层调用 `service.chat(payload)`。
2. `AIGatewayService.chat()` 执行（详细流程见 7.6 步骤五）：
   - 校验 API Key，构建请求头。
   - 构建请求体：把 `messages` 中每条消息的 `content` 转换为 `[{type: "text", text: ...}]` 格式。
   - 使用 `httpx.AsyncClient(timeout=60.0)` 发送 POST 请求。
   - 解析响应：取 `choices[0].message.content`。
   - 返回 `ChatCompletionResponse(content=content, raw=data)`。

**异常处理**：
- API Key 未配置或包含占位符 → 抛出 `ValueError`。
- HTTP 请求失败 → 抛出 `httpx.HTTPError` 或 `httpx.HTTPStatusError`。
- 超时 → 抛出 `httpx.ReadTimeout`。

---


## 8. xxxx

【根据项目代码情况编写，或根据用户追问进行添加改写】


## 9. xxxx

【根据项目代码情况编写，或根据用户追问进行添加改写】

