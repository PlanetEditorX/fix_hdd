import os
import shutil
import time

# 坏道列表
BAD_TRACK_LIST = []

def get_disk_space(path):
    """
    返回磁盘信息
    """
    total, used, free = shutil.disk_usage(path)
    total_mb = total / (1024 * 1024)
    used_mb = used / (1024 * 1024)
    free_mb = free / (1024 * 1024)
    return total_mb, used_mb, free_mb

def create_4kb_files_until_full(output_dir):
    """
    循环生成 4KB 的文本文件，直到磁盘空间满。
    每个文件的内容全是数字 '1'。
    """
    file_size = 4096  # 4KB = 4096 字节
    total_size = 0    # 已生成的总大小
    target_size = 1024 * 1024 * 1024  # 1GB = 1024 * 1024 * 1024 字节
    file_content = '1' * file_size    # 每个文件的内容
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
        total_size += file_size

        # 强制刷新文件系统缓存（仅限 Linux 系统）
        os.sync()

        # 获取当前磁盘空间信息
        total, used, free = get_disk_space(output_dir)

        # 清屏并打印多行信息
        os.system("clear")  # Unix 系统清屏命令，Windows 系统使用 "cls"
        print(f"当前工作目录是：{output_dir}")
        print(f"总空间：{total} MB")
        print(f"已用空间：{used} MB")
        print(f"剩余空间：{free} MB")
        print(f"生成文件 {file_name}, 总大小: {total_size / (1024 * 1024):.2f} MB")

        # 模拟实时更新
        time.sleep(0.1)

# 指定要检查的目录
output_directory = "./.PROHIBIT_DELETION"
create_4kb_files_until_full(output_directory)