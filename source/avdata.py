from datetime import datetime, timedelta
import time
import enum

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

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

    def FetchRSI(self, str_Date, i_Period = 14):
        i_Intervaltime = self.__GetIntervalTimingInt()
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dt_SelectedDate = self.__GetNewTradingDate(dt_SelectedDate, -i_Intervaltime * i_Period, True)
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

    def FetchMACD(self, str_Date, i_FastPeriod = 12, i_SlowPeriod = 26, i_SignalPeriod = 9):
        dict_MACD = dict()
        i_Intervaltime = self.__GetIntervalTimingInt()
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dt_SelectedDate = self.__GetNewTradingDate(dt_SelectedDate, -i_Intervaltime * i_SignalPeriod, True)
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
        dt_SelectedDate = self.__GetNewTradingDate(dt_SelectedDate, -i_Intervaltime * i_Period, True)
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

    # def CalculateLatestEMA(self):
    #     f_SMA = 0.0
    #     i_SMALength = 100
    #     i_EMALength = 450
    #     i_Intervaltime = self.__GetIntervalTimingInt()
    #     dt_SelectedDate = self.__GetNewTradingDate(self.dt_LatestDataTime, -i_Intervaltime * i_EMALength, True)
    #     # Calculate SMA
    #     dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_SMALength, False)
    #     for key, value in dict_PrevPrices.items():
    #         f_SMA += value
    #     f_SMA /= i_SMALength
    #     f_Smoother = 2 / (i_EMALength + 1)
    #     # Calculate EMA
    #     self.dict_EMA = dict()
    #     f_EMA = f_SMA
    #     dt_SelectedDate = self.dt_LatestDataTime
    #     dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_EMALength)
    #     for key, value in dict_PrevPrices.items():
    #         self.dict_EMA[key] = value
    #         f_EMA = (value - f_EMA) * f_Smoother + f_EMA
    #         # print(key + ": " + str(value))
    #     return

    def GetDayPrices(self, dt_Date):
        dt_CurrDate = dt_Date
        dt_CurrDate = dt_CurrDate.replace(hour=9,minute=31,second=0)
        str_CurrDate = dt_CurrDate.strftime(self.str_DateTimeFormat)
        i_Intervaltime = self.__GetIntervalTimingInt()
        # Prices only in that Day 
        datePrices = dict()
        datePrices[str_CurrDate] = self.apiData.get(str_CurrDate)[AVDataIndex.Close.value]
        while dt_CurrDate.hour != 16 or dt_CurrDate.minute != 0:
            # Fetch prices
            dt_CurrDate = self.__GetNewTradingDate(dt_CurrDate, i_Intervaltime)
            str_CurrDate = dt_CurrDate.strftime(self.str_DateTimeFormat)
            # Current Date doesn't exist
            if self.apiData.get(str_CurrDate) is None:
                dt_TempDate = self.__GetPreviousValidAPIDate(dt_CurrDate)
                str_TempDate = dt_TempDate.strftime(self.str_DateTimeFormat)
                # Replace Current Date value with Previous Date value
                datePrices[str_CurrDate] = self.apiData.get(str_TempDate)[AVDataIndex.Close.value]
            # Date exists   
            else:
                datePrices[str_CurrDate] = self.apiData.get(str_CurrDate)[AVDataIndex.Close.value]
        return datePrices

    def GetPreviousDatePrices(self, dt_Date, i_Range, b_AttachCurrentDate = True):
        datePrices = dict()
        dt_SelectedDate = self.__GetNewTradingDate(dt_Date, -(i_Range+1), True)
        str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
        i_Intervaltime = self.__GetIntervalTimingInt()
        # Prices before dt_Date
        # Loop through all Previous dates
        for index in range(i_Range):
            dt_SelectedDate = self.__GetNewTradingDate(dt_SelectedDate, i_Intervaltime, True)
            str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
            # Date not valid
            if self.apiData.get(str_SelectedDate) is None:
                dt_TempDate = self.__GetPreviousValidAPIDate(dt_SelectedDate)
                str_TempDate = dt_TempDate.strftime(self.str_DateTimeFormat)
                datePrices[str_SelectedDate] = float(self.apiData.get(str_TempDate)[AVDataIndex.Close.value])
            else:
                datePrices[str_SelectedDate] = float(self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value])
        # Attach dt_Date into back of Dictionary?
        if b_AttachCurrentDate == False:
            return datePrices
        # Current Date doesn't exist
        dt_SelectedDate = dt_Date
        str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
        datePrices[str_SelectedDate] = 0.0
        if self.apiData.get(str_SelectedDate) is None:
            dt_TempDate = self.__GetPreviousValidAPIDate(dt_Date)
            str_TempDate = dt_TempDate.strftime(self.str_DateTimeFormat)
            datePrices[str_SelectedDate] = float(self.apiData.get(str_TempDate)[AVDataIndex.Close.value])
        else:
            datePrices[str_SelectedDate] = float(self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value])
        
        return datePrices

    def __GetIntervalTimingInt(self):
        timing = self.str_IntervalTime.split("min")
        return int(timing[0])
    
    def __GetNewTradingDate(self, dt_OldDate, i_MinuteModifiy, b_AttachOverflowed = False):
        dt_NewDate = dt_OldDate
        dt_NewDate = dt_OldDate + timedelta(minutes=i_MinuteModifiy)
        dt_Diff = dt_NewDate
        # Check if Time out of Bounds
        if dt_NewDate.time() < self.dt_AVTimeLowerBounds.time():
            # 30 instead of 31, to keep account for 9:30 to 16:0 conversion
            dt_Diff = dt_Diff.replace(hour=9,minute=30,second=0)
            dt_Diff = dt_Diff - dt_NewDate
            dt_NewDate = dt_NewDate.replace(hour=16,minute=0,second=0)
            # Attach Overflowed minutes
            if b_AttachOverflowed:
                dt_NewDate = dt_NewDate - timedelta(minutes=dt_Diff.seconds/60)
            # Check for Weekends
            if dt_NewDate.weekday() == 0:
                dt_NewDate = dt_NewDate - timedelta(days=3)
            else:
                dt_NewDate = dt_NewDate - timedelta(days=1)
        elif dt_NewDate.time() > self.dt_AVTimeUpperBounds.time():
            dt_Diff = dt_Diff.replace(hour=16,minute=0,second=0)
            dt_Diff = dt_NewDate - dt_Diff
            dt_NewDate = dt_NewDate.replace(hour=9,minute=30,second=0)
            # Attach Overflowed minutes
            if b_AttachOverflowed:
                dt_NewDate = dt_NewDate + timedelta(minutes=dt_Diff.seconds/60)
            # Check for Weekends
            if dt_NewDate.weekday() == 4:
                dt_NewDate = dt_NewDate + timedelta(days=3)
            else:
                dt_NewDate = dt_NewDate + timedelta(days=1)

        return dt_NewDate

    def __GetPreviousValidAPIDate(self, dt_InvalidDate):
        dt_validDate = dt_InvalidDate
        str_validDate = dt_validDate.strftime(self.str_DateTimeFormat)
        i_Intervaltime = self.__GetIntervalTimingInt()
        # Find Date that exists in API Data
        while self.apiData.get(str_validDate) is None:
            dt_validDate = self.__GetNewTradingDate(dt_validDate, -i_Intervaltime)
            str_validDate = dt_validDate.strftime(self.str_DateTimeFormat)
        return dt_validDate
    