import requests
from lxml import etree
import csv
import os
import pandas as pd
import re
from pymysql import *
from utils.query import querys
class spider(object):
    def __init__(self):
        self.spiderUrl = 'https://www.haodf.com/citiao/jibing-ganmao/bingcheng.html?p=%s'
        self.header = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36'
        }

    def init(self):
        if not os.path.exists('temp1.csv'):
            with open('temp1.csv', 'a', newline='', encoding='utf-8') as wf:
                write = csv.writer(wf)
                write.writerow(["type","gender","age","time","content","docName","docHospital","department",
                                 "detailUrl","height","weight","illDuration","allergy"])
        try:
            conn = connect(host='localhost', user='root', password='123456', database='medicalinfo', port=3306,
                           charset='utf8mb4')
            sql = '''
                        create table cases(
                            id int primary key auto_increment,
                            type varchar(255),
                            gender varchar(255),
                            age varchar(255),
                            time varchar(255),
                            content varchar(255),
                            docName varchar(255),
                            docHospital varchar(255),
                            department varchar(255),
                            detailUrl varchar(2555),
                            height varchar(255),
                            weight varchar(255),
                            illDuration varchar(255),
                            allergy varchar(255)
                        )
                    '''
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        except:
            pass

    def main(self,type,page):
        pageHtml = requests.get(self.spiderUrl % page,headers=self.header).text
        page_tree = etree.HTML(pageHtml)
        # 将 ElementTree 对象转换回字符串
        html_str = etree.tostring(page_tree, pretty_print=True, method="html").decode()

        # 打印转换后的 HTML 字符串
        print(html_str)
        li_list = page_tree.xpath('//*[@id="me-content"]/main/section/div/ul/li')
        for index,li in enumerate(li_list):
            print("正则爬取页面第%d" % (index+1)+"条数据")
            initData = []
            #类型
            type = type
            initData.append(type)
            #性别
            gender = li.xpath('./a/div/span[@class="patient-name"]/text()')[0][3]
            initData.append(gender)
            #年龄
            age = re.search('\d+',li.xpath('./a/div/span[@class="patient-name"]/text()')[0]).group()
            initData.append(age)
            #时间
            try:
                time = re.search('\d{1,4}.\d{1,2}.\d{1,2}', li.xpath('./a/div/span[@class="date"]/text()')[0]).group()
            except:
                time = re.search('\d{1,2}.\d{1,2}',li.xpath('./a/div/span[@class="date"]/text()')[0]).group()
            initData.append(time)
            #描述
            content = li.xpath('./a/h3[@class="title"]/text()')[0]
            initData.append(content)
            #医生名称
            docName = li.xpath('./div/div[@class="svc-info"]/a[@class="name"]/text()')[0]
            initData.append(docName)
            #医院
            docHospital = li.xpath('./div/div[@class="svc-info"]/a[@class="hospital"]/text()')[0]
            initData.append(docHospital)
            #医院科室
            department = li.xpath('./div/div[@class="svc-info"]/a[@class="faculty"]/text()')[0]
            initData.append(department)
            #详情链接
            detailUrl = li.xpath('./a/@href')[0]
            initData.append(detailUrl)
            # print(initData)
            self.save_to_csv(initData)
        if page < 1:
            self.main(type, page + 1)

    def save_to_csv(self,resultData):
        with open('temp1.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(resultData)

    def save_to_sql(self):
        with open('temp1.csv', 'r', encoding='utf-8') as r_f:
            reader = csv.reader(r_f)
            for i in reader:
                if i[0] == 'type':
                    continue
                querys('''
                    insert into cases(type,gender,age,time,content,docName,docHospital,department,detailUrl)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ''',[i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8]])

if __name__ == '__main__':
    spiderObj = spider()
    spiderObj.init()
    spiderObj.main('感冒',1)
    # spiderObj.save_to_sql()