# Jetson_nano_t265使用2025_3_21

## 方法一
---

使用提前制作好的镜像，优点是不会在这上面耗费太多时间，缺点是如果需要根据需求修改部分代码会摸不着头脑。

### 一、镜像下载与烧录

1. 下载链接：
   https://pan.quark.cn/s/81c8e362904b
2. 烧录镜像可以参考这个教程：
   https://blog.csdn.net/weixin_44222088/article/details/135616176
   
   或者这个视频：
   https://www.bilibili.com/video/BV1WV4y1d7s6/?share_source=copy_web&vd_source=1f085
3. 密码我没记错应该是100860

### 二、T265使用

1. 建议用原厂线连接T265与nano，非原厂的可能会出问题，比如数据传输到一半突然掉线，我之前遇到过这种问题，你们可以在淘宝再找找能用的非原厂线。
2. 运行nano.py这个文件，应该能在终端看到坐标输出，T265的坐标可以参考《t265使用说明》。

### 三、nano与飞控的通信

1. nano的引脚定义图：
   https://blog.csdn.net/gr1423428723/article/details/132698823
2. 串口的修改：
   ```python
   def serial_open(n=0):
    global COMM
    #serial_port = '/dev/ttyAMA0'
    serial_port = '/dev/ttyTHS1'
    #serial_port = set_com_port(n)
    COMM = serial.Serial(serial_port, 115200, timeout=0.01)
    if COMM.isOpen():
        print(serial_port, "open success")
        return 0
    else:
        print("open failed")
        return 255
   ```
   在上面的代码块中，serial_port只能有一条不被注释，serial_port = '/dev/ttyTHS1'代表使用nano的自带的串口，serial_port = '/dev/ttyAMA0'是树莓派自带的串口，serial_port = set_com_port(n)是外置的usb转ttl串口。




## 方法二
---------


要求：
   1. 有 Linux 基础
   2. 了解 Systemd
   3. 了解 Python 
   4. 了解 Cmake 和 make 等 GCC 工具链，必要的情况下还会使用交叉编译

如果都不会？那也没有关系，**Google + AI + 积极求索的心** 足以解决这些并不困难的问题

### 一、介绍

要使用 T265 深度相机，首先需要明白 T265 是什么：T265 是由 Intel 公司研发的一款专门为室内定位和导航设计的视觉惯性里程计 (VIO) 模块。

简单来说，T265 就像是室内环境的 GPS，它能够让机器人、无人机等在没有外部定位系统（如 GPS）的情况下，自主感知自身在空间中的位置和姿态。

它通过结合双目鱼眼摄像头和 IMU，利用 VIO 和 SLAM 技术，获得小范围环境下的高精度坐标。经实际使用测量，在 10m² 的室内长时间飞行精度可以控制在 10cm 以内，是电赛赛题的大杀器。


