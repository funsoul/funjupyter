# -*- coding: utf-8 -*-
import re
import requests
from lxml import etree
import pandas as pd
import datetime
import time
import sys
# import pymysql

# 定义请求头，不然爬不了链家
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/'
                         '62.0.3202.94 Safari/537.37'}
# 数据库连接
# con = pymysql.connect(db='crawler', user='root', password='123456', charset='utf8')
# cur = con.cursor()


# 定义一个Lianjia类，用来获取链家所有的数据
class Lianjia(object):
    city = ''

    def __init__(self, city):
        self.city = city
        self.url = "https://gz.lianjia.com/ershoufang/"  # 二手房网站
        self.url_bash = "https://gz.lianjia.com"  # 广州链家主网站
        self.headers = headers  # 需要外部的headers

    # 用于获得每个区域的名字和二级链接
    def get_area_url_name(self):
        url = self.url
        html = requests.post(url, headers=self.headers).text  # 使用post方式请求
        selector = etree.HTML(html)  # 解析网页
        areas = selector.xpath('//div[@data-role="ershoufang"]/div/a/text()')  # 区域名称
        urls = selector.xpath('//div[@data-role="ershoufang"]/div/a/@href')  # 不完整的区域链接
        return urls, areas

    # 用于获取每个区域的某一页二手房信息
    def get_area_one_house(self, url_area, page):
        url = self.url_bash + url_area  # 拼接网页，得到完整的区域链接
        url_page = url + 'pg' if page == 0 else url + 'pg%s' % str(page + 1)  # 某个区域某一页的链接
        print("当前页：{}" . format(url_page))
        html = requests.post(url_page, headers=self.headers).text  # 请求某个区域某一页的链接
        selector = etree.HTML(html)  # 解析
        lianjia_data = dict()
        try:
            li = selector.xpath('//ul[@class="sellListContent"]//li')[0]
            lianjia_data['introduction'] = li.xpath('//div[@class="info clear"][1]/div[@class="title"]/a/text()')  # 简介
            lianjia_data['url'] = li.xpath('//div[@class="info clear"][1]/div[@class="title"]/a/@href')  # 每个房子的链接
            descriptions = li.xpath('//div[@class="houseInfo"]/text()')  # 户型、面积、朝向、装修、有无电梯
            com_street = li.xpath('//div[@class="positionInfo"]/a/text()')  # 小区-街道
            freq = li.xpath('//div[@class="followInfo"]/text()')  # 关注人数、带看人次，发布时间
            # lianjia_data['subway'] = li.xpath('//div[@class="tag"]/span[@class="subway"]/text()')  # 标签：近地铁
            # lianjia_data['taxfree'] = li.xpath('//div[@class="tag"]/span[@class="taxfree"]/text()')  # 标签：满几年
            lianjia_data['price'] = li.xpath('//div[@class="totalPrice"]/span/text()')  # 价格，单位：万
            unit_price = li.xpath('//div[@class="unitPrice"]/span/text()')  # 单价
            lianjia_data['unit_price'] = [int(re.findall(r"\d+\.?\d*", i)[0]) for i in unit_price]

            lianjia_data['community'] = com_street[::2]
            lianjia_data['street'] = com_street[1::2]

            # descriptions每个列表包括7类，将其拆分
            lianjia_data['room_type'] = [i.split(' | ')[0] for i in descriptions]  # 户型
            acreage = [i.split(' | ')[1] for i in descriptions]  # 面积
            lianjia_data['acreage'] = [re.findall(r"\d+\.?\d*", i)[0] for i in acreage]

            lianjia_data['toward'] = [i.split(' | ')[2] for i in descriptions]  # 朝向
            lianjia_data['decoration'] = [i.split(' | ')[3] for i in descriptions]  # 装修情况
            floor = [i.split(' | ')[4] for i in descriptions]  # 楼层
            lianjia_data['floor_type'] = [re.findall(r"(.*?)[层]", i)[0] for i in floor]
            lianjia_data['floor_total'] = [int(re.findall(r"\d+\.?\d*", i)[0]) for i in floor]

            year = [i.split(' | ')[5] if '年' in i.split(' | ')[5] else '-' for i in descriptions]  # 年限
            lianjia_data['year'] = [int(re.findall(r"\d+\.?\d*", i)[0]) if i != '-' else '-' for i in year]

            lianjia_data['type'] = []
            for i in descriptions:
                if len(i.split(' | ')) == 7:
                    lianjia_data['type'].append(i.split(' | ')[6])
                elif len(i.split(' | ')) == 6 and i.split(' | ')[5] != '暂无数据':
                    lianjia_data['type'].append(i.split(' | ')[5])
                else:
                    lianjia_data['type'].append('-')

            # freq每个列表包括两类，将其拆分
            follow = [i.split(' / ')[0] for i in freq]  # 关注人数
            lianjia_data['follow'] = [int(re.findall(r"\d+\.?\d*", i)[0]) for i in follow]

            lianjia_data['release_time'] = [i.split(' / ')[1] for i in freq]  # 发布时间

        except IndexError as e:
            print(e.with_traceback())
        return lianjia_data

    # 用于获取每个区域的所有二手房信息
    def get_area_all_house(self, url_area, area):
        url = self.url_bash + url_area
        html = requests.post(url, headers=self.headers).text  # 请求某个区域某一页的链接
        selector = etree.HTML(html)  # 解析
        max_pages = selector.xpath('//div[@class="page-box fr"]/div/@page-data')[0]  # 此区域最大页面数
        pattern = '{"totalPage":(.*?),"curPage":1}'  # 正则字符串
        max_page = re.findall(pattern, max_pages)[0]  # 使用正则表达式得到最大页码数字，以备后用
        lianjia_area_data = pd.DataFrame()
        print("总页数：{}" . format(max_page))
        for page in range(int(max_page)):
            # if page == 2:
            #     break
            lianjia_data = self.get_area_one_house(url_area, page)
            df = pd.DataFrame.from_dict(lianjia_data, orient='index')
            lianjia_area_data = lianjia_area_data.append(df.T)
            print('已爬取%s区第%s页。' % (area, page+1))
        return lianjia_area_data

    def get_all_house(self):
        start_time = datetime.datetime.now()  # 爬取开始的时间
        urls, areas = self.get_area_url_name()
        lianjia_area_datas = pd.DataFrame()
        # 遍历每一个区域
        for i in range(len(urls)):
            if urls[i] == '/ershoufang/{}/' . format(self.city):
                lj_data = self.get_area_all_house(urls[i], areas[i])
                print("{}长度：{}" . format(self.city, len(lj_data)))
                lianjia_area_datas = lianjia_area_datas.append(lj_data)

        print('{}区所有数据已爬取！\n' . format(self.city))
        end_time = datetime.datetime.now()  # 爬取结束的时间
        run_time = (end_time - start_time).seconds  # 爬取总时间
        print('用时%s秒。' % run_time)
        return lianjia_area_datas


if __name__ == '__main__':
    lj = Lianjia(city=sys.argv[1])
    lianjia_area_datas = lj.get_all_house()

    print("一共{}条房源数据" . format(len(lianjia_area_datas)))

    lianjia_area_datas.index = range(len(lianjia_area_datas))
    lianjia_area_datas.to_csv("./lianjia_{}_ershoufang_{}.csv" . format(sys.argv[1],
                                                                        time.strftime('%Y-%m-%d_%H:%M:%S',
                                                                                      time.localtime(time.time()))))

