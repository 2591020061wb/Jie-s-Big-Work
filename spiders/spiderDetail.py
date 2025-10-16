import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from utils.query import querys

# service = Service('./chromedriver.exe')
# browser =webdriver.Chrome(service=service)
# option = webdriver.ChromeOptions()
# browser.get('https://www.baidu.com/')
class spider(object):
    def __init__(self,spiderUrl):
        self.spiderUrl = spiderUrl

    def startBrowser(self):
        service = Service('./chromedriver.exe')
        option = webdriver.ChromeOptions()
        option.add_experimental_option("debuggerAddress","localhost:9223")
        browser = webdriver.Chrome(service=service,options=option)
        # browser.get('https://www.baidu.com/')
        return browser

    def main(self,id):
        browser = self.startBrowser()
        print('列表URL为'+self.spiderUrl)
        browser.get(self.spiderUrl)
        if browser.find_element(by=By.XPATH,value='//span[contains(text(),"疾病描述")]/following-sibling::span[1]'):
            #身高
            try:
                height = re.findall('\d+', browser.find_element(by=By.XPATH,value='//span[contains(text(),"身高体重")]/following-sibling::span[1]').text)[0]
            except:
                height = '无'
            #体重
            try:
                weight = re.findall('\d+',browser.find_element(by=By.XPATH,value='//span[contains(text(),"身高体重")]/following-sibling::span[1]').text)[1]
            except:
                weight = '无'
            #患病时间
            try:
                illDuration = browser.find_element(by=By.XPATH,value='//span[contains(text(),"患病时长")]/following-sibling::span[1]').text
            except:
                illDuration = '无'
            #过敏史
            try:
                allergy = re.search(r'([\u4e00-\u9fa5]+)\(',browser.find_element(by=By.XPATH,value='//span[contains(text(),"过敏史")]/following-sibling::span[1]').text).group(1)
            except:
                allergy = '暂无信息'
            print(height,weight,illDuration,allergy)
            querys('UPDATE cases SET height=%s,weight=%s,illDuration=%s,allergy=%s WHERE id = %s',
                   [height,weight,illDuration,allergy,id])
        else:
            return '爬取失败'


if __name__ == '__main__':
    caseList = querys('select * from cases',[],'select')
    for i in caseList[:]:
        spiderObj = spider(i[9])
        spiderObj.main(i[0])

