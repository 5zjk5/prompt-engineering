from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import LangchainNodeParser
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core import load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.langchain import LangChainLLM
from llama_index.readers.json import JSONReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.tools import RetrieverTool
from llama_index.core.retrievers import RouterRetriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.postprocessor import KeywordNodePostprocessor
from llama_index.core import Document
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.postprocessor import LongContextReorder
from llama_index.core.postprocessor import SentenceEmbeddingOptimizer
import chromadb
import faiss
import os.path


class LoadModel():

    @classmethod
    def langchain_llm(cls):
        """
        https://docs.llamaindex.ai/en/stable/examples/llm/langchain/
        langchian 加载的模型，在 llmaindex 中使用，这里演示就使用通义
        设置为全局：
            from llama_index.core import Settings
            Settings.llm = LoadModel.langchain_llm()
        :return:
        """
        from langchain_community.llms import Tongyi
        DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
        model = Tongyi(temperature=1, model_name='qwen-7b-chat', dashscope_api_key=DASHSCOPE_API_KEY)
        llm = LangChainLLM(llm=model)
        return llm

    @classmethod
    def load_local_embedding_model(cls, embedding_model_path, device='cpu'):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/models/embeddings/
        加载本地向量模型
        设置为全局：
            from llama_index.core import Settings
            Settings.embed_model = LoadModel.load_local_embedding_model('../bge-small-zh-v1.5')
        :param embedding_model_path:
        :param device:
        :return:
        """
        embedding_model = HuggingFaceEmbedding(
            model_name=embedding_model_path, device=device
        )
        return embedding_model


class DocsLoader():

    @classmethod
    def directory_load(cls, directory_path, num_workers=4, recursive=True, input_files=None, exclude=None,
                       required_exts=None, num_files_limit=100, encoding='utf-8', file_metadata=None,
                       file_extractor=None):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/loading/simpledirectoryreader/
        加载指定目录下所有文件
        :param directory_path: 数据目录，目录下支持不同格式数据
        :param num_workers: 并行加载，进程数数据
        :param recursive: 子目录读取
        :param input_files: 传递文件路径列表，而不是所有文件 e.g [data/son/cat.csv, ....]
        :param exclude: 传递要排除的文件路径列表 e.g [data/son/cat.csv, ....] 参数不生效，不知道为什么
        :param required_exts: 加载具有这些扩展名的文件 [".pdf", ".docx"]
        :param num_files_limit: 加载的最大文件数量
        :param encoding: 编码
        :param file_metadata: 指定一个函数，该函数将读取每个文件并通过传递以下函数来提取附加到每个文件的结果对象的元数据，参数会报错，不知道为什么
        :param file_extractor: 指定的文件类型，自定义读取方式，详见文档
            如果只想单独加载某类文件，可以重写配置一下其他参数，并且使用这个参数设定加载方法，可以看官网加载器：
            https://llamahub.ai/
        :return:
        """
        reader = SimpleDirectoryReader(
            input_dir=directory_path,
            recursive=recursive,
            input_files=input_files,
            exclude=exclude,
            required_exts=required_exts,
            num_files_limit=num_files_limit,
            encoding=encoding,
            file_metadata=file_metadata,
            file_extractor=file_extractor
        )
        documents = reader.load_data(num_workers=num_workers)
        return documents

    @classmethod
    def json_load(cls, input_file, levels_back=None, collapse_length=None, ensure_ascii=False, is_jsonl=False,
                  clean_json=True, langchian_convert=False):
        """
        https://llamahub.ai/l/readers/llama-index-readers-json
        :param input_file:
        :param levels_back: JSON树中要返回的级别数。设置为0可遍历所有级别。默认值为“无”。
        :param collapse_length: JSON片段将在输出中折叠的最大字符数。默认值为“无”
        :param ensure_ascii: 如果为True，则确保输出是ASCII编码的。默认值为False。
        :param is_jsonl: 表示该文件为JSONL（JSON Lines）格式。默认值为False。
        :param clean_json: 如果为True，则从输出中删除仅包含格式的行。默认值为True。
        :param langchian_convert: 是否转换为 langchain 的 document 对象
        :return:
        """
        reader = JSONReader(
            # The number of levels to go back in the JSON tree. Set to 0 to traverse all levels. Default is None.
            levels_back=levels_back,
            # The maximum number of characters a JSON fragment would be collapsed in the output. Default is None.
            collapse_length=collapse_length,
            # If True, ensures that the output is ASCII-encoded. Default is False.
            ensure_ascii=ensure_ascii,
            # If True, indicates that the file is in JSONL (JSON Lines) format. Default is False.
            is_jsonl=is_jsonl,
            # If True, removes lines containing only formatting from the output. Default is True.
            clean_json=clean_json,
        )
        # Load data from JSON file
        documents = reader.load_data(input_file=input_file, extra_info={})
        if langchian_convert:
            documents = [
                doc.to_langchain_format()
                for doc in documents
            ]
        return documents


