# A Sample Carrom Agent to get you started. The logic for parsing a state
# is built in
from Utils import *
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


## ADFVOREVJODAVAE

holes =[(0,0),(0,800),(800,0),(800,800)]

def get_coin_max_sep(coin_list) :
    maxi_index = 0
    maxi_dist = 0
    dist = 0
    for i in range(0,len(coin_list)) :
        dist = get_dist(coin_list,i)
        if dist > maxi_dist :
            maxi_dist = dist
            maxi_index = i
    return maxi_index

def get_dist(coin_list, index) :
    distance = 0;
    for j in range(0,len(coin_list)):
        distance = distance + dist(coin_list[j],coin_list[index])
        return dist

def find_nearest_hole(coin) :
    maxi_index = 0
    maxi_dist = 0
    distance = 0
    for j in range(0,len(holes)):
        distance = dist(holes[j],coin)
        if distance > maxi_dist :
            maxi_dist = distance
            maxi_index = j
    return holes[maxi_index],math.sqrt(maxi_dist)


def get_most_suitable_x(list_of_x,coin_list,to_hit, angle_to_hole) :
    max_max_travelable_dist = 0
    random.shuffle(list_of_x)
    index = 0
    
    # y = 145
    # x=to_hit[0] + (y-to_hit[1])*math.tan(angle_to_hole)
    # x = max(min(630,x),170)
    # return x,dist(to_hit,(x,y))

    for i in range (0,len(list_of_x)) :
        unobstructed_distance = (to_hit[0] - list_of_x[i])*(to_hit[0] - list_of_x[i]) + (to_hit[1] - 145)*(to_hit[1] - 145)
        #angle = math.atan2((to_hit[1]-145),(to_hit[0]-list_of_x[i]))
        minx = min(list_of_x[i], to_hit[0])
        maxx = max(list_of_x[i], to_hit[0])
        miny = min(145, to_hit[1])
        maxy = max(145, to_hit[1])
        for j in range(0,len(coin_list)):
            if coin_list[j][0] >= minx and coin_list[j][0] <= maxx and coin_list[j][1] >= miny and coin_list[j][1] <= maxy :
                distance = dist(coin_list[j],(list_of_x[i],145))
                if distance < unobstructed_distance :
                    unobstructed_distance = distance
        if unobstructed_distance == dist(to_hit,(list_of_x[i],145)):
            return list_of_x[i], unobstructed_distance

        if unobstructed_distance > max_max_travelable_dist : 
            max_max_travelable_dist = unobstructed_distance
            index = i
    return list_of_x[index], max_max_travelable_dist





# Given a message from the server, parses it and returns state and action


def parse_state_message(msg):
    s = msg.split(";REWARD")
    s[0] = s[0].replace("Vec2d", "")
    reward = float(s[1])
    state = ast.literal_eval(s[0])
    return state, reward


def agent_1player(state):

    flag = 1
    # print state
    try:
        state, reward = parse_state_message(state)  # Get the state and reward
    except:
        pass

    # Assignment 4: your agent's logic should be coded here




    a = str(random.random()) + ',' + \
        str(random.randrange(-45, 225)) + ',' + str(random.random())

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


# while 1:
#     state = s.recv(1024)  # Receive state from server
#     if num_players == 1:
#         if agent_1player(state) == 0:
#             break
#     elif num_players == 2:
#         if agent_2player(state, color) == 0:
#             break
# s.close()
while 1:
    tm = s.recv(1024)
    try:
        S,r=parse_state_message(tm)
        # print S,r
    except:
        print "Something went wrong",tm

        
    if  len(S["White_Locations"])!=0 or len(S["Black_Locations"])!=0 or len(S["Red_Location"])!=0:
        if port%2==1:
            to_hit_list=S["White_Locations"]+S["Red_Location"]
        else:
            to_hit_list=S["Black_Locations"]+S["Red_Location"]
        if len(to_hit_list) == 2 and len(S["Red_Location"])!=0 :
            to_hit = S["Red_Location"][0]
        else :
            try:
                to_hit = to_hit_list[get_coin_max_sep(to_hit_list)]
            except:
                to_hit = [(400,400)]
        hole,dist1 = find_nearest_hole(to_hit)
        angle_to_hole = math.atan2((to_hit[1]-hole[1]),(to_hit[0]-hole[0]))
        point_to_aim = ((to_hit[0]) - 20.6*math.cos(angle_to_hole),(to_hit[1]) - 20.6*math.sin(angle_to_hole))
        list_of_x = [170,190,210,230,250,270,290,310,330,350,370,390,410,430,450,470,490,510,530,550,570,590,610,630]
        x,dist2 = get_most_suitable_x(list_of_x,to_hit_list,to_hit, angle_to_hole)
        loc = (x,145)
        angle=math.atan2((to_hit[1]-loc[1]),(to_hit[0]-loc[0]))
        if angle < 0:
            angle = angle + 2*3.14
        angle=angle/3.14*180
        if angle>=315 and angle<=360:
            angle=angle-360
        
        a=a=str(float(x-170)/float(460))+','+str(angle)+ ','+str(0.5)
            #a=str(angle)+ ',' + str(float(x-170)/float(460))+','+str(random.random()/1.25) # Remove in actual test
            #a=str(angle)+ ',' + str(float(x-170)/float(460))+','+str(0.5*dist2/800) # Remove in actual test
    else:
        a=None
    try:
        #print a + ":::" + str(to_hit) + "+++" + str(loc)
        # print "Here"
        s.send(a)
        # print "Here1"
    except:
        print "Error in sending:",  a
    # print "Closing Connection"
    # break
s.close()