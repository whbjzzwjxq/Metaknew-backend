import json
import random

from django.shortcuts import HttpResponse
from django.db.models import Max
from tools.models import *

batch_size = 256
small_integer = 65535
device_id = 0


def id_generator(number, content, jump=3):
    if number * jump > small_integer:
        raise IndexError('Too Large Number/Fill_Ratio For IdGenerating Once')

    # 确定当前block编号和id
    if isinstance(content, str):
        block = GlobalLabelBlock.objects.filter(PrimaryLabel=content)
        record = LabelBlockId
    elif isinstance(content, int):
        block = GlobalDeviceBlock.objects.filter(DeviceId=content)
        record = DeviceBlockId
    else:
        raise TypeError('%s must be int or str' % content)
    # 如果该Label还从来没有注册
    if len(block) == 0:
        # 新建一个block
        block_id = new_block(content=content)
        # base_number是block的基准值 block_id 是从1开始的
        base_number = (block_id - 1) * (small_integer + 1)
        head = 0
    else:
        block = block.annotate(Max('id'))
        block_id = block[0].id
        base_number = (block_id - 1) * (small_integer + 1)
        last_id = record.objects.filter(BlockId=block_id).last().OutId
        head = last_id - base_number

    needed_space = number * (jump + 1) / 2
    if head + needed_space <= small_integer:
        id_list = ordered_sample(_num=number, jump=jump, base=base_number, _min=head, _max=small_integer)
        commit(id_list, block_id=block_id, record=record)
        return id_list
    else:
        free_num = int((small_integer - head) * 2 / (jump + 1))
        extra_num = number - free_num
        block_id2 = new_block(content=content)
        base_number2 = (block_id2 - 1) * (small_integer + 1)
        id_list1 = ordered_sample(_num=free_num, jump=jump, base=base_number, _min=head, _max=small_integer)
        id_list2 = ordered_sample(_num=extra_num, jump=jump, base=base_number2, _min=0, _max=small_integer)
        commit(id_list1, block_id=block_id, record=record)
        commit(id_list2, block_id=block_id2, record=record)
        id_list1.extend(id_list2)
        return id_list1


def new_block(content):
    if isinstance(content, str):
        block = GlobalLabelBlock.objects.create(PrimaryLabel=content)
    elif isinstance(content, int):
        block = GlobalDeviceBlock.objects.create(DeviceId=content)
    else:
        raise TypeError('%s must be int or str' % content)
    block.save()
    return block.id


def ordered_sample(_num, jump, base, _min, _max: 65535):
    link = _min
    _list = []
    for i in range(0, _num):
        if link + (_num - i) < _max:
            delta = random.randint(1, jump)
        else:
            delta = 1
        link += delta
        _list.append(link + base)
    return _list


def commit(id_list, block_id, record):
    write_list = [record(BlockId=block_id, OutId=_id) for _id in id_list]
    record.objects.bulk_create(write_list, batch_size=batch_size)


# 测试用 设备/节点都测试完毕
def new_id_list(request):
    num = request.GET.get('num')
    jump = request.GET.get('jump')
    result = id_generator(number=int(num), content=0, jump=int(jump))
    return HttpResponse(json.dumps(result))
