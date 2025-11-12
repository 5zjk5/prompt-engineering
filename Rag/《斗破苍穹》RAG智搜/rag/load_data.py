from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader


class DocsLoader():

    @classmethod
    def txt_loader(cls, filepath):
        """
        加载 txt 数据
        :param filepath:
        :return:
        """
        loader = TextLoader(filepath, encoding='utf8')
        docs = loader.load()
        return docs

    @classmethod
    def file_directory_loader(cls, filepath, glob="**/[!.]*", loader_cls=TextLoader, silent_errors=False, show_progress=True,
                              use_multithreading=True, max_concurrency=4, exclude=[], recursive=True):
        """
        https://python.langchain.com/docs/modules/data_connection/document_loaders/file_directory/
        根据目录加载里面所有数据，不会加载文件.rst或.html文件
        :param filepath:
        :param glob: 默认加载所有非隐藏文件
                    *.txt：只加载所有 txt
        :param loader_cls: 加载器，默认是 UnstructuredFileLoader，可以指定文本加载器（TextLoader）避免编码报错
        :param autodetect_encoding: 自动检测编码
        :param silent_errors: 跳过无法加载的文件并继续加载过程
        :param show_progress: 显示进度条
        :param use_multithreading: 多线程开启加载
        :param max_concurrency: 线程数量
        :param exclude: 指定不加的文件格式，列表格式
        :param recursive: 递归加载文件，目录下还有文件夹，加载里面的文件
        :return:
        """
        text_loader_kwargs = {'autodetect_encoding': True}
        loader = DirectoryLoader(filepath, glob=glob, loader_cls=loader_cls, silent_errors=silent_errors,
                                 loader_kwargs=text_loader_kwargs, show_progress=show_progress,
                                 use_multithreading=use_multithreading, max_concurrency=max_concurrency,
                                 exclude=exclude, recursive=recursive)
        docs = loader.load()
        return docs


    @classmethod
    def markdown_loader(cls, filepath, mode='single'):
        """
        https://python.langchain.com/docs/modules/data_connection/document_loaders/markdown/
        加载 markdown
        :param filepath:
        :param mode: 分割模式，single 全部合在一起，elements 把每一块都单独分开
        :return:
        """
        loader = UnstructuredMarkdownLoader(filepath, mode=mode)
        data = loader.load()
        return data

    @classmethod
    def pdf_loader(cls, filepath, extract_images=True, is_directory=False):
        """
        https://python.langchain.com/docs/modules/data_connection/document_loaders/pdf/
        加载 pdf，默认 page 是页码，但可能多出几页
        :param filepath:
        :param extract_images: 默认提取图片文字，是否提取 pdf 中的图片的文字
        :param is_directory: 如果传入进来是目录，加载此路径下的所有 pdf，但图片中的文字不能识别
        :return:
        """
        if is_directory:
            loader = PyPDFDirectoryLoader(filepath)
            docs = loader.load()
            return docs
        else:
            if extract_images:
                loader = PyPDFLoader(filepath, extract_images=extract_images)
            else:
                loader = PyMuPDFLoader(filepath)  # 最快的 PDF 解析选项，但不能提取图片中的文字
            pages = loader.load_and_split()
            return pages


    @classmethod
    def word_loader(cls, filepath, mode='single'):
        """
        https://python.langchain.com/docs/integrations/document_loaders/microsoft_word/
        :param filepath:
        :param mode: 分割模式，single 全部合在一起，elements 把每一页单独分开，不能识别图片文字
        :return:
        """
        loader = UnstructuredWordDocumentLoader(filepath, mode=mode)
        data = loader.load()
        return data

