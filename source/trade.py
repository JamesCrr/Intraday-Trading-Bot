from datetime import datetime, timedelta
from avdata import AVData, AVDataIndex
from account import TradeAccount
import time
import pytz

class TradeBot:
    def __init__(self):
        self.TradeAccount = TradeAccount()
        self.AVData = AVData()

    def StartProgram(self):
        # Load Account Info here..
        if self.TradeAccount.LoadFromFile() == False:
            self.TradeAccount.CreateNewAccount()

        if self.__MarketStillOpen():
            self.__StartTrading_RealTime()
        else:
            print("Market is already Closed.")
            self.__StartTrading_SimulatePastDay()
        
        print("Exiting Program..")

    def __StartTrading_RealTime(self):
        return

    def __StartTrading_SimulatePastDay(self):

        for name in self.TradeAccount.GetSelectedEquityNames():
            self.AVData.FetchEquityData(name, True)
            break
        
        # dayprices = self.AVData.GetDayPrices(self.AVData.dt_LatestDataTime)
        # for k, v in dayprices.items():
        #     print(k + " | " + str(v))

        # prevDate = datetime.strptime("2020-07-2 16:0:00", self.AVData.str_DateTimeFormat)
        # prevprices = self.AVData.GetPreviousDatePrices(prevDate, 5)
        # for k, v in prevprices.items():
        #     print(k + " | " + str(v))
        
        # olddate = datetime.strptime("2020-07-6 16:0:00", self.AVData.str_DateTimeFormat)
        # newdate = self.AVData.GetNewTradingDate(olddate, 7)
        # print(newdate.strftime(self.AVData.str_DateTimeFormat))

    def __MarketStillOpen(self):
        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        datetimeStr_NY = datetime_NY.strftime(self.AVData.str_DateTimeFormat)
        print("NYC Time: " + datetimeStr_NY)
        
        datetimeStr_NY = datetimeStr_NY.split()
        hour_NY = int((datetimeStr_NY[1])[:2])
        if hour_NY < 16 and hour_NY > 8:
            return True

    

if __name__ == "__main__":
    tb = TradeBot()
    tb.StartProgram()