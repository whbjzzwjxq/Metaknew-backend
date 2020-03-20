from dataclasses import dataclass
from typing import List, Dict

from base_api.interface_frontend import Interface


@dataclass(init=False)
class UserPropResolveData(Interface):
    Key: str = Interface.meta_field()
    FieldType: str = Interface.meta_field()
    ResolveType: str = Interface.meta_field()


@dataclass(init=False)
class UserPropUpdateData(Interface):
    DataList: List[UserPropResolveData] = Interface.meta_field(cls=UserPropResolveData, is_list=True)


@dataclass(init=False)
class UserPLabelPropsData(Interface):
    Key: str = Interface.meta_field()
    PropNames: List[str] = Interface.meta_field(default_factory=list)


@dataclass(init=False)
class UserPLabelUpdatePropsData(Interface):
    DataList: List[UserPropResolveData] = Interface.meta_field(cls=UserPLabelPropsData, is_list=True)
