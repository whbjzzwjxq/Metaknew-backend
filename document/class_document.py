from time import time
from typing import Optional, Union, Type

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg

from document.models import DocGraph, Comment
from subgraph.class_node import BaseNodeModel, NodeModel
from tools import base_tools
from tools.id_generator import id_generator
from users.models import UserConcern
from tools.global_const import item_id, source_type
from typing import List
from subgraph.class_link import SystemMadeLinkModel


class Graph:

    def __init__(self, nodes, links, medias, svgs):
        self.nodes: List[NodeSetting] = nodes
        self.links: List[LinkSetting] = links
        self.medias: List[MediaSetting] = medias
        self.svgs: List[SvgSetting] = svgs

    @staticmethod
    def dict_to_graph(graph: dict):
        nodes = [NodeSetting(**node, setting=node) for node in graph['nodes']]
        links = [LinkSetting(**link, setting=link) for link in graph['links']]
        medias = [MediaSetting(**media, setting=media) for media in graph['medias']]
        svgs = [SvgSetting(**svg, setting=svg) for svg in graph['svgs']]
        return Graph(nodes, links, medias, svgs)

    @staticmethod
    def empty_graph():
        return Graph([], [], [], [])

    def visual_node_setting(self):
        result = []
        result.extend(self.nodes)
        result.extend(self.medias)
        return result


class BaseSetting:

    def __init__(self, _id: item_id, _type: source_type, _label: str, setting: dict):
        self._id = _id
        self._type = _type
        self._label = _label
        self.setting = setting

    def get_query_object(self):
        result = self.setting
        result.update({
            '_id': self._id,
            '_type': self._type,
            '_label': self._label
        })
        return result

    def setting_checker(self):
        pass

    @property
    def id(self):
        return self._id


class NodeSetting(BaseSetting):

    def __init__(self, _id: item_id, _type: source_type, _label: str, _name: str, _image: str, setting: dict):
        super().__init__(_id, _type, _label, setting)
        self._name = _name
        self._image = _image


class MediaSetting(BaseSetting):

    def __init__(self, _id: item_id, _label: str, _name: str, _src: str, setting: dict):
        super().__init__(_id, 'media', _label, setting)
        self._name = _name
        self._src = _src


VisualNode = Union[Type[NodeSetting], Type[MediaSetting]]


class LinkSetting(BaseSetting):

    def __init__(self, _id: item_id, _label: str, _start: VisualNode, _end: VisualNode, setting: dict):
        super().__init__(_id, 'link', _label, setting)
        self._start = _start
        self._end = _end


class SvgSetting(BaseSetting):

    def __init__(self, _id: item_id, _label: str, _points: [], _text: str, setting: dict):
        super().__init__(_id, 'svg', _label, setting)
        self._points = _points
        self._text = _text


