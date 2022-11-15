import os
import sys
import time
import numpy as np
import math
import threading
import atexit

from queue import Queue
from threading import Thread
from xarm.wrapper import XArmAPI

from pythonosc import dispatcher
from pythonosc import osc_server


class robotThread(threading.Thread):
    def __init__(self, target, args):
        threading.Thread.__init__(self, group=None, target, args)
        self.flag = threading.Event()
        self.running = threading.Event()
        self.target = target

    def run(self):
        while self.running.isSet():
            self.flag.wait()
            if self._target:
                print("run the target")
                self.target(*self._args)

        # while True:
        #     with self.pause_cond:
        #         while self.paused:
        #             self.pause_cond.wait(timeout=None)
        #         while not self.paused:
        #             if self._target:
        #                 self._target(*self._args, **self._kwargs)

    def pause(self):
        self.flag.clear()

    def resume(self):
        self.flag.set()


def robotOne(name, playing, volume):
    print("robot 1")
    ARMONE[1] = volume
    if ARMONE[0] != playing:
        ARMONE[0] = playing

        if playing:
            xArm0.resume()
        else:
            xArm0.pause()

def robotTwo(name, playing, volume):
    ARMTWO[1] = volume
    if ARMTWO[0] != playing:
        ARMTWO[0] = playing

        if playing:
            xArm1.resume()
        else:
            xArm1.pause()


def robotThree(name, playing, volume):
    ARMTHREE[1] = volume
    if ARMTHREE[0] != playing:
        ARMTHREE[0] = playing

        if playing:
            xArm2.resume()
        else:
            xArm2.pause()


def robotFour(name, playing, volume):
    ARMFOUR[1] = volume
    if ARMFOUR[0] != playing:
        ARMFOUR[0] = playing

        if playing:
            xArm3.resume()
        else:
            xArm3.pause()



def robotFive(name, playing, volume):
    ARMFIVE[1] = volume
    if ARMFIVE[0] != playing:
        ARMFIVE[0] = playing

        if playing:
            xArm4.resume()
        else:
            xArm4.pause()



def default_handler(address, *args):
    print(f"DEFAULT {address}: {args}")


def setup():
    for a in range(len(arms)):
        arms[a].set_simulation_robot(on_off=False)
        arms[a].motion_enable(enable=True)
        arms[a].clean_warn()
        arms[a].clean_error()
        arms[a].set_mode(0)
        arms[a].set_state(0)
        curIP = IP[a]
        arms[a].set_servo_angle(angle=curIP, wait=False, speed=4, acceleration=20, is_radian=False)

        # arms[a].set_servo_angle(angle=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], wait=False, speed=10, acceleration=0.25, is_radian=False)


def setup2():
    for a in range(len(arms)):
        curIP = IP[a]
        arms[a].set_servo_angle(angle=curIP, wait=False, speed=4, acceleration=20, is_radian=False)

        # print(curIP)


def fifth_poly(q_i, q_f, t):
    # time/0.005
    traj_t = np.arange(0, t, 0.004)
    dq_i = 0
    dq_f = 0
    ddq_i = 0
    ddq_f = 0
    a0 = q_i
    a1 = dq_i
    a2 = 0.5 * ddq_i
    a3 = 1 / (2 * t ** 3) * (20 * (q_f - q_i) - (8 * dq_f + 12 * dq_i) * t - (3 * ddq_f - ddq_i) * t ** 2)
    a4 = 1 / (2 * t ** 4) * (30 * (q_i - q_f) + (14 * dq_f + 16 * dq_i) * t + (3 * ddq_f - 2 * ddq_i) * t ** 2)
    a5 = 1 / (2 * t ** 5) * (12 * (q_f - q_i) - (6 * dq_f + 6 * dq_i) * t - (ddq_f - ddq_i) * t ** 2)
    traj_pos = a0 + a1 * traj_t + a2 * traj_t ** 2 + a3 * traj_t ** 3 + a4 * traj_t ** 4 + a5 * traj_t ** 5
    return traj_pos


def strumbot(numarm: object, traj: object, position) -> object:
    j_angles = position
    track_time = time.time()
    initial_time = time.time()
    for i in range(len(traj)):
        # run command
        # start_time = time.time()
        j_angles[4] = traj[i]

        presend = time.time()
        numarm.set_servo_angle_j(angles=j_angles, is_radian=False)
        postlogger = time.time()
        print("first logger is ", postlogger - presend)

        while track_time < initial_time + 0.004:
            track_time = time.time()
            time.sleep(0.0001)
            weird = time.time()
        # print("speed logger is ", track_time - initial_time)
        initial_time += 0.004


def prepGesture(numarm, traj):
    pos = IP[numarm]
    j_angles = pos.copy()
    track_time = time.time()
    initial_time = time.time()
    for i in range(len(traj)):
        # run command
        j_angles[1] = pos[1] + traj[i]
        j_angles[3] = pos[3] + traj[i]
        arms[numarm].set_servo_angle_j(angles=j_angles, is_radian=False)
        # print(j_angles)
        while track_time < initial_time + 0.004:
            track_time = time.time()
            time.sleep(0.0001)
        initial_time += 0.004


