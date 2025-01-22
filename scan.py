import os
import shutil
from pathlib import Path

# 总文件数
TOTAL_INDEX = 0
# 坏道列表
BAD_TRACK_LIST = []
# 磁盘大小
FILE_SIZE = 0

def get_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free

# 获取当前位置磁盘空间信息
current_directory = os.getcwd()
print(f"当前磁盘挂载目录是：{current_directory}")
total, used, free = get_disk_space(current_directory)
print(f"总空间：{total / (1024 * 1024 * 1024):.2f} GB")
print(f"已用空间：{used / (1024 * 1024):.2f} MB")
print(f"剩余空间：{free / (1024 * 1024 * 1024):.2f} GB")
print("注：为降低服务器压力加快生成速度，以上数据仅为初次读取的数据大小，不会实时更新")
print("==============================================================================")
def create_4kb_files_until_full(output_dir):
    """
    循环生成 4KB 的文本文件，直到磁盘空间满。
    每个文件的内容全是数字 '1'。
    """
    global TOTAL_INDEX, FILE_SIZE
    FILE_SIZE = 4096 * 256 * 10 # 4KB = 4096 字节, 10MB = 4KB * 256 * 10
    total_size = 0    # 已生成的总大小
    # 获取当前磁盘空间信息
    disk_path = os.getcwd()
    total, used, free = get_disk_space(disk_path)
    target_size = total
    used_size = target_size - used
    file_content = '1' * FILE_SIZE    # 每个文件的内容为全1
    file_index = 0                    # 文件编号

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    while total_size < target_size:
        # 生成文件名
        file_index += 1
        file_name = os.path.join(output_dir, f"{file_index}")

        # 写入文件
        with open(file_name, "w") as file:
            file.write(file_content)

        # 更新总大小
        total_size += FILE_SIZE

        print(f"剩余空间：{(used_size - total_size)/ (1024 * 1024):.2f} MB, 生成文件 {file_name}, 总大小: {total_size / (1024 * 1024):.2f} MB", end="\r")

    TOTAL_INDEX = file_index
    print("Completed generating files")

# 指定要检查的目录
badblocks_path = "./.BADBLOCKS"
create_4kb_files_until_full(badblocks_path)
