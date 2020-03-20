import json

from django.http import HttpResponse

from base_api.interface_user import UserPropUpdateData, UserPLabelUpdatePropsData
from base_api.logic_class import UserApi, HttpRequestUser
from users.logic_class import UserPropResolveModel, UserPLabelExtraPropsModel


class UserDataApi(UserApi):
    """
    user编辑内容的api
    """
    URL = 'user/data/'
    abstract = True


class UserEditDataUpdateApi(UserDataApi):
    """
    用户表直接编辑
    """
    URL = ''
    abstract = True
    method = 'POST'
    frontend_data = UserPropUpdateData
    model = UserPropResolveModel

    def _main_hook(self, result: UserPropUpdateData, request: HttpRequestUser):
        user_model = request.user
        prop_model = self.model(user_model.user_id)
        prop_model.update_create(result.DataList)
        return prop_model

    def _save_hook(self, result: UserPropResolveModel):
        result.model.objects.bulk_create(result.create_list)
        result.model.objects.bulk_update(result.update_list, result.model.update_fields())
        return None

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200)


class UserPropResolveUpdate(UserEditDataUpdateApi):
    """
    prop_resolve更新 与新建是同一个Api
    """
    URL = 'prop_resolve/update'
    abstract = False


class UserLabelPropsUpdate(UserEditDataUpdateApi):
    """
    标签和属性组 与新建是同一个Api
    """
    URL = 'label/props/update'
    abstract = False
    method = 'POST'
    frontend_data = UserPLabelUpdatePropsData
    model = UserPLabelExtraPropsModel


class UserEditDataQuery(UserDataApi):
    """
    请求用户配置数据
    """
    URL = 'query'
    abstract = False
    method = 'GET'
    frontend_data = None

    def _main_hook(self, result: None, request: HttpRequestUser):
        user_model = request.user
        # 跟前端UserEditData对应
        res = {
            'UserPropResolve': {},
            'PLabelExtraProps': {}
        }
        try:
            res['UserPropResolve'] = UserPropResolveModel(user_model.user_id).frontend_dict()
        except BaseException as e:
            pass

        try:
                res['PLabelExtraProps'] = UserPLabelExtraPropsModel(user_model.user_id).frontend_dict()
        except BaseException as e:
            pass
        return res

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


apis = [UserPropResolveUpdate, UserLabelPropsUpdate, UserEditDataQuery]
