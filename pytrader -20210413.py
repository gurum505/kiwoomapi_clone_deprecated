import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import sqlite3
import time

form_class = uic.loadUiType("main_window.ui")[0]
#account="8162528011" 8자리+11
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()#키움연결

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        self.pushButton_2.clicked.connect(self.check_balance)

        self.timer2 = QTimer(self) #실시간조회 10초에 한번씩 호출
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        self.load_buy_sell_list() #매매목록불러오는 것 후에 함수 고칠것 네이버용으로
        self.trade_stocks_done = False
        
        self.interesting_stock()
        self.kiwoom._reset_real_data_output()
        
        self.timer3=QTimer(self)
        self.timer3.setInterval(1000)
        self.timer3.timeout.connect(self.check_vp)
        self.timer3.start()
        
        self.lineEdit.textChanged.connect(self.code_changed)
        self.pushButton.clicked.connect(self.send_order)

        self.timer4=QTimer(self)
        self.timer4.setInterval(5000)
        self.timer4.timeout.connect(self.accel_rate) #실시간데이터가 아니라 최대 0.3초에1번
        self.timer4.start()

        self.pushButton_3.clicked.connect(self.update_interesting_stock)

        self.lineEdit_4.setText("로딩완료")
    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar=QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data: #18은 최대 20개의 보유종목에 대한 데이터를 리턴하기때문에 반복문필요
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        #0001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
        #예수금
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)
        #총매입 총평가 총손익 ....
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)
        # 아이템크기맞춰조절
        self.tableWidget.resizeRowsToContents()

        # Item list tablewidget2
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)
        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)
        self.tableWidget_2.resizeRowsToContents()

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    def load_buy_sell_list(self): #매매할 거 불러오기 네이버 검색순위 상위로 변경 
        
        f = open("buy_list.txt", 'rt',encoding='utf-8')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt',encoding='utf-8')
        sell_list = f.readlines()
        f.close()  

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        #buylist
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()
        
    def trade_stocks(self): #장시작에 맞춰 정해진 주문방식에 따라 주문을 수행 변경필요
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("buy_list.txt", 'rt',encoding='utf-8')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt',encoding='utf-8')
        sell_list = f.readlines()
        f.close() 

        account=self.kiwoom.get_login_info("ACCNO")#문제있을시 위의 account전역변수설정
        account = account.split(';')[0]

        #buy_list 매수전일때 주문냄
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")

        # buy list
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # file update
        f = open("buy_list.txt", 'wt',encoding='utf-8')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")
        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = open("sell_list.txt", 'wt',encoding='utf-8')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    def timeout(self):
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True

    def check_vp(self):#실시간 체결강도 #나중에 db에 기록기능도추가
        cnt=0
        for code in self.set_real_reg_code_list:
            if(cnt==0):
                self.kiwoom.set_real_reg("1000",code,"9001:302;10;11;25;12;13","0")
            else:
                self.kiwoom.set_real_reg("1000",code,"9001:302;10;11;25;12;13","1")

            if(code in self.kiwoom.code_list): #이 구문이 필요한가? #
                item=QTableWidgetItem(self.kiwoom.code_list[code]['price'])
                self.tableWidget_4.setItem(cnt,1,item)
                item=QTableWidgetItem(self.kiwoom.code_list[code]['rate'])
                self.tableWidget_4.setItem(cnt,2,item)
                item=QTableWidgetItem(self.kiwoom.code_list[code]['vp'])
                self.tableWidget_4.setItem(cnt,3,item)
            cnt=cnt+1
                
            

    def interesting_stock(self):
        self.kiwoom.set_code_name()
        self.set_real_reg_code_list=[]
        con=sqlite3.connect("네이버검색상위.db")
        cursor=con.cursor() 
        in_text="select distinct title from searchtop where date>'{0}' and rate>15".format(time.strftime('%Y-%m-%d'))
        cursor.execute(in_text)
        #today로 바꾸기
        index=0
        for row in cursor:
            if(row[0] in self.kiwoom.kospi_name_list): #name으로 code번호를 찾는 for문 테이블4에 이름하고 코드를 적는다 
                item=QTableWidgetItem(row[0])
                self.tableWidget_4.setItem(index,0,item)
                code_index=self.kiwoom.kospi_name_list.index(row[0]) #cospi로만 하니까 안잡히는 것들이 있다 수정필요
                item=QTableWidgetItem(self.kiwoom.kospi_code_list[code_index])
                self.set_real_reg_code_list.append(self.kiwoom.kospi_code_list[code_index])
                self.tableWidget_4.setItem(index,4,item)
                index=index+1
        con.commit()
        con.close()

        self.lineEdit_3.setText(time.strftime('%Y-%m-%d'))
      
      

    def code_changed(self):
        code=self.lineEdit.text()
        name=self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        order_type = self.comboBox.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_2.currentText()
        num = self.spinBox_2.value()
        price = self.spinBox.value()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account= account_number.split(';')[0]
        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price, hoga_lookup[hoga], "")

    def accel_rate(self):
        self.kiwoom.set_input_value("시장구분","000")#0전체 001코스피 101 코스닥
        self.kiwoom.set_input_value("정렬구분","1")#급등1 급락2
        self.kiwoom.set_input_value("거래량조건","0000")#00000 전체
        self.kiwoom.set_input_value("종목조건","1")#1 관리종목제외
        self.kiwoom.set_input_value("신용조건","0")#0 전체
        self.kiwoom.set_input_value("가격조건","0")#0 전체
        self.kiwoom.set_input_value("상하한포함","0")#0 미포함
        self.kiwoom.set_input_value("거래량대금조건","0")#0 미포함

        self.kiwoom.comm_rq_data("opt10027_req","opt10027",0,"1101")

        self.tableWidget_5.setRowCount(len(self.kiwoom.accel_rate))
        for index in range(len(self.kiwoom.accel_rate)):#종목명, 현재가 등락률 체결강도 종목코드
            name=self.kiwoom.accel_rate[index]["종목명"]
            price=self.kiwoom.accel_rate[index]["현재가"]
            accel_rate=self.kiwoom.accel_rate[index]["등락률"]
            vp_rate=self.kiwoom.accel_rate[index]["체결강도"]
            code=self.kiwoom.accel_rate[index]["종목코드"]
            item=QTableWidgetItem(name)
            self.tableWidget_5.setItem(index,0,item)
            item=QTableWidgetItem(price)
            self.tableWidget_5.setItem(index,1,item) 
            item=QTableWidgetItem(accel_rate)
            self.tableWidget_5.setItem(index,2,item) 
            item=QTableWidgetItem(vp_rate)
            self.tableWidget_5.setItem(index,3,item) 
            item=QTableWidgetItem(code)
            self.tableWidget_5.setItem(index,4,item) 
            index=index+1
    def update_interesting_stock(self):
        import 네이버금융크롤링
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()