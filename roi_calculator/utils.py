import yfinance as yf
from .math_constants import THOUSAND as K, MILLION as M, HUNDRED as H
import statistics


def valuation_dictionary(ticker):
    # Data from yf info method
    basic_info = yf.Ticker(ticker).info
    if basic_info['regularMarketPrice'] == None:
        return None
    shares_outstanding_in_mil = basic_info['sharesOutstanding'] / M
    # Data from yf balance_sheet method
    quarterly_balance_sheet = yf.Ticker(ticker).quarterly_balancesheet
    balance_sheet = yf.Ticker(ticker).balancesheet
    earnings = yf.Ticker(ticker).earnings
    roe_4yrs_median = roe_4yrs_median(balance_sheet, earnings)
    total_stockholders_equity_in_mil = quarterly_balance_sheet.loc[
        'Total Stockholder Equity'][0] / M
    # Data from yf earnings method
    quarterly_earnings = yf.Ticker(ticker).quarterly_earnings
    ytd_earnings = year_to_date_earnings(quarterly_earnings)
    eps = earnings_per_share(
        ytd_earnings, shares_outstanding_in_mil)
    pe_ratio = price_earnings_ratio(basic_info['regularMarketPrice'], eps)
    roe = return_on_equity(ytd_earnings, total_stockholders_equity_in_mil)
    tse_per_share = total_stockholders_equity_per_share(
        total_stockholders_equity_in_mil, shares_outstanding_in_mil)
    ticker_fundamentals = {
        'name': basic_info['longName'],
        'symbol': basic_info['symbol'],
        'price': basic_info['regularMarketPrice'],
        'currency': basic_info['currency'],
        'shares_outstanding': shares_outstanding_in_mil,
        'payout_ratio': basic_info['payoutRatio'],
        'ytd_earnings': ytd_earnings,
        'eps': eps,
        'pe_ratio': pe_ratio,
        'roe': roe,
        'tse': total_stockholders_equity_in_mil,
        'tse_per_share': tse_per_share
    }
    return ticker_fundamentals


def year_to_date_earnings(quarterly_earnings):
    return quarterly_earnings['Earnings'].sum()


def earnings_per_share(quarterly_earnings, shares_outstanding):
    return quarterly_earnings / (shares_outstanding * M)


def price_earnings_ratio(price, eps):
    return price / eps if price / eps <= 25 else 25


def return_on_equity(earnings, equity):
    return (earnings / (equity * M)) * H


def total_stockholders_equity_per_share(tse, shares_outstanding):
    return tse / shares_outstanding


def seven_yrs_overview(fundamentals):
    year1 = [
        fundamentals['tse_per_share'],
        fundamentals['tse_per_share'] * fundamentals['roe'] / H,
        (fundamentals['tse_per_share'] * fundamentals['roe'] / H) * fundamentals['payout_ratio']
    ]
    year2 = [
        year1[0] + year1[1] - year1[2],
        ((year1[0] + year1[1] - year1[2]) * fundamentals['roe']) / H,
        (((year1[0] + year1[1] - year1[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    year3 = [
        year2[0] + year2[1] - year2[2],
        ((year2[0] + year2[1] - year2[2]) * fundamentals['roe']) / H,
        (((year2[0] + year2[1] - year2[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    year4 = [
        year3[0] + year3[1] - year3[2],
        ((year3[0] + year3[1] - year3[2]) * fundamentals['roe']) / H,
        (((year3[0] + year3[1] - year3[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    year5 = [
        year4[0] + year4[1] - year4[2],
        ((year4[0] + year4[1] - year4[2]) * fundamentals['roe']) / H,
        (((year4[0] + year4[1] - year4[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    year6 = [
        year5[0] + year5[1] - year5[2],
        ((year5[0] + year5[1] - year5[2]) * fundamentals['roe']) / H,
        (((year5[0] + year5[1] - year5[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    year7 = [
        year6[0] + year6[1] - year6[2],
        ((year6[0] + year6[1] - year6[2]) * fundamentals['roe']) / H,
        (((year6[0] + year6[1] - year6[2]) * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]
    return {
        '1': year1,
        '2': year2,
        '3': year3,
        '4': year4,
        '5': year5,
        '6': year6,
        '7': year7,
    }


def sum_of_dividends(overview):
    dividends = 0
    for key in overview:
        dividends += overview[key][2]
    return dividends * 0.85  # after tax


def return_on_investment(fundamentals, overview):
    total_dividend = sum_of_dividends(overview)
    expected_price_including_dividends = (
        overview['7'][1] * fundamentals['pe_ratio']) + total_dividend
    expected_percentage_roi = expected_price_including_dividends / fundamentals['price']
    expected_yearly_return = ((expected_percentage_roi + 1)**(1/7))-1
    return {
        'tseps': fundamentals['tse_per_share'],
        'total_dividend': total_dividend,
        'expected_price_including_dividends': expected_price_including_dividends,
        'expected_absolute_roi': expected_price_including_dividends - fundamentals['price'],
        'expected_percentage_roi': expected_percentage_roi,
        'expected_yearly_return': expected_yearly_return
    }


def roe_4yrs_median(balance_sheet, earnings):
    tse_last_4yrs = balance_sheet.loc['Total Stockholder Equity'][:].tolist()[::-1]
    earnings_last_4yrs = earnings['Earnings'].tolist()
    roe_last_4yrs = []
    for i in range(0, len(earnings_last_4yrs)):
        roe_in_year = earnings_last_4yrs[i] / tse_last_4yrs[i]
        roe_last_4yrs.append(roe_in_year)
    return statistics.median(roe_last_4yrs) * H
