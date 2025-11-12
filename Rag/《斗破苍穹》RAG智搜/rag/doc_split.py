from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextSpliter():

    @classmethod
    def text_split_by_manychar_or_charnum(cls, docs, separator=["\n\n", "\n", " ", ""], chunk_size=100, chunk_overlap=20,
                               length_function=len, is_separator_regex=True):
        """
        https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter/
        按照 chunk_size 字数分割，separator 不需要传，保持默认值即可
        多个字符拆分，separator 指定，符合列表中的字符就会被拆分
        :param docs: 文档，必须为 str，如果是 langchain 加载进来的需要转换一下
        :param separator: 分割字符，默认以列表中的字符去分割 ["\n\n", "\n", " ", ""]
        :param chunk_size: 每块大小
        :param chunk_overlap: 允许字数重叠大小
        :param length_function:
        :param is_separator_regex:
        :return:
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # 指定每块大小
            chunk_overlap=chunk_overlap,  # 指定每块可以重叠的字符数
            length_function=length_function,
            is_separator_regex=is_separator_regex,
            separators=separator  # 指定按照什么字符去分割，如果不指定就按照 chunk_size +- chunk_overlap（100+-20）个字去分割
        )
        docs = docs.page_content  # langchian 加载的 txt 转换为 str
        split_text = text_splitter.create_documents([docs])
        return split_text

    @classmethod
    def semantic_chunker_split(cls, txt, embedding_model, breakpoint_threshold_type="percentile"):
        """
        https://python.langchain.com/docs/modules/data_connection/document_transformers/semantic-chunker/
        语义分块
        :param txt: txt 字符串
        :param embedding_model:
        :param breakpoint_threshold_type: 分割断点
            percentile：默认的分割方式是基于百分位数。在此方法中，计算句子之间的所有差异，然后分割任何大于 X 百分位数的差异
            standard_deviation：任何大于 X 个标准差的差异都会被分割。
            interquartile：使用四分位数距离来分割块
        :return:
        """
        text_splitter = SemanticChunker(embedding_model, breakpoint_threshold_type=breakpoint_threshold_type)
        docs = text_splitter.create_documents([txt])
        return docs