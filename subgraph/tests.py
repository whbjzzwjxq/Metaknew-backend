from django.test import TestCase
import re
from subgraph.models import BaseNode, Person
# Create your tests here.


def get_dict(node):
    keylist = []
    for key in dir(node):
        if not re.match(r'__.*__', key):
            keylist.append(key)
    return keylist


PrimaryLabel = 'Person'

init = {
    'Person': Person,
    'BaseNode': BaseNode
}

a = init[PrimaryLabel]()



