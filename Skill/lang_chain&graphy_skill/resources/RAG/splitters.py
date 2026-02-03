# https://docs.langchain.com/oss/python/integrations/splitters

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter, 
    CharacterTextSplitter, 
    MarkdownHeaderTextSplitter,
    RecursiveJsonSplitter,
    Language
)


document = """
综合来看，袋鼠先生的鸡胸肉产品市场评价非常不错，是健康食品领域的知名品牌，尤其受到健身和减脂人群的青睐。

口感与质地： 多个评价都提到其口感“鲜嫩多汁”、“不柴不腻”。品牌采用了低温慢煮或蒸煮等先进工艺，能有效锁住鸡肉的水分，避免了传统水煮鸡胸肉容易变柴、干硬的问题，提升了食用体验。
口味选择： 提供多种口味，如原味、黑胡椒、奥尔良、香辣、孜然等，选择丰富，可以避免长期食用单一口味带来的乏味感。
营养与健康： 产品主打“低脂高蛋白”、“低热量”，符合健身增肌和减脂代餐的需求。原料选用优质鸡胸肉，脂肪含量低，蛋白质含量高。
食用便捷性： 产品为即食或加热即食，独立小包装，开袋即食，非常适合上班族、健身人群作为代餐或加餐，方便快捷。
综合评价： 在品质、口感、营养价值和便捷性方面表现均衡，是市场上广受好评的选择。如果您追求口感好、方便且营养的鸡胸肉产品，袋鼠先生是一个非常值得尝试的品牌。
中澜 水煮鸡胸肉
在您提供的现有资料中，没有关于“中澜”这个品牌水煮鸡胸肉的具体信息或用户评价。

这可能意味着以下几种情况：

品牌知名度较低： “中澜”可能是一个新兴品牌或区域性品牌，在主流电商平台和媒体上的曝光度和讨论度不高。
产品线不同： 该品牌可能不主打或不生产即食鸡胸肉产品。
信息不足： 目前缺乏足够的用户反馈和专业评测来判断其产品的品质、口感和性价比。
总结与建议：

袋鼠先生： 是一个经过市场验证的成熟品牌，其水煮鸡胸肉在口感、口味、营养和便利性上都有出色表现，推荐尝试。
中澜： 基于现有信息无法做出评价。如果您想尝试这个品牌，建议您在购买前：
查看电商平台（如京东、天猫）上的用户真实评价。
对比产品的营养成分表（重点关注蛋白质含量、脂肪含量、钠含量和添加剂）。
了解其加工工艺和原料来源。
总而言之，如果您在寻找一款可靠的即食水煮鸡胸肉，袋鼠先生是一个安全且高口碑的选择。对于“中澜”，则需要您自行收集更多信息后再做决定。
"""

"""
基于文本结构的
文本自然而然地组织成段落、句子和单词等层级单元
。我们可以利用这种固有的结构来指导我们的分割策略，创建能够保持自然语言流畅性、维持分割内部语义一致性并适应不同文本粒度级别的分割结果。
LangChainRecursiveCharacterTextSplitter正是实现了这一概念：
递归字符文本分割器会尝试保持较大的单元（例如，段落）完整。
如果一个单元超过块大小，它将移到下一级（例如，句子）。
如有必要，此过程会一直向下进行到单词级别。

对于大多数使用场景，建议首先使用RecursiveCharacterTextSplitter。它能够在保持上下文完整性和控制文本块大小之间取得良好的平衡
https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
"""
text_splitter = RecursiveCharacterTextSplitter(
    separators=["，"],
    chunk_size=100,  # 块的最大大小，优先保证块大小，再考虑 separators 中分割符号
    chunk_overlap=0, # 目标块之间的重叠。重叠的块有助于减少上下文在不同块之间分离时造成的信息丢失。
    length_function=len,  # 用于计算文本长度的函数。默认值为len，即Python的内置长度函数。
    is_separator_regex=False,  # 是否应将分隔符列表（默认为["\n\n", "\n", " ", ""]）解释为正则表达式。如果指定 sequence，则设置为 true
)
rec1_texts = text_splitter.split_text(document)  # 分割为多个文本块
rec2_texts = text_splitter.create_documents([document])  # 分割为多个 langchain 文档对象
pass


