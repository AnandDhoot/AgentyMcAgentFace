# A Sample Carrom Agent to get you started. The logic for parsing a state
# is built in
from thread import *
import time
import socket
import sys
import argparse
import random
import ast
import math
import os

import agent1Player
import agent2Player

# Parse arguments
parser = argparse.ArgumentParser()

parser.add_argument('-np', '--num-players', dest="num_players", type=int,
                    default=1,
                    help='1 Player or 2 Player')
parser.add_argument('-p', '--port', dest="port", type=int,
                    default=12121,
                    help='port')
parser.add_argument('-rs', '--random-seed', dest="rng", type=int,
                    default=0,
                    help='Random Seed')
parser.add_argument('-c', '--color', dest="color", type=str,
                    default="Black",
                    help='Legal color to pocket')
args = parser.parse_args()


host = '127.0.0.1'
port = args.port
num_players = args.num_players
random.seed(args.rng)  # Important
color = args.color

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect((host, port))



# Given a message from the server, parses it and returns state and action
def parse_state_message(msg):
    s = msg.split(";REWARD")
    s[0] = s[0].replace("Vec2d", "")
    try:
        reward = float(s[1])
    except:
        reward = 0
    state = ast.literal_eval(s[0])
    return state, reward




def agent_1player(state, turn):
    flag = 1
    # print state
    try:
        # print state
        state, reward = parse_state_message(state)  # Get the state and reward
        # print state, reward, type(state)
    except:
        pass

    if not state:
        # print "\n\n\n\n\n Exiting \n\n\n\n\n"
        return 0

    position, angle, force = agent1Player.getAction(state, turn)
    a = str(position) + ',' + \
        str(angle) + ',' + str(force)

    try:
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0

    return flag


def agent_2player(state, color, turn):

    flag = 1
    

    # print state
    try:
        # print state
        state, reward = parse_state_message(state)  # Get the state and reward
        # print state, reward, type(state)
    except:
        pass

    if not state:
        # print "\n\n\n\n\n Exiting \n\n\n\n\n"
        return 0

    position, angle, force = agent2Player.getAction(state, turn, color)

    a = str(position) + ',' + \
        str(angle) + ',' + str(force)


    try:
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0

    return flag


turn = 0
while 1:
    state = s.recv(1024)  # Receive state from server
    turn += 1
    if num_players == 1:
        if agent_1player(state, turn) == 0:
            break
    elif num_players == 2:
        if agent_2player(state, color, turn) == 0:
            break
s.close()
