import json
import random
import datetime

from django.shortcuts import HttpResponse
from tools.models import *
from tools.redis_process import query_word_index

batch_size = 256
small_integer = 65535
device_id = 0
base_time = datetime.date(year=2019, month=7, day=23)
methods = {
    'node': {
        'manager': NodeBlockManager,
        'record': NodeBlockIdRecord
    },
    'device': {
        'manager': DeviceBlockManager,
        'record': DeviceBlockIdRecord
    },
    'time': {
        'manager': RecordBlockManager,
        'record': RecordBlockIdRecord
    },
    'word': {
        'manager': DeviceBlockManager,
        'record': DeviceBlockIdRecord
    },
}


# todo 把这个服务配置成主-从模式 level: 2
def id_generator(number, method, content, jump=3):
    if number <= 0:
        return []
    else:
        if number * jump > small_integer:
            raise IndexError('Too Large Number/Fill_Ratio For IdGenerating Once')
        try:
            manager = methods[method]['manager']
            record = methods[method]['record']
            if method == 'node':
                content = query_word_index([content])
                if not content:
                    raise TypeError('method node need label as content')
                else:
                    content = content[0]
            if method == 'time':
                try:
                    content -= base_time
                    content = content.days
                except TypeError('method time need date as content'):
                    return None
        except AttributeError('%s must be node or device or time or word' % method):
            return None

        block = record.objects.last()  # 注意这里是本机的record 也就是只有new_block依赖于主数据库
        # 如果该content还从来没有注册
        if len(block) == 0 or not block:
            # 新建一个block
            block_id = new_block(manager=manager, content=content)
            # base_number是block的基准值 block_id 是从1开始的
            base_number = (block_id - 1) * (small_integer + 1)
            head = 0
        else:
            block = block.BlockId
            block_id = block.OutId
            base_number = (block_id - 1) * (small_integer + 1)
            last_id = record.objects.filter(BlockId=block_id).last().OutId
            head = last_id - base_number

        needed_space = number * (jump + 1) / 2
        if head + needed_space <= small_integer:
            id_list = ordered_sample(_num=number, jump=jump, base=base_number, _min=head)
            commit(id_list, block_id=block_id, record=record)
            return id_list
        else:
            free_num = int((small_integer - head) * 2 / (jump + 1))
            extra_num = number - free_num
            block_id2 = new_block(manager=manager, content=content)
            base_number2 = (block_id2 - 1) * (small_integer + 1)
            id_list1 = ordered_sample(_num=free_num, jump=jump, base=base_number, _min=head)
            id_list2 = ordered_sample(_num=extra_num, jump=jump, base=base_number2, _min=0)
            commit(id_list1, block_id=block_id, record=record)
            commit(id_list2, block_id=block_id2, record=record)
            id_list1.extend(id_list2)
            return id_list1


def new_block(manager, content):
    block = manager.objects.create(Classifier=content)
    block.save()
    return block.id


def ordered_sample(_num, jump, base, _min):
    _max = small_integer
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
    result = id_generator(number=int(num), method='node', content='Person', jump=int(jump))
    return HttpResponse(json.dumps(result))
