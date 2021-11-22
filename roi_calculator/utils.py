import yfinance as yf
from .math_constants import THOUSAND as K, MILLION as M, HUNDRED as H
import statistics
from datetime import datetime


def valuation_dictionary(ticker):
    # Data from yf info method
    ticker = yf.Ticker(ticker)
    basic_info = ticker.info
    regularMarketPrice = basic_info['regularMarketPrice']
    if regularMarketPrice == None:
        return None
    shares_outstanding_in_mil = basic_info['sharesOutstanding'] / M
    # Data from yf balance_sheet method
    quarterly_balance_sheet = ticker.quarterly_balancesheet
    balance_sheet = ticker.balancesheet
    earnings = ticker.earnings
    roe_4yrs_median = return_on_equity_4yrs_median(balance_sheet, earnings)
    total_stockholders_equity_in_mil = quarterly_balance_sheet.loc[
        'Total Stockholder Equity'][0] / M
    # Data from yf earnings method
    quarterly_earnings = ticker.quarterly_earnings
    ytd_earnings = year_to_date_earnings(quarterly_earnings)
    eps = earnings_per_share(ytd_earnings, shares_outstanding_in_mil)
    pe_ratio = price_earnings_ratio(regularMarketPrice, eps)
    roe = return_on_equity(ytd_earnings, total_stockholders_equity_in_mil)
    tse_per_share = total_stockholders_equity_per_share(total_stockholders_equity_in_mil, shares_outstanding_in_mil)
    
    # TEMP START
    earnings_dict = earnings['Earnings'].to_dict()

    last_4_fiscal_yrs = (list(earnings_dict.keys()))[::-1]
    print('last fiscal 4 yrs:')
    print(last_4_fiscal_yrs)

    splits = ticker.splits.to_dict().items()
    split_list = [[2018, 2.0]]
    for split in splits:
        year = split[0].to_pydatetime().year
        coeficient = split[1]
        if year >= last_4_fiscal_yrs[-1]:
            split_list.append([year, coeficient])
    # if len(split_list) > 1:
    #     for i in range(1, len(split_list)):
    #         split_list[i][1] *= split_list[i-1][1]
    split_list = split_list[::-1]
    print(split_list)
    
    shares_outstanding_last_4_yrs = [[last_4_fiscal_yrs[0], shares_outstanding_in_mil]]
    
    for year in last_4_fiscal_yrs:
        for split_event in split_list:
            if year in split_event and year not in shares_outstanding_last_4_yrs[-1]:
                shares_outstanding_last_4_yrs.append([year, shares_outstanding_last_4_yrs[-1][1] / split_event[1]])
            if year not in split_event and year not in shares_outstanding_last_4_yrs[-1]:
                shares_outstanding_last_4_yrs.append([year, shares_outstanding_last_4_yrs[-1][1]])

    print('shares outstanding history:')
    print(shares_outstanding_last_4_yrs)


    # for i in range(0,len(last_4_fiscal_yrs)):
        


    # TEMP END
    ticker_fundamentals = {
        'name': basic_info['longName'],
        'symbol': basic_info['symbol'],
        'price': regularMarketPrice,
        'currency': basic_info['currency'],
        'shares_outstanding': shares_outstanding_in_mil,
        'payout_ratio': basic_info['payoutRatio'],
        'ytd_earnings': ytd_earnings,
        'eps': eps,
        'pe_ratio': pe_ratio,
        'roe': roe,
        'tse': total_stockholders_equity_in_mil,
        'tse_per_share': tse_per_share,
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
    return float(tse / shares_outstanding)


def compute_year(previous_year, fundamentals):
    return [
        previous_year[0] + previous_year[1] - previous_year[2],
        ((previous_year[0] + previous_year[1] - previous_year[2]) * fundamentals['roe']) / H,
        (((previous_year[0] + previous_year[1] - previous_year[2])
         * fundamentals['roe']) / H) * fundamentals['payout_ratio'],
    ]


def seven_yrs_overview(fundamentals):
    year1 = [
        fundamentals['tse_per_share'],
        fundamentals['tse_per_share'] * fundamentals['roe'] / H,
        (fundamentals['tse_per_share'] * fundamentals['roe'] / H) * fundamentals['payout_ratio']
    ]
    year2 = compute_year(year1, fundamentals)
    year3 = compute_year(year2, fundamentals)
    year4 = compute_year(year3, fundamentals)
    year5 = compute_year(year4, fundamentals)
    year6 = compute_year(year5, fundamentals)
    year7 = compute_year(year6, fundamentals)

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


def return_on_equity_4yrs_median(balance_sheet, earnings):
    tse_last_4yrs = balance_sheet.loc['Total Stockholder Equity'][:].tolist()[::-1]
    earnings_last_4yrs = earnings['Earnings'].tolist()
    roe_last_4yrs = []
    for i in range(0, len(earnings_last_4yrs)):
        roe_in_year = earnings_last_4yrs[i] / tse_last_4yrs[i]
        roe_last_4yrs.append(roe_in_year)
    return statistics.median(roe_last_4yrs) * H


def pe_ratio_4_yrs_median():
    yield 0
