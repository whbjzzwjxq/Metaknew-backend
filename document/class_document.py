from time import time
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.db.models import Avg
from py2neo.database import TransactionError

from base_api.interface_setting import GraphInfoFrontend
from document.models import DocGraph, Comment
from subgraph.class_link import SysLinkModel
from subgraph.class_node import BaseNodeModel, NodeModel
from tools import base_tools
from tools.id_generator import id_generator
from users.models import UserConcern
from tools.global_const import re_for_frontend_id


# todo node link 改写为类 level: 2 NeoNode还没同步
class DocGraphModel:

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.user_id = int(user_id)
        self.id = int(_id)
        assert not re_for_frontend_id.match(str(_id))
        self.collector = collector
        self.is_create = False  # 是否创建状态
        self._base_node: Optional[BaseNodeModel] = None  # DocumentNode模型
        self._graph: Optional[DocGraph] = None  # DocumentGraph模型

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
                self._graph_item_init()
                return self._graph
        else:
            return self._graph

    def branch(self):
        pass

    def _graph_item_init(self):
        self._graph = DocGraph(DocId=self.id, Nodes=[], Links=[], Medias=[], Texts=[], Conf={})

    def create(self, frontend_data: GraphInfoFrontend):
        self.is_create = True
        self.update(frontend_data)
        return self

    def update(self, data: GraphInfoFrontend):
        self.update_node_to_doc_relationship(data)
        self.update_content(data)
        self.ctrl_update()
        return self

    def update_node_to_doc_relationship(self, data: GraphInfoFrontend):
        """
        生成专题和节点的关系
        :return:
        """
        # Doc2graph关系生成
        content = data.Content
        # 待更新列表的id_list
        current_node_id_list = [item.id for item in content.vis_node]
        # 数据库列表的id_list
        remote_node_id_list = [node['_id'] for node in self.graph.Nodes + self.graph.Medias]
        # 需要生成的link
        create_link = []
        # 需要更新的link
        update_link = []

        # 如果节点不在现有列表中
        add_node_list = [node for node in content.vis_node if int(node.id) not in remote_node_id_list]
        # 如果现有节点不在列表中
        remove_node_list = [node for node in self.graph.Nodes if int(node["_id"]) not in current_node_id_list]

        # 已经存在(有记录)的link
        for node in add_node_list:
            # 这是RelationshipCtrl
            exist_link = SysLinkModel.query_by_node('DocToNode', start=self.base_node.id, end=node.id)
            if exist_link:
                link = SysLinkModel(_id=exist_link.ItemId, user_id=self.user_id, _label='DocToNode',
                                    collector=self.collector)
                link._ctrl = exist_link
                link.update({
                    'IsMain': node.View['isMain'],
                    'IsUsed': True,
                    'Correlation': 50,
                    'DocumentImp': 50
                })
                update_link.append(link)
            else:
                create_link.append(
                    [self.base_node.graph_node, self.collector.match_node(node.id).first(), node.View['isMain']])

        for node in remove_node_list:
            remove_link = SysLinkModel.query_by_node('DocToNode', start=self.base_node.id, end=node.id)
            if remove_link:
                if not remove_link.IsUsed:
                    pass  # 不需要做事情
                else:
                    link = SysLinkModel(_id=remove_link.ItemId, user_id=self.user_id, _label='DocToNode',
                                        collector=self.collector)
                    link._ctrl = remove_link
                    link.delete()
                    update_link.append(link)
            else:
                pass  # 不需要做事情

        link_id_list = id_generator(len(create_link), method='link')
        model_list = [SysLinkModel(_id=_id, user_id=self.user_id, _label='DocToNode', collector=self.collector).create({
            'Start': link[0],
            'End': link[1],
            'CreateType': 'SystemAuto',
            'IsMain': link[2],
            'IsUsed': True,
            'Correlation': 50,
            'DocumentImp': 50
        })
            for _id, link in zip(link_id_list, create_link)]
        try:
            if len(update_link) > 0:
                SysLinkModel.bulk_save_update(update_link, collector=self.collector)
            if len(model_list) > 0:
                SysLinkModel.bulk_save_create(model_list, collector=self.collector)
            self.graph.LinkFailed = True
        except TransactionError or DatabaseError or BaseException as e:
            self.graph.LinkFailed = False

    def update_content(self, data: GraphInfoFrontend):
        self.graph.Nodes = [node.to_dict for node in data.Content.nodes]
        self.graph.Links = [link.to_dict for link in data.Content.links]
        self.graph.Medias = [media.to_dict for media in data.Content.medias]
        self.graph.Texts = [text.to_dict for text in data.Content.texts]

    def ctrl_update(self):
        """
        更新ctrl部分
        :return:
        """
        self.graph.Size = len(self.graph.Nodes) + len(self.graph.Medias)
        self.graph.Complete = 50
        self.graph.MainNodes = [node["_id"] for node in self.graph.Nodes
                                if node["View"]["isMain"] and node["_id"] != self.id]

    def get_item_list(self, _type):
        if _type == 'link':
            return self.graph.Links
        elif _type == 'node':
            return self.graph.Nodes
        elif _type == 'media':
            return self.graph.Medias
        else:
            return self.graph.Texts

    @staticmethod
    def check_reference():
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
                "nodes": self.graph.Nodes,
                "links": self.graph.Links,
                "medias": self.graph.Medias,
                "texts": self.graph.Texts
            },
            "Conf": self.graph.Conf,
        }
        return result

    def handle_for_frontend(self):
        """
        只传回node
        :return:
        """
        return self.base_node.handle_for_frontend()

    @classmethod
    def bulk_save_create(cls, graph_list):
        if len(graph_list) > 0:
            DocGraph.objects.bulk_create([model.graph for model in graph_list])
            return [graph.id for graph in graph_list]
        else:
            return []

    @classmethod
    def bulk_save_update(cls, graph_list):
        if len(graph_list) > 0:
            DocGraph.objects.bulk_update([model.graph for model in graph_list])
            return [graph.id for graph in graph_list]
        else:
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
