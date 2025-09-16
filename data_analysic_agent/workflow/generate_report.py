import re
import random
import string
import os
import time
import requests
from logs.logger import logger
from llm.modelscope_api import modelscope_api
from prompt.summary import summary_prompt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
from output_report import pdf_save_fold


class GenerateReport:

    def __init__(self, dimension_conclusion):
        """
        初始化报告生成器
            Args:
                dimension_conclusion: 维度分析结果的列表
        """
        self.dimension_conclusion = dimension_conclusion

    def run(self):
        # 结论拼接
        concat_conclusion_str = conclusion_concat(self.dimension_conclusion)

        # 总结 markdown 数据
        logger.info("正在总结 markdown 数据.....")
        summary_str = summary(self.dimension_conclusion)

        # 拼接最后结论
        final_conclusion = """""# 数据报告\n----\n{String1}\n----\n{String2}"""
        final_conclusion = final_conclusion.format(String1=concat_conclusion_str, String2=summary_str)

        # 保存文件名
        file_name = time.time()

        # 保存 markdown
        logger.info("正在保存 markdown.....")
        save_markdown(final_conclusion, output_dir=pdf_save_fold, file_name=file_name)
        logger.info(f'✅ 数据分析报告 markdown 生成完成.....')

        # markdown to pdf
        # logger.info("正在 markdown to pdf.....")
        # convert_markdown_to_pdf(final_conclusion, output_dir=pdf_save_fold, file_name=file_name)
        # logger.info(f'✅ 数据分析报告 pdf 生成完成.....')


def conclusion_concat(dimension_conclusion):
    format_str = """\n# {String1}\n![{String3}]({String4})\n- {String2}"""
    concat_conclusion_str = ''
    for dc in dimension_conclusion:
        title = dc['title']
        txt = dc['txt']
        img_path = dc['save_path']

        # 路径特殊处理，markdown 不支持绝对路径
        directory, filename = os.path.split(img_path)
        img_path = os.path.join('../save_chart', filename)

        string = format_str.format(String1=title, String2=txt, String3=title, String4=img_path)
        concat_conclusion_str += string + '\n----'
    return concat_conclusion_str


def summary(dimension_conclusion):
    data = ''
    for dc in dimension_conclusion:
        outputmarkdown = dc['result']['markdown']
        data += outputmarkdown + '\n\n'
    prompt = summary_prompt.format(outmarkdown=data)
    content = modelscope_api(prompt)
    return content


class MarkdownToPDF:
    def __init__(self, output_path):
        self.c = canvas.Canvas(output_path, pagesize=A4)
        self.width, self.height = A4
        self.y = self.height - 50
        self.left_margin = 40
        self.line_height = 20
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        self.styles = {
            'normal': {
                'font': 'STSong-Light',
                'size': 12,
                'color': colors.black
            },
            'title': {
                'font': 'STSong-Light',
                'size': 16,
                'color': colors.black
            }
        }

    def download_image(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return ImageReader(BytesIO(response.content))
        except Exception as e:
            print(f"下载图片失败: {e}")
        return None

    def draw_image(self, url):
        img = self.download_image(url)
        if img:
            img_width = self.width - 2 * self.left_margin
            img_height = img_width * 0.5
            if self.y - img_height < 50:
                self.c.showPage()
                self.y = self.height - 50
            self.c.drawImage(img, self.left_margin, self.y - img_height, width=img_width, height=img_height)
            self.y -= (img_height + 20)

    def clean_text(self, text):
        if not text:
            return text

        # 处理换行符
        text = text.replace('\\n', '\n')

        # 移除HTML标签，保留内容
        text = re.sub(r'<[^>]+>', '', text)

        # 处理数字之间的空格
        text = re.sub(r'(\d+)\s+(\d+)', r'\1\2', text)

        # 处理连字符
        text = re.sub(r'\s*-\s*', '-', text)

        # 处理时间戳
        def format_date(match):
            try:
                timestamp = int(match.group(0))
                return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d %H:%M:%S')
            except:
                return match.group(0)

        text = re.sub(r'\b\d{10}\b', format_date, text)

        # 移除开头的特殊字符
        text = re.sub(r'^[^\w\s-]+', '', text)

        return text.strip()

    def draw_text_with_style(self, text, style='normal', x=None):
        if not text:
            return 0
        if x is None:
            x = self.left_margin
        style_config = self.styles[style]
        self.c.setFont(style_config['font'], style_config['size'])
        self.c.setFillColor(style_config['color'])
        self.c.drawString(x, self.y, text)
        return self.c.stringWidth(text, style_config['font'], style_config['size'])

    def draw_paragraph(self, text, is_list_item=False):
        if not text:
            return

        # 预处理文本
        text = self.clean_text(text)

        # 如果是空行，只添加间距
        if not text.strip():
            self.y -= self.line_height
            return

        x = self.left_margin
        if is_list_item:
            self.c.drawString(x, self.y, "•")
            x += 20

        current_x = x

        # 将文本按照实际换行符分割
        lines = text.split('\n')
        for line in lines:
            current_x = x
            words = list(line.strip())

            for word in words:
                word_width = self.c.stringWidth(word, self.styles['normal']['font'], self.styles['normal']['size'])

                if current_x + word_width > self.width - self.left_margin:
                    self.y -= self.line_height
                    current_x = x

                if self.y < 50:
                    self.c.showPage()
                    self.y = self.height - 50

                width = self.draw_text_with_style(word, 'normal', current_x)
                current_x += width

            self.y -= self.line_height

        self.y -= self.line_height * 0.5

    def process_markdown(self, markdown_text):
        lines = markdown_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.y -= self.line_height
                continue
            if line.startswith('# '):
                self.y -= 10
                self.draw_text_with_style(line[2:], 'title')
                self.y -= 20
                continue
            if '![' in line and '](' in line:
                match = re.search(r'!\[.*?\]\((.*?)\)', line)
                if match:
                    self.draw_image(match.group(1))
                continue
            if line.startswith('- '):
                self.draw_paragraph(line[2:], True)
                continue
            self.draw_paragraph(line)

    def save(self):
        self.c.save()


def generate_random_filename():
    letters = ''.join(random.choices(string.ascii_letters, k=6))
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{letters}{numbers}.pdf"


def convert_markdown_to_pdf(markdown_text, output_dir, file_name):
    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    while True:
        filename = generate_random_filename()
        output_path = os.path.join(output_dir, filename)
        if not os.path.exists(output_path):
            break

    pdf = MarkdownToPDF(output_path)
    pdf.process_markdown(markdown_text)
    pdf.save()


def save_markdown(final_conclusion, output_dir, file_name):
    with open(os.path.join(output_dir, f'{file_name}.md'), "w", encoding="utf-8") as f:
        f.write(final_conclusion)
