from __future__ import print_function
import random
import math
from collections import deque
import numpy as np
import sys
sys.path.insert(0, '../one_step/')
import util, Utils
import json
from keras import initializations
from keras.initializations import normal, identity
from keras.models import model_from_json
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD , Adam
from one_step import simulate,validate
ACTIONS = 256               #num of actions ==> which board position is being targeted?
GAMMA = 0.99 # decay rate of past observations
OBSERVATION = 50. # timesteps to observe before training
EXPLORE = 3000000. # frames over which to anneal epsilon
FINAL_EPSILON = 0.0001 # final value of epsilon
INITIAL_EPSILON = 0.1 # starting value of epsilon
REPLAY_MEMORY = 500 # number of previous transitions to remember
BATCH = 32 # size of minibatch
FRAME_PER_ACTION = 1
OBSERVE = 1e3
input_dimension = 256       #num of states ==> 16*16 sized board    
final_output_dim = ACTIONS

D = deque() #TODO global

def buildmodel():
	model = Sequential()
	model.add(Dense(output_dim=64, input_dim=input_dimension))
	model.add(Activation("relu"))
	model.add(Dense(output_dim=50))
	model.add(Activation("relu"))
	model.add(Dense(output_dim=40))
	model.add(Activation("relu"))
	model.add(Dense(output_dim=final_output_dim))
	adam = Adam(lr=1e-3)
	model.compile(loss='mse',optimizer=adam)
	return model
# model.add(Activation("relu"))
# model.compile(loss='mse', optimizer='rmsprop', metrics=['accuracy'])


def getActionFromIndex(action_index):
	x_target = action_index//16
	y_target = action_index%16
	x_target = x_target*50+25
	y_target = y_target*50+25

	target = (x_target,y_target)
	pocket = util.nearest_pocket(target)
	#striker to start from (x,y)
	y = 140
	x = target[0] + float(target[0]-pocket[0])/float(target[1]-pocket[1]) * (y-target[1])
	if x<170 or x>630:
		x = 400
	angle = 180/util.pi * math.atan2(target[1]-y, target[0]-x)
	if angle < -45:
		angle = angle+360
	force = 1
	position = float(x-170)/float(460)

	return (position, angle,force)


def getStateFromDict(stateDict):
	state = np.zeros([input_dimension])
	whites = stateDict["White_Locations"]
	blacks = stateDict["Black_Locations"]
	rednecks = stateDict["Red_Location"]
	for w in whites+blacks+rednecks:
		x = w[0]//50
		y = w[1]//50
		state[16*x+y] +=1
	# state= state.T
	s_t = state
	s_t = s_t.reshape(1,s_t.shape[0])
	return s_t

