from datetime import datetime, timedelta
import pytz
import time
import enum
import os
import json

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

from dotenv import load_dotenv
load_dotenv()

dateStrFormat = "%Y-%m-%d %H:%M:%S"
accFundStr = "funds"
accComStr = "coms"
accComFundPercentStr = "fundPercent"
accComSharesLeftStr = "sharesLeft"
accComSharesPriceStr = "sharesPrice"


class AVDataIndex(enum.Enum):
    Open = "1. open"
    High = "2. high"
    Low = "3. low"
    Close = "4. close"
    Volume = "5. volume"
class AVData:
    def __init__(self):
        self.ts = TimeSeries(key=os.environ.get("ALPHA_VANTAGE_KEY"))
        self.ti = TechIndicators(key=os.environ.get("ALPHA_VANTAGE_KEY"))
        self.apiData = dict()
        self.latestData_Time = None
        self.latestData_Price = dir({})
        self.rsiData = dict()

    def FetchAPIData(self, selectedCompanySymbol, fullSize):
        print("Fetching Data from API..")
        # Want full Market data or just latest
        # Get json object with the intraday data and another with the call's metadata
        if fullSize:
            fullApiData, meta_data = self.ts.get_intraday(symbol=selectedCompanySymbol, interval="1min", outputsize="full")
            # # Trim off other days
            # prevDay = datetime.strptime(next(iter(fullApiData.keys())), dateStrFormat)
            # prevDay = prevDay.replace(hour=0,minute=0,second=0)
            # currDay = None
            # for key, value in fullApiData.items():
            #    currDay = datetime.strptime(key, dateStrFormat)
            #    currDay = currDay.replace(hour=0,minute=0,second=1)
            #    if currDay < prevDay:
            #         break
            #    self.apiData[key] = value
            self.apiData = fullApiData
        else:
            self.apiData, meta_data = self.ts.get_intraday(symbol=selectedCompanySymbol, interval="1min", outputsize="compact")
        
        # Get latest time from data
        newTime = list(self.apiData.keys())[0] 
        self.latestData_Time = datetime.strptime(newTime, dateStrFormat)
        self.latestData_Price = list(self.apiData.values())[0]
        newTime = newTime.split()
        print("Latest Time from API: " + str(newTime[0]) + " " + str(newTime[1]))
        # print("Current Prices: ", self.latestData_Price)
        # print (self.latestData_Price[AVDataIndex.Open.value])

    def FetchRSI(self, selectedCompanySymbol, rsiDate, period = 14):
        # Check if key already exists
        if rsiDate in self.rsiData:
            return self.rsiData[rsiDate]
        # Declare vars
        firstTotalGains = 0.0
        firstTotalLoss = 0.0
        firstSampleRange = period * 5
        secondSampleRange = period
        lastRecordedDate = ""
        previousPrices = self.GetPrice_Previous(rsiDate, firstSampleRange + secondSampleRange)
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
            lastRecordedDate = keyList[index]
        
        # # Get Total Gain and Loss
        # previousPrices = self.GetPrice_Previous(rsiDate, period)
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

        # Check if date valid
        if rsiDate in self.rsiData:
            return self.rsiData[rsiDate]
        else:
           return self.rsiData[lastRecordedDate]

    def FetchEMA(self, selectedCompanySymbol, emaDate, period = 10):
        # Declare vars
        ema = 0.0
        smaPeriod = 10  # Applies an 18.18% weighting to the most recent price
        multipler = 2 / (period + 1)
        previousPrices = self.GetPrice_Previous(emaDate, period + smaPeriod)
        keyList=sorted(previousPrices.keys())
        # Find Initial EMA first by using SMA
        recordedPriceCounter = 0
        for index, keyValue in enumerate(keyList):
            if index == smaPeriod:
                break
            if previousPrices[keyValue] is None:
                continue
            ema += float(previousPrices[keyValue][AVDataIndex.Close.value])
            recordedPriceCounter += 1
        ema = ema / recordedPriceCounter
        # Calculate target day EMA using Initial EMA
        for index in range(smaPeriod, len(previousPrices)):
            if previousPrices[keyList[index]] is None:
                continue
            ema = ((float(previousPrices[keyList[index]][AVDataIndex.Close.value]) - ema) * multipler) + ema
        # Return EMA
        return ema 

    def FetchMACDLine(self, selectedCompanySymbol, macdDate, shortTermEMAPeriod = 12, longTermEMAPeriod = 26):
        macdLine = self.FetchEMA(selectedCompanySymbol, macdDate, shortTermEMAPeriod) - self.FetchEMA(selectedCompanySymbol, macdDate, longTermEMAPeriod)
        return macdLine

    def GetDayPrices(self, selectedCompanySymbol, dayStr):
        currDay = datetime.strptime(dayStr, dateStrFormat)
        currDay = currDay.replace(hour=16,minute=0,second=0)
        currDayStr = currDay.strftime(dateStrFormat)
        if currDay in self.apiData:
            return None

        datePrices = dict()
        datePrices[currDayStr] = self.apiData.get(currDayStr)
        while currDay.hour != 9 or currDay.minute != 30:
            currDay = currDay - timedelta(minutes=1)
            currDayStr = currDay.strftime(dateStrFormat)
            if self.apiData.get(currDayStr) is None:
                continue
            datePrices[currDayStr] = self.apiData.get(currDayStr)
        # return Prices only in that Day 
        return datePrices
    def GetPrice_NextPrevious(self, centerDate, scopeRange = 0):
        if self.apiData.get(centerDate) == None:
            return None
        selectedDates = dict()
        selectedDates[centerDate] = self.apiData.get(centerDate)
        if scopeRange > 0:
            currDate = datetime.strptime(centerDate, dateStrFormat)
            newDate = currDate
            newDateStr = ""
            # Forward Days
            for d in range(scopeRange):
                if newDate.hour == 16:
                    if newDate.weekday() == 4:
                        newDate = newDate + timedelta(days=3)
                    else:
                        newDate = newDate + timedelta(days=1)
                    newDate = newDate.replace(hour=9, minute=31, second=0)
                else:
                    newDate = newDate + timedelta(minutes=1)
                newDateStr = newDate.strftime(dateStrFormat)
                if self.apiData.get(newDateStr) == None:
                    break
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)
            # Previous Days
            newDate = currDate
            for d in range(scopeRange):
                if newDate.hour == 9 and newDate.minute == 31:
                    if newDate.weekday() == 0:
                        newDate = newDate - timedelta(days=3)
                    else:
                        newDate = newDate - timedelta(days=1)
                    newDate = newDate.replace(hour=16, minute=0, second=0)
                else:
                    newDate = newDate - timedelta(minutes=1)
                newDateStr = newDate.strftime(dateStrFormat)
                if self.apiData.get(newDateStr) == None:
                    break
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)
        return selectedDates
    def GetPrice_Previous(self, firstDate, previousRange = 0):
        if self.apiData.get(firstDate) is None:
            return None
        selectedDates = dict()
        selectedDates[firstDate] = self.apiData.get(firstDate)
        if previousRange > 0:
            currDate = datetime.strptime(firstDate, dateStrFormat)
            newDate = currDate
            newDateStr = ""
            # Previous Days
            for d in range(previousRange):
                if newDate.hour == 9 and newDate.minute == 31:
                    if newDate.weekday() == 0:
                        newDate = newDate - timedelta(days=3)
                    else:
                        newDate = newDate - timedelta(days=1)
                    newDate = newDate.replace(hour=16, minute=0, second=0)
                else:
                    newDate = newDate - timedelta(minutes=1)
                # Check date exists in API
                newDateStr = newDate.strftime(dateStrFormat)
                if self.apiData.get(newDateStr) is None:
                    # If date missing, fill in None
                    selectedDates[newDateStr] = None
                else:
                    selectedDates[newDateStr] = self.apiData.get(newDateStr)

        return selectedDates

