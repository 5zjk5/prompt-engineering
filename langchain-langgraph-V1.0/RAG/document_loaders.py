"""
https://docs.langchain.com/oss/python/integrations/document_loaders

可以加载外部一些平台数据，键文档支持

这里只考虑常见格式
"""
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import JSONLoader, BSHTMLLoader
from langchain_docling.loader import DoclingLoader


# 加载每个文档仅包含一行的csv数据。
# 您还可以使用 . 加载表格UnstructuredCSVLoader。 键文档
# 使用 的一个优点UnstructuredCSVLoader是，如果您在"elements"模式下使用它，则表格的 HTML 表示形式将在元数据中可用。
loader = CSVLoader(
    file_path=r"langchain-langgraph-V1.0\RAG\demo.csv",
    source_column="MLB Team",  # source_column参数可指定从每一行创建的文档的来源。否则，file_path将使用 CSV 文件作为所有文档的来源。必须是存在的列名或重命名后的
    csv_args={
        "delimiter": ",",  # 指定CSV文件中字段之间的分隔符
        "quotechar": '"',  # 指定用于引用字段的字符 当字段值中包含分隔符（逗号）时，可以使用双引号将字段值括起来
        "fieldnames": ["MLB Team", "Payroll in millions"],  # 指定CSV文件中各列的名称，必须跟source_column参数指定的列名数量一致
    },
)
data = loader.load()
print(data)



"""
非结构化
https://docs.langchain.com/oss/python/integrations/document_loaders/unstructured_file#overview
本笔记本介绍了如何使用Unstructured 文档加载器加载多种类型的文件。Unstructured目前支持加载文本文件、PowerPoint 文件、HTML 文件、PDF 文件、图像文件等。
使用的第三方服务，需要 api，见文档
"""



"""
json
https://docs.langchain.com/oss/python/integrations/document_loaders/json#overview
"""
# json
loader = JSONLoader(
    file_path=r"langchain-langgraph-V1.0\RAG\demo.json",
    jq_schema=".",  # . 为加载所有内容
    text_content=False,
)
data1 = loader.load()
print(data1[0].page_content)
# jsonl
loader = JSONLoader(
    file_path="langchain-langgraph-V1.0\RAG\demo.jsonl",
    jq_schema=".name",  # 只提取 name 字段
    text_content=False,
    json_lines=True,  # 必选
)
docs = loader.load()
print(docs)
# 选择字段或者这样搭配提取
# jq_schema=".",
# content_key="sender_name",  # 从 sender_name 字段提取内容



"""
https://docs.langchain.com/oss/python/integrations/document_loaders/bshtml#adding-separator-to-bs4
"""
# loader = BSHTMLLoader(
#     file_path="./example_data/fake-content.html", get_text_separator=", "  # 分隔符
# )
# docs = loader.load()
# print(docs[0])



"""
可以将 PDF、DOCX、PPTX、HTML 和其他格式解析为丰富的统一表示形式，包括文档布局、表格等
https://docs.langchain.com/oss/python/integrations/document_loaders/docling#integration-details

file_path：源文件为单个字符串（URL 或本地文件）或其可迭代对象。
converter（可选）：要使用的任何特定 Docling 转换器实例
convert_kwargs（可选）：转换执行所需的任何特定关键字参数
export_type（可选）：要使用的导出模式：（ExportType.DOC_CHUNKS默认）或 ExportType.MARKDOWN
md_export_kwargs（可选）：任何特定的 Markdown 导出关键字参数（用于 Markdown 模式）
chunker（可选）：要使用的任何特定 Docling 分块器实例（用于文档分块模式）
meta_extractor（可选）：要使用的任何特定元数据提取器
"""
FILE_PATH = r"langchain-langgraph-V1.0\RAG\demo.docx"
loader = DoclingLoader(file_path=FILE_PATH)
docs = loader.load()
for d in docs[:3]:
    print(f"- {d.page_content=}")

