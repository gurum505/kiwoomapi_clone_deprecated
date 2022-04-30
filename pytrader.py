import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import sqlite3
import time

form_class = uic.loadUiType("main_window.ui")[0]
#account="8162528011" 8자리+11

class Buy_Stock(QThread):#살 종목의 정보를 받고 모니터링
    Transfer_to_buy=pyqtSignal(list)
    def __init__(self):
        QThread.__init__(self)
        self.code_list=[] #사고 팔 주식
        self.code_info={} # 주식 정보 저장
        
    def __del__(self):
        self.wait()
        
    def run(self): 
        while(True): 
            used=[]
            for i in range(len(self.code_list)):
                #전략에 따라 살지 팔지 결정
                code_price=self.code_list[i]
                code=list(code_price.values())[0]#주식코드
                if(self.when_to_buy(code)):
                    price=list(code_price.values())[1]
                    price=price['price']
                    self.Transfer_to_buy.emit([code,price]) #정보,signal 전달
                    used.append(i)
                    print("transfer info to selling:",code)
            new_code_list=[]
            for i in range(len(self.code_list)):
                if i not in used:
                    new_code_list.append(self.code_list[i])
            self.code_list=new_code_list
            self.sleep(1) 

    def append(self,code,price,rate,vp):
        self.code_list.append({'code':code,'init':{'price':price,'rate':rate,'vp':vp}}) #체결정보를 갖고 와야할듯?

    def update(self,code,price,rate,vp):
        self.code_info.update({code:{'price':price,'rate':rate,'vp':vp}})

    def when_to_buy(self,code):
        #2분뒤 부터 시작
        #init에 price가 내려오고 난뒤 잰다
        #양봉 연속2봉이면 산다

        price=self.code_info[code]['rate']
        rate=self.code_info[code]['rate']
        vp=self.code_info[code]['vp']

        if float(rate)<15.00 and float(vp)>100: #98?
            return True
        if float(rate)<13.00:
            return True
        return False

