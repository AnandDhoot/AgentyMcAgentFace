from __future__ import print_function
import sys
import math

sys.path.insert(0, './1_player_server/')
import Utils


all_pockets = [(755.9, 755.9), (44.1, 755.9), (755.9, 44.1), (44.1, 44.1)]
pi = 3.14159


def dist(pt1, pt2):
    return math.sqrt(pow(pt1[0]-pt2[0],2)+pow(pt1[1]-pt2[1],2))

def nearest_pocket(coin):
    ret_pock = all_pockets[0]
    min_dist = dist(coin, ret_pock)
    lim = 4
    if coin[1]>175: lim = 2
    for i in xrange(1,lim):
        if dist(coin, all_pockets[i]) < min_dist:
            min_dist = dist(coin, all_pockets[i])
            ret_pock = all_pockets[i]
    return ret_pock 


def isPosValid(pos, coins):
    for coin in coins: 
        if(dist(pos, coin) < (Utils.COIN_RADIUS + Utils.STRIKER_RADIUS)):
            return False
    return True

