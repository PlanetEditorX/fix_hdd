import os
import shutil
from pathlib import Path
import sys
import logging
import threading
import configparser

###################
# 通过写入填充磁盘 #
###################

# 创建ConfigParser对象
config = configparser.ConfigParser()

# 总文件数
TOTAL_INDEX = 0
# 坏道列表
BAD_TRACK_LIST = []
# 磁盘大小
FILE_SIZE = 0
# 线程数量
THREADING_SUM = 5

def get_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free

# 获取当前位置磁盘空间信息
if len(sys.argv) > 1:
    CURRENT_DIRECTORY = sys.argv[1]
else:
    CURRENT_DIRECTORY = os.getcwd()
# 填充位置
BADBLOCKS_PATH = f"{CURRENT_DIRECTORY}/.BADBLOCKS"
# 日志位置
LOG_PATH = "/root/badblocks.log"
# 坏道列表
BAD_TRACK_LIST_PATH = "/root/badblocks.txt"

# 读取配置文件
read_config = config.read("config.ini")
if not read_config:
    config["DEFAULT"] = {
        "current_directory": "none",
        "badblocks_path": "none",
        "log_path": "none",
        "bad_track_list_path": "none",
        "threading_sum": "none",
        "init": "false"
    }
if config.getboolean('DEFAULT','INIT'):
    GET_CONFIG = input(f"获取到配置文件，是否从配置中读取(Y/n)：")
    if GET_CONFIG in ['Y', 'y', '']:
        CURRENT_DIRECTORY = config['DEFAULT']['CURRENT_DIRECTORY']
        BADBLOCKS_PATH = config['DEFAULT']['BADBLOCKS_PATH']
        LOG_PATH = config['DEFAULT']['LOG_PATH']
        BAD_TRACK_LIST_PATH = config['DEFAULT']['BAD_TRACK_LIST_PATH']
        THREADING_SUM = int(config['DEFAULT']['THREADING_SUM'])
CURRENT_DIRECTORY_INPUT = input(f"当前的磁盘挂载目录为：{CURRENT_DIRECTORY}, 生成文件填充路径为：{BADBLOCKS_PATH}, 日志位置为：{LOG_PATH}, 坏道列表位置为：{BAD_TRACK_LIST_PATH}, 线程数量为：{THREADING_SUM}\r\n是否确认(Y/n): ")
while CURRENT_DIRECTORY_INPUT not in ['Y', 'y', '']:
    CURRENT_DIRECTORY = input(f"请输入磁盘挂载目录（默认值：{CURRENT_DIRECTORY}）：") or CURRENT_DIRECTORY
    BADBLOCKS_PATH = input(f"请输入生成文件填充路径（默认值：{BADBLOCKS_PATH}）：") or BADBLOCKS_PATH
    LOG_PATH = input(f"请输入日志位置（默认值：{LOG_PATH}）：") or LOG_PATH
    BAD_TRACK_LIST_PATH = input(f"请输入坏道列表位置（默认值：{BAD_TRACK_LIST_PATH}）：") or BAD_TRACK_LIST_PATH
    THREADING_SUM = int(input(f"请输入线程数量（默认值：{THREADING_SUM}）：") or THREADING_SUM)
    CURRENT_DIRECTORY_INPUT = input(f"当前的磁盘挂载目录为：{CURRENT_DIRECTORY}, 生成文件填充路径为：{BADBLOCKS_PATH}, 日志位置为：{LOG_PATH}, 坏道列表位置为：{BAD_TRACK_LIST_PATH}, 线程数量为：{THREADING_SUM}\r\n是否确认(Y/n): ")

# 写入配置文件
config['DEFAULT']['CURRENT_DIRECTORY'] = CURRENT_DIRECTORY
config['DEFAULT']['BADBLOCKS_PATH'] = BADBLOCKS_PATH
config['DEFAULT']['LOG_PATH'] = LOG_PATH
config['DEFAULT']['BAD_TRACK_LIST_PATH'] = BAD_TRACK_LIST_PATH
config['DEFAULT']['THREADING_SUM'] = str(THREADING_SUM)
config['DEFAULT']['INIT'] = 'true'
with open("config.ini", "w") as configfile:
    config.write(configfile)

# 配置日志模块
logging.basicConfig(
    level = logging.INFO,  # 设置日志级别为INFO
    format = '%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    filename = LOG_PATH,  # 设置日志文件路径
    filemode = 'a'  # 设置文件模式为追加（'a'）或覆盖（'w'）
)

print(f"当前磁盘挂载目录是：{CURRENT_DIRECTORY}")
total, used, free = get_disk_space(CURRENT_DIRECTORY)
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
        text = f"无效的中心文件名：{center_name}，必须是整数"
        logging.error(text)
        raise ValueError(text)

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
        text = f"读取文件时发生错误：{e}"
        print(text)
        logging.warning(text)
        return False


