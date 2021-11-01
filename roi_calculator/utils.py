import yfinance as yf


def ticker_info(ticker):
    return yf.Ticker(ticker).info
