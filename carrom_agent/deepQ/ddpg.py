""" 
Implementation of DDPG - Deep Deterministic Policy Gradient

Algorithm and hyperparameter details can be found here: 
	http://arxiv.org/pdf/1509.02971v2.pdf

The algorithm is tested on the Pendulum-v0 OpenAI gym task 
and developed with tflearn + Tensorflow

Author: Patrick Emami
"""
import tensorflow as tf
import numpy as np
# import gym 
import tflearn

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
import timeit
sys.path.insert(0, '../../one_step/')
sys.path.insert(0, '../../1_player_server/')
import Utils
from one_step import simulate
from one_step import validate


# Parse arguments

# parser = argparse.ArgumentParser()

# parser.add_argument('-np', '--num-players', dest="num_players", type=int,
#                     default=1,
#                     help='1 Player or 2 Player')
# parser.add_argument('-p', '--port', dest="port", type=int,
#                     default=12121,
#                     help='port')
# parser.add_argument('-rs', '--random-seed', dest="rng", type=int,
#                     default=0,
#                     help='Random Seed')
# parser.add_argument('-c', '--color', dest="color", type=str,
#                     default="Black",
#                     help='Legal color to pocket')
# args = parser.parse_args()


# host = '127.0.0.1'
# port = args.port
# num_players = args.num_players
# random.seed(args.rng)  # Important
# color = args.color

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# sock.connect((host, port))



from replay_buffer import ReplayBuffer

# ==========================
#   Training Parameters
# ==========================
# Max training steps
MAX_EPISODES = 50000
# Max episode length
MAX_EP_STEPS = 500
# Base learning rate for the Actor network
ACTOR_LEARNING_RATE = 0.0001
# Base learning rate for the Critic Network
CRITIC_LEARNING_RATE = 0.001
# Discount factor 
GAMMA = 0.99
# Soft target update param
TAU = 0.001

# ===========================
#   Utility Parameters
# ===========================
# Render gym env during training
RENDER_ENV = True
# Use Gym Monitor
GYM_MONITOR_EN = True
# Gym environment
ENV_NAME = 'Pendulum-v0'
# Directory for storing gym results
MONITOR_DIR = './results/gym_ddpg'
# Directory for storing tensorboard summary results
SUMMARY_DIR = './results/tf_ddpg'
RANDOM_SEED = 1234
# Size of replay buffer
BUFFER_SIZE = 10000
MINIBATCH_SIZE = 64

# ===========================
#   Actor and Critic DNNs
# ===========================
class ActorNetwork(object):
	""" 
	Input to the network is the state, output is the action
	under a deterministic policy.

	The output layer activation is a tanh to keep the action
	between -2 and 2
	"""
	def __init__(self, sess, state_dim, action_dim, action_bound, action_offset, learning_rate, tau):
		self.sess = sess
		self.s_dim = state_dim
		self.a_dim = action_dim
		self.action_bound = action_bound
		self.action_offset = action_offset
		self.learning_rate = learning_rate
		self.tau = tau

		# Actor Network
		self.inputs, self.out, self.scaled_out = self.create_actor_network()

		self.network_params = tf.trainable_variables()

		# Target Network
		self.target_inputs, self.target_out, self.target_scaled_out = self.create_actor_network()
		
		self.target_network_params = tf.trainable_variables()[len(self.network_params):]

		# Op for periodically updating target network with online network weights
		self.update_target_network_params = \
			[self.target_network_params[i].assign(tf.mul(self.network_params[i], self.tau) + \
				tf.mul(self.target_network_params[i], 1. - self.tau))
				for i in range(len(self.target_network_params))]

		# This gradient will be provided by the critic network
		self.action_gradient = tf.placeholder(tf.float32, [None, self.a_dim])
		
		# Combine the gradients here 
		self.actor_gradients = tf.gradients(self.scaled_out, self.network_params, -self.action_gradient)

		# Optimization Op
		self.optimize = tf.train.AdamOptimizer(self.learning_rate).\
			apply_gradients(zip(self.actor_gradients, self.network_params))

		self.num_trainable_vars = len(self.network_params) + len(self.target_network_params)

	def create_actor_network(self): 
		inputs = tflearn.input_data(shape=[None, self.s_dim])
		net = tflearn.fully_connected(inputs, 38, activation='relu')
		net = tflearn.fully_connected(net, 38, activation='relu')
		# Final layer weights are init to Uniform[-3e-3, 3e-3]
		w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)
		out = tflearn.fully_connected(net, self.a_dim, activation='tanh', weights_init=w_init)
		scaled_out = tf.add(self.action_offset, tf.mul(out, self.action_bound)) # Scale output to -action_bound to action_bound
		return inputs, out, scaled_out 

	def train(self, inputs, a_gradient):
		self.sess.run(self.optimize, feed_dict={
			self.inputs: inputs,
			self.action_gradient: a_gradient
		})

	def predict(self, inputs):
		return self.sess.run(self.scaled_out, feed_dict={
			self.inputs: inputs
		})

	def predict_target(self, inputs):
		return self.sess.run(self.target_scaled_out, feed_dict={
			self.target_inputs: inputs
		})

	def update_target_network(self):
		self.sess.run(self.update_target_network_params)

	def get_num_trainable_vars(self):
		return self.num_trainable_vars