class VirtualTrading:
    def __init__(self):
        self.account = dict()
        self.companiesFromAccount = []
        rootDirPath = os.path.dirname(os.getcwd())
        print(os.getcwd())
        self.dataDirPath = os.path.join(os.getcwd(), "data")
        self.dataFilePath = os.path.join(os.getcwd(), "data", "accountInfo.json")
        self.AVData = AVData()

    def StartProgram(self):

        if not self.LoadFromFile():
            self.CreateNewAccount()

        if self.MarketStillOpen():
            self.StartTrading_RealTime()
        else:
            print("Market is already Closed.")
            self.StartTrading_SimulatePastDay()
        
        print("Exiting Program..")

    def StartTrading_RealTime(self):
        selectedCompanyKey = self.companiesFromAccount[0]
        selectedPercent = self.account[accComStr][selectedCompanyKey][accComFundPercentStr] / 100.0
        startingBalance = self.account[accFundStr]
        bought = False
        entryPrice = 0.0
        if self.account[accComStr][selectedCompanyKey][accComSharesLeftStr] > 0:
            bought = True
            entryPrice = self.account[accComStr][selectedCompanyKey][accComSharesPriceStr]

        print("Starting Balance: $" + str(startingBalance))
        currFunds = self.account[accFundStr] * selectedPercent
        transactionCounter = 0

        while(self.AVData.latestData_Time.hour < 16):
            self.FetchAPIData(selectedCompanyKey, False)
            if self.AVData.latestData_Time.hour == 16:
                break
            # Evaluate Prices 
            for key, value in self.AVData.apiData.items():
                if bought:
                    # Decide when to sell
                    if self.AVData.FetchRSI(selectedCompanyKey, key) < 70:
                        continue
                    if self.AVData.FetchMACDLine(selectedCompanyKey, key) > 0:
                        continue
                    bought = False
                    transactionCounter += 1
                    currFunds = currFunds * (float(value[AVDataIndex.Close.value])/entryPrice)
                else:
                    # Decide when to buy
                    if self.AVData.FetchRSI(selectedCompanyKey, key) > 30:
                        continue
                    # if self.AVData.FetchMACDLine(selectedCompanyKey, key) < 0:
                    #     continue
                    bought = True
                    entryPrice = float(value[AVDataIndex.Close.value])
                    transactionCounter += 1
                # Don't evaluate previous prices
                break
            # Sleep for 60s bfr fetching new data
            time.sleep(60)
        print("Final Balance: $" + str(self.account[accFundStr]))
        print("Transaction Count: " + str(transactionCounter))
        print("Net Gain: " + str(1-self.account[accFundStr]/startingBalance) + "%")
        self.SaveToFile()
        print("Market has Closed.")
        

    def StartTrading_SimulatePastDay(self):
        selectedCompanyKey = self.companiesFromAccount[0]
        selectedPercent = self.account[accComStr][selectedCompanyKey][accComFundPercentStr] / 100.0
        startingBalance = self.account[accFundStr]
        bought = False
        entryPrice = 0.0
        if self.account[accComStr][selectedCompanyKey][accComSharesLeftStr] > 0:
            bought = True
            entryPrice = self.account[accComStr][selectedCompanyKey][accComSharesPriceStr]

        self.AVData.FetchAPIData(selectedCompanyKey,True)
        print("Starting Balance: $" + str(startingBalance))
        todayPrices = self.AVData.GetDayPrices(selectedCompanyKey, self.AVData.latestData_Time.strftime(dateStrFormat))
        currFunds = self.account[accFundStr] * selectedPercent
        transactionCounter = 0
        for key, value in sorted(todayPrices.items()):
            if bought:
                # Decide when to sell
                if self.AVData.FetchRSI(selectedCompanyKey, key) < 70:
                    continue
                if self.AVData.FetchMACDLine(selectedCompanyKey, key) > 0:
                    continue
                bought = False
                transactionCounter += 1
                currFunds = currFunds * (float(value[AVDataIndex.Close.value])/entryPrice)
            else:
                # Decide when to buy
                if self.AVData.FetchRSI(selectedCompanyKey, key) > 30:
                    continue
                # if self.AVData.FetchMACDLine(selectedCompanyKey, key) < 0:
                #     continue
                bought = True
                entryPrice = float(value[AVDataIndex.Close.value])
                transactionCounter += 1
        # Record down shares left in market
        if bought:
            self.account[accComStr][selectedCompanyKey][accComSharesLeftStr] = 1
            self.account[accComStr][selectedCompanyKey][accComSharesPriceStr] = entryPrice
        self.account[accFundStr] = currFunds
        print("Final Balance: $" + str(self.account[accFundStr]))
        print("Transaction Count: " + str(transactionCounter))
        # print("Net Gain: " + str(1-self.account[accFundStr]/startingBalance) + "%")
        print("Net Gain: " + str(((self.account[accFundStr]-startingBalance)/startingBalance)*100) + "%")
        self.SaveToFile()
        # selectedDates = self.AVData.GetPrice_Previous("2020-05-22 09:31:00", 3)
        # for key, value in sorted(selectedDates.items()):
            # ownRSI = self.AVData.FetchRSI("WIX", key)
            # print(key + " / " + value[AVDataIndex.Close.value] + " / RSI: " + str(ownRSI))

        # strTime = '2020-05-22 16:00:00'
        # ownRSI = self.AVData.FetchRSI("WIX", strTime)
        # print(strTime + ": " + str(ownRSI))
        # strTime = '2020-05-22 15:24:00'
        # ownRSI = self.AVData.FetchRSI("WIX", strTime)
        # print(strTime + ": " + str(ownRSI))
        # strTime = '2020-05-22 10:26:00'
        # ownRSI = self.AVData.FetchRSI("WIX", strTime)
        # print(strTime + ": " + str(ownRSI))

        # strTime = '2020-05-22 15:00:00'
        # MACDLine = self.AVData.FetchMACDLine("WIX", strTime)
        # print(strTime + " MACDLine: " + str(MACDLine))

    def MarketStillOpen(self):
        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        datetimeStr_NY = datetime_NY.strftime(dateStrFormat)
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
        # print("Saving Account Info..")
        with open(self.dataFilePath, 'w+') as outFile:
            json.dump(self.account, outFile)
        # print("Account Saved")
        return True
    def LoadFromFile(self):
        if os.path.exists(self.dataDirPath) == False:
            print("Unable to find accountInfo.json file under: " + self.dataDirPath)
            print("Aborting Load")
            return False
        with open(self.dataFilePath) as jsonFile:
            self.account = json.load(jsonFile)
        for key, value in self.account[accComStr].items():
            self.companiesFromAccount.append(key)
        return True
    def CreateNewAccount(self):
        print("Creating new account")
        self.account = dict()
        self.account[accFundStr] = 10000
        self.account[accComStr] = dict()
        self.account[accComStr]["WIX"] = dict()
        self.account[accComStr]["WIX"][accComFundPercentStr] = 100
        self.account[accComStr]["WIX"][accComSharesLeftStr] = 0
        self.account[accComStr]["WIX"][accComSharesPriceStr] = 0
        for key, value in self.account[accComStr].items():
            self.companiesFromAccount.append(key)

        if os.path.exists(self.dataDirPath) == False:
            os.mkdir(self.dataDirPath)
        with open(self.dataFilePath, 'w+') as outFile:
            json.dump(self.account, outFile)
        print("New Account made with inital fund of: $" + str(self.account[accFundStr]))

if __name__ == "__main__":
    vt = VirtualTrading()
    vt.StartProgram()
    