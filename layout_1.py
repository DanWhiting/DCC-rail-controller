from control import *

if __name__ == "__main__":
    resetAll()    

    scotsman = Loco(3)
    signal = Accessory(42,["green","red","yellow","two yellow"])    
    
    signal.setState("red")
    scotsman.setSpeedAndDirection(20,1)
    time.sleep(20)
    stopAll()
    time.sleep(5)
    signal.setState("green")
    time.sleep(1)
    scotsman.setSpeedAndDirection(40,1)
    time.sleep(5)
    scotsman.setSpeedAndDirection(75,1)
    time.sleep(10)
    scotsman.setSpeedAndDirection(40,1)
    time.sleep(10)
    
    stopAll()
    ser.close()             # close port
