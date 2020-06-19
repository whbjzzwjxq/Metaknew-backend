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
class DocumentItemSetting(BaseSetting):
    _isMain: bool = Interface.meta_field()

    @property
    def is_main(self):
        return self._isMain


@dataclass(init=False)
class NodeSetting(DocumentItemSetting):
    _name: str = Interface.meta_field()
    _label: str = Interface.meta_field()
    _image: str = Interface.meta_field(default='', required=False)
    InGraph: dict = Interface.meta_field()
    InPaper: dict = Interface.meta_field()


@dataclass(init=False)
class LinkSetting(DocumentItemSetting):
    _start: QueryObject = Interface.meta_field(cls=QueryObject)
    _end: QueryObject = Interface.meta_field(cls=QueryObject)
    InGraph: dict = Interface.meta_field()
    InPaper: dict = Interface.meta_field()


@dataclass(init=False)
class MediaSetting(DocumentItemSetting):
    _name: str = Interface.meta_field()
    _src: str = Interface.meta_field()
    InGraph: dict = Interface.meta_field()
    InPaper: dict = Interface.meta_field()


@dataclass(init=False)
class TextSetting(DocumentItemSetting):
    _text: str = Interface.meta_field()
    InGraph: dict = Interface.meta_field()
    InPaper: dict = Interface.meta_field()


@dataclass(init=False)
class DocumentContent(Interface):
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
class DocumentSetting(BaseSetting):
    pass


@dataclass(init=False)
class DocumentComponents(Interface):
    InGraph: dict = Interface.meta_field()
    InPaper: dict = Interface.meta_field()


@dataclass(init=False)
class DocumentFrontend(Interface):
    Setting: DocumentSetting = Interface.meta_field(cls=DocumentSetting)
    Components: DocumentComponents = Interface.meta_field(cls=DocumentComponents)
    Content: DocumentContent = Interface.meta_field(cls=DocumentContent)


@dataclass(init=False)
class GraphBulkCreateData(Interface):
    GraphList: List[DocumentFrontend] = Interface.meta_field(cls=DocumentFrontend, is_list=True)
    CreateType: str = Interface.meta_field(default='USER')
