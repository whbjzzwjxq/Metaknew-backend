from django.test import TestCase

# Create your tests here.


class BaseNode:
    def __init__(self):
        self.TEST = 3


class Person(BaseNode):
    def __init__(self):
        super().__init__()
        self.PeriodStart = 2
        self.PeriodEnd = 1
        self.BirthPlace = 1
        print(self.__dict__)


init = {
    'Person': Person,
    'BaseNode': BaseNode
}

a = init['Person']()

# a = 'Person'
# b = type(a, (), {})
# c = Person('Person')
# print(c.PeriodStart)
