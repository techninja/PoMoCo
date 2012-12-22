import time
import math
import os
import threading
import ConfigParser
import sys

import servotorComm
from robot import hexapod
import serial

floor = 60

class BotPresetControl():
    def __init__(self):
        self.con = servotorComm.Controller() # Servo controller
        self.hexy = hexapod(self.con)
        self.loadOffsets()

        self.estop()

    def quitApp(self):
        self.estop()

    # def gui_estop(self):
    #    servotorComm.runMovement(self.estop)

    def loadOffsets(self):
        # If there is one offset file in the folder, automatically load it
        off_files = []
        for filename in os.listdir(os.getcwd()):
            start, ext = os.path.splitext(filename)
            if ext == '.cfg':
                off_files.append(filename)

        if len(off_files) == 1:
            print "opening",off_files[0]
            config = ConfigParser.ConfigParser()
            config.read(off_files[0])

            try:
                offsets = config.items('offsets')
                for offset in offsets:
                    servoNum = int(offset[0])
                    offset = int(offset[1])
                    for servo in self.con.servos:
                        if self.con.servos[servo].servoNum == servoNum:
                            #print "set servo",servoNum,"offset as",offset
                            self.con.servos[servo].setOffset(timing=offset)
                            break
                print "automatically loaded offsets from",off_files[0]
            except:
                print "automatic offset load failed, is there an offset file in the program directory?"

    def estop(self):
        self.con.killAll()
    def parseTextCommand(self, cmd):
        # Dictionary list of functions
        cmds = {'kill':  self.estop,
                'fwd':  self.move_moveForward,
                'back':  self.move_moveBackward,
                'reset': self.move_reset,
                'left':  self.move_rotateLeft,
                'right': self.move_rotateRight,
                'wave':  self.move_wave}
        try:
            cmds[cmd]() # Run the function that matches!
        except:
             print "Unrecognized command, try: " + str(cmds.keys())

    def move_reset(self):
        print "Hexy resetting to default stance..."
        deg = -30
        #put all the feet centered and on the floor.
        self.hexy.RF.replantFoot(deg,stepTime=0.3)
        self.hexy.LM.replantFoot(1,stepTime=0.3)
        self.hexy.RB.replantFoot(-deg,stepTime=0.3)
        time.sleep(0.5)
        self.hexy.LF.replantFoot(-deg,stepTime=0.3)
        self.hexy.RM.replantFoot(1,stepTime=0.3)
        self.hexy.LB.replantFoot(deg,stepTime=0.3)
        time.sleep(0.5)

    def move_rotateLeft(self):
        print "Hexy shimmying left..."
        deg = 40

        #set neck to where body is turning
        self.hexy.neck.set(deg)

        #re-plant tripod2 deg degrees forward
        for leg in self.hexy.tripod2:
            leg.replantFoot(deg,stepTime=0.2)
        time.sleep(0.3)

        #raise tripod1 feet
        for leg in self.hexy.tripod1:
            leg.setFootY(int(floor/2.0))
        time.sleep(0.3)

        #swing tripod2 feet back 2*deg degrees (to -deg)
        for leg in self.hexy.tripod2:
            leg.setHipDeg(-deg,stepTime=0.3)

        #reset neck as body turns
        self.hexy.neck.set(0)
        time.sleep(0.4)

        #lower tripod1 feet
        for leg in self.hexy.tripod1:
            leg.setFootY(floor)
        time.sleep(0.3)

        #re-plant tripod2 deg degrees to starting position
        for leg in self.hexy.tripod2:
            leg.replantFoot(0,stepTime=0.3)
        time.sleep(0.3)

    def move_rotateRight(self):
        print "Hexy shimmying right..."
        deg = -40

        #set neck to where body is turning
        self.hexy.neck.set(deg)

        #re-plant tripod1 deg degrees forward
        for leg in self.hexy.tripod1:
            leg.replantFoot(deg,stepTime=0.2)
        time.sleep(0.5)

        #raise tripod2 feet in place as tripod1 rotate and neck
        for leg in self.hexy.tripod2:
            leg.setFootY(int(floor/2.0))
        time.sleep(0.3)

        #swing tripod1 feet back 2*deg degrees (to -deg)
        for leg in self.hexy.tripod1:
            leg.setHipDeg(-deg,stepTime=0.3)

        #reset neck as body turns
        self.hexy.neck.set(0)
        time.sleep(0.4)

        #lower tripod2 feet
        for leg in self.hexy.tripod2:
            leg.setFootY(floor)
        time.sleep(0.3)

        #re-plant tripod1 deg degrees to starting position
        for leg in self.hexy.tripod1:
            leg.replantFoot(0,stepTime=0.3)
        time.sleep(0.3)

    def move_moveForward(self):
        print "Hexy moving forward..."
        deg = 25
        midFloor = 30
        hipSwing = 25
        pause = 0.5

        #tripod1 = RF,LM,RB
        #tripod2 = LF,RM,LB

        for timeStop in range(2):
            #time.sleep(0.1)
            # replant tripod2 forward while tripod1 move behind
            #   relpant tripod 2 forward
            self.hexy.LF.replantFoot(deg-hipSwing,stepTime=0.5)
            self.hexy.RM.replantFoot(hipSwing,stepTime=0.5)
            self.hexy.LB.replantFoot(-deg-hipSwing,stepTime=0.5)

            #   tripod1 moves behind
            self.hexy.RF.setHipDeg(-deg-hipSwing,stepTime=0.5)
            self.hexy.LM.setHipDeg(hipSwing,stepTime=0.5)
            self.hexy.RB.setHipDeg(deg-hipSwing,stepTime=0.5)
            time.sleep(0.6)

            # replant tripod1 forward while tripod2 move behind
            #   replant tripod1 forward
            self.hexy.RF.replantFoot(-deg+hipSwing,stepTime=0.5)
            self.hexy.LM.replantFoot(-hipSwing,stepTime=0.5)
            self.hexy.RB.replantFoot(deg+hipSwing,stepTime=0.5)

            #   tripod2 moves behind
            self.hexy.LF.setHipDeg(deg+hipSwing,stepTime=0.5)
            self.hexy.RM.setHipDeg(-hipSwing,stepTime=0.5)
            self.hexy.LB.setHipDeg(-deg+hipSwing,stepTime=0.5)
            time.sleep(0.6)

    def move_moveBackward(self):
        print "Hexy moving backward (sorta)..."
        deg = -25
        midFloor = 30
        hipSwing = 25
        pause = 0.5

        #tripod1 = RF,LM,RB
        #tripod2 = LF,RM,LB

        for timeStop in range(2):
            #time.sleep(0.1)
            # replant tripod2 backwards while tripod1 moves forward
            #   relpant tripod 2 backwards
            self.hexy.LF.replantFoot(deg+hipSwing,stepTime=0.5)
            self.hexy.RM.replantFoot(-hipSwing,stepTime=0.5)
            self.hexy.LB.replantFoot(-deg+hipSwing,stepTime=0.5)

            #   tripod1 moves forward
            self.hexy.RF.setHipDeg(-deg+hipSwing,stepTime=0.5)
            self.hexy.LM.setHipDeg(-hipSwing,stepTime=0.5)
            self.hexy.RB.setHipDeg(deg+hipSwing,stepTime=0.5)
            time.sleep(0.6)

            # replant tripod1 backwards while tripod2 moves behind
            #   replant tripod1 backwards
            self.hexy.RF.replantFoot(-deg-hipSwing,stepTime=0.5)
            self.hexy.LM.replantFoot(hipSwing,stepTime=0.5)
            self.hexy.RB.replantFoot(deg-hipSwing,stepTime=0.5)

            #   tripod2 moves behind
            self.hexy.LF.setHipDeg(deg-hipSwing,stepTime=0.5)
            self.hexy.RM.setHipDeg(hipSwing,stepTime=0.5)
            self.hexy.LB.setHipDeg(-deg-hipSwing,stepTime=0.5)
            time.sleep(0.6)

    def move_point(self):
        self.hexy.neck.set(0)
        time.sleep(1)
        self.hexy.neck.set(30)
        time.sleep(1)
        self.hexy.RF.knee(-60)
        self.hexy.RF.ankle(-40)
        time.sleep(0.2)
        self.hexy.RF.hip(20)
        time.sleep(0.3)
        self.hexy.RF.hip(50)
        time.sleep(0.3)
        self.hexy.RF.hip(10)
        time.sleep(1)
        self.hexy.neck.set(0)

    def move_leanBack(self):

        # Pick up back feet
        self.hexy.RB.setHipDeg(45,stepTime=0.3)
        self.hexy.LB.setHipDeg(-45,stepTime=0.3)
        self.hexy.RB.setFootY(40)
        self.hexy.LB.setFootY(40)
        # Push side feet down
        self.hexy.RM.setFootY(70)
        self.hexy.LM.setFootY(70)
        time.sleep(0.2)

        # Put hands into air
        self.hexy.LF.hip(45)
        self.hexy.LF.knee(0)
        self.hexy.LF.ankle(0)
        self.hexy.RF.hip(-45)
        self.hexy.RF.knee(0)
        self.hexy.RF.ankle(0)
        time.sleep(0.4)

    def move_leanBackToReset(self):

        # Put front feet back down
        print "Put hands into air"
        self.hexy.RF.setHipDeg(30,stepTime=0.1)
        self.hexy.LF.setHipDeg(-30,stepTime=0.1)
        self.hexy.RF.setFootY(floor)
        self.hexy.LF.setFootY(floor)
        time.sleep(0.1)

        # Reset back feet back down
        self.hexy.RB.setHipDeg(30,stepTime=0.1)
        self.hexy.LB.setHipDeg(-30,stepTime=0.1)
        self.hexy.RB.setFootY(floor)
        self.hexy.LB.setFootY(floor)

        # Pull side feet back up
        print "Push side feet down"
        self.hexy.RM.setFootY(floor)
        self.hexy.LM.setFootY(floor)
        time.sleep(0.2)

        self.move_reset()

    def move_setZero(self):
        for servo in self.con.servos:
            self.con.servos[servo].setPos(deg=0)

    def move_tiltLeft(self):
        self.hexy.LF.setFootY(0)
        self.hexy.LM.setFootY(-10)
        self.hexy.LB.setFootY(0)

        self.hexy.RF.setFootY(75)
        self.hexy.RM.setFootY(75)
        self.hexy.RB.setFootY(75)

    def move_tiltRight(self):
        self.hexy.LF.setFootY(75)
        self.hexy.LM.setFootY(75)
        self.hexy.LB.setFootY(75)

        self.hexy.RF.setFootY(0)
        self.hexy.RM.setFootY(-10)
        self.hexy.RB.setFootY(0)

    def move_tiltReset(self):
        self.hexy.LF.setFootY(floor)
        self.hexy.LM.setFootY(floor)
        self.hexy.LB.setFootY(floor)

        self.hexy.RF.setFootY(floor)
        self.hexy.RM.setFootY(floor)
        self.hexy.RB.setFootY(floor)

    def move_tiltForward(self):
        self.hexy.LF.setFootY(floor/4)
        self.hexy.LM.setFootY(floor/2)
        self.hexy.LB.setFootY(floor)

        self.hexy.RF.setFootY(floor/4)
        self.hexy.RM.setFootY(floor/2)
        self.hexy.RB.setFootY(floor)

    def move_tiltBackward(self):
        self.hexy.LF.setFootY(floor)
        self.hexy.LM.setFootY(floor/2)
        self.hexy.LB.setFootY(floor/4)

        self.hexy.RF.setFootY(floor)
        self.hexy.RM.setFootY(floor/2)
        self.hexy.RB.setFootY(floor/4)

    def move_killAllHumans(self):
        # tilt forward
        self.move_tiltForward()

        time.sleep(0.3)

        #prep paw
        self.hexy.LF.hip(-40)
        self.hexy.LF.knee(0)
        self.hexy.LF.ankle(0)

        time.sleep(0.3)

        #swipe paw
        self.hexy.LF.hip(60)

        time.sleep(0.3)

        #set paw down
        self.hexy.LF.ankle(-60)

        time.sleep(0.3)

        #swing other paw
        self.hexy.RF.hip(40)
        self.hexy.RF.knee(0)
        self.hexy.RF.ankle(0)

        time.sleep(0.3)

        #swipe paw
        self.hexy.RF.hip(-60)

    def move_dance(self):
        self.move_tiltLeft()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltRight()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)

        self.move_tiltLeft()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltRight()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)

        self.move_tiltForward()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltBackward()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)

        self.move_tiltForward()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltBackward()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)

    def move_bellyFlop(self):
        self.move_setZero()
        time.sleep(2)
        self.move_tiltRight()
        self.move_tiltLeft()
        time.sleep(0.3)
        self.move_tiltReset()
        time.sleep(0.5)
        self.move_reset()

    def move_danceCircle(self):
        self.move_tiltLeft()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltForward()
        time.sleep(0.2)
        self.move_tiltReset()
        time.sleep(0.2)
        self.move_tiltRight()
        time.sleep(0.2)

    def move_wave(self):
        print "Hexy says hi!..."
        self.move_reset()
        self.hexy.neck.set(0)

        self.hexy.LF.hip(-20)
        self.hexy.LF.knee(0)
        self.hexy.LF.ankle(0)

        time.sleep(0.2)

        for i in range(3):
            self.hexy.LF.hip(-20)
            self.hexy.LF.knee(-50)
            self.hexy.LF.ankle(-20)

            time.sleep(0.2)

            self.hexy.LF.knee(-10)
            self.hexy.LF.ankle(0)
            time.sleep(0.2)

        self.hexy.LF.knee(-40)
        time.sleep(1)
        self.move_reset()
    def move_typing(self):
        self.move_leanBack()
        time.sleep(0.3)

        for i in range(10):
            self.hexy.RF.knee(0)
            self.hexy.LF.knee(60)

            time.sleep(0.3)

            self.hexy.RF.knee(60)
            self.hexy.LF.knee(0)

            time.sleep(0.3)

    def move_demo(self):
        self.move_reset()
        time.sleep(0.3)
        self.move_tiltForward()
        time.sleep(0.3)
        self.move_tiltReset()
        time.sleep(0.3)
        self.move_tiltBackward()
        time.sleep(0.3)
        self.move_tiltReset()
        time.sleep(0.3)
        self.move_tiltRight()
        time.sleep(0.3)
        self.move_tiltReset()
        time.sleep(0.3)
        self.move_tiltLeft()
        time.sleep(0.3)
        self.move_tiltReset()
        time.sleep(0.3)
        self.move_moveForward()
        time.sleep(0.2)
        self.move_moveBackward()
        time.sleep(0.2)
        self.move_reset()
        time.sleep(0.2)
        self.move_rotateLeft()
        time.sleep(0.2)
        self.move_rotateLeft()
        time.sleep(0.2)
        self.move_rotateRight()
        time.sleep(0.2)
        self.move_rotateRight()

