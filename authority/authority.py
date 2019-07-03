# from authority import models
#
#
# # 添加权限
# def add(filedata={}):
#     auth = models.authority.objects.create(**filedata)
#     return auth
#
#
# # 添加权限的状态
# def addAuthState(**filedata):
#     authState = models.doc_state.objects.create(**filedata)
#     return authState
#
#
# # 查看用户是否有读的权限
# def selectReadAuth(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.read_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
#
#
# # 查看用户是否有写的权限
# def selectWriteAuth(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.write_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
#
#
# # 查看用户是否有删除的权限
# def selectDeleteAuth(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.delete_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
#
#
# # 查看用户是否有引用的权限
# def selectExportAuth(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.export_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
#
#
# # 查看用户是否有修改状态的权限
# def selectChangeState(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.change_state_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
#
#
# # 查看用户是否有引用的权限
# def selectReference(documentId, userId):
#     doc = models.authority.objects.filter(uuid=documentId)
#     for d in doc:
#         userIds = d.reference_privilege
#         if userId in userIds:
#             return True
#         else:
#             return False
