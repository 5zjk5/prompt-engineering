from enum import Enum
from langchain_community.document_loaders import PyPDFLoader, JSONLoader, BSHTMLLoader
from langchain_docling.loader import DoclingLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document


class ExportType(str, Enum):
    """Enumeration of available export types."""

    MARKDOWN = "markdown"
    DOC_CHUNKS = "doc_chunks"


class DataLoader:
    
    @classmethod
    def load_pdf(cls, file_path: str):
        loader = PyPDFLoader(
            file_path=file_path,
            mode="single",  # 提取模式，可以是"single"表示整个文档，或"page"表示分页提取。
        )
        docs = loader.load()
        # for doc in docs:
        #     doc.metadata = {
        #         'source': file_path,
        #         'page_label': doc.metadata.get('page_label'),
        #         'total_pages': doc.metadata.get('total_pages'),
        #     }  # 元数据设定字段，可添加需要的其他字段
        return docs

    @classmethod
    def load_docx(cls, file_path: str):
        loader = DoclingLoader(
            file_path=file_path,
            export_type=ExportType.MARKDOWN  # 不会分块，设定这个值
        )
        docs = loader.load()
        return docs

    @classmethod
    def load_csv(cls, file_path: str):
        loader = CSVLoader(
            file_path=file_path,
            csv_args={
                "delimiter": ",",  # 指定CSV文件中字段之间的分隔符
                "quotechar": '"',  # 指定用于引用字段的字符 当字段值中包含分隔符（逗号）时，可以使用双引号将字段值括起来
            },
            autodetect_encoding=True  # 中文自动编码
        )
        docs = loader.load()
        return docs

    @classmethod
    def load_html(cls, file_path: str):
        # 只提取了其中文字
        loader = BSHTMLLoader(
            file_path=file_path,
            open_encoding='utf8'
        )
        docs = loader.load()
        return docs

    @classmethod
    def load_json(cls, file_path: str):
        json_lines = True if 'jsonl' in file_path else False
        loader = JSONLoader(
            file_path=file_path,
            jq_schema=".",  # 提取所有字段
            text_content=False,
            json_lines=json_lines,
        )
        docs = loader.load()
        for doc in docs:
            doc.page_content = doc.page_content.encode().decode('unicode_escape')
        return docs


    @classmethod
    def load_markdown(cls, file_path: str):
        loader = DoclingLoader(
            file_path=file_path,
            export_type=ExportType.MARKDOWN  # 不会分块，设定这个值
        )
        docs = loader.load()
        return docs

    @classmethod
    def load_other(cls, file_path: str):
        with open(file_path, 'r', encoding='utf8') as f:
            content = f.read()
        docs = [
            Document(
                page_content=content,
                metadata={"source": file_path},
            ),
        ]
        return docs
