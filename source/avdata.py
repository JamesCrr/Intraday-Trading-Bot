from datetime import datetime, timedelta
import time
import enum

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

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


    def FetchEquityData(self, str_Name, b_FullSize):
        print("Fetching " + str_Name + " Equity Data..")
        # Full Market data or just Latest
        # Get json object with the intraday data and another with the call's metadata
        if b_FullSize:
            fullApiData, meta_data = self.ts.get_intraday(symbol=str_Name, interval=self.str_IntervalTime, outputsize="full")
            self.apiData = fullApiData
        else:
            self.apiData, meta_data = self.ts.get_intraday(symbol=str_Name, interval=self.str_IntervalTime, outputsize="compact")
        
        # Get latest time from data
        newTime = list(self.apiData.keys())[0] 
        self.dt_LatestDataTime = datetime.strptime(newTime, self.str_DateTimeFormat)
        newTime = newTime.split()
        print("Latest Time from API: " + str(newTime[0]) + " " + str(newTime[1]))

    def FetchRSI(self, str_Date, i_period = 14):
        i_Intervaltime = self.__GetIntervalTimingInt()
        dt_SelectedDate = datetime.strptime(str_Date, self.str_DateTimeFormat)
        dt_SelectedDate = self.__GetNewTradingDate(dt_SelectedDate, -i_Intervaltime * i_period, True)
        f_AverageGains = 0.0
        f_AverageLosts = 0.0
        f_PriceDiff = 0.0
        i_AddedCounter = 0
        # Calculate Initial i_period day Avg Gain/Loss
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_period-1)
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
        dict_PrevPrices = self.GetPreviousDatePrices(dt_SelectedDate, i_period)
        list_PrevPricesKeys = list(dict_PrevPrices.keys())
        for index, value in enumerate(list_PrevPricesKeys):
            if index == 0:
                continue
            f_PriceDiff = dict_PrevPrices[value] - dict_PrevPrices[list_PrevPricesKeys[index-1]]
            if f_PriceDiff > 0:
                f_AverageGains = (f_AverageGains*(i_period-1)+f_PriceDiff)/i_period
                f_AverageLosts = (f_AverageLosts*(i_period-1))/i_period
            elif f_PriceDiff < 0:
                f_AverageLosts = (f_AverageLosts*(i_period-1)+(-f_PriceDiff))/i_period
                f_AverageGains = (f_AverageGains*(i_period-1))/i_period
        # Calculate Final RSI
        f_RS = f_AverageGains / f_AverageLosts
        f_RSI = 100 - (100/(1+f_RS))
        return f_RSI

    def GetDayPrices(self, dt_Date):
        dt_CurrDate = dt_Date
        dt_CurrDate = dt_CurrDate.replace(hour=9,minute=31,second=0)
        str_CurrDate = dt_CurrDate.strftime(self.str_DateTimeFormat)
        i_Intervaltime = self.__GetIntervalTimingInt()
        # Prices only in that Day 
        datePrices = dict()
        datePrices[str_CurrDate] = self.apiData.get(str_CurrDate)
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

    def GetPreviousDatePrices(self, dt_Date, i_Range):
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
        i_MinDiff = 0
        # Check if Time out of Bounds
        if dt_NewDate.hour == 9 and dt_NewDate.minute < 31:
            # 30 instead of 31, to keep account for 9:30 to 16:0 conversion
            i_MinDiff = 30 - dt_NewDate.minute
            dt_NewDate = dt_NewDate.replace(hour=16,minute=0,second=0)
            # Attach Overflowed minutes
            if b_AttachOverflowed:
                dt_NewDate = dt_NewDate - timedelta(minutes=i_MinDiff)
            # Check for Weekends
            if dt_NewDate.weekday() == 0:
                dt_NewDate = dt_NewDate - timedelta(days=3)
            else:
                dt_NewDate = dt_NewDate - timedelta(days=1)
        elif dt_NewDate.hour == 16 and dt_NewDate.minute > 0:
            i_MinDiff = dt_NewDate.minute
            dt_NewDate = dt_NewDate.replace(hour=9,minute=30,second=0)
            # Attach Overflowed minutes
            if b_AttachOverflowed:
                dt_NewDate = dt_NewDate + timedelta(minutes=i_MinDiff)
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
    