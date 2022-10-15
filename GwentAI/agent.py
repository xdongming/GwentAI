import random
from random import choice
import numpy as np
import collections
from tqdm import tqdm
import torch
import torch.nn.functional as F


class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = collections.deque(maxlen=capacity)

    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        transitions = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done = zip(*transitions)
        return np.array(state), action, reward, np.array(next_state), done

    def size(self):
        return len(self.buffer)


class DQN:
    def __init__(self, state_dim, hidden_dim, action_dim, learning_rate, gamma, epsilon, target_update, device,
                 CardSet, dqn_type='VanillaDQN'):
        self.action_dim = action_dim
        if dqn_type == 'DuelingDQN':
            self.q_net = VAnet(state_dim, hidden_dim, self.action_dim).to(device)
            self.target_q_net = VAnet(state_dim, hidden_dim, self.action_dim).to(device)
        else:
            self.q_net = Qnet(state_dim, hidden_dim, self.action_dim).to(device)
            self.target_q_net = Qnet(state_dim, hidden_dim, self.action_dim).to(device)
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 100)
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=learning_rate)
        self.gamma = gamma
        self.epsilon = epsilon
        self.target_update = target_update
        self.count = 0
        self.device = device
        self.dqn_type = dqn_type
        self.action_set = CardSet + ['skill', 'end']

    def take_action(self, state, action_space, episode):
        if np.random.random() < self.epsilon * (0.999 ** episode):
            return choice(np.array(self.action_set)[action_space.cpu().numpy() == 1])
        else:
            state = torch.tensor(state, dtype=torch.float).to(self.device)
            q_value = self.q_net(state).ravel()
            max_q = max(q_value[action_space.cpu().numpy() == 1]).item()
            for i in range(len(self.action_set)):
                if q_value[i] == max_q:
                    break
            return self.action_set[i]

    def max_q_value(self, state):
        state = torch.tensor([state], dtype=torch.float).to(self.device)
        return self.q_net(state).max().item()

    def update(self, transition_dict):
        states = torch.tensor(transition_dict['states'], dtype=torch.float).to(self.device)
        actions = torch.tensor(transition_dict['actions']).view(-1, 1).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'], dtype=torch.float).view(-1, 1).to(self.device)
        next_states = torch.tensor(transition_dict['next_states'], dtype=torch.float).to(self.device)
        dones = torch.tensor(transition_dict['dones'], dtype=torch.float).view(-1, 1).to(self.device)
        q_values = self.q_net(states).gather(1, actions)
        if self.dqn_type == 'DoubleDQN':
            max_action = self.q_net(next_states).max(1)[1].view(-1, 1)
            max_next_q_values = self.target_q_net(next_states).gather(1, max_action)
        else:
            max_next_q_values = self.target_q_net(next_states).max(1)[0].view(-1, 1)
        q_targets = rewards + self.gamma * max_next_q_values * (1 - dones)
        dqn_loss = torch.mean(F.mse_loss(q_values, q_targets))
        self.optimizer.zero_grad()
        dqn_loss.backward()
        self.optimizer.step()

        if self.count % self.target_update == 0:
            self.target_q_net.load_state_dict(self.q_net.state_dict())
        self.count += 1


def train_DQN(agent, env, num_episodes, replay_buffer, minimal_size, batch_size):
    return_list = []
    max_q_value_list = []
    max_q_value = 0
    for i in range(100):
        with tqdm(total=int(num_episodes / 100), desc='Iteration %d' % i) as pbar:
            for i_episode in range(int(num_episodes / 100)):
                state = env.reset()
                initial_state = state
                done = False
                present_episode = num_episodes / 100 * i + i_episode + 1
                while not done:
                    if env.turn:
                        action_space = env.cal_action_space('self')
                        if initial_state == state:
                            action_space[-1] = 0.
                        action = agent.take_action(state, action_space, present_episode)
                        max_q_value = agent.max_q_value(state) * 0.005 + max_q_value * 0.995
                        max_q_value_list.append(max_q_value)
                        next_state, _, reward, done = env.step(action)
                    else:
                        action_space = env.cal_action_space('enemy')
                        action = enemy_agent.take_action(state, action_space, present_episode)  #
                        max_q_value = agent.max_q_value(state) * 0.005 + max_q_value * 0.995
                        max_q_value_list.append(max_q_value)
                        _, next_state, reward, done = env.step(action)
                    replay_buffer.add(state, agent.action_set.index(action), reward, next_state, done)
                    state = next_state
                    if replay_buffer.size() > minimal_size:
                        b_s, b_a, b_r, b_ns, b_d = replay_buffer.sample(batch_size)
                        transition_dict = {'states': b_s, 'actions': b_a, 'next_states': b_ns, 'rewards': b_r,
                                           'dones': b_d}
                        agent.update(transition_dict)
                return_list.append(max(env.self_reward, env.enemy_reward))
                if (i_episode + 1) % 10 == 0:
                    pbar.set_postfix({'episode': '%d' % (num_episodes / 100 * i + i_episode + 1),
                                      'return': '%.3f' % np.mean(return_list[-10:])})
                pbar.update(1)
    torch.save(agent.q_net.state_dict(), './model/model.pth')
    return return_list, max_q_value_list


class VAnet(torch.nn.Module):
    def __init__(self, state_dim, hidden_dim, action_dim):
        super(VAnet, self).__init__()
        self.fc1 = torch.nn.Linear(state_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc4 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc_A = torch.nn.Linear(hidden_dim, action_dim)
        self.fc_V = torch.nn.Linear(hidden_dim, 1)
        self.dropout = torch.nn.Dropout(0.3)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu((self.fc2(x)))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.dropout(x)
        A = self.fc_A(F.relu(self.fc4(x)))
        V = self.fc_V(F.relu(self.fc4(x)))
        Q = V + A - A.mean(-1).view(-1, 1)
        return Q
