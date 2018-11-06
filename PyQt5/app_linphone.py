#!/usr/bin/python3

import os
import sys
import cv2
import time
import threading
from PyQt5 import QtCore, QtGui, QtWidgets, uic


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        super(MainUI, self).__init__()
        uic.loadUi('design.ui', self) #init desing form
        self.CallButton.setText("Сall")
        self.CallButton.clicked.connect(self.press_button)


    def run_linphone(self): #init, register linphone and make call
        data = ['login','sip.linphone.org','password','sip:client@sip.linphone.org'] # login, server, pass, dial address
        os.system('linphonecsh init -C -D')
        time.sleep(2)
        os.system('linphonecsh register --username {0} --host {1} --password {2}' .format(data[0], data[1], data[2]))
        time.sleep(1)
        os.system('linphonecsh dial {0}'.format(data[3]))


    def check_video(self): #check window video (wmctrl) and resize fullscreen
        while True:
            vwindow="Video"
            time.sleep(2)
            cmd = os.system("wmctrl -l | grep {0}".format(vwindow))
            print(cmd, "checking window...")
            if cmd == 0:
                time.sleep(1)
                os.system('wmctrl -a {0} -b toggle,fullscreen'.format(vwindow))
                break
    
    
    def ping(self):
        while True:
            hostname = "8.8.8.8"
            response = os.system("ping -c 1 " + hostname)
            if response == 0:
                print (hostname, 'is up!')
                self.CallButton.setEnabled(True)
                self.CallButton.setText("Call")
            else:
                print (hostname, 'is down!')
                self.CallButton.setEnabled(False)
                self.CallButton.setText("Sorry, now the terminal is down")
    
    
    def press_button(self):
        thread_call = threading.Thread(target=self.run_linphone, name="call")
        thread_screen = threading.Thread(target=self.check_video, name="screen")
        thread_ping = threading.Thread(target=self.ping, name="ping")
        thread_call.start()
        thread_ping.start()
        time.sleep(2)
        thread_screen.start()


def app_start():
    app = QtWidgets.QApplication(sys.argv)
    window = MainUI()
    window.setWindowTitle('Call Window')
    window.showFullScreen()
    time.sleep(2)
    sys.exit(app.exec_())


if __name__=='__main__':
    app_start()
