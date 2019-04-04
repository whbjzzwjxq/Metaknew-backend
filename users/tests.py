from django.test import TestCase

# Create your tests here.
from users.models import User
from django.shortcuts import render

def add_user(userid, username, userpw):
    User.update({User.username: username, User.userpassword: userpw}).where(User.userid == userid).execute()

    # return render(request,'add_user.html',{'user':user})



if __name__ == '__main__':
    add_user("1", "asd", "1234567890")