from path import models


# 新增路径
def add(filedata = {}):
    path = models.Path.objects.create(**filedata)
    return path

# 查询全部路径列表
def showById(path_id):
    assert path_id
    paths = models.Path.objects.filter(path_id=path_id)
    return paths