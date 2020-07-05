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
        self.str_IntervalTime = "1min" # 1, 5, 15, 30, 60 are supported
        self.apiData = None
        self.dt_LatestDataTime = None
        # Technical Indicators
        self.rsiData = None


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
                datePrices[str_SelectedDate] = self.apiData.get(str_TempDate)[AVDataIndex.Close.value]
            else:
                datePrices[str_SelectedDate] = self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value]
        # Current Date doesn't exist
        dt_SelectedDate = dt_Date
        str_SelectedDate = dt_SelectedDate.strftime(self.str_DateTimeFormat)
        datePrices[str_SelectedDate] = 0
        if self.apiData.get(str_SelectedDate) is None:
            dt_TempDate = self.__GetPreviousValidAPIDate(dt_Date)
            str_TempDate = dt_TempDate.strftime(self.str_DateTimeFormat)
            datePrices[str_SelectedDate] = self.apiData.get(str_TempDate)[AVDataIndex.Close.value]
        else:
            datePrices[str_SelectedDate] = self.apiData.get(str_SelectedDate)[AVDataIndex.Close.value]
        
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
    