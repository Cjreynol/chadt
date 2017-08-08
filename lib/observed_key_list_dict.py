from collections.abc import MutableMapping

class ObservedKeyListDict(MutableMapping):
    
    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self.observers = []

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        if key not in self._dict:
            self._dict[key] = value
            self.notify_observers()
        else:   
            self._dict[key] = value

    def __delitem__(self, key):
        if key in self._dict:
            del self._dict[key]
            self.notify_observers()
        else:
            del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def notify_observers(self):
        for observer in self.observers:
            observer()

    def add_observer(self, observer):
        self.observers.append(observer)
