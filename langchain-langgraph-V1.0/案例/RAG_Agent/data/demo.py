# 读取jsonl（包括换行）
import json

def load_nonstandard_jsonl(file_path):
    """处理非标准的多行JSONL文件"""
    data_list = []
    current_obj = []
    in_object = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            
            if not stripped:  # 忽略空行
                continue
                
            if stripped == '{':
                in_object = True
                current_obj = [stripped]
            elif stripped == '}' and in_object:
                current_obj.append(stripped)
                try:
                    data = json.loads(''.join(current_obj))
                    data_list.append(data)
                except json.JSONDecodeError as e:
                    print(f"解析错误：{e}\n内容：{''.join(current_obj)}")
                in_object = False
            elif in_object:
                current_obj.append(stripped)
                
    return data_list

# 使用示例
data_list = load_nonstandard_jsonl("your_file.jsonl")



# 处理大模型生成json缺失括号的代码
import re

def convert_quotes(text):
    # 定义一个字典来存储需要保留双引号的情况
    special_chars = {':', '{', '}', ',', ' ', '[', ']', '\n'}
    
    # 定义一个函数来检查是否需要转换引号
    def replace_quotes(match):
        quote = match.group()
        start, end = match.start(), match.end()
        
        # 检查双引号前后是否有特殊字符
        if (start > 0 and text[start - 1] in special_chars) or \
           (end < len(text) and text[end] in special_chars):
            return quote
        else:
            # 否则将双引号替换为单引号
            return quote.replace('"', "'")
    
    # 使用正则表达式查找所有的双引号
    json_str = re.sub(r'"', replace_quotes, text)
    
    # 去掉 } 和 ] 前的逗号
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # 将{}前后的“”替换为"
    json_str = re.sub(r'”}', '"}', json_str)
    json_str = re.sub(r'\{“', '{"', json_str)
    
    return json_str