class Sell_Stock(QThread):#산 종목의 정보를 받고 모니터링
    #Transfer_to_sell=pyqtSignal(str,int)
    Transfer_to_sell=pyqtSignal(list)
    def __init__(self):
        QThread.__init__(self)
        self.code_list=[] #사고 팔 주식
        self.code_info={} # 주식 정보 저장
        
    def __del__(self):
        self.wait()
        
    def run(self): 
        while(True):         
            used=[]
            for i in range(len(self.code_list)):
                #전략에 따라 살지 팔지 결정
                code_count=self.code_list[i]
                #print("code_list, i",self.code_list,i)
                code=list(code_count.keys())[0]#주식코드
                count=list(code_count.values())[0]#주식개수
                if(self.when_to_sell(code)):
                    self.Transfer_to_sell.emit([code,count]) #정보,signal 전달
                    used.append(i)
                    print("transfer info to selling:",code,count)
            new_code_list=[]
            for i in range(len(self.code_list)):
                if i not in used:
                    new_code_list.append(self.code_list[i])
            self.code_list=new_code_list
            self.sleep(1) 

    def append(self,code,count,price,rate,vp):
        if rate==0 and vp==0:
            rate=self.code_info[code]['rate']
            vp=self.code_info[code]['vp']
            self.code_list.append({code:count,'init':{'price':price,'rate':rate,'vp':vp}})
        else:
            self.code_list.append({code:count,'init':{'price':price,'rate':rate,'vp':vp}}) #체결정보를 갖고 와야할듯?


    def update(self,code,price,rate,vp):
        self.code_info.update({code:{'price':price,'rate':rate,'vp':vp}})

    def when_to_sell(self,code):#check if 조건에 맞는지 정보도 갖고 오고
        #print("when to sell")

        market_end_time = QTime(15, 29, 50)
        current_time = QTime.currentTime()

        #price=self.code_info[code]['rate']
        rate=self.code_info[code]['rate']
        vp=self.code_info[code]['vp']

        if float(rate)<12:
            return True
        

        return False
        #if current_time >= market_end_time:#수정필요 이득일시 담날 아침에 손해일시 바로 손절
        #    return True


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #키움연결
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        #self.kiwoom.OnReceiveChejanData.connect(이쪽함수 테이블2에 넣기)

        #sell_stock 멀티프로세스로 실행   
        self.sell_stock=Sell_Stock()
        self.sell_stock.start()
        self.sell_stock.Transfer_to_sell.connect(self.sell_excute)

        #buy_stock 멀티프로세스로 실행
        self.buy_stock=Buy_Stock()
        self.buy_stock.start()
        self.buy_stock.Transfer_to_buy.connect(self.buy_excute)

        #서버연결확인 1초마다
        self.timer = QTimer(self) #타이머를 하나로 연동? 수정필요
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        ####서순주의 이미 갖고있던걸 다 판다음 buy_stock(deposit을 참조하기 때문에) 
        #처음에 계좌확인 및 저번에 산것 다 팔기 alrday_buy_list에 있는 것을 판다
        self.already_buy_list={}
        self.pushButton_4.clicked.connect(self.sell_already_buy_list)
        #계좌10초마다 호출
        self.pushButton_2.clicked.connect(self.check_balance)
        
        self.timer2 = QTimer(self) #실시간조회 10초에 한번씩 호출
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)
        
        #### 서순주의 interesting stock에서 accel_rate를 참조한다
        #급등주 조회 5초마다
        self.accel_code_set=set({})
        self.timer4=QTimer(self)
        self.timer4.setInterval(5000)
        self.timer4.timeout.connect(self.accel_rate) #실시간데이터가 아니라 최대 0.5초에1번
        self.timer4.start() #목록만 받아오고 나머지는 real_data로 받자 수정필요
        
        #####
        #실시간 조회 및 실시간으로 살 것 결정 1초마다 (안그럼 엄청 깜박여서 보기 힘듦)
        self.buy_list=set({})
        self.kiwoom._reset_real_data_output()
        self.interesting_stock()
        
        self.timer3=QTimer(self)
        self.timer3.setInterval(1000)
        self.timer3.timeout.connect(self.update_interesting_stock_value)
        self.timer3.start()
        #####

        #수동주문 활성화 & 버튼연결
        self.lineEdit.textChanged.connect(self.code_changed)
        self.pushButton.clicked.connect(self.send_order)
        self.pushButton_3.clicked.connect(self.update_naver_stock) 
        
    def sell_excute(self,list): #send sell order #self.땜에 count가 인식이 안됐었음
        code=str(list[0])
        try:
            num=int(list[1].replace(',',''))
        except:
            num=int(list[1])
        price=0
        account_number = self.kiwoom.get_login_info("ACCNO")
        account= account_number.split(';')[0]
        self.kiwoom.send_order("send_order_req", "0101", account, '2', code, num, price, '03', "")
        print("sell executed:",code,num)
        #{'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        #{'지정가': "00", '시장가': "03"}

    def buy_excute(self,list):
        
        #전략에 맞춰 주식을 산다.
        #1. 이미 샀는지 확인한다.
        #if code in self.already_buy_list: #{code:num}
        #    return
        #이미 샀는지는 상관없지 앞에서 이미 산거 다 팔아버리고 새로 조건문 확인하는 거니
        code=str(list[0])
        #2. 10분의1만큼 산다
        account_number = self.kiwoom.get_login_info("ACCNO")
        account= account_number.split(';')[0]
        #예수금
        try:
            deposit=self.deposit
            deposit=int(deposit.replace(',',''))
            price=int(list[1].replace(',',''))
        except:
            deposit=1
            price=int(list[1])

        num=(deposit//(int(price)*10))
        if  num != 0:        
            self.kiwoom.send_order("send_order_req", "0101", account, '1', code, num, price, '03', "")
            #{'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
            #{'지정가': "00", '시장가': "03"}
            #개수와 종목
            print("buy executed",code,num)
            rate=0
            vp=0
            self.sell_stock.append(code,num,price,rate,vp)

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
        self.deposit=self.kiwoom.d2_deposit
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)
        #총매입 총평가 총손익 ....
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1]) #try error 필요?
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)
        # 아이템크기맞춰조절
        self.tableWidget.resizeRowsToContents()

        # Item list tablewidget2
        tmp_alreday_buy_list={}
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)
        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

            tmp_alreday_buy_list.update({row[6][1:]:row[1]})#맨앞A빼야함
        self.tableWidget_2.resizeRowsToContents()
        self.already_buy_list=tmp_alreday_buy_list
        
    def sell_already_buy_list(self):
        code_l=list(self.already_buy_list.keys())#주식코드
        count_l=list(self.already_buy_list.values())#주식개수

        for i in range(len(self.already_buy_list)):#{code:count}
            self.sell_excute([code_l[i],count_l[i]])
        

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    def timeout3(self):
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()

        if current_time > market_start_time:
            self.trade_stocks()
           

    def update_interesting_stock_value(self):#실시간 체결강도 #나중에 db에 기록기능도추가

        for index in range(len(self.set_real_reg_code_list)):
            code=self.tableWidget_4.item(index,4).text()
            if(code in self.kiwoom.code_list):
                price=self.kiwoom.code_list[code]['price']
                item=QTableWidgetItem(price)
                self.tableWidget_4.setItem(index,1,item)
                rate=self.kiwoom.code_list[code]['rate']
                item=QTableWidgetItem(rate)
                self.tableWidget_4.setItem(index,2,item)
                vp=self.kiwoom.code_list[code]['vp']
                item=QTableWidgetItem(vp)
                self.tableWidget_4.setItem(index,3,item)
                
                self.sell_stock.update(code,price,rate,vp)
                self.buy_stock.update(code,price,rate,vp)

                #if float(vp)>100 and float(rate)>15:
                #    if code not in self.buy_list:
                #        self.buy_list.update({code})
                #        self.buy_stock.append(code,price,rate,vp)

    def interesting_stock(self):
        self.kiwoom.set_code_name()
        self.set_real_reg_code_list=[]
        con=sqlite3.connect("네이버검색상위.db")
        cursor=con.cursor() 
        in_text="select distinct title from searchtop where date>'{0}' and rate>15".format(time.strftime('%Y-%m-%d'))
        cursor.execute(in_text)
        
        index=0
        for row in cursor:
            if(row[0] in self.kiwoom.kospi_name_list): #name으로 code번호를 찾는 for문 테이블4에 이름하고 코드를 적는다 
                item=QTableWidgetItem(row[0])
                self.tableWidget_4.setItem(index,0,item)
                code_index=self.kiwoom.kospi_name_list.index(row[0]) 
                item=QTableWidgetItem(self.kiwoom.kospi_code_list[code_index])
                self.set_real_reg_code_list.append(self.kiwoom.kospi_code_list[code_index])
                self.tableWidget_4.setItem(index,4,item)
                index=index+1
        con.commit()
        con.close()

        self.lineEdit_3.setText(time.strftime('%Y-%m-%d'))
        cnt=0
        for code in self.set_real_reg_code_list:
            if(cnt==0):
                self.kiwoom.set_real_reg("1000",code,"9001:302;10;11;25;12;13","0")
            else:
                self.kiwoom.set_real_reg("1000",code,"9001:302;10;11;25;12;13","1")
            cnt=cnt+1

    def code_changed(self):
        code=self.lineEdit.text()
        name=self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):#수동으로 주문하기
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
            self.accel_code_set.update({code})

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

            
            self.sell_stock.update(code,price,accel_rate,vp_rate)
            self.buy_stock.update(code,price,accel_rate,vp_rate)

            if float(vp_rate)>100 and float(accel_rate)>15:
                if code not in self.buy_list:
                    self.buy_list.update({code})
                    self.buy_stock.append(code,price,accel_rate,vp_rate)

    def update_naver_stock(self):
        import 네이버금융크롤링
        self.interesting_stock()
        self.lineEdit_4.setText("로딩완료")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()