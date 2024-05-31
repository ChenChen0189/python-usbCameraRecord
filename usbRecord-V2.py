# !/usr/bin/python
# -*- coding: UTF-8 -*-
# @Time      : 2024/4/26 21:41
# @Filename  : usbRecord.py
# @Author    : Chen.Chen
# @software  : PyCharm

import cv2
import os
import time
import logging
import sys
import threading
import pygame.camera
from rich.logging import RichHandler


def logging_init() -> None:
    """ logger初始化. """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(
        RichHandler(rich_tracebacks=True, tracebacks_show_locals=True, log_time_format="[%Y/%m/%d %H:%M:%S]",
                    keywords=['Camera'], omit_repeated_times=False))


def create_directory():
    """在脚本同级创建命名为Picture的目录, 然后脚本每次执行时会创建新的子目录, 并以时间戳来命名"""
    main_dir = "Videos"
    current_dir = os.getcwd()
    main_dir_path = os.path.join(current_dir, main_dir)

    # 如果主目录不存在，则创建它
    if not os.path.exists(main_dir_path):
        os.makedirs(main_dir_path)

    # 获取当前时间，并格式化为字符串（年月日_时分秒）
    time_str = time.strftime("%Y%m%d_%H%M%S")
    sub_dir_path = os.path.join(main_dir_path, time_str)

    # 创建子目录
    os.makedirs(sub_dir_path)
    return sub_dir_path


def start_thread(target, args):
    """
    创建并启动一个线程。
    参数:
    - target: 要在线程中执行的可调用对象。
    - args: 传递给目标函数的参数元组。
    返回值:
    - 启动的线程对象。
    如果传入的target不是可调用对象，将记录错误并退出程序。
    如果在启动线程时发生异常，将记录错误并退出程序。
    """
    try:
        # 检查target是否为可调用对象
        if not callable(target):
            logging.error(f'The incoming target argument must be a callable object!')
            sys.exit(1)
        # 创建线程对象，并传入执行目标和参数
        thread = threading.Thread(target=target, args=args)
        thread.start()  # 启动线程
        logging.info(f"Thread start: ID={thread.ident}, Target={thread.name}")  # 记录线程启动信息
        return thread
    except Exception as e:
        logging.error(f"An error occurred while starting the thread: {e}")  # 记录启动线程时的异常
        sys.exit(1)


def show_and_select_camera():
    """检测、显示可用摄像头，并返回手动所选择Camera的编号。

    使用 pygame 来检测设备连接的摄像头列表，如果没有检测到摄像头，程序将打印提示信息并退出。
    如果检测到摄像头，函数将打印出可用的摄像头列表和对应的 ID。
    """
    try:
        pygame.camera.init()  # 初始化 pygame 的摄像头模块
        camera_list = pygame.camera.list_cameras()  # 获取设备上的摄像头列表
    except Exception as e:
        logging.error(f"Failed to initialize cameras or list cameras: {e}")
        sys.exit(1)

    if not camera_list:
        logging.error("Do not find any cameras.")
        sys.exit(1)

    cameras = dict(enumerate(camera_list))  # 创建 ID 到摄像头名称的映射
    cameras_num = len(cameras)
    logging.info(f"Available Cameras as follow, Please choose one: (range: [0-{cameras_num - 1}])")
    logging.info('{:=>50}'.format(''))
    for id, dev in cameras.items():
        logging.info(f"{id} : {dev}")
    logging.info('{:=>50}'.format(''))

    index = int(input(f'Please select the camera index from [0-{cameras_num - 1}]:'))
    if 0 <= index < cameras_num:
        camera = cameras[index]
        logging.info(f'You selection is: [ {index}: {camera} ]')
        return index
    else:
        logging.error(f'Out of the selection range, please select again!')
        sys.exit(1)


