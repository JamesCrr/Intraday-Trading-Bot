# Intraday Trading Bot
A Intraday Trading Bot that tries to use Technical Analysis to earn small profits on the Stock Market.\
**Real-Time** Stock prices are fetched from [here](https://www.alphavantage.co/).\
**NOTE:** 
- This is simply a simulation, it is **NOT** using real funds.
- It is using **Real** Stock prices for calculations. 

## Installation
### Setup
Download the project or<br /> Clone using
```
git clone https://github.com/JamesCrr/Intraday-Trading-Bot.git
```
### Install required packages
Make sure you have pipenv installed 
```
pip install pipenv
```
Install dependencies in the pipefile.
```
pipenv install
```
### Get your key and Create your .env
Get your own Key from [here](https://www.alphavantage.co/support/#api-key). Create your .env file at root and place your key
```
ALPHA_VANTAGE_KEY = YOUR KEY
```
### Run on Local machine
Start the Virtual Environment, then Run the python File
```
pipenv shell
python [Path to python File]
```
Or Run the python File outside the Virtual Environment
```
pipenv run python [Path to python File]
```


## Future possible todos
- [x] Menu to select different companies
- [ ] Menu to use different strategies
- [ ] Menu to use customise strategies