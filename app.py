import os
import openai

def gpt(api_key):
    completion = openai.ChatCompletion.create(
     model="gpt-3.5-turbo", 
     messages=[{"role": "user", "content": "Generate a fake news story"}]
    )

return completion.choices[0].message.content

demo = gr.Interface(fn=gpt, inputs="text", outputs="text")
    
demo.launch()