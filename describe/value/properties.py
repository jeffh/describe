
class Properties(object):
    """An object that invokes wrapper to all getattr and getitem.

    This is used to lazily eval all get calls.
    """
    def __init__(self, value, wrapper, *args, **kwargs):
        self.__describe_value = value
        self.__describe_wrapper = wrapper
        self.__args, self.__kwargs = args, kwargs

    def __getitem__(self, key):
        return self.__describe_wrapper(lambda: self.__describe_value[key], *self.__args, **self.__kwargs)

    def __getattr__(self, key):
        return self.__describe_wrapper(lambda: getattr(self.__describe_value, key), *self.__args, **self.__kwargs)

