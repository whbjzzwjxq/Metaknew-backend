from typing import List

from django.http import HttpRequest

from base_api.interface_frontend import FragmentInfoFrontend
from base_api.subgraph.common import ItemApi
from subgraph.class_base import FragmentModel


class FragmentApi(ItemApi):
    """
    碎片相关内容
    """
    abstract = True
    URL = 'fragment/'


class FragmentBulkCreate(FragmentApi):
    """
    生成碎片
    """
    abstract = False
    URL = 'bulk_create'
    frontend_data = FragmentInfoFrontend

    def _main_hook(self, result: List[FragmentInfoFrontend], request: HttpRequest):
        FragmentModel


class FragmentBulkUpdate(FragmentApi):
    """
    碎片更新
    """
    abstract = False
    URL = 'bulk_update'


class FragmentDelete(FragmentApi):
    """
    碎片删除
    """
    abstract = False
    URL = 'delete'
