import json
import random
import datetime
import typing
from django.shortcuts import HttpResponse
from tools.models import *

batch_size = 256
small_integer = 65535
device_id = 0
base_time = datetime.date(year=2020, month=1, day=1)

methods = {
    # node取号
    "node": {
        "manager": NodeBlockManager,
        "record": NodeBlockIdRecord
    },
    # link取号
    "link": {
        "manager": LinkBlockManager,
        "record": LinkBlockIdRecord
    },
    # 按照设备取号
    "device": {
        "manager": DeviceBlockManager,
        "record": DeviceBlockIdRecord
    },
    # 按照时间取号
    "time": {
        "manager": TimeBlockManager,
        "record": TimeBlockIdRecord
    }
}


# todo 把这个服务配置成主-从模式 level: 2
def id_generator(number, method, jump=3) -> typing.List[int]:
    assert method in ['node', 'link', 'device', 'time']
    if number <= 0:
        return []
    else:
        if number * jump > small_integer:
            raise IndexError("Too Large Number/Fill_Ratio For IdGenerating Once")
        try:
            manager = methods[method]["manager"]
            record = methods[method]["record"]
        except AttributeError("%s must be node or device or time" % method):
            return []

        block = manager.objects.filter(RegisterDevice=device_id)
        # 如果还没有block注册
        if len(block) == 0:
            # 新建一个block 获得block的id
            block_id = new_block(manager=manager).BlockId
            # base_number是该block下id的基准值 例如block2的基准值是1 * 65536
            base_number = (block_id - 1) * (small_integer + 1)
            # 取号范围的第一个值
            head = 0
        else:
            block_id = block.last().BlockId
            row = record.objects.filter(BlockId=block_id).last()
            base_number = (block_id - 1) * (small_integer + 1)
            head = row.OutId - base_number

        needed_space = int(number * (jump + 1) / 2)
        if head + needed_space <= small_integer:
            # 如果当前最小值+所需空间小于65535 就直接生成
            id_list = ordered_sample(_num=number, jump=jump, base=base_number, _min=head)
            commit(id_list, block_id=block_id, record=record)
            return id_list
        else:
            # 否则先算当前可以满足的num 然后用新的block去弄额外的数字
            free_num = int((small_integer - head) * 2 / (jump + 1))
            id_list1 = ordered_sample(_num=free_num, jump=jump, base=base_number, _min=head)
            commit(id_list1, block_id=block_id, record=record)

            # 额外数字
            extra_num = number - free_num
            block_id2 = new_block(manager=manager)
            base_number2 = (block_id2 - 1) * (small_integer + 1)
            id_list2 = ordered_sample(_num=extra_num, jump=jump, base=base_number2, _min=0)
            commit(id_list2, block_id=block_id2, record=record)
            id_list1.extend(id_list2)
            return id_list1


def new_block(manager):
    block = manager.objects.create(RegisterDevice=device_id)
    block.save()
    return block


def ordered_sample(_num, jump, base, _min):
    """
    取号
    :param _num: 需要号的数量
    :param jump: 间隔值
    :param base: 基准值 例如block2的基准值是65536
    :param _min: 最小位置 指针 例如一开始指针是0
    :return:
    """
    _max = small_integer
    link = _min  # 当前id
    _list = []
    for i in range(0, _num):
        if link + (_num - i) < _max:
            # 如果还需要id的数量小于_max 那么还可以jump
            delta = random.randint(1, jump)
        else:
            # 否则jump失效 1个1个取号
            delta = 1
        link += delta
        _list.append(link + base)
    return _list


def commit(id_list, block_id, record):
    write_list = [record(BlockId=block_id, OutId=_id) for _id in id_list]
    record.objects.bulk_create(write_list, batch_size=batch_size)


# 测试用 设备/节点都测试完毕
def new_id_list(request):
    num = request.GET.get("num")
    jump = request.GET.get("jump")
    result = id_generator(number=int(num), method="node", jump=int(jump))
    return HttpResponse(json.dumps(result))
