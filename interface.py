# -*- coding: utf-8 -*-
"""
Author: Dr. Daniel J. Whiting

Date: 26/02/2018

DCC control software designed to conform to NMRA S-9.2 and S-9.2.1 standards.

---- Notes ----

Currently does not support extended decoder addresses.

"""

### IMPORTS
import serial
import time

### GUI
import sys
import PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QGridLayout, QToolTip, QPushButton, QSlider, QFileDialog
from matplotlib.backends.backend_qt5agg import *


# ================ Baseline Packets ==================

def baseline_speedAndDirection(address,speed,direction):
    ''' 
    Set speed and direction for locomotives. 
    Direction = 1 for forwards travel and 0 for reverse  travel. 
    Speed -3-28 (-3 for stop, -1 for emergency stop)
    '''
    addr = '0'+format(address,'07b') # address data byte: leading bit (0) is occationally used to set headlights
    packet = '<'+14*'1'+'0'+addr
    speed_str = format(speed+3,'05b'); speed_str = speed_str[-1]+speed_str[:-1] 
    instr = '01'+str(direction)+'0'+speed_str #01DCSSSS
    err_byte = format(int(addr, 2) ^ int(instr, 2),'08b') # bitwise exclusive or of addr and instr bytes
    packet += '0'+instr+'0'+err_byte
    packet += '1>'
    ser.write(packet.encode('utf-8'))
    print(packet)

def resetAll():
    ''' Erase volatile memory of all decoders '''
    packet = '<'+14*'1'+'0'+'00000000'+'0'+'00000000'+'0'+'00000000'+'1>'
    ser.write(packet.encode('utf-8'))
    print(packet)

def idleAll():
    packet = '<'+14*'1'+'0'+'11111111'+'0'+'00000000'+'0'+'11111111'+'1>'
    ser.write(packet.encode('utf-8'))
    print(packet)

def StopAll():
    ''' Bring all locos to a controlled stop '''
    packet = '<'+14*'1'+'0'+'00000000'+'0'+'01110000'+'0'+'01110000'+'1>' 
    ser.write(packet.encode('utf-8'))
    print(packet)

# ================ Multi Function Decoder Packets ==================

def speedAndDirection(address,speed,direction,nsteps=128):
    ''' 
    Set speed and direction for locomotives. 
    Direction = 1 for forwards travel and 0 for reverse  travel. 
    If nsteps = 128: speed -1 -> 126 (-1 for stop, 0 for emergency stop)
    If nsteps = 28: speed -3-28 (-3 for stop, -1 for emergency stop)
    '''
    addr = '0'+format(address,'07b') # address data byte: leading bit (0) is occationally used to set headlights
    packet = '<'+14*'1'+'0'+addr
    if nsteps==128:
        # Advanced Operations Instruction (001)
        instr1 = '00111111' # Set speed and direction with 128 steps 
        speed_str = format(speed+1,'07b')
        instr2 = str(direction)+speed_str
        err_byte = format(int(addr, 2) ^ int(instr1, 2) ^ int(instr2, 2),'08b') # bitwise exclusive or of addr and instr bytes
        packet += '0'+instr1+'0'+instr2+'0'+err_byte 
    else:
        speed_str = format(speed+3,'05b'); speed_str = speed_str[-1]+speed_str[:-1] 
        instr = '01'+str(direction)+'0'+speed_str #01DCSSSS
        err_byte = format(int(addr, 2) ^ int(instr, 2),'08b') # bitwise exclusive or of addr and instr bytes
        packet += '0'+instr+'0'+err_byte
    packet += '1>'
    ser.write(packet.encode('utf-8'))
    print(packet)

def functionGroup1(address,data_string):
    '''
    Sets the on/off states of the functions FL(F0) and F1-F4
    Data string DDDDD: FL,F4,F3,F2,F1 (FL = lights)
    '''
    addr = '0'+format(address,'07b')
    instr ='100'+data_string
    err = format(int(addr, 2) ^ int(instr, 2),'08b')
    packet = '<'+'1'*14+'0'+addr+'0'+instr+'0'+err+'1>'
    ser.write(packet.encode('utf-8'))
    print(packet)
    