def check_files(file_path):
    """
    检查文件，验证文件内容是否全部为数字 '1'。
    """
    global BAD_TRACK_LIST,FILE_SIZE,BAD_TRACK_LIST_PATH

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
            text_1 = f"读取文件时发生错误：{file_path}，错误信息：{e}"
            print(text_1)
            logging.warning(text_1)
            surrounding_paths = get_surrounding_paths(directory, Path(file_path).name)
            BAD_TRACK_LIST.extend(surrounding_paths)
            text_2 = f"新增错误列表：{surrounding_paths}"
            print(text_2)
            logging.warning(text_2)
            # 写入列表
            with open(BAD_TRACK_LIST_PATH, 'a', encoding='utf-8') as file:
                file.write(surrounding_paths)
            return False

def write_to_file(thread_id, filename, content):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        logging.info(f"Thread {thread_id} finished writing to {filename}")
    except Exception as e:
        text = "写入异常"
        print(text)
        logging.error(text)

def create_4kb_files_until_full(output_dir):
    """
    循环生成 4KB 的文本文件，直到磁盘空间满。
    每个文件的内容全是数字 '1'。
    """
    global TOTAL_INDEX, FILE_SIZE, CURRENT_DIRECTORY, THREADING_SUM
    FILE_SIZE = 4096 * 256 * 10 # 4KB = 4096 字节, 10MB = 4KB * 256 * 10
    total_size = 0    # 已生成的总大小
    # 获取当前磁盘空间信息
    disk_path = CURRENT_DIRECTORY
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
        text = f"读取到运行前存在的最大文件名：{largest_file}"
        print(text)
        logging.info(text)
        file_index = int(largest_file)
        total_size = file_index * FILE_SIZE

    while total_size < target_size:
        # 生成文件名
        file_index += 1
        # 写入文件
        try:
            threads = []
            for i in range(THREADING_SUM):  # 创建线程
                file_name = os.path.join(output_dir, f"{file_index + i}")
                thread = threading.Thread(target=write_to_file, args=(i, file_name, file_content))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()
                # 更新总大小
                total_size += FILE_SIZE
                total_per = (total_size / target_size) * 100
                file_enable = check_files(os.path.join(output_dir, str(file_index)))
                print(f"生成文件:{file_name}, 可读写: {file_enable}, 剩余空间: {(used_size - total_size)/ (1024 * 1024):.2f} MB, 总大小: {total_size / (1024 * 1024):.2f} MB, 总进度: {((total_size / target_size) * 100):.2f}%", end="\r")
                # 生成文件名
                file_index += 1
                file_name = os.path.join(output_dir, f"{file_index}")

            # 多加了一个
            file_index -= 1
        except OSError as e:
            if e.errno == 28:  # errno.ENOSPC: No space left on device
                text = "错误：磁盘空间不足，无法完成写入操作。"
                print(text)
                logging.info(text)
                total, used, free = get_disk_space(disk_path)
                if FILE_SIZE < free:
                    raise OSError("错误：磁盘IO异常，请手动重启服务器或插拔磁盘")
                file_content = '1' * free
                try:
                    with open(file_name, "w") as file:
                        file.write(file_content)
                    print(f"剩余空间：0 MB, 生成文件 {file_name}, 总大小: {total_size / (1024 * 1024):.2f} MB", end="\r")
                except Exception as e:
                    print(e)
                    logging.error(e)
            else:
                print(f"发生错误：{e}")
        except Exception as e:
            print(f"写入文件发生错误：{e}")

    TOTAL_INDEX = file_index
    text ="Completed generating files"
    print(text)
    logging.info(text)

create_4kb_files_until_full(BADBLOCKS_PATH)

def del_right_file(directory):
    """
    遍历指定目录中的所有文件，删除正常的扇区占用文件
    """
    global BAD_TRACK_LIST
    # 地址去重
    BAD_TRACK_LIST = list(set(BAD_TRACK_LIST))
    if os.path.isfile(BAD_TRACK_LIST_PATH):
        temp_list = []
        # 打开文件并逐行读取
        with open("BAD_TRACK_LIST_PATH", "r", encoding="utf-8") as file:
            for line in file:
                temp_list.append(line.strip())
        BAD_TRACK_LIST = list(set(BAD_TRACK_LIST.extend(temp_list)))
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # 检查文件
        if os.path.isfile(file_path):
            if not file_path in BAD_TRACK_LIST:
                # os.remove(file_path)
                text = f"os.remove({file_path})"
                print(text)
                logging.info(text)

# # 删除正常扇区文件
del_right_file(BADBLOCKS_PATH)
