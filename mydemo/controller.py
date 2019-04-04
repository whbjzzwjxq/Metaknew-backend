from django.http import HttpResponse

import mydemo.views as test


def addCard(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '')
            title = request.POST.get('title', '')
            mobile = request.POST.get('mobile ', '')
            companyName = request.POST.get('companyName', '')
            more = request.POST.get('more', '')
            email = request.POST.get('email', '')
            address = request.POST.get('address', '')
            obj = test.TestMongoEngine()
            print(name, title, mobile, companyName, more, email, address)
            result = obj.add(name, title, mobile, companyName, more, email, address)
            return HttpResponse(result)
        except Exception as e:
            print(e)
            return HttpResponse('网络出错!')


def deleteCard(request):
    if request.method == 'POST':
        try:
            id = request.POST.get('id', '')
            print(id)
            obj = test.TestMongoEngine()
            obj.delete(id)
        except Exception as e:
            print(e)
            return HttpResponse('网络出错!')