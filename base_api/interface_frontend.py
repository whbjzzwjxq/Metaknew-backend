import random
from dataclasses import dataclass, is_dataclass, MISSING, field, asdict, astuple, fields
from typing import List, Type

from tools.global_const import item_id, item_type, default_translate


@dataclass(init=False)
class DataClass:
    """
    简写的方法
    """

    @property
    def to_dict(self):
        return asdict(self)

    @property
    def to_tuple(self):
        return astuple(self)

    @classmethod
    def fields(cls):
        return fields(cls)


@dataclass(init=False)
class Interface(DataClass):

    def __init__(self, *args, **kwargs):
        for k in self.fields():
            prop = k.name
            # 子级的Interface
            if k.metadata['cls']:
                cls = k.metadata['cls']
                if not k.metadata['is_list']:
                    if is_dataclass(cls):
                        setattr(self, prop, cls(**kwargs[prop]))
                    else:
                        setattr(self, prop, cls(kwargs[prop]))
                else:
                    value = []
                    for data in kwargs[prop]:
                        value.append(cls(**data))
                    setattr(self, prop, value)
            # 不需要实例化interface 而只是简单数据类型 str int 等等
            else:
                if prop in kwargs and kwargs[prop] is not None:
                    setattr(self, prop, kwargs[prop])
                # 如果没有该字段 报错
                elif k.metadata['required']:
                    raise AttributeError('需要的字段' + k.name + '没有传回')
                # 如果不是必须 使用API构造时的默认值
                else:
                    if not k.default == MISSING:
                        v = k.default
                    elif not k.default_factory == MISSING:
                        v = k.default_factory()
                    else:
                        v = None
                    setattr(self, prop, v)
        self.__after_init__()

    def __after_init__(self):
        """
        类似于__post_init__
        :return:
        """
        pass

    @staticmethod
    def meta_field(
            required: bool = True,
            cls: Type[DataClass] = None,
            is_list: bool = False,
            default=MISSING,
            default_factory=MISSING,
            *args,
            **kwargs):
        """

        :param required: 是否必须
        :param cls: 接口类
        :param is_list: 是否是列表
        :param default: 默认值
        :param default_factory: 默认工厂函数
        """
        _meta_data = {'required': required, 'cls': cls, 'is_list': is_list}
        return field(
            default=default,
            default_factory=default_factory,
            metadata=_meta_data,
            *args,
            **kwargs)


@dataclass(init=False)
class InfoFrontend(Interface):
    _id: item_id = Interface.meta_field()
    type: item_type = Interface.meta_field()
    PrimaryLabel: item_type = Interface.meta_field()
    Name: str = Interface.meta_field()
    Description: dict = Interface.meta_field(default_factory=default_translate)
    Labels: List[str] = Interface.meta_field(default_factory=list)
    ExtraProps: dict = Interface.meta_field(default_factory=dict)
    StandardProps: dict = Interface.meta_field(default_factory=dict)
    IsCommon: bool = Interface.meta_field()
    IsFree: bool = Interface.meta_field()
    IsOpenSource: bool = Interface.meta_field()


@dataclass(init=False)
class NodeInfoFrontend(InfoFrontend):
    Alias: List[str] = Interface.meta_field(default_factory=list)
    BaseImp: int = Interface.meta_field()
    BaseHardLevel: int = Interface.meta_field()
    BaseUseful: int = Interface.meta_field()
    Language: str = Interface.meta_field(default='auto')
    Topic: List[str] = Interface.meta_field(default_factory=list)
    IncludedMedia: str = Interface.meta_field()
    MainPic: str = Interface.meta_field()
    Translate: str = Interface.meta_field()


@dataclass(init=False)
class NodeBulkCreateData(Interface):
    Data: List[NodeInfoFrontend] = Interface.meta_field(required=True, cls=NodeInfoFrontend, is_list=True, default=list)
    CreateType: str = Interface.meta_field(default='USER')


@dataclass(init=False)
class LoginByPhoneData(Interface):
    Phone: str = Interface.meta_field()
    Code: str = Interface.meta_field()


@dataclass(init=False)
class LoginUserNameData(Interface):
    Name: str = Interface.meta_field()
    Password: str = Interface.meta_field()
    IsEmail: bool = Interface.meta_field()


@dataclass(init=False)
class RegisterBaseInfo(Interface):
    Phone: str = Interface.meta_field()
    Code: str = Interface.meta_field()
    Name: str = Interface.meta_field(required=False, default='')
    Password: str = Interface.meta_field(required=False, default='')
    Email: str = Interface.meta_field(required=False, default='')

    def __after_init__(self):
        if not self.Name:
            self.Name = 'User' + self.Phone
        if not self.Password:
            self.Password = str(random.randint(12345678, 98765432))


@dataclass(init=False)
class RegisterData(Interface):
    Info: RegisterBaseInfo = Interface.meta_field(cls=RegisterBaseInfo)
    Addition: dict = Interface.meta_field(required=False, default_factory=dict)


@dataclass
class CheckInfoDuplicateData(Interface):
    Phone: str = Interface.meta_field(required=False)
    Email: str = Interface.meta_field(required=False)
    Name: str = Interface.meta_field(required=False)
    """
    有且只有一个值
    """


@dataclass(init=False)
class SendCodeData(Interface):
    Phone: str = Interface.meta_field()