from area import models

#根据id选择area
def selectById(id):
    assert id
    # user = User.get(User.useremail == email)
    area = models.Area.objects.get(id=id)
    return area

# add
def add(filedata={}):
    area = models.Area.objects.create(**filedata)
    return area