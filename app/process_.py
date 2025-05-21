from docx import Document
import pandas as pd
import re
import os
import zipfile
import requests
import json
import base64
from wand.image import Image

qwen_key = os.getenv("QWEN_KEY")

# 提取图片和公式
def extract_images_from_runs(paragraph, doc):
    images = []
    for run in paragraph.runs:
        xml = run._element.xml
        # 查找所有 r:id="rIdXXX"
        rids = re.findall(r'(?:r:id|r:embed)="(rId\d+)"', xml)
        for rid in rids:  # 这里不是元组，而是直接的rId字符串
            try:
                rel = doc.part.rels.get(rid)
                if rel and "image" in rel.target_ref:
                    image_name = os.path.basename(rel.target_ref)
                    images.append(image_name)
            except Exception as e:
                print(f"处理rId {rid}时出错: {e}")
    return images

# 提取文档中的文本、图片及结构化题目
def extract_doc_content(doc_path):
    """提取文档中的文本、图片及结构化题目"""
    doc = Document(doc_path)
    questions = []
    current_question = None
    # image_map = {}  # 存储图片ID与本地路径的映射
    collecting = False

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        # # 遍历文档xml格式
        # for run in paragraph.runs:
        #     print(run.element.xml)
        # 匹配题号（如 "1."）
        if re.match(r'^\d+\.', text):
            if current_question:
                questions.append(current_question)
            current_question = {
                "id": re.match(r'^(\d+)\.', text).group(1),
                "content": text,
                # "to_answer": [],
                "options": [],
                "images": [],
                "formulas": []
            }
            collecting = True
            # 提取题号行的图片
            current_question["images"].extend(extract_images_from_runs(paragraph, doc))

        # 提取剩余内容
        elif collecting and current_question is not None and text:
            if current_question["content"]:
                current_question["content"] += "\n" + text
            else:
                current_question["content"] = text

            # 提取正文行的图片
            current_question["images"].extend(extract_images_from_runs(paragraph, doc))
                
        # 匹配选项（如 "A."）
        elif re.match(r'^[A-D]\.', text):
            option = {"text": text, "images": []}
            option["images"].extend(extract_images_from_runs(paragraph, doc))
            current_question["options"].append(option)
        # 其他内容也提取图片
        else:
            if current_question is not None:
                current_question["images"].extend(extract_images_from_runs(paragraph, doc))

    # 添加最后一个题目
    if current_question:
        questions.append(current_question)
    return questions

# 提取并存储图片/公式
def extract_media(docx_path, output_dir):
     # 清空目标文件夹
    if os.path.exists(output_dir):
        # 删除目录下所有文件
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            # 如果需要也删除子目录，取消下面注释
            # elif os.path.isdir(file_path):
            #     shutil.rmtree(file_path)
        print(f"已清空目录 {output_dir}")

    # 创建输出目录（确保media文件夹存在）
    os.makedirs(output_dir, exist_ok=True)
    image_map = {}

    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        media_files = [f for f in zip_ref.namelist() if f.startswith('word/media/')]
        print(f"找到 {len(media_files)} 个媒体文件")

        for file in media_files:
            #获取为文件数据直接写入新位置
            filename = os.path.basename(file)
            if not filename:
                print(f"警告：跳过空文件名 {file}")
                continue

            temp_path = os.path.join(output_dir, filename)
            try:
                # 提取文件内容并直接写入目标路径
                with zip_ref.open(file) as source, open(temp_path, 'wb') as target:
                    target.write(source.read())

                # 检查是否需要转换格式
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext == '.wmf':
                    png_filename = filename.replace('.wmf', '.png')
                    png_path = os.path.join(output_dir, png_filename)
                    try:
                        with Image(filename=temp_path) as img:
                            img.format = 'png'
                            img.save(filename=png_path)

                        os.unlink(temp_path)  # 删除原WMF文件
                        print(f"已将 {filename} 转换为 {png_filename}")

                        image_map[filename] = png_path
                        image_map[png_filename] = png_path
                    except Exception as e:
                        print(f"转换 {filename} 时出错: {e}")
                        image_map[filename] = temp_path

                else:
                    image_map[filename] = temp_path

            except Exception as e:
                print(f"提取 {file} 时出错: {e}")
    return image_map

# mathpix图片公式提取   弃用
def convert_formula_to_latex(image_path):
    # 使用Mathpix API转换公式图片为LaTeX
    response = requests.post(
        "https://api.mathpix.com/v3/text",
        files={"file": open(image_path, "rb")},
        headers={"app_id": "YOUR_APP_ID", "app_key": "YOUR_APP_KEY"}
    )
    return response.json().get("text", "")

