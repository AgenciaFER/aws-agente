class Session:
    def __init__(self, *args, **kwargs):
        pass
    def client(self, *args, **kwargs):
        class Dummy:
            def __getattr__(self, name):
                def method(*args, **kwargs):
                    return {}
                return method
        return Dummy()
    def resource(self, *args, **kwargs):
        class Dummy:
            def __getattr__(self, name):
                def method(*args, **kwargs):
                    return {}
                return method
        return Dummy()
