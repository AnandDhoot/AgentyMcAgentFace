from __future__ import print_function
from __future__ import division
import random
import math
import sys

import util
sys.path.append('one_step/')
import one_step

forceControlCoins = 18
queenFocusCoins = 6
pocketCloseness = 240     # Reduce force if coin is close to pocket

forceBase = 1
forceWings = 0.2
forceReduction = 0.01
forceForwardMin = 0.05
forceForwardAdd = 0.055
# forceForwardAdd = 0.02
forceBackwardMin = 0.005
forceBackwardAdd = 0.035


def num_neighbors(coin, all_coins, dist):
    ret = 0
    nbrs = []
    for c in all_coins:
        if c!=coin and util.dist(c, coin)<=dist:
            ret=ret+1
            nbrs += [c]
    return ret, nbrs

def getLocation(target):
    loc = 'None' 
    if(target[0] < util.startpos_y and target[1] > target[0] and target[0] + target[1] < 800):
        loc = 'Left'
    elif(target[0] > util.BOARD_SIZE - util.startpos_y and target[1] < target[0] and target[0] + target[1] > 800):
        loc = 'Right'
    elif(target[1] < util.startpos_y):
        loc = 'Bottom'
    elif(target[1] > util.BOARD_SIZE - util.startpos_y):
        loc = 'Top'
    else:
        loc = 'Center'

    return loc

def directShotAvl(coins, allCoins):
    result = []
    for target in coins:
        pocket = util.nearest_pocket(target)
        x = target[0] + float(target[0]-pocket[0])/float(target[1]-pocket[1]) * (util.startpos_y-target[1])

        if(150 < x < 170):
            x = 170
        if(630 > x > 650):
            x = 630

        if(170 <= x <= 630):
            result += [target]

    random.shuffle(result)
    return result


def getPosition(target, pocket):
    targetLoc = getLocation(target)
    x = target[0] + float(target[0]-pocket[0])/float(target[1]-pocket[1]) * (util.startpos_y-target[1])
    if(150 < x < 170):
        print('--')
        x = 170
    if(630 > x > 650):
        print('--')
        x = 630

    directShot = True
    if x<170 or x>630:
        directShot = False

        if target[0] < 400:
            x = 170
        else:
            x = 630

        opposite = int(targetLoc in ['Bottom', 'Top', 'Center'])
        if(opposite):
            x = 800 - x

    return x, directShot

def getAngle(target, x, pocket):
    angle = 180/util.pi * math.atan2(target[1]-util.startpos_y, target[0]-x)
    if angle < -45:
        angle = angle+360

    aimAngle = 180/math.pi * math.atan2(target[1]-util.startpos_y, target[0]-x)
    pockAngle = 180/math.pi * math.atan2(pocket[1]-util.startpos_y, pocket[0]-x)

    angleChange = 0
    print(aimAngle, pockAngle)
    if(abs(aimAngle - pockAngle) < 5):
        if x < 400: 
            angleChange = 6
        else:
            angleChange = -6

    return angle, angleChange

def getForce(target, x, pocket, directShot, coins, angleChange):
    global forceForwardMin
    global forceForwardAdd

    targetLoc = getLocation(target)
    print(targetLoc)
    force = 0.3

    if(targetLoc in ['Left', 'Right']):
        force = forceWings
    
    if(directShot):
        print('Taking a direct shot')

        minDist = util.dist((170, util.startpos_y), util.all_pockets[1])
        maxDist = util.dist((630, util.startpos_y), util.all_pockets[1])
        actDist = util.dist((x, util.startpos_y), pocket)

        # print(x, actDist, minDist, maxDist)

        force = forceForwardMin + forceForwardAdd * (actDist - minDist) / (maxDist - minDist)
        if(util.dist(target, pocket) < pocketCloseness):
            print('Coin too close to pocket')
            force -= forceReduction

    if(targetLoc == 'Bottom'):
        print('Aiming at a bottom pocket.')
        minDist = util.dist((170, util.startpos_y), util.all_pockets[3])
        maxDist = util.dist((630, util.startpos_y), util.all_pockets[3])
        actDist = util.dist((x, util.startpos_y), pocket)

        force = forceBackwardMin + forceBackwardAdd * (actDist - minDist) / (maxDist - minDist)

    if not(force == 0.3 or force == forceWings):
        angleChange = 0

    if(len(coins) < 10): 
        angleChange /= 2
    # if(len(coins) < 5):
    #     angleChange /= 2

    return force, angleChange
    

