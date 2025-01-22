import os
import shutil
from pathlib import Path

# 总文件数
TOTAL_INDEX = 0
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
    global TOTAL_INDEX
    file_size = 4096 * 256 * 10 # 4KB = 4096 字节, 10MB = 4KB * 256 * 10
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

    TOTAL_INDEX = file_index
    print("Completed generating files")

# 指定要检查的目录
badblocks_path = "./.BADBLOCKS"
# create_4kb_files_until_full(badblocks_path)

def get_surrounding_paths(base_path: Path, center_name: str, range_size: int = 10):
    """
    获取指定路径前后指定范围内的路径。
    :param base_path: 基础目录路径
    :param center_name: 中心文件名（如 '100'）
    :param range_size: 前后范围大小（默认为 10）
    :return: 生成的路径列表
    """
    global TOTAL_INDEX
    # test/待删除
    # TOTAL_INDEX = 3000
    try:
        # 将中心文件名转换为整数
        center_num = int(center_name)
    except ValueError:
        raise ValueError(f"无效的中心文件名：{center_name}，必须是整数")

    # 生成前后范围内的路径
    start = max(0, center_num - range_size)
    end = min(TOTAL_INDEX, center_num + range_size + 1)

    paths = []
    for num in range(start, end):
        # 构造路径
        num_path = os.path.join(base_path, str(num))
        path = Path(num_path)
        if path.exists():  # 检查路径是否存在
            paths.append(num_path)

    return paths

def check_files(directory):
    """
    遍历指定目录中的所有文件，检查文件大小是否为1MB，
    并验证文件内容是否全部为数字 '1'。
    """
    global BAD_TRACK_LIST
    if not os.path.exists(directory):
        print(f"目录不存在：{directory}")
        return

    if not os.path.isdir(directory):
        print(f"路径不是一个目录：{directory}")
        return

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # 检查文件
        if os.path.isfile(file_path):
            try:
                # 检查文件大小是否为10MB
                file_size = os.path.getsize(file_path)
                if file_size != 4096 * 256 * 10:
                    raise ValueError(f"文件大小不为 1MB：{file_path}，大小为 {file_size} 字节")

                # 检查文件内容是否全部为数字 '1'
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if content.strip() != '1' * (file_size // len('1')):
                        raise ValueError(f"文件内容不正确：{file_path}")
                    else:
                        print(f"文件读取正常：{file_path}", end='\r')
            except Exception as e:
                print(f"读取文件时发生错误：{file_path}，错误信息：{e}")
                surrounding_paths = get_surrounding_paths(directory, Path(file_path).name)
                BAD_TRACK_LIST.extend(surrounding_paths)
                print(BAD_TRACK_LIST)
                return


def del_right_file(directory):
    """
    遍历指定目录中的所有文件，删除正常的扇区占用文件
    """
    global BAD_TRACK_LIST
    # 地址去重
    BAD_TRACK_LIST = list(set(BAD_TRACK_LIST))
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # 检查文件
        if os.path.isfile(file_path):
            if not file_path in BAD_TRACK_LIST:
                os.remove(file_path)

# 指定要检查的目录
check_files(badblocks_path)
# 删除正常扇区文件
del_right_file(badblocks_path)