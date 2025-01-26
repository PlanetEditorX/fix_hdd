import os
import shutil
from pathlib import Path
import sys
import logging
import threading
import configparser
import time
from collections import deque

###################
# 通过复制填充磁盘 #
###################

# 总文件数
TOTAL_INDEX = 0
# 坏道列表
BAD_TRACK_LIST = []
# 磁盘大小
FILE_SIZE = 0
# 线程数量
THREADING_SUM = 1

def get_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free

# 获取当前位置磁盘空间信息
if len(sys.argv) > 1:
    CURRENT_DIRECTORY = sys.argv[1]

# 创建ConfigParser对象
config = configparser.ConfigParser()
# 读取配置文件
read_config = config.read("config.ini")
if read_config and config['DEFAULT']:
    CURRENT_DIRECTORY = config['DEFAULT']['CURRENT_DIRECTORY']
else:
    config["DEFAULT"] = {
        "CURRENT_DIRECTORY": "none",
        "BADBLOCKS_PATH": "none",
        "LOG_PATH": "none",
        "BAD_TRACK_LIST_PATH": "none",
        "THREADING_SUM": "none",
        "TEMPLATE_PATH": "none",
        "INIT": "false",
        "TOTAL_INDEX": "0",
        "CHECK_INDEX": "0"
    }
    CURRENT_DIRECTORY = input(f"请输入磁盘挂载目录：")

# 填充位置
BADBLOCKS_PATH = f"{CURRENT_DIRECTORY}/.BADBLOCKS"
GETCWD = os.getcwd()
# 日志位置
LOG_PATH = f"{GETCWD}/badblocks.log"
# 坏道列表
BAD_TRACK_LIST_PATH = f"{GETCWD}/badblocks.txt"
# 模板位置
TEMPLATE_PATH = f"{CURRENT_DIRECTORY}/.BADBLOCKS/0"
# 最大文件序号
MAX_INDEX = 0
# 最大检测序号
CHECK_INDEX = 0

if config.getboolean('DEFAULT','INIT'):
    GET_CONFIG = input(f"获取到配置文件，是否从配置中读取(Y/n)：")
    if GET_CONFIG in ['Y', 'y', '']:
        CURRENT_DIRECTORY = config['DEFAULT']['CURRENT_DIRECTORY']
        BADBLOCKS_PATH = config['DEFAULT']['BADBLOCKS_PATH']
        LOG_PATH = config['DEFAULT']['LOG_PATH']
        BAD_TRACK_LIST_PATH = config['DEFAULT']['BAD_TRACK_LIST_PATH']
        THREADING_SUM = int(config['DEFAULT']['THREADING_SUM'])
        TEMPLATE_PATH = config['DEFAULT']['TEMPLATE_PATH']
        TOTAL_INDEX = int(config['DEFAULT']['TOTAL_INDEX'])
        CHECK_INDEX = int(config['DEFAULT']['CHECK_INDEX'])

