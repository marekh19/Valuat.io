import yfinance as yf
from .math_constants import THOUSAND as K, MILLION as M, HUNDRED as H
import statistics
from datetime import datetime


def valuation_dictionary(ticker):
    ticker = yf.Ticker(ticker)
    # BASIC INFO
    info = ticker.info
    current_shares_outstanding_in_mil = info['sharesOutstanding'] / M
    market_price = info['regularMarketPrice']
    # BALANCE SHEET
    balance_sheet = ticker.balancesheet
    quarterly_balance_sheet = ticker.quarterly_balancesheet
    # EARNINGS
    earnings = ticker.earnings
    quarterly_earnings = ticker.quarterly_earnings
    earnings_dict = ticker.earnings['Earnings'].to_dict()
    # CALCULATED VALUES
    last_4_fiscal_yrs = sorted(list(earnings_dict.keys()), reverse=True)
    total_stockholders_equity_in_mil = quarterly_balance_sheet.loc[
        'Total Stockholder Equity'][0] / M
    earnings_last_4_quarters_sum = earnings_sum_last_4_quarters(quarterly_earnings)
    current_eps = earnings_per_share(earnings_last_4_quarters_sum, current_shares_outstanding_in_mil)
    current_pe_ratio = price_earnings_ratio(market_price, current_eps)
    current_roe = return_on_equity(earnings_last_4_quarters_sum, total_stockholders_equity_in_mil)
    tse_per_share = total_stockholders_equity_per_share(
        total_stockholders_equity_in_mil, current_shares_outstanding_in_mil)
    eps_last_4_yrs = earnings_per_share_last_4_yrs_in_mil(
        last_4_fiscal_yrs, earnings_dict, current_shares_outstanding_in_mil)
    roe_4_yrs_median = return_on_equity_4yrs_median(balance_sheet, earnings)
    pe_ratio_4_yrs_median = price_earnings_ratio_4_yrs_median(ticker, last_4_fiscal_yrs, eps_last_4_yrs)
    payout_ratio_4_yrs_median = dividend_payout_ratio_4_yrs_median(
        ticker, last_4_fiscal_yrs, earnings_dict, current_shares_outstanding_in_mil)

    ticker_fundamentals = {
        # basics
        'name': info['longName'],
        'symbol': info['symbol'],
        'price': market_price,
        'currency': info['currency'],
        'market_cap': info['marketCap'] / M,
        'shares_outstanding': current_shares_outstanding_in_mil,
        # ratios, earnings, roe
        'peg_ratio': info['pegRatio'],
        'pfcf_ratio': info['marketCap'] / info['freeCashflow'] if info['freeCashflow'] != None else None,
        'ps_ratio': info['priceToSalesTrailing12Months'],
        'pb_ratio': info['priceToBook'],
        'ytd_earnings': earnings_last_4_quarters_sum,
        'eps': current_eps,
        'pe_ratio': current_pe_ratio,
        'pe_ratio_median': pe_ratio_4_yrs_median,
        'roe': current_roe,
        'roe_median': roe_4_yrs_median,
        'debt_to_equity': info['debtToEquity'] / H if info['debtToEquity'] != None else None,
        'quick_ratio': info['quickRatio'],
        'current_ratio': info['currentRatio'],
        'tse': total_stockholders_equity_in_mil,
        'tse_per_share': tse_per_share,
        # dividends
        'dividend_yield': info['dividendYield'] * H if info['dividendYield'] != None else None,
        'dividend_value': info['lastDividendValue'],
        'payout_ratio': info['payoutRatio'],
        'payout_ratio_median': payout_ratio_4_yrs_median,

    }
    return ticker_fundamentals


def earnings_per_share_last_4_yrs_in_mil(last_4_fiscal_yrs, earnings_dict, shares_outstanding):
    eps_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        eps_last_4_yrs[year] = (earnings_dict[year] / shares_outstanding) / M
    return eps_last_4_yrs


def yearly_median_price_last_4_yrs(ticker, last_4_fiscal_yrs):
    price_history = ticker.history(period="5y")
    median_price_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        median_price_last_4_yrs[year] = price_history[str(year) + '-01-01':str(year) + '-12-31']['Close'].median()
    return median_price_last_4_yrs


