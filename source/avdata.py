from datetime import datetime, timedelta
import time
import enum

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

class AVDataTraverse(enum.Enum):
    NewDate = "newDate"
    Index = "index"
class MACDIndex(enum.Enum):
    MACDLine = "diff"
    SignalLine = "signal"
    Histogram = "hist"
class AVDataIndex(enum.Enum):
    Open = "1. open"
    High = "2. high"
    Low = "3. low"
    Close = "4. close"
    Volume = "5. volume"
# Data from API Timing typical range runs from 9:31 to 16:0
class AVData:
    def __init__(self):
        self.ts = TimeSeries(key='4ZXG1S4Z055LPBAW')
        self.str_DateTimeFormat = "%Y-%m-%d %H:%M:%S"
        self.str_IntervalTime = "1min"      # 1, 5, 15, 30, 60 are supported
        self.apiData = None
        self.dt_LatestDataTime = None
        self.dt_AVTimeLowerBounds = datetime.strptime("9:31:0", '%H:%M:%S')
        self.dt_AVTimeUpperBounds = datetime.strptime("16:0:0", '%H:%M:%S')
        # self.dict_EMA = None

    def FetchEquityData(self, str_Name, b_FullSize):
        print("============  API Call  ===============")
        print("Fetching [" + str_Name + "] Equity Data")
        # Full Market data or just Latest
        # Get json object with the intraday data and another with the call's metadata
        if b_FullSize:
            self.apiData, meta_data = self.ts.get_intraday(symbol=str_Name, interval=self.str_IntervalTime, outputsize="full")
        else:
            self.apiData, meta_data = self.ts.get_intraday(symbol=str_Name, interval=self.str_IntervalTime, outputsize="compact")
        
        # Get latest time from data
        newTime = list(self.apiData.keys())[0] 
        self.dt_LatestDataTime = datetime.strptime(newTime, self.str_DateTimeFormat)
        newTime = newTime.split()
        print("Latest Time from API: " + str(newTime[0]) + " " + str(newTime[1]))
        print("=======================================\n")

    def FetchRSI(self, str_Date, i_DateIndex, i_Period = 14):
        i_Intervaltime = self.__GetIntervalTimingInt()
        dict_DateResult = self.__GetNewTradingDate_Dictionary(None, -i_Intervaltime * i_Period, i_DateIndex)
        dt_SelectedDate = dict_DateResult[AVDataTraverse.NewDate.value] 
        f_AverageGains = 0.0
        f_AverageLosts = 0.0
        f_PriceDiff = 0.0
        i_AddedCounter = 0
        # Calculate Initial i_Period day Avg Gain/Loss
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_Period-1)
        list_PrevPricesKeys = list(dict_PrevPrices.keys())
        for index, value in enumerate(list_PrevPricesKeys):
            if index == 0:
                continue
            f_PriceDiff = dict_PrevPrices[value] - dict_PrevPrices[list_PrevPricesKeys[index-1]]
            if f_PriceDiff > 0:
                f_AverageGains += f_PriceDiff
                i_AddedCounter += 1
            elif f_PriceDiff < 0:
                f_AverageLosts += -f_PriceDiff
                i_AddedCounter += 1
        f_AverageGains /= i_AddedCounter
        f_AverageLosts /= i_AddedCounter
        # Subsequent calculations uses prior averages
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_Period)
        list_PrevPricesKeys = list(dict_PrevPrices.keys())
        for index, value in enumerate(list_PrevPricesKeys):
            if index == 0:
                continue
            f_PriceDiff = dict_PrevPrices[value] - dict_PrevPrices[list_PrevPricesKeys[index-1]]
            if f_PriceDiff > 0:
                f_AverageGains = (f_AverageGains*(i_Period-1)+f_PriceDiff)/i_Period
                f_AverageLosts = (f_AverageLosts*(i_Period-1))/i_Period
            elif f_PriceDiff < 0:
                f_AverageLosts = (f_AverageLosts*(i_Period-1)+(-f_PriceDiff))/i_Period
                f_AverageGains = (f_AverageGains*(i_Period-1))/i_Period
        # Calculate Final RSI
        f_RS = f_AverageGains / f_AverageLosts
        f_RSI = 100.0 - (100.0/(1.0+f_RS))
        return f_RSI

    def FetchMACD(self, str_Date, i_DateIndex, i_FastPeriod = 12, i_SlowPeriod = 26, i_SignalPeriod = 9):
        dict_MACD = dict()
        i_Intervaltime = self.__GetIntervalTimingInt()
        dict_DateResult = self.__GetNewTradingDate_Dictionary(None, -i_Intervaltime * i_SignalPeriod, i_DateIndex)
        dt_SelectedDate = dict_DateResult[AVDataTraverse.NewDate.value]
        # Signal SMA
        f_SignalEMA = 0.0
        f_Smoother = 2 / (i_SignalPeriod + 1)
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_SignalPeriod, False)
        for key, value in dict_PrevPrices.items():
            f_SignalEMA += (self.FetchEMA(key, i_FastPeriod)-self.FetchEMA(key, i_SlowPeriod))
        f_SignalEMA /= len(dict_PrevPrices)
        # Signal EMA
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_SignalPeriod)
        for key, value in dict_PrevPrices.items():
            f_EMADiff = self.FetchEMA(key, i_FastPeriod)-self.FetchEMA(key, i_SlowPeriod)
            f_SignalEMA = (f_EMADiff - f_SignalEMA) * f_Smoother + f_SignalEMA
        # Record
        dict_MACD[MACDIndex.MACDLine.value] = self.FetchEMA(str_Date, i_FastPeriod) - self.FetchEMA(str_Date, i_SlowPeriod)
        dict_MACD[MACDIndex.SignalLine.value] = f_SignalEMA
        dict_MACD[MACDIndex.Histogram.value] = dict_MACD[MACDIndex.MACDLine.value] - f_SignalEMA
        return dict_MACD


    def FetchEMA(self, str_Date, i_Period):
        i_Intervaltime = self.__GetIntervalTimingInt()
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dict_DateResult = self.__GetNewTradingDate_Dictionary(dt_SelectedDate, -i_Intervaltime * i_Period)
        dt_SelectedDate = dict_DateResult[AVDataTraverse.NewDate.value]
        # Calculate SMA
        f_SMA = 0.0
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_Period, False)
        for key, value in dict_PrevPrices.items():
            f_SMA += value
        f_SMA /= len(dict_PrevPrices)
        f_Smoother = 2 / (i_Period + 1)
        # Calculate EMA
        f_EMA = f_SMA
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_Period)
        for key, value in dict_PrevPrices.items():
            f_EMA = (value - f_EMA) * f_Smoother + f_EMA
        return f_EMA

    def GetDayPrices(self, dt_Date):
        # Prices only in that Day
        str_CurrDate = dt_Date.strftime(self.str_DateTimeFormat)
        str_CurrDate = str_CurrDate.split()
        str_TempDate = ""
        i_Intervaltime = self.__GetIntervalTimingInt()
        list_APIDataKeys = list(self.apiData.keys())
        datePrices = dict()
        for index, value in enumerate(list_APIDataKeys):
            str_TempDate = value.split()
            if str_TempDate[0] == str_CurrDate[0]:
                datePrices[value] = self.apiData[value][AVDataIndex.Close.value]
            else:
                break
        return datePrices

    def GetPreviousDatePrices(self, dt_Date, i_Range, b_AttachCurrentDate = True):
        datePrices = dict()
        dict_DateResult = self.__GetNewTradingDate_Dictionary(dt_Date, -(i_Range+1))
        dt_SelectedDate = dict_DateResult[AVDataTraverse.NewDate.value]
        str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
        i_Intervaltime = self.__GetIntervalTimingInt()
        # Prices before dt_Date
        # Loop through all Previous dates
        for index in range(i_Range):
            dict_DateResult = self.__GetNewTradingDate_Dictionary(dt_SelectedDate, i_Intervaltime, dict_DateResult[AVDataTraverse.Index.value])
            dt_SelectedDate = dict_DateResult[AVDataTraverse.NewDate.value]
            str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
            datePrices[str_SelectedDate] = float(self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value])
        # Attach dt_Date into back of Dictionary?
        if b_AttachCurrentDate == False:
            return datePrices
        # Current Date
        dt_SelectedDate = dt_Date
        str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
        datePrices[str_SelectedDate] = float(self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value])
        return datePrices

    def __GetIntervalTimingInt(self):
        timing = self.str_IntervalTime.split("min")
        return int(timing[0])

    def __GetNewTradingDate_Dictionary(self, dt_OldDate, i_TraverseCount, i_StartingIndex = -1):
        dict_Result = dict()
        list_APIDataKeys = list(self.apiData.keys())
        if i_StartingIndex < 0:
            str_OldDate = dt_OldDate.strftime(self.str_DateTimeFormat)
            if str_OldDate in self.apiData is None:
                return None
            i_StartingIndex = list_APIDataKeys.index(str_OldDate)
        i_StartingIndex -= i_TraverseCount
        if i_StartingIndex < 0:
            return None
        dt_NewDate = datetime.strptime(list_APIDataKeys[i_StartingIndex], self.str_DateTimeFormat)
        dict_Result[AVDataTraverse.NewDate.value] = dt_NewDate
        dict_Result[AVDataTraverse.Index.value] = i_StartingIndex 
        return dict_Result
        
    