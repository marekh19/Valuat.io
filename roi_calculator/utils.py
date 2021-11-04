import yfinance as yf


def valuation_dictionary(ticker):
    # Data from yf info method
    basic_info = yf.Ticker(ticker).info
    if basic_info['regularMarketPrice'] == None:
        return None

    # Data from yf balance_sheet method
    balance_sheet = yf.Ticker(ticker).balancesheet
    total_stockholders_equity = balance_sheet.loc['Total Stockholder Equity'][0]
    # Data from yf earnings method
    quarterly_earnings = yf.Ticker(ticker).quarterly_earnings
    ytd_earnings = year_to_date_earnings(quarterly_earnings)
    eps = earnings_per_share(
        ytd_earnings, basic_info['sharesOutstanding'])
    pe_ratio = price_earnings_ratio(basic_info['regularMarketPrice'], eps)
    roe = return_on_equity(ytd_earnings, total_stockholders_equity)
    ticker_fundamentals = {
        'symbol': basic_info['symbol'],
        'price': basic_info['regularMarketPrice'],
        'shares_outstanding': basic_info['sharesOutstanding'],
        'payout_ratio': basic_info['payoutRatio'],
        'ytd_earnings': ytd_earnings,
        'eps': eps,
        'pe_ratio': pe_ratio,
        'roe': roe
    }
    return ticker_fundamentals


def year_to_date_earnings(quarterly_earnings):
    return quarterly_earnings['Earnings'].sum()


def earnings_per_share(quarterly_earnings, shares_outstanding):
    return quarterly_earnings / shares_outstanding


def price_earnings_ratio(price, eps):
    return price / eps


def return_on_equity(earnings, equity):
    return earnings / equity
