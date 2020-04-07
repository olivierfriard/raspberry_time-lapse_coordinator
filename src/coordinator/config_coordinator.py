# configuration file for bluetooth_coordinator.py

# raspberries list with bluetooth MAC address

RASPBERRY_LIST  = {
    "rasp00": "b8:27:eb:0b:06:8c",
    "rasp01": "b8:27:eb:42:d2:32"
}

# maximum time difference between coordinator and raspberries (in seconds)
MAX_TIME_DIFFERENCE = 10

# directory where files received by bluetooth are saved
RECEIVED_FILES_DIR = "/tmp/"

# seconds between 2 pictures in time lapse mode
DEFAULT_INTERVAL = 20

# number of columns in the interface
GUI_COLUMNS_NUMBER = 2

RECEIVER_BUFFER_SIZE = 1024

RESOLUTIONS = ["3280x2464", "1920x1080", "1640x1232", "1640x922", "1280x720", "640x480"]
DEFAULT_RESOLUTION = 5 # index of RESOLUTIONS (list starts at index 0!)
