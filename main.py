import os
import shutil

# 坏道列表
BAD_TRACK_LIST = []

def get_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free

# 获取当前位置磁盘空间信息
current_directory = os.getcwd()
print(f"当前磁盘挂载目录是：{current_directory}")
total, used, free = get_disk_space(current_directory)
print(f"总空间：{total / (1024 * 1024):.2f} MB")
print(f"已用空间：{used / (1024 * 1024):.2f} MB")
print(f"剩余空间：{free / (1024 * 1024):.2f} MB")
print("注：为降低服务器压力加快生成速度，以上数据仅为初次读取的数据大小，不会实时更新")
print("==============================================================================")
def create_4kb_files_until_full(output_dir):
    """
    循环生成 4KB 的文本文件，直到磁盘空间满。
    每个文件的内容全是数字 '1'。
    """
    file_size = 4096 * 256 # 4KB = 4096 字节, 1MB = 4KB * 256
    total_size = 0    # 已生成的总大小
    # 获取当前磁盘空间信息
    disk_path = os.getcwd()
    total, used, free = get_disk_space(disk_path)
    target_size = total
    used_size = target_size - used
    file_content = '1' * file_size    # 每个文件的内容为全1
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

        print(f"剩余空间：{(used_size - total_size)/ (1024 * 1024):.2f} MB, 生成文件 {file_name}, 总大小: {total_size / (1024 * 1024):.2f} MB", end="\r")

    print("Completed generating files up to 1GB.")

# 指定要检查的目录
badblocks_path = "./.BADBLOCKS"
create_4kb_files_until_full(badblocks_path)

def check_files(directory):
    """
    遍历指定目录中的所有文件，检查文件大小是否为 4KB，
    并验证文件内容是否全部为数字 '1'。
    """
    if not os.path.exists(directory):
        print(f"目录不存在：{directory}")
        return

    if not os.path.isdir(directory):
        print(f"路径不是一个目录：{directory}")
        return

    # 获取目录中所有文件的路径
    all_files = [os.path.join(directory, filename) for filename in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, filename))]

    # 按文件名排序（确保顺序一致）
    all_files.sort()

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # 检查文件
        if os.path.isfile(file_path):
            # 检查文件大小是否为 4KB
            file_size = os.path.getsize(file_path)
            if file_size != 4096:
                print(f"文件大小不为 4KB：{file_path}，大小为 {file_size} 字节")
                continue

            # 检查文件内容是否全部为数字 '1'
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if content.strip() != '1' * (file_size // len('1')):
                        print(f"文件内容不正确：{file_path}")
                    else:
                        print(f"文件读取正常：{file_path}", end='\r')
            except Exception as e:
                print(f"读取文件时发生错误：{file_path}，错误信息：{e}")
                # 获取前后2056个文件（10MB）的路径
                start_index = max(0, index - 2056)
                end_index = min(len(all_files), index + 2056 + 1)
                BAD_TRACK_LIST.extend(all_files[start_index:end_index])
                print(BAD_TRACK_LIST)
                return

# 指定要检查的目录
check_files(badblocks_path)
