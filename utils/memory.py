import numpy as np
import torch


class ReplayBuffer(object):
    def __init__(self, state_dim, action_dim, max_size=int(5e3)):
        self.max_size = int(max_size)
        self.ptr = 0
        self.size = 0

        self.state = np.zeros((self.max_size, state_dim))
        self.action = np.zeros((self.max_size, action_dim))
        self.next_state = np.zeros((self.max_size, state_dim))
        self.reward = np.zeros((self.max_size, 1))
        self.not_done = np.zeros((self.max_size, 1))

        self.h = np.zeros((self.max_size, 256))
        self.nh = np.zeros((self.max_size, 256))

        self.c = np.zeros((self.max_size, 256))
        self.nc = np.zeros((self.max_size, 256))

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")

    def add(
        self, state, action, next_state, reward, done, hiddens, next_hiddens
    ):

        h, c = hiddens
        nh, nc = next_hiddens

        self.state[self.ptr] = state
        self.action[self.ptr] = action
        self.next_state[self.ptr] = next_state
        self.reward[self.ptr] = reward
        self.not_done[self.ptr] = 1. - done

        # Detach the hidden state so that BPTT only goes through 1 timestep
        self.h[self.ptr] = h.detach().cpu()
        self.c[self.ptr] = c.detach().cpu()
        self.nh[self.ptr] = nh.detach().cpu()
        self.nc[self.ptr] = nc.detach().cpu()

        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = np.random.randint(0, self.size, size=int(batch_size))

        h = torch.tensor(self.h[ind][None, ...], requires_grad=True).to(self.device)
        c = torch.tensor(self.c[ind][None, ...], requires_grad=True).to(self.device)
        nh = torch.tensor(self.nh[ind][None, ...], requires_grad=True).to(self.device)
        nc = torch.tensor(self.nc[ind][None, ...], requires_grad=True).to(self.device)

        s = torch.FloatTensor(self.state[ind][:, None, :]).to(self.device)
        a = torch.FloatTensor(self.action[ind][:, None, :]).to(self.device)
        ns = \
            torch.FloatTensor(self.next_state[ind][:, None, :]).to(self.device)
        r = torch.FloatTensor(self.reward[ind][:, None, :]).to(self.device)
        d = torch.FloatTensor(self.not_done[ind][:, None, :]).to(self.device)
        return s, a, ns, r, d, (h, c), (nh, nc)