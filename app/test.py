import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from clear import clear_download_folder



# 定义初始URL
url = "https://www.shijuan1.com/a/sjsxzk/list_706_1.html"

# 创建保存下载文件的文件夹
download_folder = "data"
os.makedirs(download_folder, exist_ok=True)
# # 清空下载文件夹中的所有文件
# clear_download_folder(download_folder)

for i in range(1, 10):
    # 发送HTTP请求并解析网页内容
    try:
        response = requests.get(url)
    except Exception as e:
        print(f"请求失败: {e}")
        break
    response.encoding = 'gbk'
    soup = BeautifulSoup(response.text, "html.parser")

    # 查找所有包含目标下载链接的HTML元素
    td_elements = soup.find_all("td", {"width": "52%", "height": "23"})

    for td in td_elements:
        # 查找文章标题和详情页链接
        a_tag = td.find("a", {"class": "title"}, string=re.compile(r"\s*(江苏|浙江)\s*"))
        # print("a_tag:", a_tag)
        if a_tag:
            detail_page_url = urljoin(url, a_tag.attrs["href"])# 拼接完整的详情页URL
            title = a_tag.text.strip()

            # 进入详情页，查找下载链接
            detail_response = requests.get(detail_page_url)# 发送GET请求获取详情页内容
            detail_response.encoding = 'gbk'
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            download_link = detail_soup.find("a", attrs={"target": "_blank"}, string=re.compile(r"\s*本地下载\s*"))# 查找文本为“本地下载”的<a>标签

            if not download_link:
                download_link = detail_soup.find("a", href=re.compile(r"\.rar$"))# 查找href属性以“.rar”结尾的<a>标签
            print("download_link:", download_link)
            if not download_link:
            # 如果未找到下载链接，打印调试信息
                print(f"未找到下载链接，详情页URL: {detail_page_url}")

            else:
                # 拼接完整的下载链接
                file_url = urljoin(detail_page_url, download_link.attrs["href"])
                file_name = os.path.join(download_folder, f"{title}.rar") 
                if not file_url or not file_name:
                    print(f"File URL not found or File Name not found for {title}")

                print(f"file_url: {file_url}")
                print(f"flie_name: {file_name}")

                # # 下载文件并保存
                # print(f"Downloading: {file_url}")
                # file_response = requests.get(file_url)
                # with open(file_name, "wb") as file:
                #     file.write(file_response.content)
                # print(f"Saved to: {file_name}")
    # 查找下一页链接
    next_page = soup.find("a", string=re.compile(r"\s*下一页\s*"))
    if next_page:
        url = urljoin(url, next_page.attrs["href"])  # 拼接下一页的URL
        print(f"下一页URL: {url}")
    else:
        url = None  # 没有下一页，结束循环