CURRENT_DIRECTORY_INPUT = input(f"当前的磁盘挂载目录为：{CURRENT_DIRECTORY}, 生成文件路径为：{BADBLOCKS_PATH}, 生成线程数量为：{THREADING_SUM}, 日志位置为：{LOG_PATH}, 坏道列表位置为：{BAD_TRACK_LIST_PATH}, 模板文件位置为：{TEMPLATE_PATH}\r\n是否确认(Y/n): ")
while CURRENT_DIRECTORY_INPUT not in ['Y', 'y', ''] or CURRENT_DIRECTORY in ['/root', '/', '']:
    if  CURRENT_DIRECTORY in ['/root', '/', '']:
        CURRENT_DIRECTORY = input(f"磁盘挂载目录不能为'/root','/','', 请重新输入：") or CURRENT_DIRECTORY
    else:
        CURRENT_DIRECTORY = input(f"请输入磁盘挂载目录（默认值：{CURRENT_DIRECTORY}）：") or CURRENT_DIRECTORY
    BADBLOCKS_PATH = f"{CURRENT_DIRECTORY}/.BADBLOCKS"
    BADBLOCKS_PATH = input(f"请输入生成文件路径（默认值：{BADBLOCKS_PATH}）：") or BADBLOCKS_PATH
    LOG_PATH = input(f"请输入日志位置（默认值：{LOG_PATH}）：") or LOG_PATH
    BAD_TRACK_LIST_PATH = input(f"请输入坏道列表位置（默认值：{BAD_TRACK_LIST_PATH}）：") or BAD_TRACK_LIST_PATH
    THREADING_SUM = int(input(f"请输入生成线程数量（默认值：{THREADING_SUM}）：") or THREADING_SUM)
    while THREADING_SUM < 1 or THREADING_SUM > 10:
        THREADING_SUM = int(input(f"请重新输入生成线程数量（当前值：{THREADING_SUM}，范围：1-10）："))
    TEMPLATE_PATH = input(f"请输入模板文件位置（默认值：{TEMPLATE_PATH}）：") or TEMPLATE_PATH
    CURRENT_DIRECTORY_INPUT = input(f"当前的磁盘挂载目录为：{CURRENT_DIRECTORY}, 生成文件路径为：{BADBLOCKS_PATH}, 生成线程数量为：{THREADING_SUM}, 日志位置为：{LOG_PATH}, 坏道列表位置为：{BAD_TRACK_LIST_PATH}, 模板文件位置为：{TEMPLATE_PATH}\r\n是否确认(Y/n): ")

# 写入配置文件
config['DEFAULT']['CURRENT_DIRECTORY'] = CURRENT_DIRECTORY
config['DEFAULT']['BADBLOCKS_PATH'] = BADBLOCKS_PATH
config['DEFAULT']['LOG_PATH'] = LOG_PATH
config['DEFAULT']['BAD_TRACK_LIST_PATH'] = BAD_TRACK_LIST_PATH
config['DEFAULT']['THREADING_SUM'] = str(THREADING_SUM)
config['DEFAULT']['TEMPLATE_PATH'] = TEMPLATE_PATH
config['DEFAULT']['INIT'] = 'true'
with open("config.ini", "w") as configfile:
    config.write(configfile)

# 模板文件不在机械硬盘上，创建临时缓存目录
if TEMPLATE_PATH != f"{CURRENT_DIRECTORY}/.BADBLOCKS/0":
    TEMPORARY_FILES_PATH = f"{os.path.dirname(TEMPLATE_PATH)}/.template"
    # 删除临时缓存目录
    if os.path.exists(TEMPORARY_FILES_PATH):
        shutil.rmtree(TEMPORARY_FILES_PATH)
    os.makedirs(TEMPORARY_FILES_PATH, exist_ok=True)

print("==============================================================================")
OPERATION_OPTIONS = False
IS_CREATE = False
IS_CHECK = False
IS_DEL = False
while OPERATION_OPTIONS not in ['','1','2','3','a','A','b','B']:
    print("操作列表")
    print("【1】生成填充文件，占满磁盘空间")
    print("【2】检查填充文件读取是否正常，生成坏道列表")
    print("【3】删除正常填充文件，保留坏道占用文件，防止写入")
    print("【a】执行【1】【2】")
    print("【b】执行【2】【3】")
    OPERATION_OPTIONS = input(f"请输入操作（回车默认依次执行）：")
    match(OPERATION_OPTIONS):
        case '':
            IS_CREATE = True
            IS_CHECK = True
            IS_DEL = True
        case '1': IS_CREATE = True
        case '2': IS_CHECK = True
        case '3': IS_DEL = True
        case 'a' | 'A':
            IS_CREATE = True
            IS_CHECK = True
        case 'b' | 'B':
            IS_CHECK = True
            IS_DEL = True
        case _:
            print(f"输入错误，请重新输入！")
print("==============================================================================")

# 配置日志模块
logging.basicConfig(
    level = logging.INFO,  # 设置日志级别为INFO
    format = '%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    filename = LOG_PATH,  # 设置日志文件路径
    filemode = 'a'  # 设置文件模式为追加（'a'）或覆盖（'w'）
)

