# coding:utf8
import os
from llm.llm_chain import str_chain
from llm.llm_glm import zhipu_glm_4


llm = zhipu_glm_4(temperature=0.5)


if __name__ == '__main__':
    file_list = os.listdir('../data/dataset/pdf_txt_file')
    save_path = '../data/dataset/pdf_txt_file_new'
    for index, file in enumerate(file_list):
        print(f'-------------{index}/{len(file_list)}-------------------')
        with open(os.path.join('../data/dataset/pdf_txt_file', file), 'r', encoding='utf-8') as f:
            all_text = f.read()
            f.seek(0)
            txt = f.readlines()
            txt = txt[:20] + txt[-20:]

        prompt = """
        阅读一下信息，判断是跟哪家公司相关的招股书，直接给我公司名称，如果没有公司名称则回复`无法判断`：
        ```
        {question}
        ```
        """
        try:
            company = str_chain(txt, prompt, llm)
        except:
            txt = txt[:20]
            company = str_chain(txt, prompt, llm)
        if '无法判断' in company:
            company = file.split('.')[0]
        company = company.replace('\n', '')
        print(f'公司-{company}')

        try:
            with open(os.path.join(save_path, company + '.txt'), 'w', encoding='utf8') as wf:
                wf.write(all_text)
        except:
            with open(os.path.join(save_path, file), 'w', encoding='utf8') as wf:
                wf.write(all_text)
