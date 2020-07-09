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

        self.__StateMainMenu()
        
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
        
    def __Trade_RSI_MACD(self, str_EquityName):
        # Print Opening
        self.__PrintTradeOpening(str_EquityName, TRADESTRATEGY.RSI_MACD)
        b_Bought = False
        i_TradeCount = 0
        i_BeforeBalance = self.TradeAccount.GetEquityFundStake(str_EquityName)
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
                f_EntryPrice = self.TradeAccount.GetEquityEntryPrice(str_EquityName)
                f_FundStake = self.TradeAccount.GetEquityFundStake(str_EquityName)
                f_PercentageDiff = float(value) / f_EntryPrice
                f_FundStake *= f_PercentageDiff
                self.TradeAccount.SetEquityFundStake(str_EquityName, f_FundStake)
                i_TradeCount += 1
                b_Bought = False
            i_DateIndex -= 1
            
        # Print Closing
        self.__PrintTradeClosing(str_EquityName, i_BeforeBalance, i_TradeCount)
        dict_TradeDetails = dict()
        dict_TradeDetails[TRADEDETAILS.StartingBalance] = i_BeforeBalance
        dict_TradeDetails[TRADEDETAILS.TradeCount] = i_TradeCount
        return dict_TradeDetails

    def __GetNYCTime(self):
        tz_NYC = pytz.timezone('America/New_York') 
        dt_NYC = datetime.now(tz_NYC)
        str_NYC = dt_NYC.strftime(self.AVData.str_DateTimeFormat)
        return str_NYC
    def __MarketStillOpen(self):
        str_NYC = self.__GetNYCTime()
        str_NYC = str_NYC.split()
        hour_NY = int((str_NYC[1])[:2])
        if hour_NY < 16 and hour_NY > 8:
            return True
        return False

    def __PrintTradeOpening(self, str_EquityName, enum_TradeStrategy):
        print("*************  Trade Start  ***************")
        print("Fetching [" + str_EquityName + "] Equity Data")
        print("Now Trading          :   " + str_EquityName + " || " + enum_TradeStrategy.value)
        print("Please Hold...")
    def __PrintTradeClosing(self, str_EquityName, i_InitialBalance, i_TradeCount):
        print("**************  Trade End  ****************")
        print("Balance BEFORE trade : " + str(i_InitialBalance))
        print("Balance AFTER trade  : " + str(self.TradeAccount.GetEquityFundStake(str_EquityName)))
        print("Trade Count          : " + str(i_TradeCount))
        print("Trade Gain $         : " + str(self.TradeAccount.GetEquityFundStake(str_EquityName) - i_InitialBalance))
        print("Trade Gain %         : " + str(((self.TradeAccount.GetEquityFundStake(str_EquityName)-i_InitialBalance)/i_InitialBalance)*100.0)  + " %")
        print("*******************************************\n")
    def __PrintStateOpening(self, str_StateName):
        print("\n[------- " + str_StateName + " -------]")
    def __PrintStateClosing(self, str_StateName):
        i_Length = len(str_StateName)
        str_Dashes = ""
        for index in range(i_Length):
            str_Dashes += "-"
        print("[--------" + str_Dashes + "--------]")
    def __PrintAccountDetails(self):
        list_Equities = self.TradeAccount.GetSelectedEquityNames()
        f_AvailableFunds = self.TradeAccount.GetRemainderFunds()
        print("Total Funds      : " + str(self.TradeAccount.GetTotalFunds()))
        print("Available Funds  : " + str(f_AvailableFunds))
        print("Current Equities : ")
        for index in range(len(list_Equities)):
            print("(" + str(index + 1) + ") " + list_Equities[index] + " || " + str(self.TradeAccount.GetEquityFundStake(list_Equities[index])))

    def __StateMainMenu(self):
        str_StateName = "Menu"
        self.__PrintStateOpening(str_StateName)
        print("NYC Time: " + self.__GetNYCTime())
        b_MarketStillOpen = self.__MarketStillOpen()
        if b_MarketStillOpen:
            print("[1] Real-Time Trade")
        else:
            print("[̶1̶]̶ ̶R̶e̶a̶l̶-̶T̶i̶m̶e̶ ̶T̶r̶a̶d̶e̶")
        print("[2] Simulate-Past-Day Trade")
        print("[3] Settings")
        print("[4] Exit")
        self.__PrintStateClosing(str_StateName)

        i_Result = self.__GetIntRangeInput(1,4)
        if i_Result == 1:
            if not b_MarketStillOpen:
                while i_Result == 1:
                    print("Market is already closed..")
                    i_Result = self.__GetIntRangeInput(1,4)
            else:
                self.__StartTrading_RealTime()
        if i_Result == 2:
            self.__StartTrading_SimulatePastDay()
        elif i_Result == 3:
            self.__StateSettings()
    def __StateSettings(self):
        str_StateName = "Settings"
        self.__PrintStateOpening(str_StateName)
        print("[1] Inject Funds")
        print("[2] Change Equity Traded")
        print("[3] Change Equity Fund Amount")
        print("[4] Back")
        self.__PrintStateClosing(str_StateName)
        
        i_Result = self.__GetIntRangeInput(1,4)
        if i_Result == 1:
           self.__StateSettings_ModifyFunds()
        if i_Result == 2:
            self.__StateSettings_ChangeEquityTraded()
        elif i_Result == 3:
            self.__StateSettings_ChangeEquityFund()
        elif i_Result == 4:
            self.__StateMainMenu()
    def __StateSettings_ModifyFunds(self):
        f_RemovableFunds = self.TradeAccount.GetRemainderFunds()
        print("Total Funds      : " + str(self.TradeAccount.GetTotalFunds()))
        print("Removable Funds  : " + str(f_RemovableFunds))
        print("How much new Funds to Inject?")
        f_Result = self.__GetPositiveFloatInput()
        f_Result = round(f_Result, 1)
        self.TradeAccount.ModifyTotalFunds(f_Result)
        print("Total Funds      : " + str(self.TradeAccount.GetTotalFunds()))
        print("Removable Funds  : " + str(f_RemovableFunds + f_Result))
        # Return to Settings
        print("")
        self.__StateSettings()
    def __StateSettings_ChangeEquityTraded(self):
        list_Equities = self.TradeAccount.GetSelectedEquityNames()
        self.__PrintAccountDetails()
        print("Select Equity to Change")
        i_EquityToChange = self.__GetIntRangeInput(1, len(list_Equities))
        str_OldEquity = list_Equities[i_EquityToChange-1]
        str_NewEquity = ""
        while True:
            try:
                str_NewEquity = input("Enter new Equity Symbol  : ")
            except ValueError:
                print("Please enter a valid Input.")
                continue
            # Check if new equity Exists
            str_NewEquity = str_NewEquity.upper()
            if self.AVData.FetchEquityData(str_NewEquity, False) == False:
                print("[" + str_NewEquity + "] not trading in NYSE.")
                continue
            break
        # Confirmation
        print("Replacing [" + str_OldEquity + "] with [" + str_NewEquity + "]")
        b_YesNo = self.__GetConfirmationInput()
        if b_YesNo == False:
            print("")
            self.__StateSettings()
        self.TradeAccount.ReplaceEquity(str_OldEquity, str_NewEquity)
        # Print out new Results
        self.__PrintAccountDetails()
        # Return to Settings
        print("")
        self.__StateSettings()
    def __StateSettings_ChangeEquityFund(self):
        list_Equities = self.TradeAccount.GetSelectedEquityNames()
        f_AvailableFunds = self.TradeAccount.GetRemainderFunds()
        self.__PrintAccountDetails()
        print("Select Equity to Change")
        i_EquityToChange = self.__GetIntRangeInput(1, len(list_Equities))
        str_SelectedEquity = list_Equities[i_EquityToChange-1]
        f_OldAmount = self.TradeAccount.GetEquityFundStake(str_SelectedEquity)
        print("Select new Fund Amount for " + str_SelectedEquity + ".")
        print("(Amount >= 0 AND Amount <= " + str(f_AvailableFunds + f_OldAmount) + ")")
        f_NewAmount = self.__GetPositiveFloatInput()
        while f_NewAmount > f_AvailableFunds + f_OldAmount:
            print("Not enough Available Funds")
            print("Select a lower amount.")
            f_NewAmount = self.__GetPositiveFloatInput()
        f_NewAmount = round(f_NewAmount, 1)
        print("Changing " + str(f_OldAmount) + " to " + str(f_NewAmount))
        self.TradeAccount.SetEquityFundStake_NotSale(str_SelectedEquity, f_NewAmount)
        self.__PrintAccountDetails()
        # Return to Settings
        print("")
        self.__StateSettings()

    def __GetIntRangeInput(self, i_MinInclusive, i_MaxInclusive):
        str_Prompt = "Enter number [" + str(i_MinInclusive) + ".." + str(i_MaxInclusive) + "]: "
        i_value = 0
        while True:
            try:
                i_value = int(input(str_Prompt))
            except ValueError:
                print("Please enter a valid Input.")
                continue
            if i_value < i_MinInclusive or i_value > i_MaxInclusive:
                print("Please enter Input within range.")
                continue
            break
        return i_value
    def __GetPositiveFloatInput(self):
        str_Prompt = "Enter Positive number: "
        f_value = 0
        while True:
            try:
                f_value = float(input(str_Prompt))
            except ValueError:
                print("Please enter a valid Input.")
                continue
            if f_value < 0:
                print("Please enter a Positive number.")
                continue
            break
        return f_value
    def __GetConfirmationInput(self):
        str_YesNo = ""
        while True:
            try:
                str_YesNo = input("Confirm [y/n]: ")
            except ValueError:
                print("Please enter a valid Input.")
                continue
            str_YesNo = str_YesNo.lower()
            if str_YesNo == "y" or str_YesNo == "n":
                break
            else:
                print("Please enter a valid Input.")
        if str_YesNo == "y":
            return True
        return False

if __name__ == "__main__":
    tb = TradeBot()
    tb.StartProgram()