from PIL import Image

class SensorDeviceDummy:
    """Minimal dummy sensor for debugging."""
    def __init__(self):
        self.connected = False
        self.addr = 'localhost'
        self.port = 8888

    def open(self, addr='localhost', port=8888):
        self.addr = addr
        self.port = port
        self.connected = True
        print(f"Dummy sensor open at {addr}:{port}")

    def close(self):
        if self.connected:
            print("Dummy sensor closed")
        self.connected = False

    def get_shutter(self):
        print("Dummy get_shutter")
        return 30000

    def set_shutter(self, shutter):
        print(f"Dummy set_shutter {shutter}")

    def get_gainiso(self):
        print("Dummy get_gainiso")
        return 400

    def set_gainiso(self, gainiso):
        print(f"Dummy set_gainiso {gainiso}")

    def get_lasers(self):
        print("Dummy get_lasers")
        return 0

    def set_lasers(self, pattern):
        print(f"Dummy set_lasers {pattern}")

    def get_image(self, avgcount):
        print(f"Dummy get_image {avgcount}")
        return Image.new('L', (640, 480))

    def get_frame(self):
        print("Dummy get_frame")
        return None

    def get_stats(self):
        print("Dummy get_stats")
        return "dummy stats"
