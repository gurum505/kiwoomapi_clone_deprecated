import sys
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
import time
import sqlite3
from pytrader import *

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        #self.mywindow=MyWindow()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)#send_order response
        self.OnReceiveRealData.connect(self._receive_real_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret                   

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):#SendOrder(주문발생) -> OnReceiveTRData(주문응답) -> OnReceiveMsg(주문메세지수신) -> OnReceiveChejan(주문접수/체결)
        #print(gubun)
        print("매도/매수:",self.get_chejan_data(906))
        print("종목명:",self.get_chejan_data(302))
        print("호가구분:",self.get_chejan_data(905))
        print("체결수량:",self.get_chejan_data(911))
        print("체결가:",self.get_chejan_data(910))
        print("종목코드:",self.get_chejan_data(9001))
        #2테이블기준으로 906 302 905(지정가 시장가...) 911 910 
        """
        FID	설명
        9203	주문번호
        302	종목명
        900	주문수량
        901	주문가격
        902	미체결수량
        904	원주문번호
        905	주문구분
        908	주문/체결시간
        909	체결번호
        910	체결가
        911	체결량
        10	현재가, 체결가, 실시간종가
        """

    def change_format(data):#잔고 등 0000--변환
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'

        try:
            format_data = format(int(strip_data), ',d')
        except:
            format_data = format(float(strip_data))

        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    def change_format2(data): #수익률변환
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname =="opw00001_req":
            self._opw00001(rqname,trcode)
        elif rqname =="opw00018_req":
            self._opw00018(rqname,trcode)
        elif rqname =="opt10027_req":
            self._opt10027(rqname,trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def get_server_gubun(self):#실투자와 모의투자때 받아들이는 데이터가 다르다 true시 ?
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def _opw00001(self, rqname, trcode):
        self.d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit=Kiwoom.change_format(self.d2_deposit)

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        if self.get_server_gubun(): #모의투자일때는 총수익률을 100으로 나눈뒤 출력
          total_earning_rate = float(total_earning_rate) / 100
          total_earning_rate = str(total_earning_rate)
            
        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_earning_rate))
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))
        
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")
            #
            code=self._comm_get_data(trcode, "", rqname, i, "종목번호")
            

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append(
                [name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate,code])

    def _receive_real_data(self,code,real_type,unused1):
        #실시간 데이터 받는거 정리:#체결강도이면228 #현재가10 #등락률 12 #종목명302
        """
        주식체결 실시간 데이터 예시]
          
          if(strRealType == _T("주식체결"))	// OnReceiveRealData 이벤트로 수신된 실시간타입이 "주식체결" 이면
          {
            strRealData = OpenAPI.GetCommRealData(strCode, 10);   // 현재가
            strRealData = OpenAPI.GetCommRealData(strCode, 13);   // 누적거래량
            strRealData = OpenAPI.GetCommRealData(strCode, 228);    // 체결강도
            strRealData = OpenAPI.GetCommRealData(strCode, 20);  // 체결시간
          }
          
        """
        if(real_type=='주식체결'): #다 받을 때  빈칸이 나오던데 주식체결이 아닌것들이다. 왜 이렇게 나오지?
            self.code_list.setdefault(code)
            self.code_list.update({code:{'price':0,'rate':0.00,'vp':0.00}}) 
    
            price=self._comm_get_real_data(code,10)#전일대비 하락이면 -가 붙어나오는것 같다
            rate=self._comm_get_real_data(code,12)
            vp=self._comm_get_real_data(code,228) 
            self.code_list[code]['price']=price
            self.code_list[code]['rate']=rate
            self.code_list[code]['vp']=vp
            #print(code)
            #print(self.code_list[code]['price'])
            #MyWindow().check_vp()
            #print(code,price,rate,vp) #왜이렇게 데이터가 많이 들어오지? 수정필요
       
         
    def set_real_reg(self,screen_no,code_list,fid_list,opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, int)", screen_no, code_list, fid_list, opt_type)#QString이 맞나? 리스트인데?
        #OpenAPI.SetRealReg(_T("0150"), _T("039490"), _T("9001;302;10;11;25;12;13"), "0");  // 039490종목만 실시간 등록#0새등록1추가등록
        #사용:set_real_reg('1001','039490','302;12;10;228')
    def _reset_real_data_output(self):
        self.code_list={}
    def _comm_get_real_data(self,code,fid):
        ret=self.dynamicCall("GetCommRealData(QString, int)",code,fid)#code는 QString fid는 int 위에 참조
        return ret
        

    def disconnect_real_data(self,screen_no):
        self.dynamicCall("DisConnectRealData(QString)",screen_no)
    def set_code_name(self):
        ret = self.dynamicCall("GetCodeListByMarket(QString)", ["0"])#코스피 0 코스닥 10
        self.kospi_code_list = ret.split(';')
        ret2=self.dynamicCall("GetCodeListByMarket(QString)", ["10"])#코스피 0 코스닥 10
        temp_list=ret2.split(";")
        self.kospi_code_list=self.kospi_code_list+temp_list
        self.kospi_name_list = []
        for x in self.kospi_code_list:
            name = self.dynamicCall("GetMasterCodeName(QString)", [x])
            self.kospi_name_list.append(name)
        
    def _opt10027(self,rqname,trcode):
        self.accel_rate=[]
        for i in range(20):#20수정가능
            rate=self._comm_get_data(trcode, "", rqname, i, "등락률")
            if(rate<"+15.00"): #15.00 수정가능
                continue
            price=self._comm_get_data(trcode, "", rqname, i, "현재가")
            name=self._comm_get_data(trcode, "", rqname, i, "종목명")
            code=self._comm_get_data(trcode, "", rqname, i, "종목코드")
            vp_rate=self._comm_get_data(trcode, "", rqname, i, "체결강도")
            self.accel_rate.append({"종목코드":code,"종목명":name,"현재가":price,"등락률":rate,"체결강도":vp_rate})
  

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]
    

    kiwoom.set_input_value("계좌번호", account_number)
    #kiwoom.set_real_reg("1000","003010","9001:302;10;11;25;12;13","0")
    #kiwoom.set_real_reg("1000","039490","9001:302;10;11;25;12;13","1")


    
    kiwoom.set_input_value("시장구분","000")#0전체 001코스피 101 코스닥
    kiwoom.set_input_value("정렬구분","1")#급등1 급락2
    #Kiwoom.set_input_value("시간구분","2")#분전 1 일전2
    #Kiwoom.set_input_value("시간","1")#일 혹은 분 입력 어떻게 입력하는거지?
    kiwoom.set_input_value("거래량조건","0000")#00000 전체
    kiwoom.set_input_value("종목조건","1")#1 관리종목제외
    kiwoom.set_input_value("신용조건","0")#0 전체
    kiwoom.set_input_value("가격조건","0")#0 전체
    kiwoom.set_input_value("상하한포함","0")#0 미포함
    kiwoom.set_input_value("거래량대금조건","0")#0 미포함

    kiwoom.comm_rq_data("opt10027_req","opt10027",0,"1101")#10분간격으로 가능한가?