class CriticNetwork(object):
	""" 
	Input to the network is the state and action, output is Q(s,a).
	The action must be obtained from the output of the Actor network.

	"""
	def __init__(self, sess, state_dim, action_dim, learning_rate, tau, num_actor_vars):
		self.sess = sess
		self.s_dim = state_dim
		self.a_dim = action_dim
		self.learning_rate = learning_rate
		self.tau = tau

		# Create the critic network
		self.inputs, self.action, self.out = self.create_critic_network()

		self.network_params = tf.trainable_variables()[num_actor_vars:]

		# Target Network
		self.target_inputs, self.target_action, self.target_out = self.create_critic_network()
		
		self.target_network_params = tf.trainable_variables()[(len(self.network_params) + num_actor_vars):]

		# Op for periodically updating target network with online network weights with regularization
		self.update_target_network_params = \
			[self.target_network_params[i].assign(tf.mul(self.network_params[i], self.tau) + tf.mul(self.target_network_params[i], 1. - self.tau))
				for i in range(len(self.target_network_params))]
	
		# Network target (y_i)
		self.predicted_q_value = tf.placeholder(tf.float32, [None, 1])

		# Define loss and optimization Op
		self.loss = tflearn.mean_square(self.predicted_q_value, self.out)
		self.optimize = tf.train.AdamOptimizer(self.learning_rate).minimize(self.loss)

		# Get the gradient of the net w.r.t. the action
		self.action_grads = tf.gradients(self.out, self.action)

	def create_critic_network(self):
		inputs = tflearn.input_data(shape=[None, self.s_dim])
		action = tflearn.input_data(shape=[None, self.a_dim])
		net = tflearn.fully_connected(inputs, 38, activation='relu')

		# Add the action tensor in the 2nd hidden layer
		# Use two temp layers to get the corresponding weights and biases
		t1 = tflearn.fully_connected(net, 38)
		t2 = tflearn.fully_connected(action, 38)

		net = tflearn.activation(tf.matmul(net,t1.W) + tf.matmul(action, t2.W) + t2.b, activation='relu')

		# linear layer connected to 1 output representing Q(s,a) 
		# Weights are init to Uniform[-3e-3, 3e-3]
		w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)
		out = tflearn.fully_connected(net, 1, weights_init=w_init)
		return inputs, action, out

	def train(self, inputs, action, predicted_q_value):
		return self.sess.run([self.out, self.optimize], feed_dict={
			self.inputs: inputs,
			self.action: action,
			self.predicted_q_value: predicted_q_value
		})

	def predict(self, inputs, action):
		return self.sess.run(self.out, feed_dict={
			self.inputs: inputs,
			self.action: action
		})

	def predict_target(self, inputs, action):
		return self.sess.run(self.target_out, feed_dict={
			self.target_inputs: inputs,
			self.target_action: action
		})

	def action_gradients(self, inputs, actions): 
		return self.sess.run(self.action_grads, feed_dict={
			self.inputs: inputs,
			self.action: actions
		})

	def update_target_network(self):
		self.sess.run(self.update_target_network_params)

# ===========================
#   Tensorflow Summary Ops
# ===========================
def build_summaries(): 
	episode_reward = tf.Variable(0.)
	tf.scalar_summary("Reward", episode_reward)
	episode_ave_max_q = tf.Variable(0.)
	tf.scalar_summary("Qmax Value", episode_ave_max_q)

	summary_vars = [episode_reward, episode_ave_max_q]
	summary_ops = tf.merge_all_summaries()

	return summary_ops, summary_vars