def trainNetwork(model, mode):
	# open up a game state to communicate with emulator
	# game_state = game.GameState()

	# store the previous observations in replay memory

	# get the first state by doing nothing and preprocess the image to 80x80x4
	# do_nothing = np.zeros(ACTIONS)
	# do_nothing[0] = 1
	# x_t, r_0, terminal = game_state.frame_step(do_nothing)

	# x_t = skimage.color.rgb2gray(x_t)
	# x_t = skimage.transform.resize(x_t,(80,80))
	# x_t = skimage.exposure.rescale_intensity(x_t,out_range=(0,255))

	# s_t = np.stack((x_t, x_t, x_t, x_t), axis=0)

	#In Keras, need to reshape
	# s_t = s_t.reshape(1, s_t.shape[0], s_t.shape[1], s_t.shape[2])

	# state = np.zeros([input_dimension])
	# whites = stateDict["White_Locations"]
	# blacks = stateDict["Black_Locations"]
	# rednecks = stateDict["Red_Location"]
	# for w in whites+blacks+rednecks:
	# 	x = w[0]//50
	# 	y = w[1]//50
	# 	state[16*x+y] +=1
	# # state= state.T
	# s_t = state
	# s_t = s_t.reshape(1,s_t.shape[0])

	# print(state)
	# print ("shape", state.shape)
	if mode == 'Run':
		OBSERVE = 999999999    #We keep observe, never train
		epsilon = FINAL_EPSILON
		print ("Now we load weight")
		model.load_weights("model.h5")
		adam = Adam(lr=1e-6)
		model.compile(loss='mse',optimizer=adam)
		print ("Weight load successfully")    
	else:                       #We go to training mode
		OBSERVE = OBSERVATION
		epsilon = INITIAL_EPSILON
	f = open("temp.csv",'w')

	t = 0
	MAX_EPISODES = 10000
	MAX_EPISODE_STEPS = 500
	file2 = open("ep_end_times.txt",'w')
	for ep in xrange(0, MAX_EPISODES):
		stateDict = Utils.INITIAL_STATE
		s_t = getStateFromDict(stateDict)
		# state = s_t
		
		for epstep in xrange(0, MAX_EPISODE_STEPS):
			loss = 0
			Q_sa = 0
			action_index = 0
			r_t = 0
			a_t = np.zeros([ACTIONS])
			#choose an action epsilon greedy
			if t % FRAME_PER_ACTION == 0:
				if random.random() <= epsilon:
					print("----------Random Action----------")
					action_index = random.randrange(ACTIONS)
					a_t[action_index] = 1
				else:
					# print ("st0 " + str(s_t[0]) )
					# print ("st shape ",s_t.shape)
					q = model.predict(s_t)       #input a stack of 4 images, get the prediction
					max_Q = np.argmax(q)
					action_index = max_Q
					a_t[max_Q] = 1

			#We reduced the epsilon gradually
			if epsilon > FINAL_EPSILON and t > OBSERVE:
				epsilon -= (INITIAL_EPSILON - FINAL_EPSILON) / EXPLORE

			#run the selected action and observed next state and reward
			# x_t1_colored, r_t, terminal = game_state.frame_step(a_t)

			# TODO : implement this
			# next_state, reward = play(stateDict, action_index)
			my_action = getActionFromIndex(action_index)
			next_state_dict, reward = simulate(stateDict,validate(my_action,stateDict))
			next_state = getStateFromDict(next_state_dict)
			w = len(next_state_dict["White_Locations"])
			b = len(next_state_dict["Black_Locations"])
			r = len(next_state_dict["Red_Location"])
			print("COINS : ",w,b,r , w+b+r)
			# x_t1 = skimage.color.rgb2gray(x_t1_colored)
			# x_t1 = skimage.transform.resize(x_t1,(80,80))
			# x_t1 = skimage.exposure.rescale_intensity(x_t1, out_range=(0, 255))

			# x_t1 = x_t1.reshape(1, 1, x_t1.shape[0], x_t1.shape[1])
			# s_t1 = np.append(x_t1, s_t[:, :3, :, :], axis=1)

			# store the transition in D
			D.append((s_t, action_index, reward, next_state))
			if len(D) > REPLAY_MEMORY:
				D.popleft()

			#only train if done observing
			if t > OBSERVE:
			# if t > 40:
				# sample a minibatch to train on
				minibatch = random.sample(D, BATCH)

				# inputs = np.zeros((BATCH, s_t.shape[1], s_t.shape[2], s_t.shape[3]))   #32, 80, 80, 4
				inputs = np.zeros((BATCH, s_t.shape[1]))   #32, 80, 80, 4
				targets = np.zeros((BATCH, ACTIONS))                         #32, 2

				#Now we do the experience replay
				for i in range(0, len(minibatch)):
					state_t = minibatch[i][0]
					action_t = minibatch[i][1]   #This is action index
					reward_t = minibatch[i][2]
					state_t1 = minibatch[i][3]
					# terminal = minibatch[i][4]
					# if terminated, only equals reward

					# inputs[i] = state_t    #I saved down s_t
					inputs[i:i + 1] = state_t    #I saved down s_t

					targets[i] = model.predict(state_t)  # Hitting each buttom probability
					Q_sa = model.predict(state_t1)

					terminal = False
					if state_t1.sum() < 1 : terminal= True
					if terminal:
						print("*************************************Terminal*************************************")
						targets[i, action_t] = reward_t
					else:
						targets[i, action_t] = reward_t + GAMMA * np.max(Q_sa)

				# targets2 = normalize(targets)
				loss += model.train_on_batch(inputs, targets)
			stateDict=next_state_dict
			s_t = next_state
			t = t + 1

			# save progress every 10000 iterations
			if t % 100 == 0:
				print("Now we save model")
				model.save_weights("model.h5", overwrite=True)
				with open("model.json", "w") as outfile:
					json.dump(model.to_json(), outfile)

			# print info
			state_ = ""
			if t <= OBSERVE:
				state_ = "observe"
			elif t > OBSERVE and t <= OBSERVE + EXPLORE:
				state_ = "explore"
			else:
				state_ = "train"

			print("EPISODE", ep, "/ EP_STEP ", epstep, "TIMESTEP", t , "/ STATE_", state_, \
				"/ EPSILON", epsilon, "/ ACTION", action_index, "/ My Action",my_action, "/ REWARD", reward, \
				"/ Q_MAX " , np.max(Q_sa), "/ Loss ", loss)
			comma = str(',')
			f.write(str(t)+comma+str(reward) + comma + str(np.max(Q_sa)) + '\n' )
			if (w+b+r)==0:
				break

		print("Episode finished!")
		print("************************")
		file2.write(str(ep) + str(',') + str(epstep) + '\n')
	file2.close()
	f.close()

def best_action(target, coins):
	# y=145 is the location of line from which to strike and it stretches from x=170 to x=630
	pocket = util.nearest_pocket(target)
	#striker to start from (x,y)
	y = 140
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


def getAction1(state):
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

def getAction(stateDict):
	state = np.zeros([input_dimension])
	whites = stateDict["White_Locations"]
	blacks = stateDict["Black_Locations"]
	rednecks = stateDict["Red_Location"]

	for w in whites+blacks+rednecks:
		x = w[0]//50
		y = w[1]//50
		state[16*x+y] +=1


	Q_sa = model.predict(state)

	action_index = np.argmax(Q_sa)

if __name__ == '__main__':
	model = buildmodel()
	mode = ''
	# if argv[1]: mode = argv[1]
	# trainNetwork(model,mode)
	# trainNetwork(model,'Run')
	trainNetwork(model,'')