from app import create_app
from flask import Flask, request, jsonify, render_template
from langchain_openai import ChatOpenAI
import os

# app = Flask(__name__)
app = create_app()
llm = ChatOpenAI(model=os.environ.get("LLM_MODELEND"))

# 获得问题
def get_question(data):
    return data.get('question')
# llm输出
def Get_chat_response(question):
    return llm.predict(question)
# 表单异步请求
def handle_post_request(data):
    question = get_question(data)
    response = Get_chat_response(question)
    return jsonify({
        'status': 'success',
        'response': response
    })

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        return handle_post_request(data)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    # print(Get_chat_response('法国的首都在哪?'))