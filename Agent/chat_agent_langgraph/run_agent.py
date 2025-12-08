import asyncio
import base64
from PIL import Image
from agent.agent import create_agent_graph
from agent.state import AgentInputState
from config.config import llm_text, llm_img
from agent.configuration import Configuration
from agent.utils import get_messages


def image_to_base64(image_path):
    """
    打开图片并返回base64编码的字符串

    Args:
        image_path (str): 图片文件路径

    Returns:
        str: 图片的base64编码字符串
    """
    try:
        # 打开图片
        with Image.open(image_path) as img:
            # 将图片转换为字节流
            import io

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            # 获取图片的字节数据
            img_byte = buffered.getvalue()
            # 将字节数据转换为base64编码
            img_base64 = base64.b64encode(img_byte).decode('utf-8')
            return img_base64
    except Exception as e:
        print(f"打开图片时出错: {e}")
        return None


async def main():
    """主函数，用于单独运行agent"""
    agent_graph = create_agent_graph()

    # 打开图片
    image_path_1 = "C:\\Users\\zhoujk2\\Desktop\\1.png"
    image_base64_1 = image_to_base64(image_path_1)
    image_path_2 = "C:\\Users\\zhoujk2\\Desktop\\下载.jpg"
    image_base64_2 = image_to_base64(image_path_2)
    files = [
        {"img_name": image_path_1.split("\\")[-1], "img_base64": image_base64_1},
        {"img_name": image_path_2.split("\\")[-1], "img_base64": image_base64_2},
    ]

    llm = llm_img if files else llm_text

    query = '图片中讲了什么？'
    messages = get_messages(query, files)

    # 测试运行
    input_state = AgentInputState(messages=messages)
    result = await agent_graph.ainvoke(input_state, context=Configuration(llm=llm))
    print("非流式测试结果:\n", result['messages'][-1].content)

    print('流式测试结果:')
    async for chunk in agent_graph.astream(
        {"messages": messages},
        stream_mode="messages",
        context=Configuration(llm=llm),
    ):
        print(chunk[0].content, end='')


if __name__ == "__main__":
    asyncio.run(main())
