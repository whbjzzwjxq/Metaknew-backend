import json

# todo 测试


def criteria_query(request):
    if request.method == 'GET':
        criteria = json.loads(request.body, encoding='utf-8')['criteria']
        limit = int(request.GET.get('limit', 100))
        props = {}
        for prop in criteria["props"]:
            name = prop["name"]
            query_type = prop["query_type"]
            min_range = prop["min_range"]
            max_range = prop["max_range"]
            # todo 这里是不是可能有数据库注入
            if query_type == 'equal':
                props.update({name + '__exact': min_range})
            if query_type == 'not_equal':
                props.update({name + '__not': min_range})
            if query_type == 'range':
                props.update({name + '__gte': min_range})
                props.update({name + '__lte': max_range})
            if query_type == 'more':
                props.update({name + '__gte': min_range})
            if query_type == 'less':
                props.update({name + '__lte': max_range})
            result = {
                "limit": limit,
                "labels": criteria["labels"],
                "props": props,
                "source": criteria["source"]
            }
            return result
