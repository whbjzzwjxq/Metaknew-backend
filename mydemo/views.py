from django.shortcuts import render
import psycopg2

# Create your views here.

conn = psycopg2.connect(database="demo", user="postgres", password="123456", host="localhost", port="5432")


class TestMongoEngine(object):

    # def creat(self):
    #     """新建数据库表"""
    #     conn
    #     print("连接成功")
    #     cur = conn.cursor()
    #     cur.execute("CREATE TABLE COMPANY"
    #                 "(ID INT PRIMARY KEY     NOT NULL,"
    #                 "NAME TEXT    NOT NULL,"
    #                 "AGE            INT     NOT NULL,"
    #                 "ADDRESS        CHAR(50),"
    #                 "SALARY         REAL);")
    #     conn.commit()
    #     print("已释放连接")
    #     conn.close()

    def add(self, name, title, mobile, companyname, more, email, address):
        """新增数据"""
        conn
        print("连接成功")
        cur = conn.cursor()
        print(name, title, mobile, companyname, more, email, address)
        sql = "INSERT INTO \"BusinessCard\" (NAME,TITLE,MOBILE,COMPANYNAME,MORE,EMAIL,ADDRESS) VALUES ('" + name + "', '" + title + "', '" + mobile + "', '" + companyname + "', '" + more + "', '" + email + "', '" + address + "') "
        cur.execute(sql)
        conn.commit()
        print("已释放连接")
        conn.close()

    def delete(self, id):
        """删除数据"""
        conn
        cur = conn.cursor()
        sql = "DELETE from \"BusinessCard\" where ID=" + id
        cur.execute(sql)
        conn.commit()
        conn.close()

    def selectByID(self, id):
        """查询名片数据"""
        conn
        cur = conn.cursor()
        sql = "SELECT ID, NAME,TITLE,MOBILE,COMPANYNAME,MORE,EMAIL,ADDRESS FROM \"BusinessCard\" where ID=" + id
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            print("id = ", row[0])
            print("name = ", row[1])
            print("title = ", row[2])
            print("mobile = ", row[3])
            print("companyName = ", row[4])
            print("more = ", row[5])
            print("email = ", row[6])
            print("address = ", row[7])
        conn.commit()
        conn.close()



