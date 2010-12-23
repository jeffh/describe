
class Properties(object):
    """docstring for Properties"""
    def __init__(self, value, wrapper):
        self.__describe_value = value
        self.__describe_wrapper = wrapper
        
    def __getitem__(self, key):
        return self.__describe_wrapper(lambda: self.__describe_value[key], lazy=True)
        
    def __getattr__(self, key):
        return self.__describe_wrapper(lambda: getattr(self.__describe_value, key), lazy=True)