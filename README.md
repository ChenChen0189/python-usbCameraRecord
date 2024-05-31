# python-usbCameraRecord
通过cv2库，来控制 camera 或 hdmi 采集卡进行录像

logging_init()  # 初始化 logging
path = create_directory()   # 创建目录
id = show_and_select_camera()   # 显示摄像头列表并选择摄像头
my_camera = USBRecord(device_index=id, frame_resolution=(1280, 720), frame_rate=60)     # 初始化摄像头对象
my_camera.open_record_camera()      # 打开摄像头
time.sleep(1)
my_camera.show_live_camera()        # 显示摄像头画面
time.sleep(1)
video_thread = start_thread(my_camera.start_record, args=(path, "直播切台", 1, 60))     # 录像起进程（路径，计数，录像超时时间）
time.sleep(3)
my_camera.start_time_mark()     # enable 时间戳，视频开始左上角记录时间戳，从 0 开始 HH:MM:SS.000
time.sleep(10)
my_camera.stop_record(video_thread)     # 停止录像
time.sleep(1)
my_camera.video_slice()     # 视频切片，后处理
my_camera.release_camera()  # 释放摄像头资源
