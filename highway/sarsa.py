import numpy as np
import pandas as pd


class Sarsa(object):
    def __init__(self, action_space, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = action_space  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy

        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series(
                    [0] * len(self.actions),
                    # index=str(state),
                    name=str(state),
                )
            )

    def choose_action(self, observation):
        self.check_state_exist(str(observation))
        # action selection
        if np.random.rand() < self.epsilon:
            # choose best action
            state_action = self.q_table.loc[str(observation), :]
            # some actions may have the same value, randomly choose on in these actions
            action = np.random.choice(state_action[state_action == np.max(state_action)].index)
        else:
            # choose random action
            action = np.random.choice(self.actions)
        return action

    def learn(self, *args):
        pass


# backward eligibility traces
class SarsaLambdaTable(Sarsa):
    def __init__(self, actions, state, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9, trace_decay=0.9):
        super(SarsaLambdaTable, self).__init__(actions, learning_rate, reward_decay, e_greedy)
        self.state = state
        # backward view, eligibility trace.
        self.lambda_ = trace_decay
        self.eligibility_trace = self.q_table.copy()

    def check_state_exist(self, state):
        # print("Sarsa_action")
        if state not in self.q_table.index:
            # append new state to q table
            to_be_append = pd.Series(
                [0] * len(self.actions),
                # index=str(state),
                name=str(state),
            )
            self.q_table = self.q_table.append(to_be_append)

            # also update eligibility trace
            self.eligibility_trace = self.eligibility_trace.append(to_be_append)

    def learn(self, s, a, r, s_, a_):
        # print("Sarsa_learn")
        self.check_state_exist(str(s_))
        q_predict = self.q_table.loc[str(s), a]
        if s_ != 'terminal':
            q_target = r + self.gamma * self.q_table.loc[str(s_), a_]  # next state is not terminal
        else:
            q_target = r  # next state is terminal
        error = q_target - q_predict

        # increase trace amount for visited state-action pair

        # Method 1:
        # self.eligibility_trace.loc[s, a] += 1

        # Method 2:
        # self.eligibility_trace.loc[str(s), :] *= 0
        # self.eligibility_trace.loc[str(s), a] = 1

        # Q update
        self.q_table += self.lr * error
        # self.q_table += self.lr * error * self.eligibility_trace

        # decay eligibility trace after update
        # self.eligibility_trace *= self.gamma * self.lambda_

