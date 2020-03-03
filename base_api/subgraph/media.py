import json
from typing import List, Tuple

from django.http import HttpResponse

from base_api.interface_frontend import MediaUploadToNodeData, MediaCreateData, MediaQueryData
from base_api.logic_class import HttpRequestUser
from base_api.subgraph.common import ItemApi
from subgraph.class_media import MediaModel
from subgraph.class_node import NodeModel
from tools.base_tools import NeoSet, DateTimeEncoder
from tools.id_generator import id_generator


class MediaApi(ItemApi):
    """
    媒体用的Api
    """
    abstract = True
    URL = 'media/'


class MediaUploadToNode(MediaApi):
    """
    上传媒体到节点
    """
    abstract = False
    URL = 'upload_to_node'
    method = 'POST'
    frontend_data = MediaUploadToNodeData

    def _main_hook(self, result: MediaUploadToNodeData, request: HttpRequestUser) -> Tuple[List[str], NodeModel]:
        collector = NeoSet()
        node_obj = result.TargetNode
        user_id = request.user.user_id
        target_node = NodeModel(_id=node_obj.id, user_id=user_id, _type=node_obj.type, collector=collector)
        result = target_node.media_setter(result.MediaId)
        return result, target_node

    def _save_hook(self, result: Tuple[List[str], NodeModel]) -> List[str]:
        node = result[1]
        node.info.save()
        return result[0]

    def _response_hook(self, result: List[str]) -> HttpResponse:
        if len(result) > 0:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400, content=json.dumps(result))


class MediaCreate(MediaApi):
    """
    上传媒体
    """
    abstract = False
    URL = 'create'
    method = 'POST'
    frontend_data = MediaCreateData
    meta = MediaApi.meta.rewrite()

    def _main_hook(self, result: MediaCreateData, request: HttpRequestUser) -> MediaModel:
        data = result
        user_model = request.user
        collector = NeoSet()
        _id = id_generator(number=1, method='node', jump=2)[0]
        # 获取media label
        _label = MediaModel.get_media_label(data.Info.FileName.split('.')[1])
        media_info = result.Info
        media_info.PrimaryLabel = _label
        media_model = MediaModel(_id=_id, user_id=user_model.user_id, _type='media', collector=collector)
        media_model.create(media_info, data.CreateType)

        # 移动媒体文件
        new_location = 'userResource/' + str(media_model.id) + "." + media_model.ctrl.Format
        media_model.move_remote_file(new_location)
        return media_model

    def _save_hook(self, result: MediaModel) -> MediaModel:
        result.save()
        return result

    def _response_hook(self, result: MediaModel) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps({result.frontend_id: result.id}))


class MediaQuery(MediaApi):
    """
    Media Query
    """
    abstract = False
    URL = 'query'
    method = 'POST'
    frontend_data = MediaQueryData
    meta = MediaApi.meta.rewrite(is_user=False)

    def _main_hook(self, result: MediaQueryData, request: HttpRequestUser):
        user_id = getattr(request.user, 'user_id', 0)
        return [MediaModel(_id=query, user_id=user_id, _type='media').handle_for_frontend()
                for query in result.DataList]

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result, cls=DateTimeEncoder))


apis = [MediaUploadToNode, MediaCreate, MediaQuery]
