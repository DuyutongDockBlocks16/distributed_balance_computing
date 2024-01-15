class SDK_error(RuntimeError):
    def __init__(self, msg):
        self.type = 'sdk_error'
        self.msg = msg

class NM_error(RuntimeError):
    def __init__(self, msg):
        self.type = 'nm_error'
        self.msg = msg

class Kafka_error(RuntimeError):
    def __init__(self, msg):
        self.type = 'kafka_error'
        self.msg = msg