class TextSpliter():

    @classmethod
    def langchain_split(cls, docs, separator=["\n\n", "\n", " ", ""], chunk_size=100, chunk_overlap=20,
                               length_function=len, is_separator_regex=True):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#langchainnodeparser
        按照 chunk_size 字数分割，separator 不需要传，保持默认值即可
        多个字符拆分，separator 指定，符合列表中的字符就会被拆分
        这里以 langchian 中的 RecursiveCharacterTextSplitter 为例子，其他分割参考 langchain_module.py
        :param docs: 文档
        :param separator: 分割字符，默认以列表中的字符去分割 ["\n\n", "\n", " ", ""]
        :param chunk_size: 每块大小
        :param chunk_overlap: 允许字数重叠大小
        :param length_function:
        :param is_separator_regex:
        :return:
        """
        parser = LangchainNodeParser(RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # 指定每块大小
            chunk_overlap=chunk_overlap,  # 指定每块可以重叠的字符数
            length_function=length_function,
            is_separator_regex=is_separator_regex,
            separators=separator
        ))
        nodes = parser.get_nodes_from_documents(docs)
        return nodes

    @classmethod
    def sentence_splitter(cls, docs, chunk_size=100, chunk_overlap=20):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#sentencesplitter
        在尊重句子边界的同时分割文本，按照指定字数分割，也就是每个块字数可能呢会小于 chunk_size
        llmaindex 自带的按字数分割器
        :param docs:
        :param chunk_size: 字数大小
        :param chunk_overlap: 允许重叠数量
        :return:
        """
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        nodes = splitter.get_nodes_from_documents(docs)
        return nodes

    @classmethod
    def sentence_window_node_parser(cls, docs, window_size=3):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#sentencewindownodeparser
        https://docs.llamaindex.ai/en/stable/examples/node_postprocessor/MetadataReplacementDemo/
        不同之处在于它将所有文档拆分为单个句子。生成的节点还包含元数据中每个节点周围的句子“窗口”
        可以在将节点发送到 LLM 之前用其周围的上下文替换句子。
        :param docs:
        :return:
        """
        node_parser = SentenceWindowNodeParser.from_defaults(
            # how many sentences on either side to capture
            window_size=window_size,
            # the metadata key that holds the window of surrounding sentences
            window_metadata_key="window",
            # the metadata key that holds the original sentence
            original_text_metadata_key="original_sentence",
        )
        nodes = node_parser.get_nodes_from_documents(docs)
        return nodes

    @classmethod
    def semantic_splitter_node_parser(cls, docs, embedding_model, buffer_size=1, breakpoint_percentile_threshold=95):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#semanticsplitternodeparser
        语义分割器不是使用固定块大小对文本进行分块，而是使用嵌入相似性自适应地选择句子之间的断点。这确保了“块”包含语义上彼此相关的句子。
        :param docs:
        :param buffer_size: “评估语义相似性时要组合在一起的句子数。”子数。”“设置为1以单独考虑每个句子。”“设置为>1可将句子组合在一起。”
        :param breakpoint_percentile_threshold: “在之间必须超过的余弦相似性的百分比”“一组句子和下一个组成一个节点。这个越小”“数量为，将生成的节点越多”
        :param embedding_model:
        :return:
        """
        splitter = SemanticSplitterNodeParser(
            buffer_size=buffer_size,
            breakpoint_percentile_threshold=breakpoint_percentile_threshold,
            embed_model=embedding_model
        )
        nodes = splitter.get_nodes_from_documents(docs)
        return nodes


