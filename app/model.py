import json, os, re, time, pathlib, sys
from typing import List, Dict
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import os

total_prompt_tokens = 0
total_completion_tokens = 0
total_tokens = 0

client = OpenAI(
    api_key = os.getenv("QWEN_KEY"),
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
# qwen_key = os.getenv("QWEN_KEY")
# openai.api_key  = os.getenv("QWEN_KEY")
# MODEL_NAME      = "qwen-vl-plus"       # 改成控制台里实际可用的名字
JSON_IN         = r"E:\NLP_Model\ai_edu\data\processed_data\nantong2021_questions.json"
JSON_OUT        = r"E:\NLP_Model\ai_edu\data\processed_data\taizhou2023_tagged2.json"
IMAGE_DIR       = pathlib.Path(r"E:\NLP_Model\ai_edu\data\processed_data\images")  # 所有图片都在此

# ---------- Prompt 模板 ----------
PROMPT_TMPL = """### 任务
你是一名资深中学数学命题专家，需要对题目进行两个维度的标签分类：知识点维度和题目类型维度。

**第一维度：知识点分类（必须全部填写）**
L1：固定为"知识点"
L2：一级知识点（选择一个）
- 数与代数
- 图形与几何
- 统计与概率
- 综合与实践

L3：二级知识点（根据L2选择）
当L2为"数与代数"时：
- 数与式
- 方程与不等式
- 函数

当L2为"图形与几何"时：
- 图形的性质
- 图形的变换
- 图形与坐标

当L2为"统计与概率"时：
- 数据分析
- 概率初步

当L2为"综合与实践"时：
- 数学建模

L4：三级知识点（根据L3选择）
- 数与式下：有理数运算、实数性质、代数式化简、因式分解、二次根式
- 方程与不等式下：一元一次方程、二元一次方程组、分式方程、一元二次方程、不等式(组)
- 函数下：一次函数、反比例函数、二次函数、函数图像与性质
- 图形的性质下：三角形(全等、相似、勾股定理)、四边形(平行四边形、矩形、菱形)、圆的性质与计算
- 图形的变换下：平移、旋转、轴对称、中心对称、投影与视图
- 图形与坐标下：平面直角坐标系、距离公式、函数与几何结合
- 数据分析下：平均数/中位数/众数、方差/极差、统计图表(条形图、扇形图)
- 概率初步下：随机事件概率、列举法求概率、频率估计概率
- 数学建模下：实际应用问题(行程、利润、工程)、跨学科整合

**第二维度：题目类型分类（必须全部填写）**
T1：固定为"题目类型"
T2：一级题目类型（选择一个）
- 客观题
- 解答题

T3：二级题目类型（根据T2选择）
当T2为"客观题"时：
- 选择题
- 填空题

当T2为"解答题"时：
- 计算证明题
- 综合应用题
- 探究创新题

T4：三级题目类型（根据T3选择）
- 选择题下：概念辨析、计算求解、图像判断、逻辑推理
- 填空题下：直接计算、规律探究、开放设问
- 计算证明题下：代数运算、几何证明、方程求解
- 综合应用题下：实际情境建模、图表分析、方案设计
- 探究创新题下：动态几何问题、存在性问题、最值问题、新定义题型

**注意事项**:  
- 必须输出**严格一行 JSON**，键名固定为 "L1", "L2", "L3", "L4", "T1", "T2", "T3", "T4"
- 所有键都必须有值，不允许出现空值或未分类情况
- 所有标签都必须从上述体系中选择，不能自创标签

**输出示例**:  
{{"L1":"知识点","L2":"图形与几何","L3":"图形的性质","L4":"三角形(全等、相似、勾股定理)","T1":"题目类型","T2":"解答题","T3":"计算证明题","T4":"几何证明"}}

### 题目
{QUESTION_BLOCK}

### 开始回答（仅输出一行JSON）:
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
    global total_completion_tokens, total_prompt_tokens, total_tokens

    for i in range(max_retry):
        try:
            resp = client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            if hasattr(resp, 'usage') and resp.usage:
                prompt_tokens = resp.usage.prompt_tokens
                completion_tokens = resp.usage.completion_tokens
                total_tokens_used = resp.usage.total_tokens

                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                total_tokens += total_tokens_used
                print(f"本次请求tokens: 提示={prompt_tokens}, 完成={completion_tokens}, 总计={total_tokens_used}")
            
            # print(resp.choices[0].message.content.strip())
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
    若解析失败则返回占位标签，确保L1有值
    """
    try:
        s_clean = clean_json_block(s)
        obj = json.loads(s_clean)
        
        # 确保 L1 始终有值
        if "L1" not in obj or not obj["L1"]:
            print(f"警告：L1标签为空，自动设为'未分类'")
            obj["L1"] = "未分类"
        
        # 其他标签可以为 None
        for k in {"L2", "L3", "L4"}:
            if k not in obj or obj[k] == "":
                obj[k] = None  # 使用None代替空字符串
        
        return obj
    except Exception as e:
        print(f"解析JSON失败: {e}")
        # 返回默认值，确保L1非空
        return {"L1": "未分类", "L2": None, "L3": None, "L4": None}

def main():
    questions: List[Dict] = json.load(open(JSON_IN, encoding="utf-8"))
    for q in tqdm(questions, desc="Tagging"):
        prompt = PROMPT_TMPL.format(QUESTION_BLOCK=build_question_block(q))
        # print(prompt)
        raw = call_llm(prompt)
        q["label"] = safe_json_line(raw)
    
    # 输出token使用总量统计
    print("\n===== Token使用统计 =====")
    print(f"提示tokens总计: {total_prompt_tokens}")
    print(f"完成tokens总计: {total_completion_tokens}")
    print(f"总计tokens: {total_tokens}")
    print(f"估算费用: ${total_prompt_tokens/1000 * 0.0015 + total_completion_tokens/1000 * 0.0045:.4f} (按1000tokens $0.001计算)")
    print("=======================\n")

    print(json.dumps(questions, ensure_ascii=False, indent=2))
    # json.dump(questions, open(JSON_OUT,"w",encoding="utf8"),
    #           ensure_ascii=False, indent=2)
    # print(f"共处理 {len(questions)} 道题。")

if __name__ == "__main__":
    main()