def strummer(armNum):
    # melody here in the future
    if armNum == 1:
        arm = ARMONE
    if armNum == 2:
        arm = ARMTWO
    if armNum == 3:
        arm = ARMTHREE
    if armNum == 4:
        arm = ARMFOUR
    if armNum == 5:
        arm = ARMFIVE
    armOn, _ = arm
    i = 0
    armAPI = arms[armNum - 1]
    pos = IP[armNum - 1]
    print("in strummer!" + str(armNum))
    uptraj = fifth_poly(-strumD / 2, strumD / 2, speed)
    downtraj = fifth_poly(strumD / 2, -strumD / 2, speed)
    both = [uptraj, downtraj]
    MAX_SPEED = 4
    MAX_ACC = 20


    armOn, armVolume = arm

    if armOn:
        direction = i % 2
        strumbot(armAPI, both[direction], pos)
        print("strum on" + str(armNum))
        print(armVolume / 100)
        # time.sleep((armVolume/20))
        i += 1


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ROBOT = "xArms"
    PORT = 5004
    global IP
    global arms
    global strumD
    global speed
    global notes
    global PORT_FROM_MAX

    strumD = 30
    speed = 0.25
    # source of message to max's port #

    IP0 = [-1, 87.1, -2, 126.5, -strumD / 2, 51.7, -45]
    IP1 = [2.1, 86.3, 0, 127.1, -strumD / 2, 50.1, -45]
    IP2 = [1.5, 81.6, 0.0, 120, -strumD / 2, 54.2, -45]
    IP3 = [2.5, 81, 0, 117.7, -strumD / 2, 50.5, -45]
    IP4 = [-1.6, 81.8, 0, 120, -strumD / 2, 50.65, -45]
    # [-3.9, 65, 3.5, 100.3, -strumD / 2, 42.7, 101.1]  # [-1.6, 81.8, 0, 120, -strumD/2, 50.13, -45]
    DRUM1 = [0.0, 23.1, 0.0, 51.4, 0.0, -60.8, 0.0]  # DRUMMMING
    notes = np.array([64, 60, 69, 55, 62])

    IP = [IP0, IP1, IP2, IP3, IP4]
    arm0 = XArmAPI('192.168.1.208')
    arm1 = XArmAPI('192.168.1.226')
    arm2 = XArmAPI('192.168.1.244')
    arm3 = XArmAPI('192.168.1.203')
    arm4 = XArmAPI('192.168.1.237')
    arms = [arm0, arm1, arm2, arm3, arm4]
    # arms = [arm1]
    totalArms = len(arms)
    setup()
    input("lets go")
    setup2()
    # input("letsgo again")
    for a in arms:
        a.set_mode(1)
        a.set_state(0)

    NUM_ARMS = 5
    DEFAULT_VOLUME = 50
    global ARMONE
    ARMONE = [False, DEFAULT_VOLUME]
    global ARMTWO
    ARMTWO = [False, DEFAULT_VOLUME]
    global ARMTHREE
    ARMTHREE = [False, DEFAULT_VOLUME]
    global ARMFOUR
    ARMFOUR = [False, DEFAULT_VOLUME]
    global ARMFIVE
    ARMFIVE = [False, DEFAULT_VOLUME]

    pause_cond0 = threading.Condition(threading.Lock())
    pause_cond1 = threading.Condition(threading.Lock())
    pause_cond2 = threading.Condition(threading.Lock())
    pause_cond3 = threading.Condition(threading.Lock())
    pause_cond4 = threading.Condition(threading.Lock())

    xArm0 = robotThread(target=strummer, args=(1, pause_cond0,))
    xArm1 = robotThread(target=strummer, args=(2, pause_cond1,))
    xArm2 = robotThread(target=strummer, args=(3, pause_cond2,))
    xArm3 = robotThread(target=strummer, args=(4, pause_cond3,))
    xArm4 = robotThread(target=strummer, args=(5, pause_cond4,))

    xArm0.start()
    xArm1.start()
    xArm2.start()
    xArm3.start()
    xArm4.start()

    # tension = fifth_poly(0, -10, 0.5)
    # print(tension)
    # input("TEST")
    # time.sleep(5)
    # q1.put(2)
    # input()

    PORT_FROM_MAX = 5002
    IP_MAX = "0.0.0.0"

    # qList = [False] * NUM_ARMS
    # volumes = [DEFAULT_VOLUME] * NUM_ARMS
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/0", robotOne)
    dispatcher.map("/1", robotTwo)
    dispatcher.map("/2", robotThree)
    dispatcher.map("/3", robotFour)
    dispatcher.map("/4", robotFive)
    #
    # dispatcher.map("/stop", onStop)
    # dispatcher.map("/volume", onVolume)
    dispatcher.set_default_handler(default_handler)

    input("Here!")


    def server():
        server = osc_server.ThreadingOSCUDPServer((IP_MAX, PORT_FROM_MAX), dispatcher)
        print("Serving on {}".format(server.server_address))
        server.serve_forever()
        atexit.register(server.server_close())


    threading.Thread(target=server, daemon=True).start()

    while True:
        strumnum = input("keep going")
    #
    #     qList[0].put(0)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/