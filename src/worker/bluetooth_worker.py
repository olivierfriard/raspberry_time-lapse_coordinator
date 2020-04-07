"""
bluetooth client for Raspberry Pi
"""

# require pybluez 
# apt install bluetooth libbluetooth-dev
# python3 -m pip install pybluez)
import bluetooth

import os
import sys
import logging
import datetime
import time
import json
import socket
import subprocess
import pathlib
import threading
import binascii
from picamera import PiCamera

from config import *

__version__ = "0.0.3"
__version_date__ = "2020-04-02"

try:
    camera = PiCamera()
    CAMERA_ENABLED = True
except:
    CAMERA_ENABLED = False

HOSTNAME = socket.gethostname()

LOG_FILENAME = HOSTNAME + ".log"
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
)

# read local bluetooth addr
LOCAL_BLUETOOTH_ADDR = bluetooth.read_local_bdaddr()[0]
print("Local Bluetooth addr: ", LOCAL_BLUETOOTH_ADDR)

def remove_time_lapse_info():
    if os.path.isfile("time_lapse_info.txt"):
        os.remove("time_lapse_info.txt")
        log("time_lapse_info.txt deleted")


def date_iso():
    return datetime.datetime.now().isoformat().split(".")[0].replace("T", "_")


def log(msg):
    """
    write message to log

    Args:
        msg (str): message to write
    """

    logging.info(f'{date_iso().replace("_", " ")}: {msg}')


def take_one_picture(hostname, directory, width=640, height=380):
    """
    take one picture with resolution width / height 

    Args:
        hostname (str): raspberry hostname to add to file name
        directory (str): directory where the picture will be saved
        width (int): horizontal resolution of picture
        height (int): vertical resolution of picture
    
    Returns:
        bool: False if OK else True
        str: path of picture file / error code
    """

    try:
        camera.resolution = (width, height)
        pict_file_name = str(pathlib.Path(directory) / "{hostname}_{file_name}.jpg".format(hostname=hostname,
                                                                                           file_name=date_iso()))
        camera.capture(pict_file_name)
        return False, pict_file_name
    except:
        return True, str(sys.exc_info()[0])


class Time_lapse(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         daemon=daemon)
        self.args = args
        self.kwargs = kwargs
        self.finish = False

    def run(self):

        if datetime.datetime.now().isoformat() > self.kwargs["end"]:
            log("time out of interval")
            remove_time_lapse_info()
            return

        width, height = [int(x) for x in self.kwargs["resolution"].split("x")]
        camera.resolution = (width, height)
        while True:

            t1, t2 = 0, 0
            if (self.kwargs["start"] and self.kwargs["end"] 
                and self.kwargs["start"] <= datetime.datetime.now().isoformat() <= self.kwargs["end"]):

                t1 = datetime.datetime.now()
                pict_file_name = str(pathlib.Path(self.kwargs["directory"]) / "{prefix}_{file_name}.jpg".format(prefix=self.kwargs["prefix"],
                                                                                 file_name=date_iso()))

                camera.capture(pict_file_name)
                log("picture saved {}".format(pict_file_name))

                # os.system("convert {pict_file_name} -resize 128x128 {pict_file_name}.resized128.jpg".format(pict_file_name=pict_file_name))
                # sendMessageTo(MASTER_BLUETOOTH_MAC, "picture saved {}".format(pathlib.Path(pict_file_name).name))
                t2 = datetime.datetime.now()

            if t1 and t2:
                to_wait = self.kwargs["interval"] - (t2 - t1) / datetime.timedelta (seconds=1)
                if to_wait > 0:
                    time.sleep(to_wait)
            else:
                time.sleep(self.kwargs["interval"])

            if datetime.datetime.now().isoformat() > self.kwargs["end"]:
                log("Time lapse finished: time out of time lapse interval")
                sendMessageTo(MASTER_BLUETOOTH_MAC, "Time lapse finished: time out of time lapse interval")
                remove_time_lapse_info()
                return

            if self.finish:
                log("Time lapse finished")
                sendMessageTo(MASTER_BLUETOOTH_MAC, "Time lapse finished")
                remove_time_lapse_info()
                return


def time_lapse(interval=60, directory="/tmp", hostname="", start="", end="", prefix="", resolution="1640x1232"):

    thread_tl = Time_lapse(args=(1,), kwargs={"interval": interval,
                                              "directory": directory,
                                              "hostname": hostname,
                                              "start": start,
                                              "end": end,
                                              "prefix": prefix,
                                              "resolution": resolution})
    thread_tl.start()

    with open("time_lapse_info.txt", "w") as f:
        f.write("{}\n{}\n{}\n".format(interval, start, end))
    return thread_tl
 

def receiveMessages():
    """
    receive message by bluetooth on port 1
    """

    try:
        server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = 1
        server_sock.bind(("", port))
        server_sock.listen(1)
        client_sock,address = server_sock.accept()
        data = client_sock.recv(1024)
        client_sock.close()
        server_sock.close()

        return True, address[0], data.decode("utf-8")
    except KeyboardInterrupt:
        return False, "", "quit"
    except:
        return False, "", sys.exc_info()


def sendMessageTo(targetBluetoothMacAddress, msg):
    """
    send message msg via bluetooth to target

    Args:
        targetBluetoothMacAddress (str): bluetooth address of receiver
        msg (dict): dictionary containing message to be sent. if "picture" key exists send image

    Returns:
        int: 0 -> OK 1 -> error
        str: error message (if any)
    """

    try:
        port = 2
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((targetBluetoothMacAddress, port))

        dict_to_send = {"hostname": HOSTNAME,
                        "bluetooth_address": LOCAL_BLUETOOTH_ADDR,
                        "datetime": date_iso()}
        dict_to_send = {**dict_to_send, **msg}

        sock.send(str(dict_to_send))

        sock.close()
        return 0, ""
    except:
        raise
        return 1, str(sys.exc_info()[0])

