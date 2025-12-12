# file:spiderDetail.py
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from utils.query import querys


class spider(object):
    def __init__(self, spiderUrl):
        self.spiderUrl = spiderUrl

    def startBrowser(self):
        try:
            # 修复ChromeDriver路径问题
            service = Service('./chromedriver.exe')
            option = webdriver.ChromeOptions()
            option.add_experimental_option("debuggerAddress", "localhost:9223")
            # 添加更多选项提高稳定性
            option.add_argument('--no-sandbox')
            option.add_argument('--disable-dev-shm-usage')
            browser = webdriver.Chrome(service=service, options=option)
            return browser
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            return None

    def main(self, id):
        try:
            browser = self.startBrowser()
            if not browser:
                return '浏览器启动失败'

            print('列表URL为' + self.spiderUrl)
            browser.get(self.spiderUrl)
            time.sleep(3)  # 等待页面加载

            # 检查页面是否包含所需信息
            try:
                disease_desc_element = browser.find_element(By.XPATH,
                                                            '//span[contains(text(),"疾病描述")]/following-sibling::span[1]')

                # 身高
                try:
                    height_element = browser.find_element(By.XPATH,
                                                          '//span[contains(text(),"身高体重")]/following-sibling::span[1]')
                    height_matches = re.findall(r'\d+', height_element.text)
                    height = height_matches[0] if height_matches else '无'
                except:
                    height = '无'

                # 体重
                try:
                    weight_element = browser.find_element(By.XPATH,
                                                          '//span[contains(text(),"身高体重")]/following-sibling::span[1]')
                    weight_matches = re.findall(r'\d+', weight_element.text)
                    weight = weight_matches[1] if len(weight_matches) > 1 else '无'
                except:
                    weight = '无'

                # 患病时间
                try:
                    illDuration_element = browser.find_element(By.XPATH,
                                                               '//span[contains(text(),"患病时长")]/following-sibling::span[1]')
                    illDuration = illDuration_element.text.strip() if illDuration_element.text.strip() else '无'
                except:
                    illDuration = '无'

                # 过敏史
                try:
                    allergy_element = browser.find_element(By.XPATH,
                                                           '//span[contains(text(),"过敏史")]/following-sibling::span[1]')
                    allergy_match = re.search(r'([\u4e00-\u9fa5]+)', allergy_element.text)
                    allergy = allergy_match.group(1) if allergy_match else '暂无信息'
                except:
                    allergy = '暂无信息'

                print(height, weight, illDuration, allergy)
                querys('UPDATE cases SET height=%s,weight=%s,illDuration=%s,allergy=%s WHERE id = %s',
                       [height, weight, illDuration, allergy, id])
                return '爬取成功'
            except Exception as e:
                print(f"详情页元素定位失败: {e}")
                return '爬取失败'

        except Exception as e:
            print(f"详情爬虫执行错误: {e}")
            return '爬取失败'
        finally:
            # 不要关闭浏览器，因为使用了调试模式
            pass


if __name__ == '__main__':
    try:
        caseList = querys('select * from cases where height is null or height = ""', [], 'select')
        print(f"发现{len(caseList)}条需要补充详情的数据")

        for index, i in enumerate(caseList):
            print(f"正在处理第{index + 1}条数据，ID: {i[0]}")
            if i[9]:  # 确保详情链接存在
                spiderObj = spider(i[9])
                result = spiderObj.main(i[0])
                print(f"处理结果: {result}")
                time.sleep(2)  # 避免请求过于频繁
            else:
                print("跳过：无详情链接")
    except Exception as e:
        print(f"主程序执行错误: {e}")
