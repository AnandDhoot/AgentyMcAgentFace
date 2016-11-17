from __future__ import print_function
import sys
import math

# sys.path.insert(0, './1_player_server/')
# import Utils

startpos_y = 140
all_pockets = [(755.9, 755.9), (44.1, 755.9), (755.9, 44.1), (44.1, 44.1)]
pi = 3.14159

BOARD_SIZE = 800
COIN_RADIUS = 15.01
STRIKER_RADIUS = 20.6
POCKET_RADIUS = 22.51


def dist(pt1, pt2):
    return math.sqrt(pow(pt1[0]-pt2[0],2)+pow(pt1[1]-pt2[1],2))

def nearest_pocket(coin):
    ret_pock = all_pockets[0]
    min_dist = dist(coin, ret_pock)
    lim = 4
    if coin[1] > startpos_y: 
        lim = 2
    for i in xrange(1,lim):
        if dist(coin, all_pockets[i]) < min_dist:
            min_dist = dist(coin, all_pockets[i])
            ret_pock = all_pockets[i]
    return ret_pock 


def isPosValid(pos, coins):
    for coin in coins: 
        if(dist(pos, coin) < (COIN_RADIUS + STRIKER_RADIUS)):
            return False
    return True

