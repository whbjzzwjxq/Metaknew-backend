import functools

from authority import authority
from authority import models

class Authority(object):

    def checkAuth(self,uuid,user_id,level):
            auth = level
            auths = models.doc_state.objects.filter(uuid=uuid)
            if auth == 'read':
                for a in auths:
                    if a.private is True:
                        result = authority.selectReadAuth(uuid, user_id)
                        if result is True:
                            return True
                        else:
                            return False
                    else:
                        return True
            elif auth == 'delete':
                result = authority.selectDeleteAuth(uuid, user_id)
                if result is True:
                    return True
                else:
                    return False
            elif auth == 'change_state':
                result = authority.selectChangeState(uuid, user_id)
                if result is True:
                    return True
                else:
                    return False
            elif auth == 'write':
                result = authority.selectWriteAuth(uuid, user_id)
                if result is True:
                    return True
                else:
                    return False
            elif auth == 'export':
                for a in auths:
                    if a.shared is True:
                        result = authority.selectExportAuth(uuid, user_id)
                        if result is True:
                            return True
                        else:
                            return False
                    else:
                        return False
            elif auth == 'reference':
                for a in auths:
                    if a.common is True:
                        return True
                    else:
                        result = authority.selectReference(uuid, user_id)
                        if result is True:
                            return True
                        else:
                            return False
            else:
                return False




