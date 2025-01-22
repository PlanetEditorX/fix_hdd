import os
import shutil
from pathlib import Path

# 总文件数
TOTAL_INDEX = 0
# 坏道列表
BAD_TRACK_LIST = []
# 磁盘大小
FILE_SIZE = 4096 * 256 * 10 # 4KB = 4096 字节, 10MB = 4KB * 256 * 10

def get_files_sorted(directory):
    """
    获取指定目录下的所有文件，并按文件名排序。
    假设文件名是数字。
    """
    files = os.listdir(directory)
    files.sort(key=int)
    return files

def get_largest_file(directory):
    """
    获取指定目录下最大的文件名。
    """
    files = get_files_sorted(directory)
    return files[-1] if files else None

def get_surrounding_paths(base_path: Path, center_name: str, range_size: int = 10):
    """
    获取指定路径前后指定范围内的路径。
    :param base_path: 基础目录路径
    :param center_name: 中心文件名（如 '100'）
    :param range_size: 前后范围大小（默认为 10）
    :return: 生成的路径列表
    """
    global TOTAL_INDEX
    if not TOTAL_INDEX:
        # 获取最大文件名
        largest_file = get_largest_file(base_path)
        if largest_file:
            TOTAL_INDEX = int(largest_file)
            print(f"总序号为空，读取到最大文件名：{largest_file}")
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

def is_file_all_ones(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()  # 读取整个文件内容并去除首尾空白字符
            return content == '1' * len(content)
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return False

def check_files(directory):
    """
    遍历指定目录中的所有文件，检查文件大小是否为1MB，
    并验证文件内容是否全部为数字 '1'。
    """
    global BAD_TRACK_LIST,FILE_SIZE
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
                # 检查文件内容是否全部为数字 '1'
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if not content or not is_file_all_ones(file_path):
                        raise ValueError(f"文件内容不正确：{file_path}")
                    else:
                        print(f"文件检测正确：{file_path}", end="\r")
            except Exception as e:
                print(f"读取文件时发生错误：{file_path}，错误信息：{e}")
                surrounding_paths = get_surrounding_paths(directory, Path(file_path).name)
                BAD_TRACK_LIST.extend(surrounding_paths)
                print(f"新增错误列表：{surrounding_paths}")


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
                # os.remove(file_path)
                print("os.remove({file_path})")
# 指定要检查的目录
badblocks_path = "./.BADBLOCKS"
# 指定要检查的目录
check_files(badblocks_path)
# 删除正常扇区文件
del_right_file(badblocks_path)