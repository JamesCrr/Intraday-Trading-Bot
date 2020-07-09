import os
import json

str_AccTotalFunds = "totalFunds"
str_AccTotalEquities = "totalEquities"
str_EquityEntryPrice = "entryPrice"
str_EquityFundStake = "fundStake"

class TradeAccount:
    def __init__(self):
        self.dict_Account = None
        self.__str_dataFileName = "account-info.json"
        self.__str_dataDirPath = os.path.join(os.getcwd(), "data")
        self.__str_dataFilePath = os.path.join(os.getcwd(), "data", self.__str_dataFileName)

    def ModifyTotalFunds(self, f_Amount):
        self.dict_Account[str_AccTotalFunds] += f_Amount
    def GetTotalFunds(self):
        return self.dict_Account[str_AccTotalFunds]
    def GetRemainderFunds(self):
        f_takenFunds = 0.0
        for key, value in self.dict_Account[str_AccTotalEquities].items():
            f_takenFunds += value[str_EquityFundStake]
        return round(self.GetTotalFunds() - f_takenFunds, 1)
    def ReplaceEquity(self, str_OldEquityName, str_NewEquityName):
        del self.dict_Account[str_AccTotalEquities][str_OldEquityName]
        self.dict_Account[str_AccTotalEquities][str_NewEquityName] = dict()
        self.dict_Account[str_AccTotalEquities][str_NewEquityName][str_EquityEntryPrice] = 0.0
        self.dict_Account[str_AccTotalEquities][str_NewEquityName][str_EquityFundStake] = 0.0
    def GetSelectedEquityNames(self):
        list_SelectedEquities = list()
        for key, value in self.dict_Account[str_AccTotalEquities].items():
            list_SelectedEquities.append(key)
        return list_SelectedEquities

    def GetEquityEntryPrice(self, str_Name):
        if self.dict_Account[str_AccTotalEquities].get(str_Name) is None:
            return 0
        return self.dict_Account[str_AccTotalEquities][str_Name][str_EquityEntryPrice]
    def GetEquityFundStake(self, str_Name):
        if self.dict_Account[str_AccTotalEquities].get(str_Name) is None:
            return 0
        return self.dict_Account[str_AccTotalEquities][str_Name][str_EquityFundStake]
    def SetEquityEntryPrice(self, str_Name, f_NewValue):
        if self.dict_Account[str_AccTotalEquities].get(str_Name) is None:
            return False
        self.dict_Account[str_AccTotalEquities][str_Name][str_EquityEntryPrice] = f_NewValue
        return True
    def SetEquityFundStake(self, str_Name, f_NewValue):
        if self.dict_Account[str_AccTotalEquities].get(str_Name) is None:
            return False
        # Deduct from Total fund
        self.dict_Account[str_AccTotalFunds] -= self.dict_Account[str_AccTotalEquities][str_Name][str_EquityFundStake]
        self.dict_Account[str_AccTotalEquities][str_Name][str_EquityFundStake] = f_NewValue
        # Add back to Total fund to reflect change in price
        self.dict_Account[str_AccTotalFunds] += self.dict_Account[str_AccTotalEquities][str_Name][str_EquityFundStake]
        return True
    def SetEquityFundStake_NotSale(self, str_Name, f_NewValue):
        if self.dict_Account[str_AccTotalEquities].get(str_Name) is None:
            return False
        self.dict_Account[str_AccTotalEquities][str_Name][str_EquityFundStake] = f_NewValue
        return True

    def SaveToFile(self):
        if os.path.exists(self.__str_dataFilePath) == False:
            print("Unable to find " + self.__str_dataFileName + " under: " + self.__str_dataDirPath)
            print("Aborting Save..")
            return False
        with open(self.__str_dataFilePath, 'w+') as outFile:
            json.dump(self.dict_Account, outFile)
        print("Data Saved")
        return True

    def LoadFromFile(self):
        if os.path.exists(self.__str_dataFilePath) == False:
            print("Unable to find " + self.__str_dataFileName + " under: " + self.__str_dataDirPath)
            print("Aborting Load..")
            return False
        with open(self.__str_dataFilePath) as jsonFile:
            self.dict_Account = json.load(jsonFile)
        return True

    def CreateNewAccount(self):
        print("Creating new account")
        self.dict_Account = dict()
        self.dict_Account[str_AccTotalFunds] = 1000.0
        self.dict_Account[str_AccTotalEquities] = dict()

        list_DefaultEquities = ["WIX", "IBM", "APRN"]
        for name in list_DefaultEquities:
            self.dict_Account[str_AccTotalEquities][name] = dict()
            self.dict_Account[str_AccTotalEquities][name][str_EquityEntryPrice] = 0.0
            self.dict_Account[str_AccTotalEquities][name][str_EquityFundStake] = 250.0

        if os.path.exists(self.__str_dataDirPath) == False:
            os.mkdir(self.__str_dataDirPath)
        with open(self.__str_dataFilePath, 'w+') as outFile:
            json.dump(self.dict_Account, outFile)
        print("New Account created with inital funds of: $" + str(self.dict_Account[str_AccTotalFunds]))

    