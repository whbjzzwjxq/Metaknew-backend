import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.urls import path

from record.models import ItemDraft
from subgraph.class_media import MediaModel
from subgraph.class_node import NodeModel
from tools.base_tools import NeoSet, DateTimeEncoder
from tools.global_const import re_for_frontend_id
from tools.id_generator import id_generator
from users.logic_class import BaseUser


class StandardResponse(JsonResponse):

    def __init__(self, is_dev=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.content:
            self.content = {'IsDev': is_dev}
        else:
            self.content.ctrl_update_hook({'IsDev': is_dev})


class UserApi:

    @staticmethod
    def _meta_resolve(request):

        data = json.loads(request.body)
        user_id = request.GET.get("user_id")
        user_model = BaseUser(_id=user_id)
        if user_model:
            return data, user_model
        else:
            return StandardResponse(is_dev=False, status=401, content='需要登录以继续')

    def item_draft_save(self, request):
        """
        保存item的草稿
        data_example: {
            "InfoDict": {
                "node": [],
                "link": [],
                ...
            },
            'IsAuto': bool
        }
        :param request:
        :return:
        """
        frontend_data, user_model = self._meta_resolve(request)
        info_dict = frontend_data['InfoDict']
        create_list = []
        update_list = []
        for key in info_dict:
            content_list = info_dict[key]
            remote_set = ItemDraft.objects.filter(SourceType=key, CreateUser=user_model.user_id)
            for info in content_list:
                if re_for_frontend_id.match(info['_id']):
                    _id = int(info['_id'][2:])
                else:
                    _id = int(info['_id'])
                try:
                    remote_draft = remote_set.get(SourceId=_id)
                    update_list.append(remote_draft)
                except ObjectDoesNotExist:
                    remote_draft = ItemDraft(
                        SourceId=_id,
                        SourceType=info['type'],
                        CreateUser=user_model.user_id,
                    )
                    create_list.append(remote_draft)
                remote_draft.SourceLabel = info['PrimaryLabel']
                remote_draft.Name = info['Name']
                remote_draft.IsAuto = frontend_data['IsAuto']
                remote_draft.IsUsed = True
        ItemDraft.objects.bulk_create(create_list)
        ItemDraft.objects.bulk_update(update_list)
        return HttpResponse(status=200)


class NodeApi(UserApi):

    def bulk_create(self, request):
        """
        创建Node
        data: List
        :return: HttpResponse
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)

        id_list = id_generator(number=len(frontend_data), method='node', jump=3)
        node_model_list = [
            NodeModel(_id=_id,
                      user_id=user_model.user_id,
                      _type='node',
                      collector=collector
                      ).create(frontend_node_info)
            for frontend_node_info, _id in zip(frontend_data, id_list)]
        result = NodeModel.bulk_save_create(node_model_list, collector)
        if result is not None:
            return HttpResponse(status=200, content=json.dumps(result))
        else:
            return HttpResponse(status=400, content=json.dumps(result))

    def bulk_update(self, request):
        """
        修改多个Node
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        node_model_list = [
            NodeModel(
                _id=node_info[node_info['_id']],
                _type=node_info[node_info['type']],
                user_id=user_model.user_id,
                collector=collector
            ).info_update_hook(node_info) for node_info in frontend_data
        ]
        result = NodeModel.bulk_save_update(node_model_list, collector)
        if result is not None:
            return HttpResponse(status=200, content=json.dumps(result))
        else:
            return HttpResponse(status=400, content=json.dumps(result))

    def update_media_to_node(self, request):
        """
        Media已经是服务端存在的Media
        data_example = {
            'MediaId': [''], // 注意是所有的Media
            'TargetNode': {
                '_id': '',
                '_type': '',
                '_label': ''
            }
        }
        :param request:
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        target_node = NodeModel(**frontend_data['TargetNode'], user_id=user_model.user_id, collector=collector)
        result, content = target_node.media_setter(frontend_data['MediaId'])
        if result:
            return HttpResponse(status=200, content='上传媒体文件成功')
        else:
            return HttpResponse(status=400, content=content)

    def bulk_query(self, request):
        """
        data_example = {
            'NodeId': []
        }
        :param request:
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        result = [NodeModel(_id=node_id, user_id=user_model.user_id, collector=collector).handle_for_frontend()
                  for node_id in frontend_data['NodeId']]
        return HttpResponse(status=200, content=json.dumps(result, cls=DateTimeEncoder))


class MediaApi:

    def create(self, request):
        """
        data_example = {
            'FileName': 'userFileCache/5fdf0145-e538-668a-6f9d-38f83b27904b.jpg',
            'Info': {
                '_id': '$_1',
                'type': 'media',
                'PrimaryLabel': 'image',
                'Name': '1.jpg',
                'Description': {},
                'Labels': [],
                '$IsCommon': True,
                '$IsFree': True,
                '$IsOpenSource': False,
                'ExtraProps': {}
            }
        }
        :return:
        """
        frontend_data, user_model = self.resolve.meta_resolve(request)
        if user_model:
            collector = NeoSet()
            _id = id_generator(number=1, method='node', jump=2)[0]
            # 获取media label
            _label = MediaModel.get_media_label(frontend_data['FileName'].split('.')[1])
            media_info = frontend_data['Info']
            media_info["PrimaryLabel"] = _label
            media_model = MediaModel(_id=_id, user_id=user_model.user_id, _type='media', collector=collector)
            media_model.create(media_info)

            # 移动媒体文件
            new_location = 'userResource/' + str(media_model.id) + "." + media_model.ctrl().Format
            media_model.move_remote_file(new_location)
            media_model.save()
            return HttpResponse(content={media_model.frontend_id: media_model.id}, status=200)
        else:
            return HttpResponse(status=401, content=self.resolve.response_content)

    def bulk_query(self, request):
        """
        data_example = {
            'MediaId': []
        }
        :param request:
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        result = [MediaModel(_id=_id, user_id=user_model.user_id, collector=collector).handle_for_frontend()
                  for _id in frontend_data['MediaId']]
        return HttpResponse(status=200, content=json.dumps(result, cls=DateTimeEncoder))


class LinkApi(UserApi):
    pass


url_patterns = [
    path('media/create', MediaApi().create)
]
