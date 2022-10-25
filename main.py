import os
import sys
import time
import numpy as np
import math
import threading

from queue import Queue
from threading import Thread
from xarm.wrapper import XArmAPI

from pythonosc import dispatcher
from pythonosc import osc_server

def onStart(robot):
    qList[robot] = True
    print(robot, qList[robot])

def onStop(robot):
    qList[robot] = False
    print(robot, qList[robot])

def onVolume(robot, volume):
    volumes[robot] = volume
    print(robot, volumes[robot])

def setup():
    for a in range(len(arms)):
        arms[a].set_simulation_robot(on_off=False)
        arms[a].motion_enable(enable=True)
        arms[a].clean_warn()
        arms[a].clean_error()
        arms[a].set_mode(0)
        arms[a].set_state(0)
        curIP = IP[a]
        arms[a].set_servo_angle(angle=curIP, wait=False, speed=10, acceleration=0.25, is_radian=False)

        # arms[a].set_servo_angle(angle=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], wait=False, speed=10, acceleration=0.25, is_radian=False)

def setup2():
    for a in range(len(arms)):
        curIP = IP[a]
        arms[a].set_servo_angle(angle=curIP, wait=False, speed=10, acceleration=0.25, is_radian=False)

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


def strumbot(numarm, traj):
    pos = IP[numarm]
    j_angles = pos
    track_time = time.time()
    initial_time = time.time()
    for i in range(len(traj)):
        # run command
        start_time = time.time()
        j_angles[4] = traj[i]
        arms[numarm].set_servo_angle_j(angles=j_angles, is_radian=False)
        while track_time < initial_time + 0.004:
            track_time = time.time()
            time.sleep(0.0001)
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
    i = 0
    uptraj = fifth_poly(-strumD/2, strumD/2, speed)
    downtraj = fifth_poly(strumD/2, -strumD/2, speed)
    both = [uptraj, downtraj]

    while True:
        if qList[armNum]:
            direction = i % 2
            strumbot(armNum, both[direction])
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
    PORT_FROM_MAX = 5002
    IP_MAX = "0.0.0.0"

    IP0 = [-1, 87.1, -2, 126.5, -strumD/2, 51.7, -45]
    IP1 = [2.1, 86.3, 0, 127.1, -strumD/2, 50.1, -45]
    IP2 = [1.5, 81.6, 0.0, 120, -strumD/2, 54.2, -45]
    IP3 = [2.5, 81, 0, 117.7, -strumD/2, 50.5, -45]
    IP4 = [-3.9, 65, 3.5, 100.3, -strumD/2, 42.7, 101.1]                  # [-1.6, 81.8, 0, 120, -strumD/2, 50.13, -45]
    DRUM1 = [0.0, 23.1, 0.0, 51.4, 0.0, -60.8, 0.0] #DRUMMMING
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
    input("letsgo again")
    for a in arms:
        a.set_mode(1)
        a.set_state(0)

    NUM_ARMS = 5
    DEFAULT_VOLUME = 50
    qList = [False] * NUM_ARMS
    volumes = [DEFAULT_VOLUME] * NUM_ARMS

    xArm0 = Thread(target=strummer, args=(0,))
    xArm1 = Thread(target=strummer, args=(1,))
    xArm2 = Thread(target=strummer, args=(2,))
    xArm3 = Thread(target=strummer, args=(3,))
    xArm4 = Thread(target=strummer, args=(4,))

    xArm0.start()
    xArm1.start()
    xArm2.start()
    xArm3.start()
    xArm4.start()
    # tension = fifth_poly(0, -10, 0.5)
    # print(tension)
    input("TEST")
    # time.sleep(5)
    # q1.put(2)
    # input()
    
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/start", onStart)
    dispatcher.map("/stop", onStop)
    dispatcher.map("/volume", onVolume)
    def server():
        server = osc_server.ThreadingOSCUDPServer((IP, PORT_FROM_MAX), dispatcher)
        print("Serving on {}".format(server.server_address))
        server.serve_forever()

    threading.Thread(target=server, daemon=True).start()
    
    while True:
        strumnum = input("keep going")
    #
    #     qList[0].put(0)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
