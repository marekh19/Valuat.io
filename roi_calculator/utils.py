import yfinance as yf


def valuation_dictionary(ticker):
    # Data from yf info method
    basic_info = yf.Ticker(ticker).info
    if basic_info['regularMarketPrice'] == None:
        return None
    symbol = basic_info['symbol']
    price = basic_info['regularMarketPrice']
    shares_outstanding = basic_info['sharesOutstanding']
    # Data from yf balance_sheet method
    total_stockholders_equity = total_stockholders_equity(ticker)
    # Data from yf earnings method
    # price_earnings_median =


def total_stockholders_equity(ticker):
    balance_sheet = yf.Ticker(ticker).balancesheet
    return balance_sheet.loc['Total Stockholder Equity'][0]


def price_earnings_median(ticker, shares_outstanding, price):
    earnings = yf.Ticker(ticker).earnings
    
