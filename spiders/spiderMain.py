# file:spiderMain.py
import requests
from lxml import etree
import csv
import os
import re
import time  # 确保正确导入 time 模块
import utils.query


class spider(object):
    def __init__(self):
        # 修改为动态URL模板
        self.spiderUrlTemplate = 'https://www.haodf.com/citiao/jibing-{disease}/bingcheng.html?p=%s'
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36'
        }

    def init(self):
        if not os.path.exists('temp1.csv'):
            with open('temp1.csv', 'a', newline='', encoding='utf-8') as wf:
                write = csv.writer(wf)
                write.writerow(["type", "gender", "age", "time", "content", "docName", "docHospital", "department",
                                "detailUrl", "height", "weight", "illDuration", "allergy"])
        try:
            # 修复数据库密码
            from pymysql import connect
            conn = connect(host='localhost', user='root', password='1324561qt', database='medicalinfo', port=3306,
                           charset='utf8mb4')
            sql = '''
                  create table if not exists cases \
                  ( \
                      id          int primary key auto_increment, \
                      type        varchar(255), \
                      gender      varchar(255), \
                      age         varchar(255), \
                      time        varchar(255), \
                      content     varchar(255), \
                      docName     varchar(255), \
                      docHospital varchar(255), \
                      department  varchar(255), \
                      detailUrl   varchar(2555), \
                      height      varchar(255), \
                      weight      varchar(255), \
                      illDuration varchar(255), \
                      allergy     varchar(255)
                  ) \
                  '''
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化错误: {e}")
            pass

    def main(self, disease_pinyin, disease_chinese, page):
        try:
            # 使用动态URL模板
            url = self.spiderUrlTemplate.format(disease=disease_pinyin)
            pageHtml = requests.get(url % page, headers=self.header, timeout=10).text
            page_tree = etree.HTML(pageHtml)
            li_list = page_tree.xpath('//*[@id="me-content"]/main/section/div/ul/li')

            for index, li in enumerate(li_list):
                print(f"正则爬取页面第{index + 1}条数据")
                initData = []
                # 类型（使用中文疾病名）
                initData.append(disease_chinese)
                # 性别
                try:
                    gender_text = li.xpath('./a/div/span[@class="patient-name"]/text()')[0]
                    gender = gender_text[3] if len(gender_text) > 3 else '未知'
                except:
                    gender = '未知'
                initData.append(gender)
                # 年龄
                try:
                    age_text = li.xpath('./a/div/span[@class="patient-name"]/text()')[0]
                    age = re.search(r'\d+', age_text).group() if re.search(r'\d+', age_text) else '未知'
                except:
                    age = '未知'
                initData.append(age)
                # 时间
                try:
                    time_text = li.xpath('./a/div/span[@class="date"]/text()')[0]
                    if re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', time_text):
                        time_value = re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', time_text).group()
                    elif re.search(r'\d{1,2}\.\d{1,2}', time_text):
                        time_value = re.search(r'\d{1,2}\.\d{1,2}', time_text).group()
                    else:
                        time_value = '未知'
                except:
                    time_value = '未知'
                initData.append(time_value)  # 使用 time_value 而不是 time
                # 描述
                try:
                    content = li.xpath('./a/h3[@class="title"]/text()')[0]
                except:
                    content = '无描述'
                initData.append(content)
                # 医生名称
                try:
                    docName = li.xpath('./div/div[@class="svc-info"]/a[@class="name"]/text()')[0]
                except:
                    docName = '未知医生'
                initData.append(docName)
                # 医院
                try:
                    docHospital = li.xpath('./div/div[@class="svc-info"]/a[@class="hospital"]/text()')[0]
                except:
                    docHospital = '未知医院'
                initData.append(docHospital)
                # 医院科室
                try:
                    department = li.xpath('./div/div[@class="svc-info"]/a[@class="faculty"]/text()')[0]
                except:
                    department = '未知科室'
                initData.append(department)
                # 详情链接
                try:
                    detailUrl = li.xpath('./a/@href')[0]
                    # 处理相对链接
                    if not detailUrl.startswith('http'):
                        detailUrl = 'https://www.haodf.com' + detailUrl
                except:
                    detailUrl = ''
                initData.append(detailUrl)

                self.save_to_csv(initData)

        except Exception as e:
            print(f"页面爬取错误: {e}")

        # 控制翻页
        if page < 5:  # 限制爬取页数避免被封
            time.sleep(2)  # 添加延时
            self.main(disease_pinyin, disease_chinese, page + 1)

    def save_to_csv(self, resultData):
        try:
            with open('temp1.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(resultData)
        except Exception as e:
            print(f"保存CSV错误: {e}")

    def save_to_sql(self):
        try:
            with open('temp1.csv', 'r', encoding='utf-8') as r_f:
                reader = csv.reader(r_f)
                for i in reader:
                    if i[0] == 'type':
                        continue
                    utils.query.querys('''
                                       insert into cases(type, gender, age, time, content, docName, docHospital,
                                                         department, detailUrl)
                                       values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                       ''', [i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
        except Exception as e:
            print(f"保存数据库错误: {e}")


if __name__ == '__main__':
    spiderObj = spider()
    spiderObj.init()

    # 定义疾病映射表
    diseases = {
        'ganmao': '感冒',
        'gaoxueya': '高血压',
        'weiyankangchuang': '胃炎',
        'yiyuzheng': '抑郁症',
        'guzhe': '骨折',
        'jingzhuibing': '颈椎病',
        'yaotuipengchu': '腰椎间盘突出'
    }

    # 循环爬取多种疾病数据
    for pinyin, chinese_name in diseases.items():
        print(f"开始爬取 {chinese_name} 数据...")
        spiderObj.main(pinyin, chinese_name, 1)

    spiderObj.save_to_sql()

