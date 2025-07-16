from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.callbacks.base import BaseCallbackHandler
import os
import json

class StreamCallbackHandler(BaseCallbackHandler):
    """用于流式回调的处理器"""
    def __init__(self):
        self.tokens = []
        self.final_answer_started = False
        self.in_action_json = False
        self.action_json = ""
    
    def on_llm_new_token(self, token, **kwargs):
        """每有新token时被调用"""
        # 检测 "Final Answer:" 的开始
        if "Final answer:" in token:
            self.final_answer_started = True
            return
        
        # 检测 action JSON 块的开始
        if token.strip() == "{" and not self.final_answer_started:
            self.in_action_json = True
            self.action_json = "{"
            return
        
        # 收集 action JSON
        if self.in_action_json:
            self.action_json += token
            if token.strip() == "}" and self.action_json.count("{") <= self.action_json.count("}"):
                try:
                    # 解析完整json
                    action_data = json.loads(self.action_json)
                    if action_data.get("action") == "Final Answer":
                        final_answer = action_data.get("action_input", "No Answer")
                        # 将最终答案添加到tokens
                        for char in final_answer:
                            self.tokens.append(char)
                except json.JSONDecodeError:
                    pass      
                self.in_action_json = False
                self.action_json = "" 
            return

        # 如果错过Final Answer, 收集内容
        if self.final_answer_started:
            # 过滤掉不需要的标记或空白
            clean_token = token.strip()
            if token.strip() and not clean_token.startswith("Thought:") and not token.startswith("Action:"):
                for char in token:
                    self.tokens.append(char)

    def on_llm_end(self, response, **kwargs):
        """当模型生成结束时被调用"""
        pass

    def on_llm_error(self, error, **kwargs):
        self.tokens.append(f"Error:{error}")

def create_agent(streaming=False):
    callback_handler = StreamCallbackHandler() if streaming else None
    callbacks = [callback_handler] if streaming else None

    # 创建llm
    llm = ChatOpenAI(
        model=os.environ.get("LLM_MODELEND"),
        streaming=streaming,
        callbacks=callbacks
    )

    tools = load_tools(["wikipedia", "llm-math"], llm=llm)

    agent = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
        verbose=True
    )

    return agent, callback_handler

def get_simple_llm(streaming=False):
    callback_handler = StreamCallbackHandler() if streaming else None
    callbacks = [callback_handler] if streaming else None

    llm = ChatOpenAI(
        model = os.environ.get("LLM_MODELEND"),
        streaming=streaming,
        callbacks=callbacks,
    )

    return llm, callback_handler