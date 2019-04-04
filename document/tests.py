from django.test import TestCase
from django.shortcuts import render
from document.models import Resource
from document.models import Document
import uuid
# Create your tests here.


def add_resource(uuid, url):

    resource = Resource.select().where(Resource.uuid == uuid)
    for re in resource:
        print(re)
        if re == " ":
            Resource.create(uuid=uuid, file=url)
            # return render(request, 'add_resource.html', {'resource': resource})
        else:
            urls = re.file
            urls = urls + "," + url
            Resource.update({Resource.file: urls}).where(Resource.uuid == uuid).execute()


def add_document(uuid_now, userid, title, description, url, area):
        a = uuid.uuid1()
        Document.create(uuid=a, userid=userid, title=title, description=description, url=url, area=area)
        document_now = Document.select().where(Document.uuid == uuid_now)
        print(document_now)
        for doc in document_now:
            list = doc.uuid_list
            print(list)
            if(list != None):
                list_new = list + "," + str(a)
            else:
                list_new = str(a)
            Document.update({Document.uuid_list: list_new}).where(Document.uuid == uuid_now).execute()
        # return render(request, 'add_document_relate.html', {'document': document})


def select_document_relate(uuid):
    document = Document.select({Document.uuid_list}).where(Document.uuid == uuid)
    for doc in document:
        list = doc.uuid_list
        print(list)


if __name__ == '__main__':
    # add_resource("d3abf128-015c-4f42-898d-82e6f9fbac50", "http://guge.com")
    # add_resource("979968a9-3432-4bfd-a4f8-cbe0bbc9d25f", "2345678")
    # update_resource("2", "d3abf128-015c-4f42-898d-82e6f9fbac50", "http://guge.com")
    add_document("924d061c-5517-11e9-9703-04d3b0eb8835", "27657", "45677专题领域3", "3567675描述描述描3", "3673567567http://url33333333", "36767789北京市海淀区")
