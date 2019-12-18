# -*- coding: utf-8 -*-
import re
import pandas as pd
import datetime
import time
import sys


class Analysis(object):
    df = ''

    def __init__(self, filename):
        self.df = pd.read_csv(filename)

    def all_mean(self):
        print('二手房总价平均（万）: {}' . format(self.df['price'].mean().round(0)))

    def area_count(self):
        print('区域房源数（套）：\n{}' . format(self.df['street'].value_counts()))

    def area_mean(self):
        print('区域总价平均（万）：\n{}' . format(self.df.pivot_table('price', index='street', aggfunc='mean')
                                        .sort_values(by='price', ascending=False).round()))

    def all_unit_price_mean(self):
        print('全区单价平均（元）：\n{}' . format(self.df['unit_price'].mean().round(0)))

    def area_unit_price_mean(self):
        print('区域单价平均（元）：\n{}'.format(self.df.pivot_table('unit_price', index='street', aggfunc='mean')
                                      .sort_values(by='unit_price', ascending=False).round(0)))

    def decoration_unit_price_mean(self):
        print('装修单价平均（元）：\n{}'.format(self.df.pivot_table('unit_price', index='decoration', aggfunc='mean')
                                      .sort_values(by='unit_price', ascending=False).round(0)))

    def toward_unit_price_mean(self):
        print('朝向单价平均（元）：\n{}'.format(self.df.pivot_table('unit_price', index='toward', aggfunc='mean')
                                      .sort_values(by='unit_price', ascending=False).round(0)))

    def room_type_unit_price_mean(self):
        print('房型单价平均（元）：\n{}'.format(self.df.pivot_table('unit_price', index='room_type', aggfunc='mean')
                                      .sort_values(by='unit_price', ascending=False).round(0)))


if __name__ == '__main__':
    al = Analysis(sys.argv[1])
    al.all_mean()
    al.area_count()
    al.area_mean()
    al.all_unit_price_mean()
    al.area_unit_price_mean()
    al.decoration_unit_price_mean()
    # al.toward_unit_price_mean()
    al.room_type_unit_price_mean()

