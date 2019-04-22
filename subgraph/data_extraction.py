from subgraph.translate import connect
import pandas as pd
import re

zhPattern = re.compile(u'[\u4e00-\u9fa5]+')


starttime = 0
endtime = 1
Name = 2
Architect = 3
Nation = 4
Location = 5
Address = 6
Type = 7
Remarks = 8

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
        node["PeriodStart"] = data.iloc[row,starttime]
        node["PeriodEnd"] = data.iloc[row,endtime]
        node["Name"], node["Name_en"], node["Name_zh"] = name_translation(data.iloc[row,Name])
        node["Architect_es"], node["Architect_zh"] = architect_translation(data.iloc[row,Architect])
        node["Nation"] = data.iloc[row,Nation]
        node["Location"] = data.iloc[row,Location] if str(data.iloc[row,Location]) != 'nan' else None
        # node["Address"] = data.iloc[row,Address]  if str(data.iloc[row,Address]) != 'nan' else None
        # node["Type"] = data.iloc[row,Type]     if str(data.iloc[row,Type]) != 'nan' else None
        # node["Remarks"] = data.iloc[row,Remarks]  if str(data.iloc[row,Remarks]) != 'nan' else None
        node["PrimaryLabel"] = "Project"
        node["Type"] = "StrNode"
        node["Area"] = "Architecture"
        node["Label"] = "Architecture"

        NodeList.append(node)

    # print(NodeList[327])
    # print(NodeList[309])
    # print(NodeList[288])
    return NodeList

def name_translation(name):

    '''
    Arg:
       name : (String) name string
    Return:
       (String) es_name, zh_name
    '''
    name_origin = None
    name_zh = None
    name_en = None

    if '（' in name or '(' in name:

        nameList = re.split('\(+|（+',name)

        while '' in nameList:
            nameList.remove('')

        while ' ' in nameList:
            nameList.remove(' ')

        for i in range(len(nameList)):
            if nameList[i] != "" and (nameList[i][-1] == ")" or nameList[i][-1] == "）"):
                nameList[i] = nameList[i][:-1]

        name_origin = nameList[-1]

        # print(nameList)

        for item in nameList:
            if zhPattern.search(item):
                # get zh
                name_zh = item
                break

        for item in nameList:
            language, translation = connect(item,en2zh=True) 

            if language == "en2zh-CHS":
                # get zh and en
                name_en = item
                break

        if not name_zh or not name_en:
            _, name_zh = connect(name_origin,en2zh=True) 
            _, name_en = connect(name_zh,en2zh=False)
        
    else:
        name_origin = name
        _, name_zh = connect(name,en2zh=True)
        _, name_en = connect(name_zh,en2zh=False)

    return name_origin, name_en, name_zh

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



