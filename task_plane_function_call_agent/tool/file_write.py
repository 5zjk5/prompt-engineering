
def write_to_txt(text, file_name='res.txt'):
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(text)
    return f'文件已成功写入，文件名 {file_name}'
