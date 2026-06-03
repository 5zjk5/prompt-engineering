import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests
import time
import re


def send_qq_email(to_address, subject, html_content):
    smtp_server = 'smtp.qq.com'
    smtp_port = 587

    sender_email = ''
    sender_password = ''

    message = MIMEMultipart()
    message['From'] = f'{sender_email}'
    message['To'] = to_address
    message['Subject'] = Header(subject, 'utf-8')

    html_part = MIMEText(html_content, 'html', 'utf-8')
    message.attach(html_part)

    try:
        print(f'正在连接SMTP服务器...')
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        print(f'SMTP连接成功，正在启动TLS...')
        server.starttls()
        print(f'TLS启动成功，正在登录...')
        server.login(sender_email, sender_password)
        print(f'登录成功，正在发送邮件...')
        server.sendmail(sender_email, to_address, message.as_string())
        print(f'邮件发送中...')
        server.quit()
        print(f'邮件发送成功！发送给: {to_address}')
    except smtplib.SMTPException as e:
        print(f'邮件发送失败: {str(e)}')
    except Exception as e:
        print(f'发送过程中出现错误: {str(e)}')


def get_api_content():
    try:
        print('正在调用API获取内容...')
        response = requests.get('https://127.0.0.1:7396/api/today_news', verify=False)
        # response = requests.get('https://www.muxiatong.top:7396/api/today_news')
        response.raise_for_status()
        data = response.json()
        content = data.get('today_news', '获取新闻失败')
        print(f'API调用成功，内容长度: {len(content)} 字符')
        return content
    except requests.exceptions.RequestException as e:
        print(f'API调用失败: {str(e)}')
        return f'API调用失败: {str(e)}'
    except Exception as e:
        print(f'解析数据失败: {str(e)}')
        return f'解析数据失败: {str(e)}'


def markdown_to_html(markdown_text):
    print(f'开始转换Markdown到HTML，文本长度: {len(markdown_text)} 字符')

    html = markdown_text

    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'<li>.*</li>(\n<li>.*</li>)+', r'<ul>\n\g<0>\n</ul>', html)

    html = re.sub(r'```(\w*)\n([\s\S]*?)\n```', r'<pre><code>\2</code></pre>', html)

    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    html = re.sub(
        r'^\*\*(.+?)\*\*$', r'<p><strong>\1</strong></p>', html, flags=re.MULTILINE
    )

    html = re.sub(r'\n', '<br>', html)

    print(f'Markdown转换完成，HTML长度: {len(html)} 字符')
    return html


if __name__ == '__main__':
    to_addrs = [

    ]

    print('程序启动...')

    # while True:
    #     try:
    #         print(f'\n========== 开始发送邮件 ==========')
    #         print(
    #             f'当前时间: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    #         )

    #         subject = f'【AI日报】{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}'

    #         markdown_content = get_api_content()
    #         print(f'今日内容：\n{markdown_content}')

    #         html_content = markdown_to_html(markdown_content)

    #         for addr in to_addrs:
    #             send_qq_email(addr, subject, html_content)

    #         print(f'========== 邮件发送完成 ==========\n')
    #         print(f'等待24小时后再次发送...')
    #         time.sleep(24 * 60 * 60)

    #     except Exception as e:
    #         print(f'发生异常: {str(e)}')
    #         print(f'等待1分钟后重试...')
    #         time.sleep(60)

    print(f'\n========== 开始发送邮件 ==========')
    print(
                f'当前时间: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
    subject = f'【AI日报】{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}'
    markdown_content = get_api_content()
    print(f'今日内容：\n{markdown_content}')
    html_content = markdown_to_html(markdown_content)
    for addr in to_addrs:
        send_qq_email(addr, subject, html_content)
    print(f'========== 邮件发送完成 ==========\n')
