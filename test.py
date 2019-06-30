

def test_add(func):
    def wrapped(*args, **kwargs):
        print(func.__name__)
        print(args[0].__name__)
        result = func(*args, **kwargs)
        print(2)
        return result
    return wrapped


class test(object):

    def __init__(self, user=0):
        self.user = user

    @test_add
    def save(self, props):

        print(props)


a = test(user=1)

a.save('whb')
