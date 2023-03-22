import numpy as np
import os
import re
import datetime
import time
import openai, tenacity
import argparse
import configparser
import json
import tiktoken
from get_paper_from_pdf import Paper
import gradio

# 定义Reviewer类
class Reviewer:
    # 初始化方法，设置属性
    def __init__(self, api, review_format, paper_pdf, language):
        self.api = api
        self.review_format = review_format

        self.language = language
    
        self.max_token_num = 4096
        self.encoding = tiktoken.get_encoding("gpt2")


    def review_by_chatgpt(self, paper_list):
        for paper_index, paper in enumerate(paper_list):
            sections_of_interest = self.stage_1(paper)
            # extract the essential parts of the paper
            text = ''
            try:
                text += 'Title:' + paper.title + '. '
                text += 'Abstract: ' + paper.section_texts['Abstract']
            except:
                pass
            intro_title = next((item for item in paper.section_names if 'ntroduction' in item.lower()), None)
            if intro_title is not None:
                text += 'Introduction: ' + paper.section_texts[intro_title]
            # Similar for conclusion section
            conclusion_title = next((item for item in paper.section_names if 'onclusion' in item), None)
            if conclusion_title is not None:
                text += 'Conclusion: ' + paper.section_texts[conclusion_title]
            for heading in sections_of_interest:
                if heading in paper.section_names:
                    text += heading + ': ' + paper.section_texts[heading]
            chat_review_text, total_token_used = self.chat_review(text=text)            
        return chat_review_text, total_token_used
            


    def stage_1(self, paper):
        htmls = []
        text = 'Abstract'
        paper_Abstract
        try:
            text += 'Title:' + paper.title + '. '
            paper_Abstract = paper.section_texts['Abstract']
            
        except:
            pass
        text += 'Abstract: ' + paper_Abstract
        openai.api_key = self.api
        messages = [
            {"role": "system",
             "content": f"You are a professional reviewer. "
                        f"I will give you a paper. You need to review this paper and discuss the novelty and originality of ideas, correctness, clarity, the significance of results, potential impact and quality of the presentation. "
                        f"Due to the length limitations, I am only allowed to provide you the abstract, introduction, conclusion and at most two sections of this paper."
                        f"Now I will give you the title and abstract and the headings of potential sections. "
                        f"You need to reply at most two headings. Then I will further provide you the full information, includes aforementioned sections and at most two sections you called for.\n\n"
                        f"Title: {paper.title}\n\n"
                        f"Abstract: {paper_Abstract}\n\n"
                        f"Potential Sections: {paper.section_names[2:-1]}\n\n"
                        f"Follow the following format to output your choice of sections:"
                        f"{{chosen section 1}}, {{chosen section 2}}\n\n"},
            {"role": "user", "content": text},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ''
        for choice in response.choices:
            result += choice.message.content
        # print(result)
        return result.split(',')

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)
    def chat_review(self, text):
        openai.api_key = self.api   # 读取api
        review_prompt_token = 1000        
        text_token = len(self.encoding.encode(text))
        input_text_index = int(len(text)*(self.max_token_num-review_prompt_token)/text_token)
        input_text = "This is the paper for your review:" + text[:input_text_index]
        messages=[
                {"role": "system", "content": "You are a professional reviewer. Now I will give you a paper. You need to give a complete review opinion according to the following requirements and format:"+ self.review_format +" Please answer in {}.".format(self.language)},
                {"role": "user", "content": input_text},
            ]
                
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ''
        for choice in response.choices:
            result += choice.message.content
        print("********"*10)
        print(result)
        print("********"*10)
        print("prompt_token_used:", response.usage.prompt_tokens)
        print("completion_token_used:", response.usage.completion_tokens)
        print("total_token_used:", response.usage.total_tokens)
        print("response_time:", response.response_ms/1000.0, 's')                    
        return result, response.usage.total_tokens        
                                        

def main(api, review_format, paper_pdf, language):  
    start_time = time.time()
    if not api or not review_format or not paper_pdf:
        return "请输入完整内容！"
    # 判断PDF文件
    else:
        paper_list = [Paper(path=paper_pdf)]
        # 创建一个Reader对象
        reviewer1 = Reviewer(api, review_format, paper_pdf, language)
        # 开始判断是路径还是文件：   
        comments, total_token_used = reviewer1.review_by_chatgpt(paper_list=paper_list)
    time_used = time.time() - start_time
    output2 ="使用token数："+ str(total_token_used)+"\n花费时间："+ str(round(time_used, 2)) +"秒"
    return comments, output2
        


########################################################################################################    
# 标题
title = "🤖ChatReviewer🤖"
# 描述

description = '''<div align='left'>
<img align='right' src='https://i.imgtg.com/2023/03/22/94PLN.png' width="270">

<strong>ChatReviewer是一款基于ChatGPT-3.5的API开发的论文自动评审AI助手。</strong>其用途如下：

⭐️对论文进行快速总结和评审，提高科研人员的文献阅读和理解的效率，紧跟研究前沿。

⭐️对自己的论文进行评审，根据ChatReviewer生成的审稿意见进行查漏补缺，进一步提高自己的论文质量。

⭐️辅助论文审稿，给出参考的审稿意见，提高审稿效率和审稿质量。（🈲：禁止用于未公开论文的评审！）

如果觉得很卡，可以请点击右上角的Duplicate this Space，把ChatReviewer复制到你自己的Space中！

本项目的[Github](https://github.com/nishiwen1214/ChatReviewer)，欢迎Star！（[如何获取Api Key](https://chatgpt.cn.obiscr.com/blog/posts/2023/How-to-get-api-key/)）
</div>
'''

# 创建Gradio界面
inp = [gradio.inputs.Textbox(label="请输入你的API-key(sk开头的字符串)",
                          default="",
                          type='password'),
    gradio.inputs.Textbox(
        label="请输入特定的评审要求和格式",
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
    gradio.inputs.File(label="请上传论文PDF(必填)"),
    gradio.inputs.Radio(choices=["English", "Chinese"],
                        default="English",
                        label="选择输出语言"),
]

chat_reviewer_gui = gradio.Interface(fn=main,
                                 inputs=inp,
                                 outputs = [gradio.Textbox(lines=22, label="评审结果"), gradio.Textbox(lines=2, label="资源统计")],
                                 title=title,
                                 description=description)

# Start server
chat_reviewer_gui .launch(quiet=True, show_api=False)