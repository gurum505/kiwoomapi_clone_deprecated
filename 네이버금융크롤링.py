from bs4 import BeautifulSoup
import requests
import sqlite3
from datetime import datetime


response=requests.get("https://finance.naver.com/sise/lastsearch2.nhn")
html=response.text
soup = BeautifulSoup(html, "html5lib")
tbody=soup.select(".box_type_l tbody tr td")
"""  
#no 
#이름
#검색비율
#현재가
#전일비 \\n 22500 \\t
#등락률 \\n -13.5 \\n
#거래량
#시가
#고가
#저가
#per
#roe
"""
no=[] #0
title=[] #1
price=[] #3
rate=[] #5 (%)

index=0
for tr in tbody:
    if(tr.get_text()!=''):
        if(index%12==0):
            no.append(int(tr.get_text()))
        elif(index%12==1):
            title.append(tr.get_text())
        elif(index%12==3):
            price.append(int(tr.get_text().replace(',','')))
        elif(index%12==5):  
            if(tr.get_text()[10:-10]==''):
                rate.append('0.00')
            else:                 
                rate.append(float(tr.get_text()[10:-10]))
        index+=1
day_time=datetime.today().strftime('%Y-%m-%d %H:%M:%S')

#시간이 10시랑 장종료후에
con=sqlite3.connect("네이버검색상위.db")
cursor=con.cursor()
for i in range(len(no)):
    in_text='insert into searchtop VALUES({0},"{1}",{2},{3},"{4}")'.format(no[i],title[i],price[i],rate[i],day_time)
    #print(in_text)
    cursor.execute(in_text)
con.commit()
con.close()