"""
基于长度
一种直观的策略是根据文档长度进行拆分。这种简单而有效的方法可以确保每个文件块的大小不超过指定限制。基于长度拆分文档的主要优点：
简单易行的实施
一致的块大小
可轻松适应不同模型的要求
基于长度的分割类型：
基于词元：根据词元数量分割文本，这在使用语言模型时非常有用。
按字符分割：根据字符数分割文本，这样在不同类型的文本中可以更加一致。
使用 LangChain 的 CharacterTextSplitter 进行基于词元的文本分割的示例实现：

按字符分割，可以自定义元数据，里面是字典
https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter

基于 nlp，模型分词，详见文档示例
https://docs.langchain.com/oss/python/integrations/splitters/split_by_token
"""
# 参数解释跟上面一样
text_splitter = CharacterTextSplitter(
    separator="，",
    chunk_size=50,
    chunk_overlap=2,
    length_function=len,
    is_separator_regex=False,
)
char_texts = text_splitter.create_documents([document], metadatas=[])
pass


"""
https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter
markdown 分割
"""
markdown_document = "# Foo\n\n    ## Bar\n\nHi this is Jim\n\nHi this is Joe\n\n ### Boo \n\n Hi this is Lance \n\n ## Baz\n\n Hi this is Molly"

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on,
    strip_headers=False,  # false 分割文本中保留 header
    return_each_line=True,  # true 不按照 header 进行分割，而是按照 \n 进行分割
)
md_header_splits = markdown_splitter.split_text(markdown_document)
pass



"""
它采用深度优先遍历 JSON 数据，并构建更小的 JSON 数据块。它会尽量保持嵌套 JSON 对象完整，
但如果需要，也会将其分割，以确保数据块的大小介于 `min_chunk_size` 和 `max_chunk_size` 之间。
如果值不是嵌套的 JSON，而是一个非常长的字符串，则该字符串不会被分割。如果您需要对数据块大小进行严格限制，请考虑使用递归文本分割器来分割这些数据块。
还有一个可选的预处理步骤，可以先将列表转换为 JSON（字典），然后再进行分割，从而实现列表的分割。
文本分割方式：json 值。
数据块大小的测量方式：按字符数计算。

https://docs.langchain.com/oss/python/integrations/splitters/recursive_json_splitter
"""
json_data = {
        "name": "张三",
        "age": 30,
        "city": "北京",
        "hobbies": ["篮球", "足球", "跑步"],
        "education": {
            "degree": "硕士",
            "major": "计算机科学与技术"
        }
}
splitter = RecursiveJsonSplitter(
    max_chunk_size=15,
    min_chunk_size=10,
)
json_chunks = splitter.split_json(
    json_data=json_data,
    convert_lists=True  # 默认情况下，json 分割器不会分割列表 convert_lists=True对 JSON 进行预处理，将列表内容转换为字典，index:item并将键值对转换为key:val字典
)
# docs = splitter.create_documents(texts=[json_data])  # langchain 文档对象
pass



"""
https://docs.langchain.com/oss/python/integrations/splitters/code_splitter#python
代码分割

[e.value for e in Language] 支持语言
"""
PYTHON_CODE = """
def hello_world():
    print("Hello, World!")

# Call the function
hello_world()
"""
python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON, chunk_size=50, chunk_overlap=0
)
python_docs = python_splitter.create_documents([PYTHON_CODE])
pass



"""
https://docs.langchain.com/oss/python/integrations/splitters/split_html#using-htmlheadertextsplitter
html 分割，那如果是读入 html 且只获得了其中文字，那可以不用这分割了
这分割对象是原始完整的 html
"""

