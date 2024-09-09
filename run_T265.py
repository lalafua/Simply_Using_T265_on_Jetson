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