def functionGroup2(address,data_string):
    '''
    Sets the on/off states of the functions F5-F12
    Data string SDDDD: S=1 DDDD=F8,F7,F6,F5 | S=0 DDDD = F12,F11,F10,F9
    '''
    addr = '0'+format(address,'07b')
    instr ='101'+data_string
    err = format(int(addr, 2) ^ int(instr, 2),'08b')
    packet = '<'+'1'*14+'0'+addr+'0'+instr+'0'+err+'1>'
    ser.write(packet.encode('utf-8'))
    print(packet)

def configurationVariableAccess():
    return None

# ================ Accessory Decoder Packets ==================

def basicAccessory(address,active,data_string):
    '''
    Controls basic accessories such as signals and points.
    Active sets the on/off state of the device (1/0).
    Data string is a 3 digit binary number controlling which of the accessory states is active.
    '''
    addr1 = format(address,'06b')
    addr2 = ''.join([bin(~0)[3:] if x == '0' else bin(~1)[4:] for x in format(address,'09b')[:3]]) # performs a bit flip on the 3 most significant bits (see nmra standards - ones' complement)
    packet = '<'+14*'1'+'0'
    byte1 = '10'+addr1 #'10AAAAAA'
    byte2 = '1'+addr2+active+data_string #'1AAACDDD'
    err = format(int(byte1, 2) ^ int(byte2, 2),'08b') # bitwise exclusive or of byte 1 and byte 2
    packet += byte1+'0'+byte2+'0'+err+'1>'
    ser.write(packet.encode('utf-8'))
    print(packet)   

def set_address(current_address,new_address):
    ''' Must be used in service mode on an isolated piece of track with a current limit of 250mA '''
    #resetAll()
    #preamble = 20*'1' # long preamble required to allow processing of service mode packets
    return None 

'''
Packet Sequence for Command Stations/Programmers using Direct Mode 
- Optional Power-On-Cycle, if needed 
[
- 3 or more Reset Packets 
Either:
- 5 or more Verify packets to a single CV 1-1023, followed by 1 or more Reset Packets, if an acknowledgement is detected.
Or:
- 5 or more Writes to a single CV 1-1023 
- 6 or more Identical Write or Reset packets (Decoder-Recovery-Time)   
]
- Optional Power-Off 

Direct mode instruction packet format: Long-preamble 0 0111CCAA 0 AAAAAAAA 0 DDDDDDDD 0 EEEEEEEE 1
'''

'''
Packet Sequence for Command Stations/Programmers using Address-only mode 
- Optional Power-On-Cycle, if needed 
- 3 or more Reset Packets 
- 5 or more Page-Preset-packets 
- 6 or more Page Preset or Reset packets (Decoder-Recovery-Time from write to Page Register) 
- Optional Power Off Followed by Power-On-Cycle 
[
- 3 or more Reset Packets 
Either:
- 5 or more Verifies  to CV #1
Or:
- 5 or more Writes to CV #1 
- 10 or more identical Write or Reset packets (Decoder-Recovery-Time)
]
- Optional Power Off 

Address-only mode instruction packet format: long-preamble 0 0111C000 0 0DDDDDDD 0 EEEEEEEE 1 
'''

class main(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle('Control Terminal')
        self.setWindowIcon(QIcon('web.png'))
        
        # set the layout
        layout = QGridLayout()
        layout.addWidget(QPushButton(self))
        self.setLayout(layout)        
        self.show()

def test_train():
    functionGroup1(3,'10001')
    time.sleep(3)
    functionGroup1(3,'10011')
    time.sleep(3)
    speedAndDirection(3,10,1)
    time.sleep(10)
    speedAndDirection(3,0,0)
    time.sleep(3)
    functionGroup1(3,'10000')
    
def test_signals():
    sleep_time = 0.5 # seconds
    while True:
        basicAccessory(42,'1','000') # 42
        time.sleep(sleep_time)
        basicAccessory(42,'1','001') # 42
        time.sleep(sleep_time)
        basicAccessory(42,'1','010') # 42
        time.sleep(sleep_time)
        basicAccessory(42,'1','011') # 42
        time.sleep(sleep_time)

if __name__ == "__main__":
    ser = serial.Serial('COM5',9600)  # open serial port
    try:
        #test_signals()
        test_train()
    except:
        None
    ser.close()             # close port
    
    #app = QApplication(sys.argv)
    #main = main() # include try except loop with safe exit (issue all stop packet and set arduino run pin to low)
    #sys.exit(app.exec_())