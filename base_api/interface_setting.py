from dataclasses import dataclass
from typing import List, Union

from base_api.interface_frontend import Interface, QueryObject


@dataclass(init=False)
class BaseSetting(Interface):
    _id: str = Interface.meta_field()
    _type: str = Interface.meta_field()
    _label: str = Interface.meta_field()

    @property
    def query_object(self) -> QueryObject:
        return QueryObject(**{'id': self._id, 'type': self._type, 'pLabel': self._label})

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @property
    def label(self):
        return self._label


@dataclass(init=False)
class NodeSetting(BaseSetting):
    _name: str = Interface.meta_field()
    _label: str = Interface.meta_field()
    Base: dict = Interface.meta_field()
    Border: dict = Interface.meta_field()
    Show: dict = Interface.meta_field()
    Text: dict = Interface.meta_field()
    View: dict = Interface.meta_field()


@dataclass(init=False)
class LinkSetting(BaseSetting):
    _start: QueryObject = Interface.meta_field(cls=QueryObject)
    _end: QueryObject = Interface.meta_field(cls=QueryObject)
    Arrow: dict = Interface.meta_field()
    Text: dict = Interface.meta_field()
    View: dict = Interface.meta_field()


@dataclass(init=False)
class MediaSetting(BaseSetting):
    _name: str = Interface.meta_field()
    _src: str = Interface.meta_field()
    Base: dict = Interface.meta_field()
    Border: dict = Interface.meta_field()
    Show: dict = Interface.meta_field()
    Text: dict = Interface.meta_field()
    View: dict = Interface.meta_field()


@dataclass(init=False)
class TextSetting(BaseSetting):
    _points: list = Interface.meta_field()
    _text: str = Interface.meta_field()
    Base: dict = Interface.meta_field()
    Border: dict = Interface.meta_field()
    Transition: dict = Interface.meta_field()
    Background: dict = Interface.meta_field()
    Show: dict = Interface.meta_field()


@dataclass(init=False)
class GraphConf(BaseSetting):
    Base: dict = Interface.meta_field()


@dataclass(init=False)
class GraphContent(Interface):
    nodes: List[NodeSetting] = Interface.meta_field(cls=NodeSetting, is_list=True)
    links: List[LinkSetting] = Interface.meta_field(cls=LinkSetting, is_list=True)
    medias: List[MediaSetting] = Interface.meta_field(cls=MediaSetting, is_list=True)
    texts: List[TextSetting] = Interface.meta_field(cls=TextSetting, is_list=True)

    @property
    def vis_node(self) -> List[Union[NodeSetting, MediaSetting]]:
        result: List[Union[NodeSetting, MediaSetting]] = []
        result.extend(self.nodes)
        result.extend(self.medias)
        return result


@dataclass(init=False)
class GraphInfoFrontend(Interface):
    Conf: GraphConf = Interface.meta_field(cls=GraphConf)
    Content: GraphContent = Interface.meta_field(cls=GraphContent)


@dataclass(init=False)
class GraphBulkCreateData(Interface):
    GraphList: List[GraphInfoFrontend] = Interface.meta_field(cls=GraphInfoFrontend, is_list=True)
    CreateType: str = Interface.meta_field(default='USER')