def format_time(times):
    """
    将时间（毫秒）格式化为HH:MM:SS.xxx的形式。
    参数:
    times - 表示时间的毫秒数。
    返回值:
    格式化后的时间字符串，其中HH表示小时，MM表示分钟，SS表示秒，xxx表示毫秒。
    """
    # 将总毫秒数分解为秒和毫秒
    seconds, ms = divmod(times, 1000)
    # 将秒数分解为小时和剩余的秒数
    hours, remainder = divmod(seconds, 3600)
    # 将剩余的秒数分解为分钟和秒
    minutes, seconds = divmod(remainder, 60)
    # 格式化时间为HH:MM:SS.xxx的形式，并返回
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def draw_timestamp(frame, timestamp_text):
    """
    在给定的帧上绘制时间戳文本。
    参数:
    frame: numpy.ndarray - 输入的视频帧，将在此帧上绘制时间戳。
    timestamp_text: str - 要绘制在帧上的时间戳文本。
    返回值:
    无。此函数直接在输入的frame上绘制文本并修改它。
    """
    # 设定字体和字体大小
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    # 设定字体颜色和线条类型
    font_color = (255, 255, 255)
    line_type = 2
    # # 计算文本大小，以便正确地在帧上定位它
    # text_size, _ = cv2.getTextSize(timestamp_text, font, font_scale, line_type)
    # 确保性能，直接定死文字位置
    text_origin = (10, 30)
    # text_origin = (10, 10 + text_size[1])
    # 在帧上绘制时间戳文本
    cv2.putText(frame, timestamp_text, text_origin, font, font_scale, font_color, line_type)


