"""
Raspberry remote bluetooth control

"""

# require pybluez 
# apt install bluetooth libbluetooth-dev
# python3 -m pip install pybluez)
import bluetooth  

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import sys
import json
import pathlib
import datetime
import time
import subprocess
from functools import partial

from config_coordinator import *

__version__ = "0.0.1"
__version_date__ = "2020-04-07"


class bt_receiver(QThread):
    """
    class for receiving message from raspberries by bluetooth
    """

    received = pyqtSignal(bytes)

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):

        print("bluetooth receiver thread started")

        while True:
            server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

            port = 2
            server_sock.bind(("", port))
            server_sock.listen(1)
        
            client_sock, address = server_sock.accept()
            print("Accepted connection from " + str(address))

            time1 = time.time()
            data = b""
            while True:
                try:
                    data_chunk = client_sock.recv(RECEIVER_BUFFER_SIZE)
                except:
                    break
                if len(data_chunk) == 0:
                    break
                #print("received: {%s}".format(data_chunk))
                data += data_chunk

            print(f"transmission time: {time.time() - time1}")
            #self.received.emit(data.decode("utf-8"))
            self.received.emit(data)
            client_sock.close()
            server_sock.close()


def sendMessageTo(targetBluetoothMacAddress, msg):
    """
    send message to raspberry by bluetooth

    args:
        targetBluetoothMacAddress (str): bluetooth MAC address of receiver
        msg (str): message to send

    Returns:
        bool:
        str:
    """

    try:
        port = 1
        sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((targetBluetoothMacAddress, port))
        sock.send(msg)
        sock.close()
        return False, ""
    except:
        return True, str(sys.exc_info()[0])


def date_iso():
    """
    return current date in ISO 8601 format
    """
    return datetime.datetime.now().isoformat().split(".")[0].replace("T", " ")


