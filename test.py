import sqlite3
import time
#con=sqlite3.connect("네이버검색상위.db")
#cursor=con.cursor()
#cursor.execute("Create table searchtop(no int, title string, price int, rate float, date string)")
#cursor.execute("Insert into searchtop VALUES(1,'삼성전자',81900,-0.12)")
#cursor.execute("drop table searchtop")
#cursor.execute("ALTER TABLE searchtop ADD COLUMN date string") #이걸해야 그아래 fetchone이 먹힌다

#print(cursor.fetchone())#selecta all 그아래 fetchone이 먹힌다
#SELECT CURRENT_DATE, CURRENT_TIME,
#SELECT strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime') 현지시간;
#Date, Time타입
#      TEXT: YYYY-MM-DD HH:MM:SS.SSS 형태로 저장
#cursor.execute("delete from searchtop where no=1")
#cursor.execute('insert into searchtop Values(1,abc,81800,-0.24,2020-03-02 15:17:24)')
#from 네이버금융크롤링 import *
#crawling_data=stock_crawling()
"""
print(time.strftime('%Y-%m-%d'))
print(type(time.strftime('%Y-%m-%d')))
in_text="select title from searchtop where date>'2021-03-23' and rate>15"
cursor.execute(in_text)
for row in cursor:#
    print(row[0])#str

con.commit()
con.close()
"""
"""
code_list={}
code=dict({})
code.update({'b':10,'c':20})
code_list.update({'a':code})
code_list.update({'f':code})
print(code_list['a'])
print(code)
code_list['a']['b']=100
print(len(code_list))
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread
class TicGenerator(QThread):
    """
    5초마다 틱 신호를 전달
    """
    # 사용자 정의 시그널 선언
    # 외부에서 사용할때 tic대신 Tic을 이용하여 호출할 수 있다.
    # Qt의 시그널 및 슬롯 이름은 Camel을 사용하기 때문에 파이썬의 PEP8을 지키면서 작성한다면 name을 반드시 사용
    tic = pyqtSignal(name="Tic")

    def __init__(self):
        QThread.__init__(self)

    def __del__(self): #이부분이 뭘까? : 소멸자 
        self.wait() #wait 는 다른 스레드가 끝날때까지 block calling thread

    def run(self): #run으로 이벤트 루프시작 
        #산걸 쭉 본뒤 조건에 맞으면 signal 보냄
        #정보를 받아야 함
        while True:
            t = int(time.time())
            if not t % 5 == 0:
                self.usleep(1)
                continue
            self.Tic.emit()
            self.msleep(1000)

#testthread = new TestThread(this);
#connect(testthread, SIGNAL(ThreadEnd()), this, SLOT(PrintToScreen()));
#thread와 main loop를 signal/slot형태로 연결

test_dict={'010240': '12', '011000': '23', '032080': '2,049', '038070': '1', '094820': '776', '138610': '365', '139670': '648', '256840': '768', '263750': '1'}
code_l=list(test_dict.keys())#주식코드
count_l=list(test_dict.values())#주식개수
for i in range(len(test_dict)):#{code:count}
            code=code_l[i]
            count=count_l[i]
            print(code,count)
            test_dict.pop(code)
            print(test_dict)
            
        