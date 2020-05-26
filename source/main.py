from datetime import datetime, timedelta
import pytz
import time
import enum
import os
import json

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

class AVDataIndex(enum.Enum):
    Open = "1. open"
    High = "2. high"
    Low = "3. low"
    Close = "4. close"
    Volume = "5. volume"
class AVData:
    def __init__(self):
        self.ts = TimeSeries(key='4ZXG1S4Z055LPBAW')
        self.ti = TechIndicators(key='4ZXG1S4Z055LPBAW')
        self.apiData = dict()
        self.latestData_Hour = 0
        self.latestData_Price = dir({})
        self.rsiData = dict()

    def FetchAPIData(self, selectedCompanySymbol, fullSize):
        # Want full Market data or just latest
        # Get json object with the intraday data and another with the call's metadata
        if fullSize:
            fullApiData, meta_data = self.ts.get_intraday(symbol=selectedCompanySymbol, interval="1min", outputsize="full")
            # # Trim off other days
            # prevDay = datetime.strptime(next(iter(fullApiData.keys())), "%Y-%m-%d %H:%M:%S")
            # prevDay = prevDay.replace(hour=0,minute=0,second=0)
            # currDay = None
            # for key, value in fullApiData.items():
            #    currDay = datetime.strptime(key, "%Y-%m-%d %H:%M:%S")
            #    currDay = currDay.replace(hour=0,minute=0,second=1)
            #    if currDay < prevDay:
            #         break
            #    self.apiData[key] = value
            self.apiData = fullApiData
        else:
            self.apiData, meta_data = self.ts.get_intraday(symbol=selectedCompanySymbol, interval="1min", outputsize="compact")
        

        # Getting first key and value in dictionary 
        newTime = list(self.apiData.keys())[0] 
        newTime = newTime.split()
        self.latestData_Hour = int((newTime[1])[:2])
        self.latestData_Price = list(self.apiData.values())[0]
        print("Latest Time from API: " + str(newTime[0]) + " " + str(newTime[1]))
        # print("Current Prices: ", self.latestData_Price)
        # print (self.latestData_Price[AVDataIndex.Open.value])

    def FetchRSI(self, selectedCompanySymbol, rsiDate, period = 14):
        if rsiDate in self.rsiData:
            return self.rsiData[rsiDate]
        # Declare vars
        firstTotalGains = 0.0
        firstTotalLoss = 0.0
        firstSampleRange = period * 5
        secondSampleRange = period
        previousPrices = self.GetDaysPrice_Previous(rsiDate, firstSampleRange + secondSampleRange)
        averageGain = 0.0
        averageLoss = 0.0
        currDayGain = 0.0
        currDayLoss = 0.0
        priceDiff = 0.0
        rs = 0.0
        # Find first part of RSI
        keyList=sorted(previousPrices.keys())
        for index, keyValue in enumerate(keyList):
            if index == firstSampleRange:
                break
            if previousPrices[keyValue] is None or previousPrices[keyList[index-1]] is None:
                continue
            priceDiff = float(previousPrices[keyValue][AVDataIndex.Close.value]) - float(previousPrices[keyList[index-1]][AVDataIndex.Close.value])
            if priceDiff > 0:
                firstTotalGains += priceDiff
            elif priceDiff < 0:
                firstTotalLoss += abs(priceDiff)
        averageGain = firstTotalGains / firstSampleRange
        averageLoss = firstTotalLoss / firstSampleRange
        # Second part of RSI
        for index in range(firstSampleRange, len(previousPrices)):
            if previousPrices[keyList[index]] is None or previousPrices[keyList[index-1]] is None:
                continue
            priceDiff = float(previousPrices[keyList[index]][AVDataIndex.Close.value]) - float(previousPrices[keyList[index-1]][AVDataIndex.Close.value])
            currDayGain = 0.0
            currDayLoss = 0.0
            if priceDiff > 0:
                currDayGain = priceDiff
            elif priceDiff < 0:
                currDayLoss = abs(priceDiff)
            averageGain = (averageGain*(secondSampleRange-1) + currDayGain) / secondSampleRange
            averageLoss = (averageLoss*(secondSampleRange-1) + currDayLoss) / secondSampleRange
            # Calculate RSI and set for values in period
            rs = averageGain / averageLoss
            self.rsiData[keyList[index]] = 100 - (100 / (1 + rs))
        
        # # Get Total Gain and Loss
        # previousPrices = self.GetDaysPrice_Previous(rsiDate, period)
        # keyList=sorted(previousPrices.keys())
        # for index, keyValue in enumerate(keyList):
        #     if index == 0:
        #         continue
        #     priceDiff = float(previousPrices[keyValue][AVDataIndex.Close.value]) - float(previousPrices[keyList[index-1]][AVDataIndex.Close.value])
        #     if index + 1 >= len(keyList):
        #         if priceDiff > 0:
        #             currDayGain += priceDiff
        #         elif priceDiff < 0:
        #             currDayLoss += -priceDiff
        #     else:
        #         if priceDiff > 0:
        #             averageGain += priceDiff
        #         elif priceDiff < 0:
        #             averageLoss += -priceDiff
        # # Calculate averages
        # averageGain = averageGain / period
        # averageLoss = averageLoss / period
        # rs = ((averageGain * (period-1) + currDayGain)/period) / ((averageLoss * (period-1) + currDayLoss)/period)
        # self.rsiData[rsiDate] = 100 - (100 / (1 + rs))

        # Return final Date's RSI
        return self.rsiData[rsiDate]

    def GetRSI(self, selectedCompanySymbol):
        data, meta_data = self.ti.get_rsi(symbol=selectedCompanySymbol, interval='1min', time_period=14)
        return data

    def GetMACD(self, selectedCompanySymbol):
        data, meta_data = self.ti.get_macd(symbol=selectedCompanySymbol, interval='1min')
        return data

    def GetDaysPrice_NextPrevious(self, centerDate, scopeRange = 0):
        if self.apiData.get(centerDate) == None:
            return None
        selectedDates = dict()
        selectedDates[centerDate] = self.apiData.get(centerDate)
        if scopeRange > 0:
            currDate = datetime.strptime(centerDate, "%Y-%m-%d %H:%M:%S")
            newDate = currDate
            newDateStr = ""
            # Forward Days
            for d in range(scopeRange):
                if newDate.hour == 16:
                    newDate = newDate + timedelta(days=1)
                    newDate = newDate.replace(hour=9, minute=31, second=0)
                else:
                    newDate = newDate + timedelta(minutes=1)
                newDateStr = newDate.strftime("%Y-%m-%d %H:%M:%S")
                if self.apiData.get(newDateStr) == None:
                    break
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)
            # Previous Days
            newDate = currDate
            for d in range(scopeRange):
                if newDate.hour == 9 and newDate.minute == 31:
                    newDate = newDate - timedelta(days=1)
                    newDate = newDate.replace(hour=16, minute=0, second=0)
                else:
                    newDate = newDate - timedelta(minutes=1)
                newDateStr = newDate.strftime("%Y-%m-%d %H:%M:%S")
                if self.apiData.get(newDateStr) == None:
                    break
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)
        return selectedDates
    def GetDaysPrice_Previous(self, firstDate, previousRange = 0):
        if self.apiData.get(firstDate) is None:
            return None
        selectedDates = dict()
        selectedDates[firstDate] = self.apiData.get(firstDate)
        if previousRange > 0:
            currDate = datetime.strptime(firstDate, "%Y-%m-%d %H:%M:%S")
            newDate = currDate
            newDateStr = ""
            # Previous Days
            for d in range(previousRange):
                if newDate.hour == 9 and newDate.minute == 31:
                    newDate = newDate - timedelta(days=1)
                    newDate = newDate.replace(hour=16, minute=0, second=0)
                else:
                    newDate = newDate - timedelta(minutes=1)
                # Check date exists in API
                newDateStr = newDate.strftime("%Y-%m-%d %H:%M:%S")
                if self.apiData.get(newDateStr) is None:
                    # If date missing, fill in None
                    selectedDates[newDateStr] = None
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)

        return selectedDates