def highForce(coins):
    n_neighbors_max = 0
    targets = []
    for coin in coins:
        temp, _ = num_neighbors(coin, coins, 100)
        if temp > n_neighbors_max:
            n_neighbors_max = temp

    for coin in coins :
        if num_neighbors(coin, coins, 100)[0] == n_neighbors_max :
            targets.append(coin)
    
    # Choose a target and the value of x for the striker
    for target in targets: 
        pocket = util.nearest_pocket(target)

        x_loc, directShot = getPosition(target, pocket)

        # Break if the striker can be placed
        if(util.isPosValid((x_loc, util.startpos_y), coins)):
            break

        # If no more candidate targets available, choose a random valid position
        while not util.isPosValid((x_loc, util.startpos_y), coins): 
            x_loc = random.randrange(170, 630)

    # Find the angle corresponding to the target and x found above
    angle, angChange = getAngle(target, x_loc, pocket)
    force = forceBase

    print('Changing angle by %d' % angChange)
    angle += angChange

    print("FINAL TARGET", target, 'at pocket', pocket)
    
    return x_loc, angle, force

def highPrecision(coins, redLocation, BWcoins, allCoins):
    targets = directShotAvl(coins, allCoins)
    print('Direct shot available for %d coins' % len(targets))
    print(targets)

    if(len(targets) == 0):
        print('-----------Choosing a random coin------------')
        targets = coins
        random.shuffle(targets)    

    if(len(BWcoins) <= 3 and len(redLocation) > 0 and random.random() < 0.5 + 1.0/(len(coins))):
        print('Running behind the queen')
        targets = redLocation


    # Choose a target and the value of x for the striker
    for target in targets: 
        pocket = util.nearest_pocket(target)

        x_loc, directShot = getPosition(target, pocket)

        # Break if the striker can be placed
        if(util.isPosValid((x_loc, util.startpos_y), coins)):
            break

        # If no more candidate targets available, choose a random valid position
        while not util.isPosValid((x_loc, util.startpos_y), coins): 
            x_loc = random.randrange(170, 630)
    


    # Find the angle corresponding to the target and x found above
    angle, angChange = getAngle(target, x_loc, pocket)
    force, angChange = getForce(target, x_loc, pocket, directShot, coins, angChange)

    print('Changing angle by %d' % angChange)
    angle += angChange

    print("FINAL TARGET", target, 'at pocket', pocket)
        
    return x_loc, angle, force

prevBWCoins = []
numSame = 0
flag = False
def getAction(state, turn, color=None):
    global prevBWCoins
    global numSame
    global flag

    if not state:
        # print "\n\n\n\n\n Exiting \n\n\n\n\n"
        return 0

    print(color)
    if(color is None):
        BWcoins = state["White_Locations"] + state["Black_Locations"]
    elif color == 'White':
        BWcoins = state["White_Locations"]
    elif color == 'Black':
        BWcoins = state["Black_Locations"]

    if(len(prevBWCoins) == len(BWcoins)):
        numSame += 1
    else:
        numSame = 0
    prevBWCoins = BWcoins
    
    coins = state['Red_Location'] + BWcoins
    allCoins = state['Red_Location'] + state["White_Locations"] + state["Black_Locations"]

    if(turn == 1):
        position, angle, force = 0, 0, 0
        return position, angle, force

    
    if(len(coins) >= forceControlCoins and numSame < 4 and flag != True):
        x_loc, angle, force = highForce(coins)
    else:
        print('Precision')
        flag = True
        x_loc, angle, force = highPrecision(coins, state['Red_Location'], BWcoins, allCoins)

    position = float(x_loc-170)/float(460)


    return position, angle, force