# todo node link 改写为类 level: 2 NeoNode还没同步
class DocGraphModel:

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.user_id = int(user_id)
        self.id = int(_id)
        self.collector = collector
        self.is_create = False  # 是否创建状态
        self._base_node: Optional[BaseNodeModel] = None  # DocumentNode模型
        self._graph: Optional[DocGraph] = None  # DocumentGraph模型
        self.container = Graph.empty_graph()  # 将要更新Graph的内容

    @property
    def base_node(self):
        if not self._base_node:
            self._base_node = NodeModel(_id=self.id, user_id=self.user_id, _type='document', collector=self.collector)
        return self._base_node

    @property
    def graph(self):
        if not self._graph:
            try:
                self._graph = DocGraph.objects.get(DocId=self.id)
                return self._graph
            except ObjectDoesNotExist:
                return None
        else:
            return self._graph

    def branch(self):
        pass

    def graph_item_init(self, data):
        self.container = Graph.dict_to_graph(data)

    def base_create(self, frontend_data):
        self.is_create = True
        self._graph = DocGraph(DocId=self.id, Nodes=[], Links=[], Medias=[], Svgs=[], Conf={})
        self.graph_item_init(frontend_data['Graph'])
        self.graph_update(frontend_data)
        return self

    def graph_update(self, data):
        pass

    def update_node_to_doc_relationship(self):
        """
        生成专题和节点的关系
        :return:
        """
        # Doc2graph关系生成
        # 添加的节点
        add_node_list = []
        # 移除的节点
        remove_node_list = []
        # 待更新列表的id_list
        current_node_id_list = [node.id for node in self.container.visual_node_setting()]
        # 数据库列表的id_list
        remote_node_id_list = [node['_id'] for node in self.graph.Nodes + self.graph.Medias]
        # 需要生成的link
        create_link = []
        # 需要更新的link
        update_link = []

        # 如果节点不在现有列表中
        for node in self.container.visual_node_setting():
            if int(node.id) not in remote_node_id_list:
                neo_node = self.collector.match_node(node.get_query_object())
                add_node_list.append([neo_node, node.get_query_object()])
        # 如果现有节点不在列表中
        for node in self.graph.Nodes:
            if int(node["_id"]) not in current_node_id_list:
                neo_node = self.collector.match_node(node)
                remove_node_list.append([neo_node, node])

        # 已经存在(有记录)的link
        for node in add_node_list:
            # 这是RelationshipCtrl
            exist_link = SystemMadeLinkModel.query_by_node('DocToNode', start=self.base_node.query_object, end=node[1])
            if exist_link:
                link = SystemMadeLinkModel(_id=exist_link.ItemId, user_id=self.user_id, _type='link', _label='DocToNode'
                                           , collector=self.collector)
                link._ctrl = exist_link
                link.graph_link_update({
                    'IsMain': node[1]['View']['isMain'],
                    'IsUsed': True,
                    'Correlation': 50,
                    'DocumentImp': 50
                })
                update_link.append(link)
            else:
                create_link.append([self.base_node.graph_node, node[0]])

        for node in remove_node_list:
            remove_link = SystemMadeLinkModel.query_by_node('DocToNode', start=self.base_node.query_object, end=node[1])
            if remove_link:
                if not remove_link.IsUsed:
                    pass  # 不需要做事情
                else:
                    link = SystemMadeLinkModel(_id=remove_link.ItemId, user_id=self.user_id, _type='link',
                                               _label='DocToNode'
                                               , collector=self.collector)
                    link._ctrl = remove_link
                    link.delete()
                    update_link.append(link)
            else:
                pass  # 不需要做事情

        link_id_list = id_generator(len(create_link), method='link')
        data = {
            'Start': create_link[0],
            'End': create_link[1],
            'CreateType': 'SystemAuto'
        }
        model_list = [SystemMadeLinkModel(_id=_id, user_id=self.user_id, _label='DocToNode',
                                          collector=self.collector).base_create(data)
                      for _id, link in zip(link_id_list, create_link)]
        SystemMadeLinkModel.bulk_save_update(update_link, collector=self.collector)
        SystemMadeLinkModel.bulk_save_create(model_list, collector=self.collector)

    def ctrl_update(self):
        """
        更新Info部分
        :return:
        """
        ctrl = self.base_node.ctrl
        ctrl.Size = len(self.graph.Nodes) + len(self.graph.Medias)
        ctrl.Complete = 50
        ctrl.MainNodes = [node["_id"] for node in self.graph().Nodes
                          if node["View"]["isMain"] and node["_id"] != self.id]

    def get_item_list(self, _type):
        if _type == 'link':
            return self.graph().Links
        elif _type == 'node':
            return self.graph().Nodes
        elif _type == 'media':
            return self.graph().Medias
        else:
            return self.graph().Svgs

    def bound_node(self, node_setting: NodeSetting):
        """

        :param node_setting: nodeSetting 包含_id, _type, _label
        :return: NeoNode
        """
        node = self.collector.match_node(node_setting.get_query_object())

    @staticmethod
    def check_reference(doc_id):
        pass
        return True

    # 是否在graph里存在item
    def check_exist_in_setting(self, _id, _type):
        item_list = self.get_item_list(_type)
        item_id_list = [item['_id'] for item in item_list]
        int_id = int(_id)
        try:
            return item_id_list.index(int_id)
        except ValueError:
            return -1

    def save(self):
        pass

    def re_count(self):
        result = UserConcern.objects.filter(SourceId=self.id)
        self.base_node.ctrl.Useful = result.filter(Useful__gte=0).aggregate(Avg("Useful"))
        self.base_node.ctrl.HardLevel = result.filter(HardLevel__gte=0).aggregate(Avg("HardLevel"))
        self.base_node.ctrl.Imp = result.filter(Imp__gte=0).aggregate(Avg("Imp"))
        self.base_node.ctrl.CountCacheTime = time()
        # todo hot_count level : 1

    def node_index(self):
        pass

    def save_cache(self):
        pass

    def clear_cache(self):
        pass

    def handle_for_frontend_as_graph(self):
        """
        传回node和graph
        :return:
        """
        result = {
            "Base": self.base_node.handle_for_frontend(),
            "Graph": {
                "nodes": self.graph().Nodes,
                "links": self.graph().Links,
                "medias": self.graph().Medias,
                "svgs": self.graph().Svgs
            },
            "Conf": self.graph().Conf,
        }
        return result

    def handle_for_frontend(self):
        """
        只传回node
        :return:
        """
        return self.base_node.handle_for_frontend()

    @classmethod
    def bulk_save_create(cls, graph_model_list):
        return []


class BaseComment:

    def __init__(self):
        self.comment = None

    @staticmethod
    def query_doc(doc_id):
        comment = Comment.objects.filter(Source=doc_id, Is_Delete=False)
        return comment

    @staticmethod
    def query_user(user):
        comment = Comment.objects.filter(Owner=user, Is_Delete=False)
        return comment

    @staticmethod
    def query_reply_to_user(user):
        comment = Comment.objects.filter(TargetUser=user, Is_Delete=False)
        return comment

    def add_single(self, _id, target_id, reply_id, reply_user, content, user):
        content = str(content)

        self.comment = Comment(CommentId=_id,
                               SourceId=target_id,
                               TargetId=reply_id,
                               TargetUser=reply_user,
                               Content=content,
                               Owner=user,
                               Is_Delete=False)
        self.comment.save()
        return self

    def delete(self):
        self.comment.Is_Delete = True
        self.comment.save()
        return True


class BaseNote:
    pass
