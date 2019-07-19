import json
import random

from django.db.models.query import EmptyQuerySet
from django.shortcuts import HttpResponse

from tools.models import *

small_integer = 65535
device_id = 0


def node_id_generator(number, label, jump_max=4):
    id_list = []

    if number > small_integer:
        raise IndexError('Too Large Number For IdGenerating Once')

    # 确定当前block编号和id
    block = GlobalLabelBlock.objects.filter(PrimaryLabel=label)

    # 如果该Label还没有注册
    if isinstance(block, EmptyQuerySet):
        # 新建一个block
        block = GlobalLabelBlock.objects.create(PrimaryLabel=label).save()
        block_id = block.id()
        # base_number是block的基准值
        base_number = block_id * (small_integer + 1)
        LabelBlockId.objects.create(BlockId=block_id, OutId=base_number)
        last_id = base_number
    else:
        block = block.annotate(max('id'))
        block_id = block.id()
        base_number = block_id * (small_integer + 1)
        last_id = LabelBlockId.objects.filter(BlockId=block_id).annotate(max('OutId')).pk()
    # 目前的已经从base_number移动了多少
    head = last_id - base_number

    while len(id_list) < number:
        jump = random.randint(1, jump_max)

        if head + jump < small_integer:
            head += jump
        else:
            head = small_integer
            block = GlobalLabelBlock.objects.create(PrimaryLabel=label).save()
            block_id = block.id()
        output = base_number + head
        LabelBlockId.objects.create(BlockId=block_id, OutId=output)
        id_list.append(output)
    return id_list


def new_id_list(request):

    num = request.GET.get('num')
    jump = request.GET.get('jump')
    result = node_id_generator(number=int(num), label='Person', jump_max=int(jump))
    return HttpResponse(json.dumps(result))

