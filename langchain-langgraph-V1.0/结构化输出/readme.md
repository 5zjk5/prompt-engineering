# 结构化输出示例

本目录包含了多种结构化输出实现的示例代码，展示如何使用LangChain获取结构化的响应。

## 文件说明

### struct_define_1.py - Pydantic模型结构化输出
使用Pydantic BaseModel定义结构化输出格式，包含字段验证功能。通过`ToolStrategy(ProductReview)`指定输出格式，最终结果可通过`structured_response`字段获取。

### struct_define_2.py - 数据类结构化输出
使用Python数据类(@dataclass)定义结构化输出格式，提供类型注释。与Pydantic模型类似，通过`ToolStrategy(ProductReview)`指定输出格式。

### struct_define_3_output_json.py - TypedDict结构化输出
使用TypedDict定义结构化输出格式，最终输出为JSON格式。通过`ToolStrategy(ProductReview)`指定输出格式，结果为字典类型。

### struct_define_4.py - JSON Schema结构化输出
直接使用JSON Schema定义结构化输出格式，无需创建Python类。通过`ToolStrategy(product_review_schema)`指定输出格式，其中product_review_schema是JSON Schema字典。

### struct_define_5.py - 多模式结构化输出
支持从多个可能的输出模式中自动选择合适的结构。使用`Union[ProductReview, CustomerComplaint]`定义多个可能的输出模式，模型会根据输入内容自动选择最合适的结构。

### custom_define_tool_msg.py - 自定义工具消息内容
允许自定义生成结构化输出时对话历史记录中显示的消息。通过`tool_message_content`参数设置自定义消息内容，如"Action item captured and added to meeting notes!"。

### error_handle.py - 错误处理配置
展示如何配置结构化输出的错误处理方式。支持多种错误处理策略：
- 关闭错误处理（`handle_errors=False`）
- 自定义错误信息（`handle_errors="错误信息"`）
- 处理特定异常类型（`handle_errors=ValueError`）
- 自定义错误处理函数
