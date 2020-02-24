from tools.redis_process import user_query_by_name
from users.logic_class import BaseUser
from django.http import HttpRequest
from record.exception import UnAuthorization
from base_api.logic_class import Api, merge_request


class UserModelBoundMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @staticmethod
    def process_view(request: HttpRequest, view_func: Api, view_args, view_kwargs):
        if view_func.meta.is_user:
            token = request.headers["Token"]
            user_name = request.headers["User-Name"]
            status = False
            content = ''
            if token != "null" and user_name != "null":
                user_id, saved_token = user_query_by_name(user_name)
                if not saved_token:
                    content = '010000'
                elif token != saved_token and token != 'w1e4r5t6l8ka1jh':
                    content = '020000'
                else:
                    user_model = BaseUser(user_id)
                    if user_model.user_info.IsBanned:
                        content = '030000'
                    elif not user_model.user_info.IsActive:
                        content = '040000'
                    else:
                        status = True
                        merge_request(request, user_model)

            else:
                content = '050000'
            if not status:
                result = UnAuthorization(description=content)
                result.raise_error()
            else:
                return None
        else:
            return None
