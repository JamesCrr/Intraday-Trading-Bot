from datetime import datetime, timedelta
from avdata import AVData, AVDATAINDEX, AVDATATRAVERSE, MACDINDEX
from account import TradeAccount
import time
import pytz
import enum

class TRADEDETAILS(enum.Enum):
    StartingBalance = "startBalance"
    TradeCount = "count"

class TRADESTRATEGY(enum.Enum):
    RSI_MACD = "RSI & MACD"

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

        i_TotalTradeCount = 0
        f_StartBalance = self.TradeAccount.GetTotalFunds()
        dict_Results = None
        # Fetch Equity Data
        for EquityName in self.TradeAccount.GetSelectedEquityNames():
            self.AVData.FetchEquityData(EquityName, True)
            dict_Results = self.__Trade_RSI_MACD(EquityName)
            i_TotalTradeCount += dict_Results[TRADEDETAILS.TradeCount]
            # break
        
        print("================  End of Day  =================")
        print("Starting Balance : " + str(f_StartBalance))
        print("Ending Balance   : " + str(self.TradeAccount.GetTotalFunds()))
        print("Total Trades     : " + str(i_TotalTradeCount))
        print("Total Gain $     : " + str(self.TradeAccount.GetTotalFunds() - f_StartBalance))
        print("Total Gain %     : " + str(((self.TradeAccount.GetTotalFunds()-f_StartBalance)/f_StartBalance)*100.0)  + " %")
        print("===============================================")

        # prevDate = datetime.strptime("2020-07-2 16:0:00", self.AVData.str_DateTimeFormat)
        # dict_Result = self.AVData.GetNewTradingDate_Dictionary(prevDate, -5)
        # print("NewDate: " + dict_Result[AVDATATRAVERSE.NewDate.value].strftime(self.AVData.str_DateTimeFormat))

        # dayprices = self.AVData.GetDayPrices(self.AVData.dt_LatestDataTime)
        # for k, v in dayprices.items():
        #     print(k + " | " + str(v))

        # prevDate = datetime.strptime("2020-07-2 16:0:00", self.AVData.str_DateTimeFormat)
        # prevprices = self.AVData.GetPreviousDatePrices(prevDate, 5)
        # for k, v in prevprices.items():
        #     print(k + " | " + str(v))
        

    def __MarketStillOpen(self):
        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        datetimeStr_NY = datetime_NY.strftime(self.AVData.str_DateTimeFormat)
        print("NYC Time: " + datetimeStr_NY)
        
        datetimeStr_NY = datetimeStr_NY.split()
        hour_NY = int((datetimeStr_NY[1])[:2])
        if hour_NY < 16 and hour_NY > 8:
            return True

    def __Trade_RSI_MACD(self, str_EquityName):
        # Print Opening
        self.__PrintTradeOpening(str_EquityName, TRADESTRATEGY.RSI_MACD)
        b_Bought = False
        i_TradeCount = 0
        i_BeforeBalance = self.TradeAccount.GetTotalFunds()
        dict_DayPrices = self.AVData.GetDayPrices(self.AVData.dt_LatestDataTime)
        i_DateIndex = len(dict_DayPrices) - 1
        if self.TradeAccount.GetEquityEntryPrice(str_EquityName) != 0.0:
            b_Bought = True
        # Go through all Prices in Day
        for key, value in dict_DayPrices.items():
            f_RSI = self.AVData.FetchRSI(key, i_DateIndex)
            dict_MACD = self.AVData.FetchMACD(key, i_DateIndex)

            if b_Bought == False:
                # Buy
                if f_RSI > 35 and dict_MACD[MACDINDEX.Histogram.value] > 0:
                    continue
                self.TradeAccount.SetEquityEntryPrice(str_EquityName, float(value))
                i_TradeCount += 1
                b_Bought = True
            else:
                # Sell
                if f_RSI < 65 or dict_MACD[MACDINDEX.Histogram.value] < 0:
                    continue
                self.TradeAccount.SetEquityFundStake(str_EquityName, float(value))
                i_TradeCount += 1
                b_Bought = False
            i_DateIndex -= 1
            
        # Print Closing
        self.__PrintTradeClosing(str_EquityName, i_BeforeBalance, i_TradeCount)
        dict_TradeDetails = dict()
        dict_TradeDetails[TRADEDETAILS.StartingBalance] = i_BeforeBalance
        dict_TradeDetails[TRADEDETAILS.TradeCount] = i_TradeCount
        return dict_TradeDetails

    def __PrintTradeOpening(self, str_EquityName, enum_TradeStrategy):
        print("*************  Trade Start  ***************")
        print("Fetching [" + str_EquityName + "] Equity Data")
        print("Now Trading          :   " + str_EquityName + " || " + enum_TradeStrategy.value)
        print("Please Hold...")
    def __PrintTradeClosing(self, str_EquityName, i_InitialBalance, i_TradeCount):
        print("**************  Trade End  ****************")
        print("Balance BEFORE trade : " + str(i_InitialBalance))
        print("Balance AFTER trade  : " + str(self.TradeAccount.GetTotalFunds()))
        print("Trade Count          : " + str(i_TradeCount))
        print("Trade Gain $         : " + str(self.TradeAccount.GetTotalFunds() - i_InitialBalance))
        print("Trade Gain %         : " + str(((self.TradeAccount.GetTotalFunds()-i_InitialBalance)/i_InitialBalance)*100.0)  + " %")
        print("*******************************************\n")


if __name__ == "__main__":
    tb = TradeBot()
    tb.StartProgram()