# qwen-vl图片公式提取
def qwen_vl_ocr(image_path):
    # 编码图片为base64
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    
    # 调用Qwen-VL API（示例URL）
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer{qwen_key}"  # 替换为你的API Key
               }
    payload = {
        "model": "qwen-vl-plus",
        "messages": [{
            "role": "user",
            "content": [
                    {
                        "type": "text",
                        "text": "提取图片中的文字和数学公式，公式用LaTeX表示"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
        }]
    }
    response = requests.post(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        headers=headers,
        json=payload
    )
    # 打印完整响应，用于调试
    print(f"API响应状态码: {response.status_code}")
    if response.status_code != 200:
        print(f"API错误: {response.text[:200]}...")  # 只打印前200字符避免日志过长
    
    # 增加错误处理
    try:
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        elif "error" in result:
            return f"API错误: {result.get('error', {}).get('message', '未知错误')}"
        else:
            return f"未知响应格式: {result}"
    except Exception as e:
        return f"解析响应出错: {e}"

def process_questions(questions, image_map):
    """处理题目中的图片和公式"""
    # for question in questions:
    #     # 处理题干中的图片
    #     for img_ref in question["images"]:
    #         img_path = image_map.get(img_ref)
    #         if img_path:
    #             ocr_result = qwen_vl_ocr(img_path)
    #             # 替换图片引用为OCR结果（保留原始内容）
    #             question["content"] = question["content"].replace(
    #                 f"![]({img_ref})",
    #                 f"[图片内容：{ocr_result}]"
    #             )
        
    #     # 处理选项中的图片
    #     for option in question["options"]:
    #         for img_ref in option["image_refs"]:
    #             img_path = image_map.get(img_ref)
    #             if img_path:
    #                 ocr_result = qwen_vl_ocr(img_path)
    #                 option["text"] = option["text"].replace(
    #                     f"![]({img_ref})",
    #                     f"[选项内容：{ocr_result}]"
    #                 )
    # return questions
    for question in questions:
        # 处理题干中的图片
        image_paths = []
        for img_ref in question["images"]:
            img_path = image_map.get(img_ref)
            if img_path:
                # 获取相对路径（只保留文件名）
                relative_path = os.path.basename(img_path)
                image_paths.append(f"./media/{relative_path}")
                
        # 直接在题干末尾添加图片路径列表（不使用OCR）
        if image_paths:
            question["image_paths"] = image_paths  # 添加新字段存储图片路径
        
        # 处理选项中的图片
        for option in question["options"]:
            option_image_paths = []
            # 注意：选项中应该是images而不是image_refs
            for img_ref in option.get("images", []):  # 使用get避免KeyError
                img_path = image_map.get(img_ref)
                if img_path:
                    relative_path = os.path.basename(img_path)
                    option_image_paths.append(f"./media/{relative_path}")
            
            # 直接添加图片路径列表（不使用OCR）
            if option_image_paths:
                option["image_paths"] = option_image_paths  # 添加新字段存储图片路径
    
    return questions

# 弃用
def process_docx(docx_path, output_dir):
    # 解析文档结构
    questions = extract_doc_content(docx_path)
    
    # 提取并存储媒体文件
    media_dir = os.path.join(output_dir, "media")
    extracted_images = extract_media(docx_path, media_dir)
    
    # 转换公式为LaTeX并补充到选项
    for question in questions:
        for formula in question["formulas"]:
            formula_path = extracted_images.get(formula)
            if formula_path:
                latex = convert_formula_to_latex(formula_path)
                question["content"] = question["content"].replace(f"![]({formula})", f"${latex}$")
        for option in question["options"]:
            for img_ref in option["images"]:
                img_path = extracted_images.get(img_ref)
                if img_path:
                    option["text"] = option["text"].replace(f"![]({img_ref})", f"<img src='{img_path}'>")
    
    # # 输出结构化JSON
    # with open(os.path.join(output_dir, "structured_questions.json"), "w") as f:
    #     json.dump(questions, f, indent=2, ensure_ascii=False)
    return questions


if __name__ == "__main__":
    # 主程序
    docx_path = r"E:\NLP_Model\ai_edu\data\math\2023年江苏省泰州市中考数学真题（原卷版）.docx"
    output_dir = r"E:\NLP_Model\ai_edu\data\processed_data"

    # 1. 解析文档结构
    questions = extract_doc_content(docx_path)

    # 2. 提取图片到本地
    image_map = extract_media(docx_path, os.path.join(output_dir, "media"))

    # 3. 使用Qwen-VL处理图片内容
    processed_questions = process_questions(questions, image_map)

    # 4. 保存结构化数据
    import json
    with open(os.path.join(output_dir, "labeled_questions.json"), "w", encoding="utf-8") as f:
        json.dump(processed_questions, f, indent=2, ensure_ascii=False)