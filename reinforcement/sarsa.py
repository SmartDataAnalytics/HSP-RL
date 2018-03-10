import gym
import itertools
import matplotlib
import numpy as np
import pandas as pd
import random
import sys
from fire_simulation import fireSimulation

if "../" not in sys.path:
  sys.path.append("../") 

from collections import defaultdict
from myworld import GridworldEnv
from lib import plotting

matplotlib.style.use('ggplot')

env = GridworldEnv()

fire_sim = []

def make_epsilon_greedy_policy(Q, epsilon, nA):

    def policy_fn(observation):
        A = np.ones(nA, dtype=float) * epsilon / nA
        best_action = np.argmax(Q[observation])
        A[best_action] += (1.0 - epsilon)
        return A
    return policy_fn

def sarsa(env, num_episodes, discount_factor=1.0, alpha=0.5, epsilon=0.1):

    
    # The final action-value function.
    # A nested dictionary that maps state -> (action -> action-value).
    Q = defaultdict(lambda: np.zeros(env.action_space.n))
    
    # Keeps track of useful statistics
    stats = plotting.EpisodeStats(
        episode_lengths=np.zeros(num_episodes),
        episode_rewards=np.zeros(num_episodes))

    # The policy we're following
    policy = make_epsilon_greedy_policy(Q, epsilon, env.action_space.n)
    
    for i_episode in range(num_episodes):
        
        
        # Reset the environment and pick the first action
        state = env.reset()
        action_probs = policy(state)
        action = np.random.choice(np.arange(len(action_probs)), p=action_probs)
        fire_sim = fireSimulation(4)
        
        # One step in the environment
        for t in itertools.count():
            
            # Change P (Fire Iteration)
            
            fire_sim.iterFire(fire_sim.fire)
            fire_sim.time +=1

            fire_sim.fire = env.changeP(fire_sim.fire,fire_sim.time)
    
            # Take a step
            fire_sim.fire, next_state, reward, done, _ = env.step(action,fire_sim.fire)

#            fire_sim._renderFire(fire = fire_sim.fire)
#            print()
            #print(t)
            

            # Pick the next action
            next_action_probs = policy(next_state)
            next_action = np.random.choice(np.arange(len(next_action_probs)), p=next_action_probs)
            
            # Update statistics
            stats.episode_rewards[i_episode] += reward
            stats.episode_lengths[i_episode] = t
            
            # TD Update
            td_target = reward + discount_factor * Q[next_state][next_action]
            td_delta = td_target - Q[state][action]
            Q[state][action] += alpha * td_delta
    
            if not fire_sim.checkFire(fire_sim.fire):
                print(t)
                break
                
            action = next_action
            state = next_state        
    
    return Q, stats


Q, stats = sarsa(env, 100)

#plotting.plot_episode_stats(stats)

'''
fire_sim = fireSimulation(2)
while not fire_sim.checkEmpty(fire_sim.fire):
    print()
    fire_sim.iterFire(fire_sim.fire)
    fire_sim._renderFire(fire_sim.fire)
'''