log("started")
remove_time_lapse_info()

thread_tl_main = None

while True:

    ok, address, msg = receiveMessages()

    # CTRL + C
    if not ok and msg == "quit":
        sys.exit()

    log("received from {address}: {msg}".format(address=address, msg=msg))

    if msg == "status":
        log("sending status")
        p = pathlib.Path(PICTURES_DIR)
        nb_pict = len(list(p.glob("*.jpg")))
        msg_tl = os.path.isfile("time_lapse_info.txt")

        r, msg = sendMessageTo(MASTER_BLUETOOTH_MAC,
                                {"msg": "status",
                                 "status": "OK",
                                 "local time": date_iso().replace("_", " "),
                                 "epoch": time.time(),
                                 "number of pict": nb_pict,
                                 "version installed": __version__,
                                 "camera enabled": CAMERA_ENABLED,
                                 "time lapse running": os.path.isfile("time_lapse_info.txt")
                                })
        log("Error sending status" if r else "status sent")


    if msg == "quit":
        if thread_tl_main:
            thread_tl_main.finish = True
        log("exited")
        sys.exit()


    if msg == "get_log":
        r, msg = sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": open(HOSTNAME + ".log", "r").read()})
        log(f"Error during log file transmission: {msg}" if r else "log file transmitted")


    if "one_picture*" in msg:

        if not CAMERA_ENABLED:
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"The camera is not enabled on this raspberry"})
            continue
        try:
            _, width_height = msg.split("*")
            w, h = [int(x) for x in width_height.split("x")]
        except:
            log(f"one picture wrong parameters: {msg}")
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"one picture wrong parameters {msg}"})
            continue

        r, return_msg = take_one_picture(HOSTNAME, PICTURES_DIR, width=w, height=h)
        if r:
            log(f"error taking one picture: {return_msg}")
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"error taking one picture: {return_msg}"})

        else:
            log(f"picture saved in {return_msg}")

            msg = {"picture": {"file_name": pathlib.Path(return_msg).name}}
            msg["picture"]["file_content"] = open(return_msg, "rb").read()

            r, return_msg =sendMessageTo(MASTER_BLUETOOTH_MAC, msg)

            log(f"Error: {return_msg}" if r else "image sent")


    if "time_lapse|" in msg:
        if not CAMERA_ENABLED:
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"The camera is not enabled on this raspberry"})
            continue
        if os.path.isfile("time_lapse_info.txt"):
            log("time lapse is already running")
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": "Time lapse is already running"})
            continue

        try:
            _, cmd_str = msg.split("|")
            cmd_json = json.loads(cmd_str)
        except:
            log(f"Error in time lapse parameters: {msg}")
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f'Error in time lapse parameters {msg}'})
            continue

        if cmd_json["start"] >= cmd_json["end"]:
            log(f'Error in time lapse parameters: from {cmd_json["start"]} to {cmd_json["end"]}')
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f'Error in time lapse parameters: from {cmd_json["start"]} to {cmd_json["end"]}'})
            continue

        log((f'start time lapse for exp {cmd_json["prefix"]} every {cmd_json["interval"]} s '
             f'from {cmd_json["start"]} to {cmd_json["end"]} resolution {cmd_json["resolution"]}'))

        thread_tl_main = time_lapse(start=cmd_json["start"],
                                    end=cmd_json["end"],
                                    interval=cmd_json["interval"],
                                    prefix=cmd_json["prefix"],
                                    resolution=cmd_json["resolution"],
                                    directory=PICTURES_DIR,
                                    hostname=HOSTNAME,
                                    )

        log("time lapse started")
        sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": "Time lapse started"})


    # stop time lapse
    if msg == "stop_time_lapse":
        if not CAMERA_ENABLED:
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"The camera is not enabled on this raspberry"})
            continue
        if threading.active_count() > 1:
            if thread_tl_main:
                thread_tl_main.finish = True
        else:
            log("No time lapse is running")
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": "No time lapse is running"})


    if "command***" in msg:
        try:
            _, command = msg.split("***")
            log("execute: " + command)
        except:
            log("error in " + command)
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"Error in {command}"})
            continue
        try:
            output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()

            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"command output:\n{output.decode('utf-8')}"})
        except:
            log("error executing  " + command)
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"Error executing {command}"})


    if "sync_time*" in msg:
        try:
            _, date, hour = msg.split("*")
        except:
            log("error in sync time parameters " + msg)
            sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f"error in sync time parameters: {msg}"})
            continue
        completed = subprocess.run(['sudo', 'timedatectl', 'set-ntp', '0'])
        if completed.returncode:
             log("Error in timedatectl set-ntp 0")
             sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": "error in timedatectl set-ntp 0 command"})
             continue

        completed = subprocess.run(['sudo', 'timedatectl','set-time', "{date} {hour}".format(date=date, hour=hour)]) # 2015-11-23 10:11:22

        if completed.returncode:
             log(f"Error in timedatectl set-time '{date} {hour}'")
             sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": "time NOT synchronized"})
        else:
             log(f"time synchronized {date} {hour}")
             sendMessageTo(MASTER_BLUETOOTH_MAC, {"msg": f'time synchronized\nRaspberry time is now {date_iso().replace("_"," ")}'})
