from __future__ import print_function
from __future__ import division
import one_step
import Utils
import sys

# Generate candidate first moves
# with open('allFirstMoves', 'w') as f: 
# 	for force in range(25, 103, 3):
# 		for angle in range(60, 122, 2):
# 			for position in range(30, 73, 3):
# 				f.write(str(position/100) + ' ' + str(angle) + ' ' + str(force/100) + '\n')


# Simulate each of the moves above
state = Utils.INITIAL_STATE
print('Finding best action ...')
with open('allFirstMoves', 'r') as f: 
    count = 0
    for line in f:
        count += 1 
        if(count % 100 == 0):
        	print(count, file=sys.stderr)

        [position, angle, force] = [float(x) for x in line[:-1].split(' ')]

        next_state, reward = one_step.simulate(state, one_step.validate([position, angle, force],state))
        
        white_pos = [(x[0], x[1]) for x in next_state["White_Locations"]]
        black_pos = [(x[0], x[1]) for x in next_state["Black_Locations"]]
        red_pos   = [(x[0], x[1]) for x in next_state["Red_Location"]]

        print(str(position) + ' ' + str(angle) + ' ' + str(force) + ' ' + str(len(white_pos)) + ' ' + str(len(black_pos)) + ' ' + str(len(red_pos)), end=' ')
        for x in white_pos: 
        	print(str(x[0]) + ' ' + str(x[1]), end=' ')
        for x in black_pos: 
        	print(str(x[0]) + ' ' + str(x[1]), end=' ')
        for x in red_pos: 
        	print(str(x[0]) + ' ' + str(x[1]), end=' ')
        print()
