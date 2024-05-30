class CustomState:
    def __init__(self):
        self.agent = None
        self.initialized = False
        self.state = None

    def init(self):
        self.initialized = True
        
    def reset(self):
        pass

    def calc_state(self):
        if self.initialized  == False:
            self.init()

        return self.state