class DictBuilder(type):
    def __call__(cls, **kwargs):
        d = cls.__dict__.copy()
        d.update(kwargs)
        return d


class MyDict(metaclass=DictBuilder):
    foo = 'bar'


print(MyDict(baz=1))