class Coordinator(QMainWindow):

    raspberry_msg = {}
    status_list, synctime_list, text_list = [], [], {}
    start_time, end_time, interval, prefix, resolution = {}, {}, {}, {}, {}


    def __init__(self):
        super().__init__()

        self.setWindowTitle("Raspberry coordinator")
        self.statusBar().showMessage("v. " + __version__)

        layout = QVBoxLayout()
        hlayout1 = QHBoxLayout()

        tw = QTabWidget()

        q1=QWidget()

        rasp_count = 0
        group_count = 0
        for rb in sorted(RASPBERRY_LIST.keys()):

            print("Raspberry: {rb}".format(rb=rb))
            rasp_count += 1
            l = QVBoxLayout()
            l.addWidget(QLabel(rb))

            self.text_list[rb] = QTextEdit()
            self.text_list[rb].setLineWrapMode(QTextEdit.NoWrap)
            self.text_list[rb].setFontFamily("Courrier")
            l.addWidget(self.text_list[rb])

            l2 = QHBoxLayout()
 
            self.status_list.append(QPushButton("Status", clicked=partial(self.status, rb)))
            l2.addWidget(self.status_list[-1])

            self.synctime_list.append(QPushButton("Sync time", clicked=partial(self.sync_time, rb)))
            l2.addWidget(self.synctime_list[-1])

            q = QPushButton("Get log", clicked=partial(self.get_log, rb))
            l2.addWidget(q)

            q = QPushButton("Send command", clicked=partial(self.send_command, rb))
            l2.addWidget(q)

            q = QPushButton("Clear output", clicked=partial(self.clear_log, rb))
            l2.addWidget(q)

            l.addLayout(l2)

            l2 = QHBoxLayout()
            l2.addWidget(QLabel("Resolution"))
            self.resolution[rb] = QComboBox()
            for resol in RESOLUTIONS:
                self.resolution[rb].addItem(resol)
            self.resolution[rb].setCurrentIndex(DEFAULT_RESOLUTION)
            l2.addWidget(self.resolution[rb])
            l.addLayout(l2)

            q = QPushButton("Take one picture", clicked=partial(self.one_picture, rb))
            l.addWidget(q)

            l2 = QHBoxLayout()
            q = QPushButton("Start time lapse", clicked=partial(self.start_time_lapse, rb))
            l2.addWidget(q)

            q = QPushButton("Stop time lapse", clicked=partial(self.stop_time_lapse, rb))
            l2.addWidget(q)
            l.addLayout(l2)

            l2 = QHBoxLayout()
            l2.addWidget(QLabel("Start"))
            self.start_time[rb] = QDateTimeEdit()
            self.start_time[rb].setDateTime(QDateTime.currentDateTime())
            self.start_time[rb].setDisplayFormat("yyyy-MM-dd hh:mm:ss")
            l2.addWidget(self.start_time[rb])
            l.addLayout(l2)

            l2 = QHBoxLayout()
            l2.addWidget(QLabel("End"))
            self.end_time[rb] = QDateTimeEdit()
            self.end_time[rb].setDateTime(QDateTime.currentDateTime())
            self.end_time[rb].setDisplayFormat("yyyy-MM-dd hh:mm:ss")
            l2.addWidget(self.end_time[rb])
            l.addLayout(l2)

            l2 = QHBoxLayout()
            l2.addWidget(QLabel("Interval"))
            self.interval[rb] = QSpinBox()
            self.interval[rb].setMinimum(5)
            self.interval[rb].setValue(DEFAULT_INTERVAL)
            l2.addWidget(self.interval[rb])
            l2.addWidget(QLabel("Prefix"))
            self.prefix[rb] = QLineEdit(rb)
            l2.addWidget(self.prefix[rb])

            l.addLayout(l2)

            hlayout1.addLayout(l)
            if rasp_count % GUI_COLUMNS_NUMBER == 0:
                q1.setLayout(hlayout1)
                group_count += 1
                tw.addTab(q1, f"Raspberries group #{group_count}")
                hlayout1 = QHBoxLayout()
                q1 = QWidget()

        if rasp_count % GUI_COLUMNS_NUMBER:
            q1.setLayout(hlayout1)
            tw.addTab(q1, f"Raspberries group #{group_count}")
            hlayout1 = QHBoxLayout()
            q1 = QWidget()

        layout.addWidget(tw)

        # "all" buttons
        hlayout2 = QHBoxLayout()

        pb = QPushButton("Status from all")
        pb.clicked.connect(self.status_all)
        hlayout2.addWidget(pb)

        pb = QPushButton("Sync time all")
        pb.clicked.connect(self.sync_all)
        hlayout2.addWidget(pb)

        pb = QPushButton("Send command to all")
        pb.clicked.connect(self.command_all)
        hlayout2.addWidget(pb)

        pb = QPushButton("Clear all output")
        pb.clicked.connect(self.reset_all)
        hlayout2.addWidget(pb)

        pb = QPushButton("Update all")
        pb.clicked.connect(self.update_all)
        hlayout2.addWidget(pb)

        layout.addLayout(hlayout2)

        main_widget = QWidget(self)
        main_widget.setLayout(layout)
        
        self.setCentralWidget(main_widget)
        
        self.show()

        # set bluetooth receiver thread
        self.bt_receiver_thread = bt_receiver()
        self.bt_receiver_thread.received.connect(self.thread_data_received)
        self.bt_receiver_thread.start()

        # ask status to all raspberries
        self.status_all()


    def rb_msg(self, rb, msg):
        """
        update text_list specific for raspberry rb with message

        Args:
            rb (str): raspberry id
            msg (str): messag to display
        """

        self.text_list[rb].append("{}: {}".format(date_iso(), msg))
        app.processEvents()


    def send_command(self, rb):
        text, ok = QInputDialog.getText(self, "Send a command", "Command:")
        if not ok:
            return
        self.rb_msg(rb, "sent command: {}".format(text))
        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "command***{}".format(text))
        print(f"result: {r}")
        if r:
            self.rb_msg(rb, msg)


    def status_all(self):
        """
        ask status to all raspberries
        """
        for rasp_id in sorted(RASPBERRY_LIST.keys()):
            if not RASPBERRY_LIST[rasp_id]:
                continue
            self.rb_msg(rasp_id, "asked status")
            r, msg = sendMessageTo(RASPBERRY_LIST[rasp_id], "status")
            print(rasp_id, "r", r, msg)
            if r:
                self.rb_msg(rasp_id, msg)
                # change status button color
                self.status_list[sorted(RASPBERRY_LIST.keys()).index(rasp_id)].setStyleSheet(f"background: #ff0000;")
            time.sleep(5)



    def sync_all(self):
        """
        sync time on all raspberries
        """
        for rb in sorted(RASPBERRY_LIST.keys()):
            if not RASPBERRY_LIST[rb]:
                continue
            self.rb_msg(rb, "sent sync time command")
            date, hour = date_iso().split(" ")
            r, msg = sendMessageTo(RASPBERRY_LIST[rb], "sync_time*{}*{}".format(date, hour))
            if r:
                self.rb_msg(rb, msg)


    def command_all(self):
        """
        send command to all rasp
        """
        text, ok = QInputDialog.getText(self, "Send a command to all", "Command:")
        if not ok:
            return

        for rb in sorted(RASPBERRY_LIST.keys()):
            if not RASPBERRY_LIST[rb]:
                continue
            self.rb_msg(rb, "sent command")
            r, msg = sendMessageTo(RASPBERRY_LIST[rb], "command***{}".format(text))
            if r:
                self.rb_msg(rb, msg)


    def update_all(self):
        """
        update rasp
        send the bluetooth_listener.py file to all rasp
        """
        for rb in sorted(RASPBERRY_LIST.keys()):
            if not RASPBERRY_LIST[rb]:
                continue
            completed = subprocess.run(["obexftp", "--nopath", "--noconn", "--uuid", "none", "--bluetooth",
                                        RASPBERRY_LIST[rb], "--channel", "9", "-p", "listener/bluetooth_listener.py"])
            if completed.returncode == 255:
                self.rb_msg(rb, "file sent")


    def reset_all(self):
        for rb in RASPBERRY_LIST:
             self.text_list[rb].clear()
        app.processEvents()


    def clear_log(self, rb):
        self.text_list[rb].clear()
        app.processEvents()


    def thread_data_received(self, data):
        """
        display data received by bluetooth receiver thread
        check raspberry id or bluetooth address is in RASPBERRY_LIST

        Args:
            data (bytes): data received from raspberry
        """

        try:
            d = eval(data)
            print(f'Received from {d["hostname"]}: {list(d.keys())}')
            rasp_id = d["hostname"]

            # if hostname not in list check bluetooth address
            if rasp_id not in RASPBERRY_LIST:
                for key in RASPBERRY_LIST:
                    if d["bluetooth_address"].upper() == RASPBERRY_LIST[key].upper():
                        rasp_id = key

            if "picture" in d:
                with open(RECEIVED_FILES_DIR + d["picture"]["file_name"], "wb") as f:
                    f.write(d["picture"]["file_content"])

            if "msg":
                self.rb_msg(rasp_id, d["msg"])
                # check status
                if d["msg"] == "status":
                    color = "#00ff00" if d["status"] == "OK" else "#ff0000"
                    self.status_list[sorted(RASPBERRY_LIST.keys()).index(rasp_id)].setStyleSheet(f"background: {color};")
                    # check time
                    if time.time() - MAX_TIME_DIFFERENCE < d["epoch"] < time.time() + MAX_TIME_DIFFERENCE:
                        self.synctime_list[sorted(RASPBERRY_LIST.keys()).index(rasp_id)].setStyleSheet(f"background: {color};")
                    # display status
                    self.rb_msg(rasp_id,
                                (f'status: {d["status"]}\n'
                                 f'Raspberry time: {d["local time"]}\n'
                                 f'worker version: {d["version installed"]}\n'
                                 f'time lapse running: {d["time lapse running"]}\n'
                                 f'camera enabled: {d["camera enabled"]}'
                                )
                     )

        except:
            raise
            print("Error " + str(sys.exc_info()[0]))


    def status(self, rasp_id):
        
        self.rb_msg(rasp_id, "asked status")
        r, msg = sendMessageTo(RASPBERRY_LIST[rasp_id], "status")
        if r:
            self.rb_msg(rasp_id, msg)
            # change status button color
            self.status_list[sorted(RASPBERRY_LIST.keys()).index(rasp_id)].setStyleSheet(f"background: #ff0000;")



    def sync_time(self, rb):
        self.rb_msg(rb, "sent sync time command")
        date, hour = date_iso().split(" ")
        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "sync_time*{}*{}".format(date, hour))
        print(f"result: {r}")
        if r:
            self.rb_msg(rb, msg)


    def one_picture(self, rb):
        """
        ask to raspberry to take one picture
        the taken picture is then sent back by raspberry
        """
        self.rb_msg(rb, "asked one picture " + self.resolution[rb].currentText())
        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "one_picture*" + self.resolution[rb].currentText())
        if r:
            self.rb_msg(rb, msg)


    def start_time_lapse(self, rb):

        dt1 = self.start_time[rb].dateTime().toString(Qt.ISODate)
        dt2 = self.end_time[rb].dateTime().toString(Qt.ISODate)
        if dt2 < dt1:
            QMessageBox.warning(self, "Bluetooth controller", "end time is before start time")
            return
        prefix = self.prefix[rb].text().replace(" ", "_")
        try:
            interval = self.interval[rb].value()
        except:
             QMessageBox.warning(self, "Bluetooth controller", "{} is not a valid interval (seconds)".format(self.interval[rb].text()))
             return
        self.rb_msg(rb, "Asked to start time lapse from {} to {} resolution: {}".format(dt1.replace("T", " "),
                                                                         dt2.replace("T", " "),
                                                                         self.resolution[rb].currentText()))
        command_dict = {"start":dt1, "end":dt2, "interval": interval,
                        "prefix": prefix, "resolution": self.resolution[rb].currentText()}
        #print(command_dict)

        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "time_lapse|{}".format(json.dumps(command_dict, indent=0, separators=(",",":"))))
        if r:
            self.rb_msg(rb, msg)


    def stop_time_lapse(self, rb):
        self.rb_msg(rb, "asked to stop time lapse")
        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "stop_time_lapse")
        if r:
            self.rb_msg(rb, msg)


    def get_log(self, rb):
        self.rb_msg(rb, "asked log")
        r, msg = sendMessageTo(RASPBERRY_LIST[rb], "get_log")
        print(f"result: {r}")
        if r:
            self.rb_msg(rb, msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    bt_control = Coordinator()
    sys.exit(app.exec_())