class VirtualTrading:
    def __init__(self):
        self.account = dict()
        self.dataDirPath = os.path.join(os.getcwd(), "data")
        self.dataFilePath = os.path.join(os.getcwd(), "data", "accountInfo.json")
        self.AVData = AVData()

    def StartProgram(self):

        if not self.LoadFromFile():
            print("Creating new account")
            self.account = dict()
            self.account["funds"] = 10000
            self.CreateNewAccount()

        if self.MarketStillOpen():
            self.StartTrading_RealTime()
        else:
            print("Market is already Closed.")
            self.StartTrading_SimulatePastDay()
        
        print("Exiting Program..")

    def StartTrading_RealTime(self):

        # while(self.latestData_Hour < 16):
        #     self.FetchAPIData(False)
        #     if self.latestData_Hour >= 16:
        #         break
        #     # Evaluate Prices 
            
            
        #     # Sleep for 90s bfr fetching new data
        #     time.sleep(10)
        
        print("Market has Closed.")

    def StartTrading_SimulatePastDay(self):
        self.AVData.FetchAPIData("WIX",True)

        # for key, value in sorted(self.AVData.apiData.items()):
        #     print(key + " / " + value[AVDataIndex.Close.value])

        # selectedDates = self.AVData.GetDaysPrice_Previous("2020-05-22 09:31:00", 3)
        # for key, value in sorted(selectedDates.items()):
            # ownRSI = self.AVData.FetchRSI("WIX", key)
            # print(key + " / " + value[AVDataIndex.Close.value] + " / RSI: " + str(ownRSI))

        strTime = '2020-05-22 16:00:00'
        ownRSI = self.AVData.FetchRSI("WIX", strTime)
        print(strTime + ": " + str(ownRSI))
        strTime = '2020-05-22 15:24:00'
        ownRSI = self.AVData.FetchRSI("WIX", strTime)
        print(strTime + ": " + str(ownRSI))
        strTime = '2020-05-22 10:26:00'
        ownRSI = self.AVData.FetchRSI("WIX", strTime)
        print(strTime + ": " + str(ownRSI))

    def MarketStillOpen(self):
        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        datetimeStr_NY = datetime_NY.strftime("%Y-%m-%d %H:%M:%S")
        print("NY Time: " + datetimeStr_NY)
        
        datetimeStr_NY = datetimeStr_NY.split()
        hour_NY = int((datetimeStr_NY[1])[:2])
        if hour_NY < 16 and hour_NY > 8:
            return True
        else:
            return False
    def SaveToFile(self):
        if os.path.exists(self.dataDirPath) == False:
            print("Unable to find accountInfo.json file under: " + self.dataDirPath)
            print("Aborting Save")
            return False
        with open(self.dataFilePath, 'w+') as outFile:
            json.dump(self.account, outFile)
        return True
    def LoadFromFile(self):
        if os.path.exists(self.dataDirPath) == False:
            print("Unable to find accountInfo.json file under: " + self.dataDirPath)
            print("Aborting Load")
            return False
        with open(self.dataFilePath) as jsonFile:
            self.account = json.load(jsonFile)
        return True
    def CreateNewAccount(self):
        if os.path.exists(self.dataDirPath) == False:
            os.mkdir(self.dataDirPath)
        with open(self.dataFilePath, 'w+') as outFile:
            json.dump(self.account, outFile)
        print("New Account made with inital fund of: $" + str(self.account["funds"]))

if __name__ == "__main__":
    vt = VirtualTrading()
    vt.StartProgram()
    