相关文档链接：
   - [librealsense](https://github.com/IntelRealSense/librealsense)
   - [Introduction to Intel® RealSense™ Visual SLAM and the T265 Tracking Camera](https://dev.intelrealsense.com/docs/intel-realsensetm-visual-slam-and-the-t265-tracking-camera)
   - [Intel® RealSense™ Tracking Camera T265 and Intel® RealSense™ Depth Camera D435 - Tracking and Depth](https://dev.intelrealsense.com/docs/depth-and-tracking-cameras-alignment)
   

### 二、开发

有关安装方式等外部问题请参阅上述文档，以下只讨论如何开发 T265 。

#### 1.任务组成

思考各个部件的作用，你会发现 T265 用于获得坐标，JetsonNano (也可以是其他 Linux 开发版) 用于当作 T265 的载体，调用 T265 并将坐标数据传输至飞控。因此我们可以得到如下关系：
   - T265
      - 求得坐标数据
   - JetsonNano:
      - 调用 T265 获得坐标数据
      - 将数据传输至飞控

关于 T265 自身不需要我们过多关注，只需要关注 JetsonNano 。

#### 2.坑

由于 T265 早在 2021 年就已停产，因此新版的 librealsense SDK 是不支持 T265 的，最后一个明确支持 T265 的版本是 2.50.0 。

系统及语言支持详见 [Intel® RealSense™ SDK 2.0 v2.50.0](https://github.com/IntelRealSense/librealsense/releases/tag/v2.50.0) 。
   - 值得注意的是：
      - Ubuntu: `16.04/18.04/20.04 LTS (1) . Kernel versions: 4.[4, 8,10,13,15], 4.16(4) , 4.18, 5.[0, 3, 4, 8]`
      - Python: `2.7/3.5/3.6/3.7/3.8/3.9`

如果你搜过一些教程的话会发现有一个叫 pyrealsense2 的包貌似可以直接调用 T265 ，首先恭喜你通过搜索找到了一些有效信息，但是不幸的是，这个包和 librealsense SDK 一样新版本移除了对 T265 的支持，而 2.50.0 的包唯独没有发布 aarch64.whl, 所以它在 JetsonNano 同样不适用。参考：[pyrealsense2 2.50.0.3812](https://pypi.org/project/pyrealsense2/2.50.0.3812/#files) 。

有了前人（我）趟过的坑，接下来你的路就好走多了！

#### 3.编译安装 SDK

这部分时间已久我也记不清个中细节，是参考网上内容所写，因此无法保证能够完全复现，如果遇到问题还请积极查阅资料！

1. Clone 源代码
   ```bash
   git clone --depth 1 --branch v2.50.0 https://github.com/IntelRealSense/librealsense librealsense-2.50.0
   ```

2. 安装依赖
   ```bash
   sudo apt update
   sudo apt install libudev-dev pkg-config libgtk-3-dev libusb-1.0-0-dev pkg-config libglfw3-dev libssl-dev
   ```

3. 安装权限脚本（感兴趣的可以去查查 udev）
   ```bash
   cd librealsense-2.50.0/
   sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
   sudo udevadm control --reload-rules && udevadm trigger
   ```
4. 编译
   ```bash
   mkdir build
   cd build
   cmake ../ -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS:bool=true -DPYTHON_EXECUTABLE=/usr/bin/python3
   sudo make uninstall
   make clean && make
   sudo make install
   ```

   编译完成之后，应该会有一个叫作 `realsense-viewer` 的软件，此时插上你的 T265 ，再打开这个软件就能看到 T265 回传的图像和坐标信息了。

5. 添加环境变量
   如果编译没出问题的话，就会在 `/usr/local/lib/python3.<x>/`下生成 pyrealsense2 库。
   然后用你喜欢的编辑器打开 `~/.bashrc`，
   在最后添加：
   ```sh
   export PYTHONPATH=$PYTHONPATH:/usr/local/lib:/usr/local/lib/python3.<x>/pyrealsense2
   ```
   注意这里的 `python3.<x>` 替换为你实际的 python 版本。

如果上述都没出问题的话，那么恭喜你🎉，终于可以开始写代码了！

#### 4.使用 T265

代码都在我的仓库里：[Simply_Using_T265_on_Jetson](https://github.com/lalafua/Simply_Using_T265_on_Jetson)，欢迎 Star !

Python 脚本部分比较简单，再此不做赘述，这个脚本只用到了 T265 很少最基础的一部分功能，但已足够完成任务，感兴趣的可以深入研究研究 T265 , T265 的强大超乎你的想象！ 
<details>
<summary>run_T265.py</summary>

```python
import pyrealsense2 as rs
import time, struct
import serial, binascii

class program():
    def __init__(self):
        # pipeline init
        print("pipeline init...")
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.pose)
        self.pipeline.start(config)

        # serial init
        print("serial init...")
        self.ser = serial.Serial('/dev/ttyTHS1', 500000, timeout=2, bytesize=serial.EIGHTBITS, \
                                  stopbits=serial.STOPBITS_ONE)

        # header and tail
        self.header_frame = struct.pack("BBBBB", 0xAA, 0x29, 0x05, 0x43, 0x06) # header 0x43:T265 device 
                                                                                     # 0x06: data length

    def getPoseData(self):
        frames = self.pipeline.wait_for_frames()
        pose = frames.get_pose_frame()
        if pose:
            data = pose.get_pose_data()
            # return translation(m), velocity(m/s), accleration(m/s2)
            return (data.translation, data.velocity, data.acceleration)
        else:
            return None
        
    def start(self):
        print("start program...")
        while True:
            max_retries = 5
            for i in range(max_retries):
                try:
                    trans, vec, acc = self.getPoseData()
                    # m->cm
                    x, y, z = int(trans.x*100), int(trans.y*100), int(trans.z*100)  
                    
                
                    if self.ser and self.ser.is_open:
                        # coordinate transformation
                        pose_frame = struct.pack('hhh', -z, x, y) # short integer
                        print("x:", -z, "y:", x, "z:", y)
                        he_frame = self.header_frame + pose_frame
                        
                        # sum check
                        sumcheck = sum(he_frame) % 256
                        frame = he_frame + struct.pack("B", sumcheck)
                        self.ser.write(frame)
                        print(binascii.hexlify(frame).decode('ascii'))

                except KeyboardInterrupt:
                    self.stop()
            
                except Exception as e:
                    print("Error:", e)
                    if i < max_retries -1:
                        print("trying to reconnect...")
                        time.sleep(1)

                        self.reconnect()
                    else:
                        print("Failed to reconnect. Exiting...")
                        self.stop()
                        break

    def reconnect(self):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.pose)
        self.pipeline.start(config)
        self.ser = serial.Serial('/dev/ttyTHS1', 500000, timeout=5)


    def stop(self):
        if self.pipeline:
            self.pipeline.stop()
        if self.ser and self.ser.is_open():
            self.ser.close()

if __name__ == "__main__":
    pgmctl = program()
    pgmctl.start()
```

</details>

#### 5.自启动配置

为了方便使用，为 T265 添加自启动配置，使用 `systemd` 可以非常轻松的完成。

clone 我的仓库，启用服务：
```sh
git clone https://github.com/lalafua/Simply_Using_T265_on_Jetson.git
cd Simply_Using_T265_on_Jetson/
sudo cp *.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable T265.service ttyTHS1.service
sudo systemctl start T265.service ttyTHS1.service
```

检查状态：
```sh
sudo systemctl status T265.service
sudo systemctl status ttyTHS1.service
```

<details>
<summary>T265.service</summary>

```sh
[Unit]
Description=T265 device
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python3 /home/nvidia/myjetson/t265dev/test.py
Environment=PYTHONPATH=$PYTHONPATH:/usr/local/lib:~/.local/lib/python3.6/site-packages

[Install]
WantedBy=multi-user.target
```

</details>

<details>
<summary>ttyTHS1.service</summary>

```sh
[Unit]
Description=Set permissions for /dev/ttyTHS1
After=multi-user.target

[Service]
Type=simple
Restart=always
User=root
Group=root
ExecStart=/bin/bash -c 'while true; do chmod 777 /dev/ttyTHS1; sleep 1; done'

[Install]
WantedBy=multi-user.target
```

</details>

### 三、遇到问题

如果遇到**实在无法解决的问题**，欢迎来我的[仓库](https://github.com/lalafua/Simply_Using_T265_on_Jetson)提 issue !

也可以通过邮件与我交流：qtexpsem@gmial.com ，交流之前请确保我能看懂你的问题所在。

**不会回复任何来自 QQ 和 WX 的问题请求**
   



































