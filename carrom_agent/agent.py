from __future__ import print_function
import random
import math

import util


def best_action(target, coins):
    # y=145 is the location of line from which to strike and it stretches from x=170 to x=630
    pocket = util.nearest_pocket(target)
    #striker to start from (x,y)
    y = 145
    x = target[0] + float(target[0]-pocket[0])/float(target[1]-pocket[1]) * (y-target[1])
    if x<170 or x>630:
        x = 400
    
    while not util.isPosValid((x, 145), coins): 
        x = random.randrange(170, 630)

    angle = 180/util.pi * math.atan2(target[1]-y, target[0]-x)
    if angle < -45:
        angle = angle+360
    force = 1

    # distance = dist(target, pocket)
    # force = distance/(800*math.sqrt(2))*.25
    # force = distance/(400*math.sqrt(2))*.25
    return (x, angle,force)

def num_neighbors(coin, all_coins):
    ret = 0
    for c in all_coins:
        if c!=coin and util.dist(c, coin)<=100:
            ret=ret+1
    return ret


def getAction(state):
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

    # print "TARGETS", targets 
    final_target = random.choice(targets)
    print("FINAL TARGET", final_target)
    (x_loc, angle,force) = best_action(final_target, coins)

    # while not isPosValid((x_loc, 145), coins): 
    #     x_loc = random.randrange(170, 630)

    position = float(x_loc-170)/float(460)


    # if position < 0:
    #     position = 0
    # elif position > 1:
    #     position = 1

    # a = str(position) + ',' + \
        # str(angle) + ',' + str(1)
    
    if len(coins) > 10:
        force = 1

    return position, angle, force