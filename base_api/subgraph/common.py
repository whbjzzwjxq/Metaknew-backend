from base_api.logic_class import UserApi


class ItemApi(UserApi):
    abstract = True
    URL = 'item/'


class ItemDraftApi(UserApi):
    pass


