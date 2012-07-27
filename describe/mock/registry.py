
__all__ = ('Registry', 'RegistryError')


class RegistryError(Exception):
    pass


class Registry(object):
    registries = []
    def __init__(self):
        if self not in self.registries:
            self.registries.append(self)
        self.clear()

    def __len__(self):
        return len(self.stubs)

    @classmethod
    def get_closest(cls):
        try:
            return cls.registries[-1]
        except IndexError:
            raise RegistryError('Missing Registry, please create one')

    def add(self, stub):
        if stub not in self.stubs:
            self.stubs.append(stub)

    def remove(self, stub):
        self.stubs.remove(stub)

    def destroy(self):
        self.clear()
        self.registries.remove(self)

    def clear(self):
        self.stubs = []
        self.post_verification = []

    def add_post_verify_hook(self, fn):
        self.post_verification.insert(0, fn)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.verify_mocks()
        self.destroy()

    @property
    def mocks(self):
        return [stub for stub in self.stubs if isinstance(stub, Mock)]

    def verify_mocks(self):
        for mock in self.mocks:
            mock.verify_expectations()

        for fn in self.post_verification:
            print fn
            fn()