class USBRecord:
    def __init__(self, device_index=0, frame_resolution=(1280, 720), frame_rate=60,
                 is_stop_record=False, is_record_mark=False):
        """
        初始化 USB 摄像头。
        该方法用于初始化USB摄像头的相关配置，包括设备索引、帧分辨率、帧率等。
        初始化后，摄像头对象尚未开启，需要调用相关方法来启动摄像头。
        :param device_index: 设备索引，通常默认摄像头是 0。根据计算机上连接的摄像头数量，可以指定不同的索引来选择特定的摄像头。
        :param frame_resolution: 分辨率，以元组形式 (宽度, 高度)。可以根据需求设置不同的分辨率，例如(1280, 720)表示720P分辨率。
        :param frame_rate: 摄像头的帧率。通常，帧率越高，视频越流畅。可以根据需要设置不同的帧率，例如60帧/秒。
        :param is_stop_record: 是否停止录像标志。默认为False
        :param is_record_mark: 是否enable视频时间戳标志。默认为False
        """
        self.device_index = device_index
        self.frame_resolution = frame_resolution
        self.frame_rate = frame_rate
        self.camera = None  # 初始化时，摄像头对象未设置
        self.is_stop_record = is_stop_record
        self.act_frame_width = None  # 实际帧宽度，初始化为None，使用时会根据摄像头的实际能力进行设置
        self.act_frame_height = None  # 实际帧高度，初始化为None，使用时会根据摄像头的实际能力进行设置
        self.act_frame_fps = None  # 实际帧率，初始化为None，使用时会根据摄像头的实际能力进行设置
        self.record_mark = is_record_mark  # 是否enable录像时间戳
        self.start_mark_time = None  # 记录开始标记的时间，初始化为None，当开始记录时设置
        self.record_name = None     # 视频名称，初始化为None
        self.filename = None     # 完整录像路径+文件名，初始化为None
        self.save_path = None   # 初始化保存路径，初始化为None

    def open_record_camera(self):
        """尝试打开摄像头并设置分辨率与帧率。"""
        try:
            self.camera = cv2.VideoCapture(self.device_index)
            if not self.camera.isOpened():
                self.camera.open(self.device_index)

            # 增加延时保护
            time.sleep(1)

            # 设置摄像头分辨率
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_resolution[1])
            # 设置摄像头帧率
            self.camera.set(cv2.CAP_PROP_FPS, self.frame_rate)
            # 尝试设置自动对焦
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            # 获取摄像头的实际分辨率和帧率
            self.act_frame_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.act_frame_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.act_frame_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            logging.info(
                f"Current Camera with configuration: "
                f"index: {self.device_index}, resolution: {self.act_frame_width}x{self.act_frame_height}, "
                f"frame rate: {self.act_frame_fps}fps")
        except Exception as e:
            logging.error(f"Failed to open the camera: {e}")

    def show_live_camera(self, timeout=60):
        """
        检测指定 camera 状态，并有 60 秒画面出图，进行镜头位置调整
        :return: None
        """
        start_time = time.time()
        while True:
            # 计算剩余的倒计时时间，使用 60 进制
            elapsed_time = time.time() - start_time
            remaining_time = max(0, int(timeout - elapsed_time))
            remaining_minute = remaining_time // 60
            remaining_second = remaining_time % 60
            countdown_clock = f"Countdown Clock: {remaining_minute:02d}:{remaining_second:02d}"
            # 读取图像
            ret, frame = self.camera.read()
            if not ret:     # 判断是否可以收到 camera frame，不能接收报错退出
                self.camera.release()
                logging.error(f"Can not receive camera_id:{self.device_index} frame")
                sys.exit(1)
            # 在帧上添加文本
            cv2.putText(frame, f'Camera ID: {self.device_index}', (25, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Frame Info: "
                               f"{self.act_frame_width}x{self.act_frame_height}@{self.act_frame_fps}fps", (25, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, countdown_clock, (25, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f'Enter "q" to close windows', (25, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.imshow('frame', frame)
            # 时间超时关闭
            if cv2.waitKey(1) == ord('q') or elapsed_time > timeout:
                break
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    def start_record(self, save_path=None, test_case_name=None, count=None, timeout=60):
        """
        录像功能
        参数:
        - save_path: 保存视频的路径
        - test_case_name: 用以区分不同测试案例的名称
        - count: 用于区分同一测试案例下不同视频的计数器
        - timeout: 录制视频的最长时间（秒），默认为60秒。
        无返回值
        """
        # 初始化录像标志，record_mark是视频时间戳；is_stop_record是停止录像标志
        self.record_mark = False
        self.is_stop_record = False
        self.save_path = save_path
        # 检查摄像头是否打开，如果未打开，则尝试打开
        if self.camera is None or not self.camera.isOpened():
            logging.warning("Camera is not opened. Trying to open it...")
            self.open_record_camera()
        try:
            # 获取当前时间，用于生成文件名
            now_time = time.strftime("%Y%m%d_%H%M%S")
            self.record_name = f"{test_case_name}_{now_time}_{count}"
            # 拼接路径和文件名
            self.filename = os.path.join(self.save_path, f"{self.record_name}.avi")
            # 创建VideoWriter对象，用于写入视频文件
            fourcc = cv2.VideoWriter.fourcc(*'XVID')
            writer = cv2.VideoWriter(self.filename, fourcc,
                                     self.act_frame_fps, (self.act_frame_width, self.act_frame_height))
            # 定义录像其实时间，用于计算录像总时长
            logging.info(f"Start recording")
            start_time = time.time()
            while True:
                # 读取摄像头的帧
                ret, frame = self.camera.read()
                if ret:
                    # enable时间戳，每帧添加时间戳
                    if self.record_mark:
                        if self.start_mark_time is None:
                            self.start_mark_time = time.time()
                        current_time = time.time() - self.start_mark_time
                        timestamp_text = format_time(int(current_time * 1000))
                        draw_timestamp(frame, timestamp_text)
                    # 将帧写入输出文件
                    writer.write(frame)
                    # 获取当前时间并计算录制时间
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    # 如果 is.stop_record标志为True或录制时间超过设定值，停止录制
                    if self.is_stop_record or elapsed_time >= timeout:
                        logging.info(f"Stop record")
                        logging.info(f"Video saved as: {test_case_name}_{now_time}_{count}.avi")
                        break
                else:
                    logging.warning("Failed to capture image from camera.")
        except Exception as e:
            logging.error(f"Error capturing and saving image: {e}")

    def start_time_mark(self):
        """
        开始记录标记的函数
        该方法用于开始记录一个标记，主要是通过设置记录标记的状态和记录开始标记的时间。
        参数:
        - is_record_mark (bool): 是否开始记录标记，默认为True。
        返回值:
        无
        """
        self.record_mark = True  # 更新记录标记的状态为 True
        self.start_mark_time = None  # 记录标记开始的时间

    def stop_record(self, target):
        """
        停止录像函数，并停止录像线程。
        参数:
        - target: 目标线程对象，需要停止录像的线程。
        - is_stop_record: 一个布尔值，指定是否停止记录。默认为True。
        返回值: 无
        """
        self.is_stop_record = True  # 更新停止录像标志为 True
        try:
            target.join()   # 尝试加入目标线程，等待其完成
            # 记录线程关闭信息
            logging.info(f"Thread closed: ID={target.ident}, Target={target.name}")
        except AttributeError as e:
            logging.error(f"Invalid thread object: {e}")
        except RuntimeError as e:
            logging.error(f"Error when joining thread: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def video_slice(self):
        """
        从视频中逐帧提取图像并保存到指定目录。
        方法会为每个帧创建一个JPEG图像文件，文件名包含帧计数器的值。
        参数:
        - self: 类实例，需要包含视频文件名（self.filename）和记录名称（self.record_name）。
        返回值: 无
        """
        frame_capture = None    # 初始化视频帧捕获对象
        # 创建子记录目录
        sub_record_dir_path = str(os.path.join(self.save_path, self.record_name))
        if not os.path.exists(sub_record_dir_path):
            os.makedirs(sub_record_dir_path)
        # 初始化帧计数器
        frame_count = 0
        try:
            # 打开视频文件
            frame_capture = cv2.VideoCapture(self.filename)
            if not frame_capture.isOpened():
                logging.error("Failed to open video file.")
                sys.exit(1)
            # 逐帧读取并保存视频帧
            while True:
                ret, frame = frame_capture.read()
                if ret:
                    # 构造并保存当前帧的图像文件
                    video_frame = os.path.join(sub_record_dir_path, f"{self.record_name}_frame_count_{frame_count}.jpg")
                    cv2.imwrite(video_frame, frame)
                    frame_count += 1
                else:
                    # 遇到视频末尾，退出循环
                    break
            logging.info(f"Record has been sliced: {sub_record_dir_path}")
        except Exception as e:
            logging.error(f"An error occurred during processing: {e}")
        finally:
            # 确保释放视频文件的资源
            frame_capture.release()

    def release_camera(self):
        """释放摄像头资源。"""
        if self.camera:
            self.camera.release()
            logging.info("Camera resources have been released.")

    def __del__(self):
        """确保摄像头资源被正确释放。"""
        self.release_camera()


# Example Usage:
if __name__ == "__main__":
    logging_init()
    path = create_directory()
    id = show_and_select_camera()
    my_camera = USBRecord(device_index=id, frame_resolution=(1280, 720), frame_rate=60)
    my_camera.open_record_camera()
    time.sleep(1)
    my_camera.show_live_camera()
    time.sleep(1)
    video_thread = start_thread(my_camera.start_record, args=(path, "直播切台", 1, 60))     # 录像起进程（路径，计数，录像超时时间）
    time.sleep(3)
    my_camera.start_time_mark()     # enable 时间戳，视频开始左上角记录时间戳，从 0 开始 HH:MM:SS.000
    time.sleep(10)
    my_camera.stop_record(video_thread)     # 停止录像
    time.sleep(1)
    my_camera.video_slice()     # 视频切片，后处理
    my_camera.release_camera()
