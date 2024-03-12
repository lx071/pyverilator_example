import simpy

class Socket:
    def __init__(self):
        self.data = None
        self.other_socket = None
        self.func = None

    # 将该 socket 与其他 socket 进行连接
    def bind(self, other):
        # 如果两个 socket 还未进行连接
        if (self.other_socket is None and other.other_socket is None):
            self.other_socket = other
            other.other_socket = self
        else:
            print("bind error")

    # 将 函数 注册到该 socket 中
    def register_transport(self, func):
        self.func = func

    # 调用 相连接的 socket 的函数
    def transport(self, payload, delay):
        if self.other_socket.func is not None:
            self.other_socket.func(payload, delay)

class Module:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        pass
    def __register(self, func):
        pass
