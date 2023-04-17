import numpy as np
import os
import re
from io import BytesIO
import datetime
import time
import openai, tenacity
import argparse
import configparser
import json
import tiktoken
import PyPDF2
import gradio

# 定义Reviewer类
class Reviewer:
    # 初始化方法，设置属性
    def __init__(self, api, review_format, paper_pdf, language):
        self.api = api
        self.review_format = review_format

        self.language = language
        self.paper_pdf = paper_pdf
        self.max_token_num = 4097
        self.encoding = tiktoken.get_encoding("gpt2")


    def review_by_chatgpt(self, paper_list):
        text = self.extract_chapter(self.paper_pdf)
        chat_review_text, total_token_used = self.chat_review(text=text)            
        return chat_review_text, total_token_used

   

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)
    def chat_review(self, text):
        openai.api_key = self.api   # 读取api
        review_prompt_token = 1000        
        text_token = len(self.encoding.encode(text))
        input_text_index = int(len(text)*(self.max_token_num-review_prompt_token)/(text_token+1))
        input_text = "This is the paper for your review:" + text[:input_text_index] "(This text is generated by ChatGPT for reference only, strain to copy!)"
        messages=[
                {"role": "system", "content": "You are a professional reviewer. Now I will give you a paper. You need to give a complete review opinion according to the following requirements and format:"+ self.review_format +" Must be output in {}.".format(self.language)},
                {"role": "user", "content": input_text},
            ]
                
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ''
        for choice in response.choices:
            result += choice.message.content + "\n\n⚠伦理声明/Ethics statement：\n--禁止直接复制生成的评论用于任何论文审稿工作！\n--Direct copying of generated comments for any paper review work is prohibited!"
        print("********"*10)
        print(result)
        print("********"*10)
        print("prompt_token_used:", response.usage.prompt_tokens)
        print("completion_token_used:", response.usage.completion_tokens)
        print("total_token_used:", response.usage.total_tokens)
        print("response_time:", response.response_ms/1000.0, 's')    
        output_text = insert_sentence(result, '(Generated by ChatGPT, no copying allowed!)', 10)
        return result, response.usage.total_tokens        

    def insert_sentence(text, sentence, interval):
        words = text.split()
        new_words = []
        count = 0
    
        for word in words:
            new_words.append(word)
            count += 1
    
            if count % interval == 0:
                new_words.append(sentence)
    
        return ' '.join(new_words)
        
        

    def extract_chapter(self, pdf_path):
        file_object = BytesIO(pdf_path)
        pdf_reader = PyPDF2.PdfReader(file_object)
        # 获取PDF的总页数
        num_pages = len(pdf_reader.pages)
        # 初始化提取状态和提取文本
        extraction_started = False
        extracted_text = ""
        # 遍历PDF中的每一页
        for page_number in range(num_pages):
            page = pdf_reader.pages[page_number]
            page_text = page.extract_text()

            # 如果找到了章节标题，开始提取
            if 'Abstract'.lower() in page_text.lower() and not extraction_started:
                extraction_started = True
                page_number_start = page_number
            # 如果提取已开始，将页面文本添加到提取文本中
            if extraction_started:
                extracted_text += page_text
                # 如果找到下一章节标题，停止提取
                if page_number_start + 1 < page_number:
                    break
        return extracted_text

def main(api, review_format, paper_pdf, language):  
    start_time = time.time()
    if not api or not review_format or not paper_pdf:
        return "请输入完整内容！"
    # 判断PDF文件
    else:
        # 创建一个Reader对象
        reviewer1 = Reviewer(api, review_format, paper_pdf, language)
        # 开始判断是路径还是文件：   
        comments, total_token_used = reviewer1.review_by_chatgpt(paper_list=paper_pdf)
    time_used = time.time() - start_time
    output2 ="使用token数："+ str(total_token_used)+"\n花费时间："+ str(round(time_used, 2)) +"秒"
    return comments, output2
        


########################################################################################################    
# 标题
title = "🤖ChatReviewer🤖"
# 描述

description = '''<div align='left'>
<img align='right' src='http://i.imgtg.com/2023/03/22/94PLN.png' width="270">

<strong>ChatReviewer是一款基于ChatGPT-3.5的API开发的论文自动评审AI助手。</strong>其用途如下：

⭐️对论文进行快速总结和评审，提高科研人员的文献阅读和理解的效率，紧跟研究前沿。

⭐️对自己的论文进行评审，根据ChatReviewer生成的审稿意见进行查漏补缺，进一步提高自己的论文质量。

⭐️辅助论文审稿，给出参考意见，提高审稿效率和质量。（🈲：禁止直接复制生成的评论用于任何论文审稿工作！）

如果觉得很卡，可以点击右上角的Duplicate this Space，把ChatReviewer复制到你自己的Space中！

本项目的[Github](https://github.com/nishiwen1214/ChatReviewer)，欢迎Star和Fork，也欢迎大佬赞助让本项目快速成长！💗（[获取Api Key](https://chatgpt.cn.obiscr.com/blog/posts/2023/How-to-get-api-key/)）
</div>
'''

# 创建Gradio界面
inp = [gradio.inputs.Textbox(label="请输入你的API-key(sk开头的字符串)",
                          default="",
                          type='password'),
    gradio.inputs.Textbox(lines=5,
        label="请输入特定的评审要求和格式(否则为默认格式)",
        default="""* Overall Review
Please briefly summarize the main points and contributions of this paper.
xxx
* Paper Strength 
Please provide a list of the strengths of this paper, including but not limited to: innovative and practical methodology, insightful empirical findings or in-depth theoretical analysis, 
well-structured review of relevant literature, and any other factors that may make the paper valuable to readers. (Maximum length: 2,000 characters) 
(1) xxx
(2) xxx
(3) xxx
* Paper Weakness 
Please provide a numbered list of your main concerns regarding this paper (so authors could respond to the concerns individually). 
These may include, but are not limited to: inadequate implementation details for reproducing the study, limited evaluation and ablation studies for the proposed method, 
correctness of the theoretical analysis or experimental results, lack of comparisons or discussions with widely-known baselines in the field, lack of clarity in exposition, 
or any other factors that may impede the reader's understanding or benefit from the paper. Please kindly refrain from providing a general assessment of the paper's novelty without providing detailed explanations. (Maximum length: 2,000 characters) 
(1) xxx
(2) xxx
(3) xxx
* Questions To Authors And Suggestions For Rebuttal 
Please provide a numbered list of specific and clear questions that pertain to the details of the proposed method, evaluation setting, or additional results that would aid in supporting the authors' claims. 
The questions should be formulated in a manner that, after the authors have answered them during the rebuttal, it would enable a more thorough assessment of the paper's quality. (Maximum length: 2,000 characters)
*Overall score (1-10)
The paper is scored on a scale of 1-10, with 10 being the full mark, and 6 stands for borderline accept. Then give the reason for your rating.
xxx"""
    ),
    gradio.inputs.File(label="请上传论文PDF(必填)",type="bytes"),
    gradio.inputs.Radio(choices=["English", "Chinese"],
                        default="English",
                        label="选择输出语言"),
]

chat_reviewer_gui = gradio.Interface(fn=main,
                                 inputs=inp,
                                 outputs = [gradio.Textbox(lines=25, label="评审结果"), gradio.Textbox(lines=2, label="资源统计")],
                                 title=title,
                                 description=description)

# Start server
chat_reviewer_gui .launch(quiet=True, show_api=False)