# ===========================
#   Agent Training
# ===========================
def train(sess, actor, critic):

	# Set up summary Ops
	summary_ops, summary_vars = build_summaries()

	sess.run(tf.initialize_all_variables())
	writer = tf.train.SummaryWriter(SUMMARY_DIR, sess.graph)

	# Initialize target network weights
	actor.update_target_network()
	critic.update_target_network()

	# Initialize replay memory
	replay_buffer = ReplayBuffer(BUFFER_SIZE, RANDOM_SEED)

	for i in xrange(MAX_EPISODES):

		# s = env.reset()

		ep_reward = 0
		ep_ave_max_q = 0
		s = Utils.INITIAL_STATE 
		no_coins_pocketed = 0

		for j in xrange(MAX_EP_STEPS):

			# if RENDER_ENV: 
			#     env.render()

			# Added exploration noise
			snn = s["White_Locations"] + s["Black_Locations"] + s["Red_Location"]
			snn = snn + [(0,0)]*(19 - len(snn))
			snn = np.reshape(np.array(snn), (1,38))
			# a = actor.predict(snn) + (1. / (1. + i + j))
			a = np.add(np.asarray(actor.predict(snn)), np.multiply((10./ (100. + 20*i + j)) * random.random(), np.asarray(actor.action_bound)))
			
			
			if a[0][0] > 1:
				a[0][0] = 1
			elif a[0][0] < 0:
				a[0][0] = 0

			if a[0][1] > 225:
				a[0][1] = 225
			elif a[0][1] < -45:
				a[0][1] = -45

			if a[0][2] > 1:
				a[0][2] = 1
			elif a[0][2] < 0:
				a[0][2] = 0

			curr_coins = s["White_Locations"] + s["Black_Locations"] + s["Red_Location"]
			# if j==0:
			print "\n Episode number : " + str(i) + "   Step number:" + str(j) + "\n" + str(a[0]) + "\n" + "Coins left:" + str(len(curr_coins))
				# print a[0]

			s2, r = simulate(s, validate(a[0],s))

			# if color == "White" :
			#     opp_color = "Black"
			# else:
			#     opp_color = "White"

			# my_targets = s2[color+"_Locations"]
			# opp_targets = s2[opp_color + "_Locations"]

			my_targets = s2["White_Locations"] + s2["Black_Locations"] + s2["Red_Location"] 
			# if j==0:
			   #  print "my targets size = " + str(len(my_targets)) + " Reward = " + str(r)

			if len(my_targets) >= len(curr_coins):
				no_coins_pocketed += 1
			else:
				no_coins_pocketed = 0

			terminal = False
			
			if no_coins_pocketed > 50 and len(curr_coins)>2:
				terminal = True
			elif no_coins_pocketed > 100 and len(curr_coins) <= 2:
				terminal = True


			if not my_targets:
				terminal = True

			if terminal:
				summary_str = sess.run(summary_ops, feed_dict={
					summary_vars[0]: ep_reward,
					summary_vars[1]: ep_ave_max_q / float(j)
				})

				writer.add_summary(summary_str, i)
				writer.flush()

				print '| Reward: %.2i' % int(ep_reward), " | Episode", i, \
					'| Qmax: %.4f' % (ep_ave_max_q / float(j))
				break

			s2nn = s2["White_Locations"] + s2["Black_Locations"] + s2["Red_Location"]
			s2nn = s2nn + [(0,0)]*(19 - len(s2nn))
			s2nn = np.reshape(np.array(s2nn), (1,38))
			
			# s2, r, terminal, info = env.step(a[0])

			replay_buffer.add(np.reshape(snn, (actor.s_dim,)), np.reshape(a, (actor.a_dim,)), r, \
				terminal, np.reshape(s2nn, (actor.s_dim,)))

			# Keep adding experience to the memory until
			# there are at least minibatch size samples
			if replay_buffer.size() > MINIBATCH_SIZE:     
				s_batch, a_batch, r_batch, t_batch, s2_batch = \
					replay_buffer.sample_batch(MINIBATCH_SIZE)

				# Calculate targets
				target_q = critic.predict_target(s2_batch, actor.predict_target(s2_batch))

				y_i = []
				for k in xrange(MINIBATCH_SIZE):
					if t_batch[k]:
						y_i.append(r_batch[k])
					else:
						y_i.append(r_batch[k] + GAMMA * target_q[k])

				# Update the critic given the targets
				predicted_q_value, _ = critic.train(s_batch, a_batch, np.reshape(y_i, (MINIBATCH_SIZE, 1)))
			
				ep_ave_max_q += np.amax(predicted_q_value)

				# Update the actor policy using the sampled gradient
				a_outs = actor.predict(s_batch)                
				grads = critic.action_gradients(s_batch, a_outs)
				actor.train(s_batch, grads[0])

				# Update target networks
				actor.update_target_network()
				critic.update_target_network()

			s = s2
			ep_reward += r

			
def main(_):
	with tf.Session() as sess:
		
		# env = gym.make(ENV_NAME)
		np.random.seed(RANDOM_SEED)
		tf.set_random_seed(RANDOM_SEED)
		# env.seed(RANDOM_SEED)

		# TODO : fill this in
		# state_dim = env.observation_space.shape[0]
		# action_dim = env.action_space.shape[0]
		state_dim = 19 * 2
		action_dim = 3
		# This will be a triple
		action_bound = (0.5, 135, 0.5)
		action_offset = (0.5, 90, 0.5)

		# action_bound = env.action_space.high 
		# Ensure action bound is symmetric
		# assert (env.action_space.high == -env.action_space.low)

		actor = ActorNetwork(sess, state_dim, action_dim, action_bound, action_offset, \
			ACTOR_LEARNING_RATE, TAU)

		critic = CriticNetwork(sess, state_dim, action_dim, \
			CRITIC_LEARNING_RATE, TAU, actor.get_num_trainable_vars())

		# if GYM_MONITOR_EN:
		#     if not RENDER_ENV:
		#         env.monitor.start(MONITOR_DIR, video_callable=False, force=True)
		#     else:
		#         env.monitor.start(MONITOR_DIR, force=True)

		train(sess, actor, critic)

		# if GYM_MONITOR_EN:
		#     env.monitor.close()

if __name__ == '__main__':
	tf.app.run()