def yearly_pe_ratio_last_4_yrs(last_4_fiscal_yrs, median_price_last_4_yrs, eps_last_4_yrs):
    pe_ratio_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        pe_ratio_last_4_yrs[year] = median_price_last_4_yrs[year] / eps_last_4_yrs[year]
    return pe_ratio_last_4_yrs


def price_earnings_ratio_4_yrs_median(ticker, last_4_fiscal_yrs, eps_last_4_yrs):
    median_price_last_4_yrs = yearly_median_price_last_4_yrs(ticker, last_4_fiscal_yrs)
    pe_ratio_last_4_yrs = yearly_pe_ratio_last_4_yrs(last_4_fiscal_yrs, median_price_last_4_yrs, eps_last_4_yrs)
    return statistics.median(pe_ratio_last_4_yrs.values()) if statistics.median(pe_ratio_last_4_yrs.values()) <= 25 else 25


def earnings_sum_last_4_quarters(quarterly_earnings):
    return quarterly_earnings['Earnings'].sum()


def dividends_paid_last_4_yrs(ticker, last_4_fiscal_yrs):
    dividends = ticker.dividends
    dividends_paid_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        dividends_paid_last_4_yrs[year] = dividends[str(year) + '-01-01':str(year) + '-12-31'].sum()
    return dividends_paid_last_4_yrs


def dividend_payout_ratio_last_4_yrs(last_4_fiscal_yrs, dividends_paid_last_4_yrs, earnings_per_share_last_4_yrs_in_mil):
    payout_ratio_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        payout_ratio_last_4_yrs[year] = dividends_paid_last_4_yrs[year] / earnings_per_share_last_4_yrs_in_mil[year]
    return payout_ratio_last_4_yrs


def dividend_payout_ratio_4_yrs_median(ticker, last_4_fiscal_yrs, earnings_dict, shares_outstanding):
    eps = earnings_per_share_last_4_yrs_in_mil(last_4_fiscal_yrs, earnings_dict, shares_outstanding)
    dividends_paid = dividends_paid_last_4_yrs(ticker, last_4_fiscal_yrs)
    payout_ratio = dividend_payout_ratio_last_4_yrs(last_4_fiscal_yrs, dividends_paid, eps)
    return statistics.median(payout_ratio.values())


def return_on_equity_4yrs_median(balance_sheet, earnings):
    tse_last_4yrs = balance_sheet.loc['Total Stockholder Equity'][:].tolist()
    earnings_last_4yrs = earnings['Earnings'].tolist()[::-1]
    roe_last_4yrs = []
    for i in range(0, len(earnings_last_4yrs)):
        roe_in_year = earnings_last_4yrs[i] / tse_last_4yrs[i]
        roe_last_4yrs.append(roe_in_year)
    return statistics.median(roe_last_4yrs) * H


def earnings_per_share(quarterly_earnings, shares_outstanding):
    return quarterly_earnings / (shares_outstanding * M)


def price_earnings_ratio(price, eps):
    return price / eps


def return_on_equity(earnings, equity):
    return (earnings / (equity * M)) * H


def total_stockholders_equity_per_share(tse, shares_outstanding):
    return float(tse / shares_outstanding)


def compute_year(previous_year, fundamentals):
    return [
        previous_year[0] + previous_year[1] - previous_year[2],
        ((previous_year[0] + previous_year[1] - previous_year[2]) * fundamentals['roe']) / H,
        (((previous_year[0] + previous_year[1] - previous_year[2])
         * fundamentals['roe_median']) / H) * fundamentals['payout_ratio_median'],
    ]


def seven_yrs_overview(fundamentals):
    year1 = [
        fundamentals['tse_per_share'],
        fundamentals['tse_per_share'] * fundamentals['roe'] / H,
        (fundamentals['tse_per_share'] * fundamentals['roe'] / H) * fundamentals['payout_ratio_median']
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
        overview['7'][1] * fundamentals['pe_ratio_median']) + total_dividend
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