class Store():

    @classmethod
    def faiss_vector_db(cls, split_text, vector_db_path, d=512):
        """
        https://docs.llamaindex.ai/en/stable/examples/vector_stores/FaissIndexDemo/
        https://docs.llamaindex.ai/en/stable/module_guides/storing/save_load/
        faiss 向量存储，embedding 模型没有找到设置参数，文档也没有，只能是全局的，就不用传了
            Settings.embed_model = LoadModel.load_local_embedding_model('../bge-small-zh-v1.5')
        bug：
            https://github.com/run-llama/llama_index/issues/7511#issuecomment-1703941420
        :param split_text:
        :param vector_db_path:
        :param d: 维度，可以去 embedding 模型的 json 文件中看看，类似 max_seq_length 这样的字段
        :return:
        """
        if not os.path.exists(vector_db_path):
            print('创建向量库')
            faiss_index = faiss.IndexFlatL2(d)
            vector_store = FaissVectorStore(faiss_index=faiss_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex(
                split_text, storage_context=storage_context
            )
            index.storage_context.persist(vector_db_path)
        else:
            print('加载向量库')
            vector_store = FaissVectorStore.from_persist_dir(vector_db_path)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, persist_dir=vector_db_path
            )
            index = load_index_from_storage(storage_context=storage_context)
        return index

    @classmethod
    def chromadb_vector_db(cls, split_text, vector_db_path, embed_model):
        """
        https://docs.llamaindex.ai/en/stable/examples/vector_stores/ChromaIndexDemo/
        bug：
            https://github.com/run-llama/llama_index/issues/7511#issuecomment-1703941420
        :param split_text:
        :param vector_db_path:
        :param embed_model: embedding model
        :return:
        """
        if not os.path.exists(vector_db_path):
            print('创建向量库')
            db = chromadb.PersistentClient(path=vector_db_path)
            chroma_collection = db.get_or_create_collection("quickstart")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex(
                split_text, storage_context=storage_context, embed_model=embed_model
            )
        else:
            print('加载向量库')
            db = chromadb.PersistentClient(path=vector_db_path)
            chroma_collection = db.get_or_create_collection("quickstart")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            index = VectorStoreIndex.from_vector_store(
                vector_store, embed_model=embed_model,
            )
        return index


class Query():

    @classmethod
    def query_engine(cls, index, query, similarity_top_k=2, streaming=True):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/deploying/query_engine/usage_pattern/
        查询引擎
        针对数据提出问题，查询引擎接收自然语言查询，对数据检索，传给大模型然后输出，其实已经是 RAG 了
        但我感觉开始到最后输出比较慢，这是主要问题
        支持多种查询引擎，可以看文档，例如对 csv 用自然语言查询，这功能 langchian 也有，还不是很好用，简单的可以
        还有 聊天查询 也是一样的：
            https://docs.llamaindex.ai/en/stable/module_guides/deploying/chat_engines/
        :param index: 查询索引
        :return:
        """
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        response_synthesizer = get_response_synthesizer(
            response_mode="tree_summarize", streaming=streaming,
        )
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )
        response = query_engine.query(query)
        response.print_response_stream()  # 流失传输，模型没返回一个字就输出一个字
        return response

    @classmethod
    def base_retriver(cls, index, query):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/querying/retriever/
        基本检索，可以快速查看效果
        :param index:
        :param query:
        :return:
        """
        retriever = index.as_retriever()
        nodes = retriever.retrieve(query)
        return nodes

    @classmethod
    def bm25_retriever(cls, split_text, query, similarity_top_k=2):
        """
        https://docs.llamaindex.ai/en/stable/examples/retrievers/bm25_retriever/#bm25-retriever_1
        检索最相关的块
        :param split_text: 分块的数据
        :param query:
        :param similarity_top_k:
        :return:
        """
        retriever = BM25Retriever.from_defaults(nodes=split_text, similarity_top_k=similarity_top_k)
        nodes = retriever.retrieve(query)
        return nodes

    @classmethod
    def bm25_and_vector_retriever(cls, index, split_text, query, llm, similarity_top_k=2):
        """
        https://docs.llamaindex.ai/en/stable/examples/retrievers/bm25_retriever/#router-retriever-with-bm25-method
        bm25(针对分块的数据)+向量检索
        :param split_text: 分块的数据
        :param query:
        :param similarity_top_k:
        """
        vector_retriever = VectorIndexRetriever(index)
        bm25_retriever = BM25Retriever.from_defaults(nodes=split_text, similarity_top_k=similarity_top_k)

        retriever_tools = [
            RetrieverTool.from_defaults(
                retriever=vector_retriever,
                description="Useful in most cases",
            ),
            RetrieverTool.from_defaults(
                retriever=bm25_retriever,
                description="Useful if searching about specific information",
            ),
        ]
        retriever = RouterRetriever.from_defaults(
            retriever_tools=retriever_tools,
            llm=llm,
            select_multi=True,
        )
        nodes = retriever.retrieve(query)
        return nodes

    @classmethod
    def reciprocal_rerank_fusion_retriever(cls, index, query, similarity_top_k=2, num_queries=4):
        """
        https://docs.llamaindex.ai/en/stable/examples/retrievers/reciprocal_rerank_fusion/
        不知道为什么会卡住
        互惠重排序融合，会针对 query 生成多个描述，相当于对结果重新排序了
        组合来自多个查询和多个索引的检索结果。
        检索到的节点将按照Reciprocal Rerank Fusion本文所提出的算法进行重新排序。它提供了一种有效的方法，
        无需过多的计算或依赖外部模型来对检索结果进行重新排序
        :param index:
        :param query:
        :param similarity_top_k:
        :param num_queries: 生成的 query 总数量，set this to 1 to disable query generation
        :return:
        """
        vector_retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        bm25_retriever = BM25Retriever.from_defaults(
            docstore=index.docstore, similarity_top_k=similarity_top_k
        )
        retriever = QueryFusionRetriever(
            [vector_retriever, bm25_retriever],
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,  # set this to 1 to disable query generation
            mode="reciprocal_rerank",
            use_async=True,
            verbose=True,
            # query_gen_prompt="...",  # we could override the query generation prompt here
        )
        query_engine = RetrieverQueryEngine.from_args(retriever)
        response = query_engine.query(query)
        return response


