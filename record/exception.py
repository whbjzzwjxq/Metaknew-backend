from typing import Type, Union


class CodeExistError(BaseException):
    """
    验证码已经发送
    """
    pass


class CodeExpiredError(BaseException):
    """
    验证码过期
    """
    pass


class CodeDoesNotMatchError(BaseException):
    """
    验证码不匹配
    """
    pass


class IdGenerationError(BaseException):
    """
    id生成错误
    """
    pass


class ObjectAlreadyExist(BaseException):
    """
    远端对象已存在
    """
    pass


class UnAuthorizationError(BaseException):
    """
    登录信息错误
    """
    pass


class RewriteMethodError(BaseException):
    """
    方法需要重写
    """
    pass


class WrongPasswordError(BaseException):
    """
    密码错误
    """
    pass

class TestApiError(BaseException):
    """
    Api是测试Api 显示该提示表明已经resolve_hook, main_hook已经完成
    """
    pass

class ErrorForWeb:
    def __init__(self, error: Type[BaseException], description: Union[str, bytes] = '', content: dict = dict,
                 is_dev=False, is_error=False, status: int = 400):
        """
        :param error: 错误类型
        :param description: 描述
        :param content: 由dict组成的内容
        :param is_dev: 是否是开发使用
        :param status: 响应码
        """
        self.error = error
        self.description = str(description)
        self.content = content
        self.is_dev = is_dev
        self.is_error = is_error
        self.status = status

    def __bool__(self):
        return False

    def raise_error(self):
        raise self.error(self.description)


class UnAuthorization(ErrorForWeb):
    def __init__(self, description: str):
        super().__init__(error=UnAuthorizationError, description=description, is_dev=False, is_error=False, status=401)


class WrongPassword(ErrorForWeb):
    def __init__(self, description: str):
        super().__init__(error=WrongPasswordError, description=description, is_dev=False, is_error=True, status=401)


TestApi = ErrorForWeb(error=TestApiError, description=TestApiError.__doc__, is_dev=True, is_error=True, status=403)
