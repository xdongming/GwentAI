import torch
from env import Env
import utils
import matplotlib.pyplot as plt
from agent import train_DQN, ReplayBuffer, DQN


def train():
    lr = 1e-2
    num_episodes = 100000
    hidden_dim = 128
    gamma = 0.98
    epsilon = 0.1
    target_update = 50
    buffer_size = 5000
    minimal_size = 1000
    batch_size = 64
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    env = Env()
    env_name = 'Gwent'
    state_dim = 75
    action_dim = 44
    replay_buffer = ReplayBuffer(buffer_size)
    agent = DQN(state_dim, hidden_dim, action_dim, lr, gamma, epsilon, target_update, device, env.CardSet, 'DuelingDQN')
    return_list, max_q_value_list = train_DQN(agent, env, num_episodes, replay_buffer, minimal_size, batch_size)
    episodes_list = list(range(len(return_list)))
    mv_return = utils.moving_average(return_list, 9)
    plt.semilogx(episodes_list, mv_return)
    plt.xlabel('Episodes')
    plt.ylabel('Returns')
    plt.title('Dueling DQN on {}'.format(env_name))
    plt.show()
    frames_list = list(range(len(max_q_value_list)))
    plt.semilogx(frames_list, max_q_value_list)
    plt.xlabel('Frames')
    plt.ylabel('Q value')
    plt.title('Dueling DQN on {}'.format(env_name))
    plt.show()

if __name__ == '__main__':
    train()