class RetriverRank():

    @classmethod
    def langchain_retriver_convert_NodeWithScore(cls, langchin_retriver, query):
        """
        langchian 检索回来的想使用 llmaindex 的后排序，需要先转换为 llmaindex 中检索回来的对象 NodeWithScore才能用后排序
        :param langchin_retriver: langchian 检索回来的 Document 对象
        :param query:
        :return:
        """
        def bm25_retriever(nodes, query, nodes_len):
            retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=nodes_len)
            nodes = retriever.retrieve(query)
            return nodes
        # 先转换为 llmaindex 的 Document 对象
        text_list = [doc.page_content for doc in langchin_retriver]
        documents = [Document(text=t) for t in text_list]
        # 再转为 TextNode 对象
        parser = SentenceSplitter()
        nodes = parser.get_nodes_from_documents(documents)
        # 用 llmaindex 中的 bm25 做一个中间转换为 NodeWithScore
        nodes = bm25_retriever(nodes, query, len(nodes))

        return nodes

    @classmethod
    def similarity_node_postprocessor(cls, nodes, similarity_cutoff=0.7):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/#similaritypostprocessor
        检索后率相似度低的
        :param nodes: 检索结果
        :param similarity_cutoff: 相似分数
        :return:
        """
        postprocessor = SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
        return postprocessor.postprocess_nodes(nodes)

    @classmethod
    def keyword_node_postprocessor(cls, nodes, required_keywords=[], exclude_keywords=[], lang='zh'):
        """
        不能用，有问题
        用于确保某些关键字被排除或包含。
        https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/#keywordnodepostprocessor
        :param nodes:
        :param required_keywords: 要包含的关键字, 列表
        :param exclude_keywords: 要排除的关键字，列表
        :param lang: nlp 语言，en-英文，zh-中文
        :return:
        """
        postprocessor = KeywordNodePostprocessor(
            required_keywords=required_keywords, exclude_keywords=exclude_keywords, lang=lang
        )
        return postprocessor.postprocess_nodes(nodes)

    @classmethod
    def metadata_replacement_postprocessor(cls, nodes):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/#metadatareplacementpostprocessor
        用于用节点元数据中的字段替换节点内容。如果元数据中不存在该字段，则节点文本保持不变。
        与 结合使用时非常有用SentenceWindowNodeParser。
        :param nodes:
        :return:
        """
        postprocessor = MetadataReplacementPostProcessor(
            target_metadata_key="window",
        )
        return postprocessor.postprocess_nodes(nodes)

    @classmethod
    def longcontextreorder(cls, nodes):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/#longcontextreorder
        模型很难获取扩展上下文中心的重要细节。一项研究发现，当关键数据位于输入上下文的开头或结尾时，通常性能最佳。
        此外，随着输入上下文的延长，性能会显著下降，即使是为长上下文设计的模型也是如此。
        该模块将对检索到的节点进行重新排序，这在需要大量 top-k 的情况下非常有用。
        :param nodes:
        :return:
        """
        postprocessor = LongContextReorder()
        return postprocessor.postprocess_nodes(nodes)

    @classmethod
    def sentenceembeddingoptimizer(cls, nodes, embed_model, percentile_cutoff=0.5, threshold_cutoff=0.7):
        """
        https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/#sentenceembeddingoptimizer
        :param nodes:
        :param embed_model:
        :param percentile_cutoff: 这意味着前（50%默认值）的句子将被使用。
        :param threshold_cutoff: 高于这个分数才使用
            两个参数可以一起用
        :return:
        """
        postprocessor = SentenceEmbeddingOptimizer(
            embed_model=embed_model,
            percentile_cutoff=percentile_cutoff,
            threshold_cutoff=threshold_cutoff
        )
        return postprocessor.postprocess_nodes(nodes)
