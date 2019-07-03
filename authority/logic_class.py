from subgraph.logic_class import Doc


class AuthChecker:

    def __init__(self, func):
        self._func = func

    def __call__(self, target: Doc(), *args, **kwargs):
        if self.check(target):
            return self._func(target, *args, **kwargs)
        else:
            return None

    def check(self, target):
        raise AttributeError('不能使用基础方法 需要重写')


class QueryChecker(AuthChecker):

    def check(self, target):
        # 类方法的第一个参数是self, 这里的target捕获的是self
        uuid = target.origin
        user = target.user
        auth = target.auth_sheet.objects.get(pk=uuid)  # 这里的意思是检查权限的表跟类绑定
        if auth.Common:
            return True
        elif auth.Shared and user in auth.SharedTo:
            return True
        elif user in auth.ChangeState:
            return True
        elif user == auth.Owner:
            return True
        else:
            return False

    # todo
    # 添加其他权限的装饰器
    # 1 WriteChecker
    # 2 ReferenceChecker
    # 3 DeleteChecker
    # 4 ChangeStateChecker
