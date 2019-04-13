from translate import connect
import pandas as pd
import re

zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

def dataframe2dict(data):
    '''
    Arg:
       data : (DataFrame) data read from excel
    Return:
       (list<dict>) structured data
    '''

    NodeList = []
    for row in range(len(data)):
        node = {}
        node["starttime"] = data.iloc[row,0]
        node["endtime"] = data.iloc[row,1]
        node["Name_es"], node["Name_zh"] = name_translation(data.iloc[row,2])
        node["Architect_es"], node["Architect_zh"] = architect_translation(data.iloc[row,3])
        node["Nation"] = data.iloc[row,4]
        node["Location"] = data.iloc[row,5] if str(data.iloc[row,5]) != 'nan' else None 
        node["Address"] = data.iloc[row,6]  if str(data.iloc[row,6]) != 'nan' else None
        node["Type"] = data.iloc[row,7]     if str(data.iloc[row,7]) != 'nan' else None
        node["Remarks"] = data.iloc[row,8]  if str(data.iloc[row,8]) != 'nan' else None
        NodeList.append(node)

    return NodeList

def name_translation(name):

    '''
    Arg:
       name : (String) name string
    Return:
       (String) es_name, zh_name
    '''
    
    if '（' in name or '(' in name:
        name_es = re.split('\(+|（+',name)[-1][:-1]
        name_zh = re.split('\(+|（+',name)[-2]

        if not zhPattern.search(name_zh):
            #无中文
            # print(name_es)
            name_zh = connect(name_es,en2zh=True)
    else:
        name_es = name
        name_zh = connect(name_es,en2zh=True)

    return name_es, name_zh

def architect_translation(architect):

    '''
    Arg:
       name : (String) name string
    Return:
       (String) es_name, zh_name
    '''

    if '（' in architect or '(' in architect:
        architect_es = re.split('\(+|（+',architect)[-1][:-1]
        architect_zh = re.split('\(+|（+',architect)[-2]

        if not zhPattern.search(architect_zh):
            #无中文
            architect_zh = None
    else:

        if zhPattern.search(architect):
            architect_es = None
            architect_zh = architect
        else:
            architect_es = architect
            architect_zh = None

    if architect_es:
        architect_es = re.split(' and |,|，',architect_es)
        if "" in architect_es:
            architect_es.remove("")

    if architect_zh:    
        architect_zh = re.split('，|,',architect_zh)

    return architect_es, architect_zh


if __name__ == '__main__':
    data = pd.read_excel("拉美现代建筑名单1900-1990_updating (1).xlsx")
    dataframe2dict(data)

