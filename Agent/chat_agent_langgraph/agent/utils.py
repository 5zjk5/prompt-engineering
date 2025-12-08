import base64
import io
from PIL import Image
from langchain_core.messages import HumanMessage


def compress_image_base64(
    base64_str, target_size_kb=100, max_quality=95, min_quality=10
):
    """
    压缩图片base64字符串到指定大小

    Args:
        base64_str (str): 图片的base64编码字符串
        target_size_kb (int): 目标大小，单位KB，默认100KB
        max_quality (int): 最大质量，默认95
        min_quality (int): 最小质量，默认10

    Returns:
        str: 压缩后的图片base64编码字符串
    """
    # 解码base64字符串
    img_data = base64.b64decode(base64_str)

    # 使用PIL打开图片
    img = Image.open(io.BytesIO(img_data))

    # 转换为RGB模式（如果需要）
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 初始质量设置为最大质量
    quality = max_quality

    # 二分查找最佳质量参数
    while quality >= min_quality:
        # 创建字节流
        buffer = io.BytesIO()

        # 保存图片到字节流
        img.save(buffer, format='JPEG', quality=quality)

        # 获取压缩后的大小
        compressed_size = len(buffer.getvalue()) / 1024  # 转换为KB

        # 如果大小符合要求，返回base64字符串
        if compressed_size <= target_size_kb:
            compressed_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return compressed_base64

        # 否则降低质量
        quality -= 5

    # 如果质量降到最低仍然大于目标大小，尝试缩小尺寸
    width, height = img.size
    scale_factor = 0.9  # 每次缩小10%

    while (width * height * scale_factor * scale_factor) > 0 and len(
        buffer.getvalue()
    ) / 1024 > target_size_kb:
        width = int(width * scale_factor)
        height = int(height * scale_factor)

        # 缩小图片
        resized_img = img.resize((width, height), Image.LANCZOS)

        # 保存缩小后的图片
        buffer = io.BytesIO()
        resized_img.save(buffer, format='JPEG', quality=min_quality)

        # 检查大小
        if len(buffer.getvalue()) / 1024 <= target_size_kb:
            compressed_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return compressed_base64

    # 如果所有方法都无法达到目标大小，返回最后一次尝试的结果
    compressed_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return compressed_base64


def get_messages(query, files):
    """
    生成包含图片和查询的消息列表

    Args:
        query (str): 用户查询
        files (list): 包含图片信息的列表，每个元素为字典，包含'file_name'和'base64'键

    Returns:
        list: 包含HumanMessage的列表，每个消息包含图片和查询
    """
    if not files:
        # 如果没有图片，直接返回查询消息
        return [HumanMessage(content=query)]

    # 如果有图片，创建一个包含所有图片和查询的消息
    content = []

    # 添加所有图片
    for file in files:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{compress_image_base64(file['img_base64'])}"},
            }
        )

    # 添加查询文本
    content.append({"type": "text", "text": query})

    # 返回包含所有图片和查询的单个消息
    return [HumanMessage(content=content)]
