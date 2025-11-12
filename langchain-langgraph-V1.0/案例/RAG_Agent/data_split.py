import json
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveJsonSplitter,
    Language
)
from langchain_core.documents import Document


class DataSplit():

    @classmethod
    def split_md(cls, doc):
        markdown_document = doc.page_content
        _metadata = doc.metadata
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on,
            strip_headers=False,  # false 分割文本中保留 header
            return_each_line=False,  # true 不按照 header 进行分割，而是按照 \n 进行分割
        )
        md_splits = markdown_splitter.split_text(markdown_document)
        for _ in md_splits:
            _.metadata = _.metadata | _metadata
        return md_splits

    @classmethod
    def split_json(cls, doc):
        json_document = json.loads(doc.page_content.encode().decode('unicode_escape'))
        _metadata = doc.metadata
        json_splitter = RecursiveJsonSplitter(
            max_chunk_size=15,
            min_chunk_size=10,
        )
        json_splits = json_splitter.split_text(
            json_data=json_document,
            convert_lists=True  # 默认情况下，json 分割器不会分割列表 convert_lists=True对 JSON 进行预处理，将列表内容转换为字典，index:item并将键值对转换为key:val字典
        )
        doc_json = []
        for _ in json_splits:
            doc_json.append(
                Document(
                    page_content=_,
                    metadata=_metadata,
                )
            )
        return doc_json

    @classmethod
    def split_code(cls, doc):
        code_document = doc.page_content
        _metadata = doc.metadata
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=1000, chunk_overlap=20
        )
        python_docs = python_splitter.create_documents([code_document])
        for _ in python_docs:
            _.metadata = _.metadata | _metadata
        return python_docs

    @classmethod
    def split_other(cls, doc):
        page_content = doc.page_content
        _metadata = doc.metadata
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=512,  # 块的最大大小，优先保证块大小，再考虑 separators 中分割符号
            chunk_overlap=30,  # 目标块之间的重叠。重叠的块有助于减少上下文在不同块之间分离时造成的信息丢失。
            length_function=len,  # 用于计算文本长度的函数。默认值为len，即Python的内置长度函数。
            is_separator_regex=False,  # 是否应将分隔符列表（默认为["\n\n", "\n", " ", ""]）解释为正则表达式。如果指定 sequence，则设置为 true
        )
        chunks = text_splitter.create_documents([page_content])  # 分割为多个 langchain 文档对象
        for _ in chunks:
            _.metadata = _.metadata | _metadata
        return chunks
