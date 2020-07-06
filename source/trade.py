from datetime import datetime, timedelta
from avdata import AVData, AVDataIndex, MACDIndex
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

        f_RSI = 0.0
        dict_MACD = None
        f_PreviousMACD = 0.0
        b_Bought = False
        i_TradeCount = 0
        i_TotalTradeCount = 0
        f_StartBalance = self.TradeAccount.GetTotalFunds()
        # Fetch Equity Data
        for EquityName in self.TradeAccount.GetSelectedEquityNames():
            self.AVData.FetchEquityData(EquityName, True)
            # self.AVData.CalculateLatestEMA()
            if self.TradeAccount.GetEquityEntryPrice(EquityName) != 0.0:
                b_Bought = True
            print("Now Trading -> " + EquityName + " \nPlease Hold...")
            i_BeforeBalance = self.TradeAccount.GetTotalFunds()
            i_TradeCount = 0

            # Go through all Prices in Day
            for key, value in self.AVData.GetDayPrices(self.AVData.dt_LatestDataTime).items():
                f_RSI = self.AVData.FetchRSI(key)
                dict_MACD = self.AVData.FetchMACD(key)

                if b_Bought == False:
                    # Buy
                    if f_RSI > 35:
                        continue
                    self.TradeAccount.SetEquityEntryPrice(EquityName, float(value))
                    i_TradeCount += 1
                    b_Bought = True
                else:
                    # Sell
                    if f_RSI < 65:
                        continue
                    self.TradeAccount.SetEquityFundStake(EquityName, float(value))
                    i_TradeCount += 1
                    b_Bought = False
            
            print("**********  Trade End  **********")
            print("Balance BEFORE trade : " + str(i_BeforeBalance))
            print("Balance AFTER trade  : " + str(self.TradeAccount.GetTotalFunds()))
            print("Trade Counts         : " + str(i_TradeCount))
            print("Net Gain             : " + str(((self.TradeAccount.GetTotalFunds()-i_BeforeBalance)/i_BeforeBalance)*100.0)  + " %")
            print("*********************************\n")
            i_TotalTradeCount += i_TradeCount
            # break
        
        print("============  End of Day  =============")
        print("Starting Balance : " + str(f_StartBalance))
        print("Ending Balance   : " + str(self.TradeAccount.GetTotalFunds()))
        print("Trade Counts     : " + str(i_TotalTradeCount))
        print("Net Gain         : " + str(((self.TradeAccount.GetTotalFunds()-f_StartBalance)/f_StartBalance)*100.0)  + " %")
        print("=======================================")
        # dayprices = self.AVData.GetDayPrices(self.AVData.dt_LatestDataTime)
        # for k, v in dayprices.items():
        #     print(k + " | " + str(v))

        # prevDate = datetime.strptime("2020-07-2 16:0:00", self.AVData.str_DateTimeFormat)
        # prevprices = self.AVData.GetPreviousDatePrices(prevDate, 5)
        # for k, v in prevprices.items():
        #     print(k + " | " + str(v))
        
        # olddate = datetime.strptime("2020-07-2 16:0:00", self.AVData.str_DateTimeFormat)
        # newdate = self.AVData.GetNewTradingDate(olddate, -391, True)
        # print("OldDate: " + olddate.strftime(self.AVData.str_DateTimeFormat) + " NewDate: " + newdate.strftime(self.AVData.str_DateTimeFormat))

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