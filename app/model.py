import json, os, re, time, pathlib, sys
from typing import List, Dict
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import os


client = OpenAI(
    api_key = os.getenv("QWEN_KEY"),
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
# qwen_key = os.getenv("QWEN_KEY")
# openai.api_key  = os.getenv("QWEN_KEY")
# MODEL_NAME      = "qwen-vl-plus"       # 改成控制台里实际可用的名字
JSON_IN         = r"E:\NLP_Model\ai_edu\data\processed_data\taizhou2023_questions.json"
JSON_OUT        = r"E:\NLP_Model\ai_edu\data\processed_data\taizhou2023_tagged.json"
IMAGE_DIR       = pathlib.Path(r"E:\NLP_Model\ai_edu\data\processed_data\images")  # 所有图片都在此

# ---------- Prompt 模板 ----------
PROMPT_TMPL = """### 任务
你是一名资深中学数学命题专家，只需判断“题目”所属的【一级知识模块】：
1. 数与代数     核心：实数运算、代数式变换、方程与不等式、函数体系
2. 图形与几何   核心：平面几何性质、图形变换、坐标系应用
3. 统计与概率   核心：数据统计方法、概率模型
4. 综合与实践   核心：数学建模、跨学科应用

**注意**  
- 只选以上 4 个标签之一，不能自创标签。  
- 二级 / 三级 / 难度题型字段暂时留空，占位即可。  
- 必须输出 **严格一行 JSON**，键名固定为 "L1" "L2" "L3" "L4" ，其余不得包含任何多余字符。

**输出示例**  
{{"L1":"图形与几何","L2":"","L3":"","L4":""}}

### 题目
{QUESTION_BLOCK}

### 开始回答：
"""

_rd_img = re.compile(r"\[IMG:([^\]]+?)\]")

def placeholder_to_md(text: str) -> str:
    """
    把 [IMG:xxx.png] → ![](images/xxx.png)
    """
    def _repl(m):
        fname = m.group(1)
        return f"![]({IMAGE_DIR / fname})"
    return _rd_img.sub(_repl, text)

def build_question_block(q: Dict) -> str:
    """
    用题干 + 选项拼出给 LLM 的 markdown 区块
    """
    body = placeholder_to_md(q["content"])
    if q.get("options"):
        opts = "\n".join(o["text"] for o in q["options"])
        return f"{body}\n\n**选项**\n{opts}"
    return body

def call_llm(prompt: str, max_retry: int = 3) -> str:
    """
    调 OpenAI ChatCompletion，遇到 429/500 等自动重试
    """
    for i in range(max_retry):
        try:
            resp = client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            print(resp.choices[0].message.content.strip())
            return resp.choices[0].message.content.strip()
        except Exception as e: 
            if i == max_retry - 1:
                raise
            # 指数退避
            wait = 2 ** i
            print(f"[warn] {e}. retry in {wait}s …", file=sys.stderr)
            time.sleep(wait)

def clean_json_block(s: str) -> str:
    """
    清理模型返回的 JSON 字符串，去掉开头的 ```json 或 ```，以及结尾的 ```
    """
    return re.sub(r"^```json|^```|```$", "", s.strip(), flags=re.MULTILINE).strip()

def safe_json_line(s: str) -> Dict:
    """
    从模型返回的单行 JSON 字符串解析成 dict；
    若解析失败则返回占位空标签
    """
    try:
        s_clean = clean_json_block(s)
        obj = json.loads(s_clean)
        for k in {"L1","L2","L3","L4"}:
            if k not in obj:
                obj[k] = ""
        return obj
    except Exception:
        pass
    return {"L1":"", "L2":"", "L3":"", "L4":""}

def main():
    questions: List[Dict] = json.load(open(JSON_IN, encoding="utf-8"))
    for q in tqdm(questions, desc="Tagging"):
        prompt = PROMPT_TMPL.format(QUESTION_BLOCK=build_question_block(q))
        # print(prompt)
        raw = call_llm(prompt)
        q["label"] = safe_json_line(raw)
    
    # print(json.dumps(questions, ensure_ascii=False, indent=2))
    json.dump(questions, open(JSON_OUT,"w",encoding="utf8"),
              ensure_ascii=False, indent=2)
    print(f"共处理 {len(questions)} 道题。")

if __name__ == "__main__":
    main()