def DECIMAL_CONVERSION(num):
    if num < 1024:
        return f"{num} Byte"
    elif num < 1024 * 1024:
        return f"{num / (1024):.2f} KB"
    elif num < 1024 * 1024 * 1024:
        return f"{num / (1024 * 1024):.2f} MB"
    elif num < 1024 * 1024 * 1024 * 1024:
        return f"{num / (1024 * 1024 * 1024):.2f} GB"

print(f"当前磁盘挂载目录是：{CURRENT_DIRECTORY}")
total, used, free = get_disk_space(CURRENT_DIRECTORY)
print(f"总空间：{DECIMAL_CONVERSION(total)}")
print(f"已用空间：{DECIMAL_CONVERSION(used)}")
print(f"剩余空间：{DECIMAL_CONVERSION(free)}")
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


def get_surrounding_paths(base_path: Path, center_name: str, range_size: int = 1):
    """
    获取指定路径前后指定范围内的路径。
    :param base_path: 基础目录路径
    :param center_name: 中心文件名（如 '100'）
    :param range_size: 前后范围大小（默认为 1）
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
    end = center_num + range_size + 1

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
        text = f"读取文件时发生错误：{e}"
        print(text)
        logging.warning(text)
        return False

def copy_to_file(thread_id, source_file, file_name):
    """
    多线程调用，复制文件进行填充
    """
    try:
        shutil.copy(source_file, file_name)  # 复制文件并重命名
        logging.info(f"Thread {thread_id} finished writing to {file_name}")
    except Exception as e:
        text = f"写入异常: {e}"
        print(text)
        logging.error(text)

def format_seconds(seconds):
    """
    计算小时、分钟和秒
    """
    hours, remainder = divmod(seconds, 3600)  # 3600 秒 = 1 小时
    minutes, seconds = divmod(remainder, 60)  # 60 秒 = 1 分钟
    if hours:
        return f"{int(hours):02d}H:{int(minutes):02d}M:{int(seconds):02d}S"
    elif minutes:
        return f"{int(minutes):02d}M:{int(seconds):02d}S"
    return f"{int(seconds):02d}S"

class FixedSizeArray:
    """
    动态数组
    """
    def __init__(self, size=10):
        self.size = size
        self.array = deque(maxlen=size)  # 创建一个指定长度的双端队列

    def add(self, item):
        """添加元素，如果已满会自动移除首项"""
        self.array.append(item)

    def is_full(self):
        """检查数组是否已满"""
        return len(self.array) == self.size

    def get_average(self):
        """计算并返回当前数组的平均值"""
        if len(self.array) == 0:
            return 0  # 如果数组为空，返回 0
        return sum(self.array) / len(self.array)  # 计算平均值

    def get_sum(self):
        """计算并返回当前数组的总和"""
        return sum(self.array)

    def __str__(self):
        return str(list(self.array))  # 返回数组的字符串表示

def create_4kb_files_until_full(output_dir):
    """
    循环生成 4KB 的文本文件，直到磁盘空间满。
    每个文件的内容全是数字 '1'。
    """
    global TOTAL_INDEX, FILE_SIZE, CURRENT_DIRECTORY, THREADING_SUM, TEMPLATE_PATH
    FILE_SIZE = 4096 * 256 * 20 # 4KB = 4096 字节, 20MB = 4KB * 256 * 20
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
        text = f"读取到生成文件路径'{BADBLOCKS_PATH}'中存在的最大文件名：{largest_file} OK"
        print(text)
        logging.info(text)
        file_index = max(0, int(largest_file)-10)
        back_nums = int(largest_file) - file_index
        print(f"回退{back_nums}项，将从{file_index}开始重新填充文件(0/{back_nums})", end="\r")
        for i in range(0, back_nums):
            file_path = os.path.join(output_dir, f"{file_index + i}")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"回退{back_nums}项，将从{file_index}开始重新填充文件(0/{back_nums})", end="\r")
        print(f"回退{back_nums}项，将从{file_index}开始重新填充文件({back_nums}/{back_nums}) OK")

        total, used, free = get_disk_space(disk_path)
        total_size = used

    if not os.path.isfile(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "w", encoding="utf-8") as file:
            file.write(file_content)
    speed_time = FixedSizeArray()
    speed_text = '计算中...'
    DISK_SPACE = True
    while total_size < target_size and DISK_SPACE:
        start_time = time.time()
        # 生成文件名
        file_index += 1
        # 写入文件
        try:
            threads = []
            # 先写入到临时目录，再移动到挂载目录
            if os.path.exists(TEMPORARY_FILES_PATH) and os.path.isdir(TEMPORARY_FILES_PATH):
                file_path_list = []
                for i in range(THREADING_SUM):  # 创建线程
                    file_path = os.path.join(TEMPORARY_FILES_PATH, f"{file_index + i}")
                    file_path_list.append(file_path)
                    thread = threading.Thread(target=copy_to_file, args=(i, TEMPLATE_PATH, file_path))
                    threads.append(thread)
                    thread.start()

                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                    # 生成文件名
                    file_index += 1
                    file_path = os.path.join(output_dir, f"{file_index}")
                for file_name in file_path_list:
                    new_file_name = Path(file_name).name
                    file_path = os.path.join(output_dir, new_file_name)
                    shutil.move(file_name, file_path)
                    # 更新总大小
                    total_size += FILE_SIZE
                    total_per = (total_size / target_size) * 100
                    if speed_time.is_full():
                        # (剩余空间 / 线程生成文件大小) * 线程耗时
                        speed_text = format_seconds((total - total_size) / (THREADING_SUM * FILE_SIZE * 10) * float(speed_time.get_sum()))
                    print(f"生成文件:{file_path}, 剩余空间: {DECIMAL_CONVERSION(total - total_size)}, 已用空间: {DECIMAL_CONVERSION(total_size)} 总进度: {((total_size / target_size) * 100):.2f}%, 预估时间:{speed_text}", end="\r")

            else:
                for i in range(THREADING_SUM):  # 创建线程
                    file_path = os.path.join(output_dir, f"{file_index + i}")
                    thread = threading.Thread(target=copy_to_file, args=(i, TEMPLATE_PATH, file_path))
                    threads.append(thread)
                    thread.start()

                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                    # 更新总大小
                    total_size += FILE_SIZE
                    total_per = (total_size / target_size) * 100
                    if speed_time.is_full():
                        # (剩余空间 / 线程生成文件大小) * 线程耗时
                        speed_text = format_seconds((total - total_size) / (THREADING_SUM * FILE_SIZE * 10) * float(speed_time.get_sum()))
                        # speed_text = format_seconds((total - total_size) / (THREADING_SUM * FILE_SIZE) * float(speed_time.get_average()))
                    print(f"生成文件:{file_path}, 剩余空间: {DECIMAL_CONVERSION(total - total_size)}, 已用空间: {DECIMAL_CONVERSION(total_size)} 总进度: {((total_size / target_size) * 100):.2f}%, 预估时间:{speed_text}", end="\r")
                    # 生成文件名
                    file_index += 1
                    file_path = os.path.join(output_dir, f"{file_index}")

            # 循环多加一个序号
            file_index -= 1
            end_time = time.time()
            speed_time.add(float(f"{end_time - start_time:.2f}"))

        except OSError as e:
            if e.errno == 28:  # errno.ENOSPC: No space left on device
                total, used, free = get_disk_space(disk_path)
                if FILE_SIZE < free:
                    raise OSError("错误：磁盘IO异常，请手动重启服务器或插拔磁盘")
                DISK_SPACE = False
                text = f"提示：磁盘空间剩余可用空间小于最低模板大小，保留空间{DECIMAL_CONVERSION(free)}"
                print(text)
                logging.info(text)
            else:
                print(f"发生错误：{e}")
                DISK_SPACE = False
        except Exception as e:
            print(f"写入文件发生错误：{e}")
            DISK_SPACE = False

    # 判断最大文件是否存在
    while not os.path.isfile(os.path.join(output_dir, f"{file_index}")):
        file_index -= 1
    TOTAL_INDEX = file_index
    set_check_index('TOTAL_INDEX', file_index)
    text ="Completed generating files"
    logging.info(text)

def get_percent(numerator, denominator):
    """
    返回分数的值
    :param numerator: 分子 (int)
    :param denominator: 分母 (int)
    :return: 分数的值 (str)
    """
    NUMERATOR = int(numerator)
    DENOMINATOR = int(denominator)
    if not DENOMINATOR:
        return "0.00%"
    return f"{((NUMERATOR / DENOMINATOR) * 100):.2f}%"

def set_check_index(key, index):
    config['DEFAULT'][key] = str(index)
    with open("config.ini", "w") as configfile:
        config.write(configfile)

def check_files(directory):
    """
    遍历指定目录中的所有文件验证文件内容是否全部为数字 '1'。
    """
    global BAD_TRACK_LIST,FILE_SIZE,TOTAL_INDEX
    if not os.path.exists(directory):
        print(f"目录不存在：{directory}")
        return

    if not os.path.isdir(directory):
        print(f"路径不是一个目录：{directory}")
        return
    print(f"读取到生成文件路径'{BADBLOCKS_PATH}'中填充文件总数为：{TOTAL_INDEX}")
    print(f"读取到生成文件路径'{BADBLOCKS_PATH}'中填充文件已检测：{CHECK_INDEX}")
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        if int(filename) <= CHECK_INDEX:
            continue
        file_path = os.path.join(directory, filename)

        # 检查文件
        if os.path.isfile(file_path):
            try:
                # 检查文件内容是否全部为数字 '1'
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if not content or not is_file_all_ones(file_path):
                        text = f"文件检测：{file_path} ERROR 总进度: {get_percent(filename, TOTAL_INDEX)}"
                        print(text, end="\r")
                        logging.info(text)
                        raise ValueError(f"文件内容不正确：{file_path}")
                    else:
                        text = f"文件检测：{file_path} OK 总进度: {get_percent(filename, TOTAL_INDEX)}"
                        print(text, end="\r")
                        logging.info(text)
            except KeyboardInterrupt:
                print("\n检测到 Ctrl+C，正在退出程序...")
                print(f"正在写入当前检测文件序号{filename}...")
                set_check_index('CHECK_INDEX', filename)
                sys.exit()
            except Exception as e:
                print(f"读取文件时发生错误：{file_path}，错误信息：{e}")
                surrounding_paths = get_surrounding_paths(directory, Path(file_path).name)
                BAD_TRACK_LIST.extend(surrounding_paths)
                print(f"新增错误列表：{surrounding_paths}")
                # 使用集合去重
                unique_data = set(BAD_TRACK_LIST)
                # 将去重后的数据写入文件
                with open(BAD_TRACK_LIST_PATH, "w", encoding="utf-8") as file:
                    for item in sorted(unique_data):  # 对数据排序后再写入
                        file.write(item + "\n")
    set_check_index('CHECK_INDEX', filename)

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
    if os.path.isdir(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # 检查文件
            if os.path.isfile(file_path):
                if not file_path in BAD_TRACK_LIST:
                    os.remove(file_path)
                    print(f"删除正常文件：{file_path}", end="\r")
                    logging.info(f"os.remove({file_path})")
    else:
        print(f"'{directory}' 不存在!")
        sys.exit()

if IS_CREATE:
    text = "=================================生成填充文件================================="
    print(text)
    logging.info(text)
    create_4kb_files_until_full(BADBLOCKS_PATH)
    text = "=================================生成填充文件 OK=============================="
    print(text)
    logging.info(text)

if IS_CHECK:
    text = "=================================检查填充文件================================="
    print(text)
    logging.info(text)
    check_files(BADBLOCKS_PATH)
    text = "=================================检查填充文件 OK=============================="
    print(text)
    logging.info(text)

if IS_DEL:
    text = "=================================删除填充文件================================="
    print(text)
    logging.info(text)
    del_right_file(BADBLOCKS_PATH)
    text = "=================================删除填充文件 OK=============================="
    print(text)
    logging.info(text)
