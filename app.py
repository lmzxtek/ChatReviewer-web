import gradio as gr

def greet(name):
    return "Hello " + name + "!!"

iface = gr.Interface(fn=greet, inputs1="text", inputs2="text", outputs="text")
iface.launch()