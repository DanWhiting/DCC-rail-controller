# -*- coding: utf-8 -*-
"""
Author: Daniel J. Whiting
"""

### IMPORTS
import serial
import time

ser = serial.Serial('/dev/ttyACM0',9600,timeout=1)  # open serial port /dev/ttyACM0

packet_start = '<'
packet_end = '>'

# ================ Base Classes ==================

class Loco:
    def __init__(self,address,functions=range(13),nSpeedSteps=128):
        self.address = address
        self.nSpeedSteps = nSpeedSteps
	self.functions = functions
        self.states = [0]*13

    def setSpeedAndDirection(self,speed,direction):
        ''' 
        Set speed and direction for locomotives. 
        Direction = 1 for forwards travel and 0 for reverse  travel. 
        If nSpeedSteps = 128: speed -1 -> 126 (-1 for stop, 0 for emergency stop)
        If nSpeedSteps = 28: speed -3-28 (-3 for stop, -1 for emergency stop)
        '''
        packet = [packet_start,self.address]
        if self.nSpeedSteps==128:
            # Advanced Operations Instruction (001)
            instr1 = 0x3F # Set speed and direction with 128 steps 
            instr2 = (direction << 7) | (speed + 1)
            err_byte = self.address ^ instr1 ^ instr2 # bitwise exclusive or of addr and instr bytes
            packet += [instr1,instr2,err_byte] 
        else:
            speed += 3
            instr = (1 << 6) | (direction << 5) | ((speed & 0x01) << 4) | (speed >> 1) #01DCSSSS
            err_byte = self.address ^ instr # bitwise exclusive or of addr and instr bytes
            packet += [instr,err_byte]
        ser.write(bytearray(packet+[packet_end]))
        time.sleep(0.1)        

    def setFunctionState(self,function,state):       
        if function in self.functions:
            index = self.functions.index(function)            
            self.states[index] = state
            if index < 5:
                # Function group 1
                instr = (1 << 7) | (self.states[0] << 4) | self.states[1] | (self.states[2] << 1) | (self.states[3] << 2) | (self.states[4] << 3)
            elif index < 9:
                # Function group 2
                instr = 0xA0 | (1 << 4) | self.states[5] | (self.states[6] << 1) | (self.states[7] << 2) | (self.states[8] << 3)
            else:
                # Function group 2
                instr = 0xA0 | self.states[9] | (self.states[10] << 1) | (self.states[11] << 2) | (self.states[12] << 3)
            err = self.address ^ instr
            ser.write(bytearray([packet_start,self.address,instr,err,packet_end]))
            time.sleep(0.1)
        else:
            print "Function not available"

    def test(self):
        self.setSpeedAndDirection(60,1)
        time.sleep(10)
        self.setSpeedAndDirection(0,1)
        for function in self.functions:
            self.setFunctionState(function,1)
            print 'Switched on function: ', str(function)
            time.sleep(5)
            self.setFunctionState(function,0)

class Accessory:
    def __init__(self,address,states=range(2,10),state=0):
        self.address = address
        self.states = states
        self.state = state
        self.setState(state)

    def setState(self,state):
        if state == 0:
            self.active = 0
        elif state == 1:
            self.active = 1
        elif state in self.states:
            self.active = 1
            self.state = self.states.index(state)
        else:
            print "State not available"
        self.basicAccessoryPacket()

    def basicAccessoryPacket(self):
        addr1 = self.address & 0x3F
        addr2 = (~self.address >> 2) & 0x70
        byte1 = (1 << 7) | addr1 # 10AAAAAA
        byte2 = (1 << 7) | addr2 | (self.active << 3) | self.state # 1AAACDDD
        err = byte1 ^ byte2
        ser.write(bytearray([packet_start,byte1,byte2,err,packet_end]))
        time.sleep(0.1)

    def test(self):
        for state in self.states:
            self.setState(state)
            print 'State set to: ', str(state)
            time.sleep(3)

def resetAll():
    ''' Erase volatile memory of all decoders '''
    ser.write(bytearray([packet_start,0x00,0x00,0x00,packet_end]))

def idleAll():
    ser.write(bytearray([packet_start,0xFF,0x00,0xFF,packet_end]))

def stopAll():
    ''' Bring all locos to a controlled stop '''
    ser.write(bytearray([packet_start,0x00,0x70,0x70,packet_end]))


if __name__ == "__main__":
    resetAll()    

    scotsman = Loco(3)
    scotsman.test()

    signal = Accessory(42,["green","red","yellow","two yellow"])    
    signal.test()
    
    stopAll()

    ser.close()             # close port
