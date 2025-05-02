import os

def clear_download_folder(download_folder = "data"):
    """
    清空下载文件夹中的所有文件。
    :param folder_path: 要清空的文件夹路径，默认为 "data"
    """
    # 检查文件夹是否存在
    if not os.path.exists(download_folder):
        print(f"文件夹 {download_folder} 不存在.")
        return

    # 清空下载文件夹中的所有文件
    for file in os.listdir(download_folder):
        file_path = os.path.join(download_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)  # 删除文件
                print(f"已删除文件: {file_path}")
        except Exception as e:
            print(f"删除文件失败: {file_path}, 错误: {e}")
