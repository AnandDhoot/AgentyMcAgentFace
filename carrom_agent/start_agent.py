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
    reward = float(s[1])
    state = ast.literal_eval(s[0])
    return state, reward

all_pockets = [(0, 0), (0, 800), (800, 800), (800, 0)]
pi = 3.14159


def dist(pt1, pt2):
    return math.sqrt(pow(pt1[0]-pt2[0],2)+pow(pt1[1]-pt2[1],2))

def nearest_pocket(coin):
    ret_pock = (0,0)
    min_dist = dist(coin, (0,0))
    for i in xrange(1,4):
        if dist(coin, all_pockets[i]) < min_dist:
            min_dist = dist(coin, all_pockets[i])
            ret_pock = all_pockets[i]
    return ret_pock 

def best_action(target):
    # y=145 is the location of line from which to strike and it stretches from x=170 to x=630
    pocket = nearest_pocket(target)
    #striker to start from (x,y)
    y = 145
    x = target[0] + float(target[0]-pocket[0])/float(target[1]-pocket[1]) * (y-target[1])
    if x<170 or x>630:
        x = 400
    angle = 180/pi * math.atan2(target[1]-y, target[0]-x)
    if angle < -45:
        angle = angle+360

    distance = dist((x, y), pocket)
    force = distance/(800*math.sqrt(2))*.25
    return (x, angle,force)



def num_neighbors(coin, all_coins):
    ret = 0
    for c in all_coins:
        if c!=coin and dist(c, coin)<=50 :
            ret=ret+1
    return ret

def agent_1player(state):

    flag = 1
    # print state
    try:
        # print state
        state, reward = parse_state_message(state)  # Get the state and reward
        # print state, reward, type(state)
    except:
        pass

    # Assignment 4: your agent's logic should be coded here

    if not state:
        # print "\n\n\n\n\n Exiting \n\n\n\n\n"
        return 0


    coins = state["White_Locations"]+state["Black_Locations"]+state["Red_Location"]

    # print "\n\n\n\nCoins:", coins
    # print "\n\n\n"
    # if not coins:
    #     return 0

    #neighbors within a radius of 50
    n_neighbors_max = 0
    targets = []
    for coin in coins:
        temp = num_neighbors(coin, coins)
        if temp > n_neighbors_max:
            n_neighbors_max = temp

    for coin in coins :
        if num_neighbors(coin, coins) == n_neighbors_max :
            targets.append(coin)

    print "TARGETS", targets 
    final_target = random.choice(targets)
    print "FINAL TARGET", final_target
    (x_loc, angle,force) = best_action(final_target)

    position = float(x_loc-170)/float(460)
    # if position < 0:
    #     position = 0
    # elif position > 1:
    #     position = 1

    # a = str(position) + ',' + \
        # str(angle) + ',' + str(1)
    
    if len(coins) > 10:
        force =1
    a = str(position) + ',' + \
        str(angle) + ',' + str(force)

    try:
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0

    return flag


def agent_2player(state, color):

    flag = 1

    # Can be ignored for now
    a = str(random.random()) + ',' + \
        str(random.randrange(-45, 225)) + ',' + str(random.random())

    try:
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0

    return flag


while 1:
    state = s.recv(1024)  # Receive state from server
    if num_players == 1:
        if agent_1player(state) == 0:
            break
    elif num_players == 2:
        if agent_2player(state, color) == 0:
            break
s.close()
