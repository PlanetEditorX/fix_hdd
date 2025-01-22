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
    try:
        # 将中心文件名转换为整数
        center_num = int(center_name)
    except ValueError:
        raise ValueError(f"无效的中心文件名：{center_name}，必须是整数")

    # 生成前后范围内的路径
    start = max(0, center_num - range_size)
    end = center_num + range_size

    paths = []
    for num in range(start, end):
        # 构造路径
        num_path = os.path.join(base_path, str(num))
        paths.append(num_path)
        # path = Path(num_path)
        # if path.exists():  # 检查路径是否存在
        #     paths.append(num_path)

    return paths

def is_file_all_ones(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()  # 读取整个文件内容并去除首尾空白字符
            return content == '1' * len(content)
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return False


def check_files(file_index, file_path):
    """
    检查文件，验证文件内容是否全部为数字 '1'。
    """
    global BAD_TRACK_LIST,FILE_SIZE

    # 检查文件
    if os.path.isfile(file_path):
        try:
            # 检查文件内容是否全部为数字 '1'
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content or not is_file_all_ones(file_path):
                    raise ValueError(f"文件内容不正确：{file_path}")
                else:
                    return True
        except Exception as e:
            print(f"读取文件时发生错误：{file_path}，错误信息：{e}")
            surrounding_paths = get_surrounding_paths(directory, Path(file_path).name)
            BAD_TRACK_LIST.extend(surrounding_paths)
            print(f"新增错误列表：{surrounding_paths}")
            return False

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

    # 获取最大文件名
    largest_file = get_largest_file(output_dir)
    if largest_file:
        print(f"读取到运行前存在的最大文件名：{largest_file}")
        file_index = int(largest_file)
        total_size = file_index * FILE_SIZE

    while total_size < target_size:
        # 生成文件名
        file_index += 1
        file_name = os.path.join(output_dir, f"{file_index}")

        # 写入文件
        try:
            with open(file_name, "w") as file:
                file.write(file_content)
            # 更新总大小
            total_size += FILE_SIZE
            total_per = (total_size / target_size) * 100
            file_enable = check_files(file_index, file_name)
            print(f"生成文件:{file_name}, 可读写: {file_enable}, 剩余空间: {(used_size - total_size)/ (1024 * 1024):.2f} MB, 总大小: {total_size / (1024 * 1024):.2f} MB, 总进度: {((total_size / target_size) * 100):.2f}%", end="\r")

        except Exception as e:
            print("剩余空间不足，进行末尾文件写入")
            total, used, free = get_disk_space(disk_path)
            file_content = '1' * free
            with open(file_name, "w") as file:
                file.write(file_content)
            print(f"剩余空间：0 MB, 生成文件 {file_name}, 总大小: {total_size / (1024 * 1024):.2f} MB", end="\r")

    TOTAL_INDEX = file_index
    print("Completed generating files")

# 指定要检查的目录
badblocks_path = "./.BADBLOCKS"
create_4kb_files_until_full(badblocks_path)

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
                print(f"os.remove({file_path})")


# # 删除正常扇区文件
# del_right_file(badblocks_path)