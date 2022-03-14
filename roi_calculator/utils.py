import yfinance as yf
from .values.math_constants import THOUSAND as K, MILLION as M, HUNDRED as H
import statistics
from datetime import datetime, date
import plotly.graph_objects as go
from plotly.offline import plot
from configparser import ConfigParser


def valuation_dictionary(ticker):
    ticker = yf.Ticker(ticker)
    # BASIC INFO
    info = ticker.info
    current_shares_outstanding_in_mil = info['sharesOutstanding'] / M
    market_price = info['regularMarketPrice']
    # BALANCE SHEET
    balance_sheet = ticker.balancesheet
    quarterly_balance_sheet = ticker.quarterly_balancesheet
    balance_sheet.to_csv('balance_sheet.csv')
    # EARNINGS
    earnings = ticker.earnings
    quarterly_earnings = ticker.quarterly_earnings
    earnings_dict = ticker.earnings['Earnings'].to_dict()
    # CALCULATED VALUES
    last_4_fiscal_yrs = sorted(list(earnings_dict.keys()), reverse=True)
    shares_outstanding_complete = shares_outstanding_last_4_yrs(ticker, last_4_fiscal_yrs)
    total_stockholders_equity_in_mil = quarterly_balance_sheet.loc[
        'Total Stockholder Equity'][0] / M
    earnings_last_4_quarters_sum = earnings_sum_last_4_quarters(quarterly_earnings)
    current_eps = earnings_per_share(earnings_last_4_quarters_sum, current_shares_outstanding_in_mil)
    current_pe_ratio = price_earnings_ratio(market_price, current_eps)
    current_roe = return_on_equity(earnings_last_4_quarters_sum, total_stockholders_equity_in_mil)
    tse_per_share = total_stockholders_equity_per_share(
        total_stockholders_equity_in_mil, current_shares_outstanding_in_mil)
    eps_last_4_yrs = earnings_per_share_last_4_yrs_in_mil(last_4_fiscal_yrs, earnings_dict, shares_outstanding_complete)
    roe_4_yrs_median = return_on_equity_4yrs_median(balance_sheet, earnings)
    pe_ratio_4_yrs_median = price_earnings_ratio_4_yrs_median(ticker, last_4_fiscal_yrs, eps_last_4_yrs)
    payout_ratio_4_yrs_median = dividend_payout_ratio_4_yrs_median(
        ticker, last_4_fiscal_yrs, earnings_dict, shares_outstanding_complete)
    f_score = piotroski_f_score(ticker)
    z_score = altman_z_score(ticker)

    ticker_fundamentals = {
        # basics
        'name': info['longName'],
        'symbol': info['symbol'],
        'price': market_price,
        'currency': info['currency'],
        'market_cap': info['marketCap'] / M,
        'market_cap_original': info['marketCap'],
        'shares_outstanding': current_shares_outstanding_in_mil,
        'country': info['country'],
        'description': info['longBusinessSummary'],
        'data_saved_on': datetime.now(),
        # ratios, earnings, roe
        'peg_ratio': info['pegRatio'],
        'pfcf_ratio': info['marketCap'] / info['freeCashflow'] if info['freeCashflow'] is not None else None,
        'ps_ratio': info['priceToSalesTrailing12Months'],
        'pb_ratio': info['priceToBook'],
        'ytd_earnings': earnings_last_4_quarters_sum,
        'eps': current_eps,
        'pe_ratio': current_pe_ratio,
        'pe_ratio_median': pe_ratio_4_yrs_median,
        'roe': current_roe,
        'roe_median': roe_4_yrs_median,
        'debt_to_equity': info['debtToEquity'] / H if info['debtToEquity'] is not None else None,
        'quick_ratio': info['quickRatio'],
        'current_ratio': info['currentRatio'],
        'tse': total_stockholders_equity_in_mil,
        'tse_original': total_stockholders_equity_in_mil * M,
        'tse_per_share': tse_per_share,
        # dividends
        'dividend_yield': info['dividendYield'] * H if info['dividendYield'] is not None else None,
        'dividend_value': info['lastDividendValue'],
        'payout_ratio': info['payoutRatio'] if info['dividendYield'] is not None else None,
        'payout_ratio_median': payout_ratio_4_yrs_median,
        'ex_divi_date': info['exDividendDate'],
        # scores
        'f_score': f_score,
        'z_score': z_score,
    }
    return ticker_fundamentals


# region Stock Scoring Model
def stock_overall_score(stock_scoring):
    total = 0
    num_of_elements_weighted = 0
    for key in stock_scoring:
        total += stock_scoring[key][0][0] * stock_scoring[key][1]
        num_of_elements_weighted += stock_scoring[key][1]
    return total / num_of_elements_weighted


def stock_scoring(fundamentals):
    c = ConfigParser()
    c.read('roi_calculator/values/scoring.ini')

    stock_score = {
        'debt_to_equity': (calculate_score_lower_than(fundamentals['debt_to_equity'], c.getfloat('debt_to_equity', 'bm1'), c.getfloat('debt_to_equity', 'bm2'), c.getfloat('debt_to_equity', 'bm3'), c.getfloat('debt_to_equity', 'bm4'), c.getfloat('debt_to_equity', 'bm5')), c.getfloat('debt_to_equity', 'weight')),
        'f_score': (calculate_score_higher_than(fundamentals['f_score'], c.getfloat('f_score', 'bm1'), c.getfloat('f_score', 'bm2'), c.getfloat('f_score', 'bm3'), c.getfloat('f_score', 'bm4'), c.getfloat('f_score', 'bm5')), c.getfloat('f_score', 'weight')),
        'z_score': (calculate_score_higher_than(fundamentals['z_score'], c.getfloat('z_score', 'bm1'), c.getfloat('z_score', 'bm2'), c.getfloat('z_score', 'bm3'), c.getfloat('z_score', 'bm4'), c.getfloat('z_score', 'bm5')), c.getfloat('z_score', 'weight')),
        'roe': (calculate_score_higher_than(fundamentals['roe'], c.getfloat('roe', 'bm1'), c.getfloat('roe', 'bm2'), c.getfloat('roe', 'bm3'), c.getfloat('roe', 'bm4'), c.getfloat('roe', 'bm5')), c.getfloat('roe', 'weight')),
        # EPS placeholder - need to decide if I want to score based on if it's growing yoy
        'dividend_yield': (calculate_score_higher_than(fundamentals['dividend_yield'], c.getfloat('dividend_yield', 'bm1'), c.getfloat('dividend_yield', 'bm2'), c.getfloat('dividend_yield', 'bm3'), c.getfloat('dividend_yield', 'bm4'), c.getfloat('dividend_yield', 'bm5')), c.getfloat('dividend_yield', 'weight')),
        'payout_ratio': (calculate_score_lower_than(fundamentals['payout_ratio'], c.getfloat('payout_ratio', 'bm1'), c.getfloat('payout_ratio', 'bm2'), c.getfloat('payout_ratio', 'bm3'), c.getfloat('payout_ratio', 'bm4'), c.getfloat('payout_ratio', 'bm5')), c.getfloat('payout_ratio', 'weight')) if fundamentals['dividend_yield'] is not None else ((0, 'score-na'), c.getfloat('payout_ratio', 'weight')),
        'pe_ratio': (calculate_score_lower_than(fundamentals['pe_ratio'], c.getfloat('pe_ratio', 'bm1'), c.getfloat('pe_ratio', 'bm2'), c.getfloat('pe_ratio', 'bm3'), c.getfloat('pe_ratio', 'bm4'), c.getfloat('pe_ratio', 'bm5')), c.getfloat('pe_ratio', 'weight')),
        'peg_ratio': (calculate_score_lower_than(fundamentals['peg_ratio'], c.getfloat('peg_ratio', 'bm1'), c.getfloat('peg_ratio', 'bm2'), c.getfloat('peg_ratio', 'bm3'), c.getfloat('peg_ratio', 'bm4'), c.getfloat('peg_ratio', 'bm5')), c.getfloat('peg_ratio', 'weight')),
        # PS ratio - score based on what? not possible to score based on absolute values
        'pb_ratio': (calculate_score_lower_than(fundamentals['pb_ratio'], c.getfloat('pb_ratio', 'bm1'), c.getfloat('pb_ratio', 'bm2'), c.getfloat('pb_ratio', 'bm3'), c.getfloat('pb_ratio', 'bm4'), c.getfloat('pb_ratio', 'bm5')), c.getfloat('pb_ratio', 'weight')),
        'pfcf_ratio': (calculate_score_lower_than(fundamentals['pfcf_ratio'], c.getfloat('pfcf_ratio', 'bm1'), c.getfloat('pfcf_ratio', 'bm2'), c.getfloat('pfcf_ratio', 'bm3'), c.getfloat('pfcf_ratio', 'bm4'), c.getfloat('pfcf_ratio', 'bm5')), c.getfloat('pfcf_ratio', 'weight')),
        'quick_ratio': (calculate_score_higher_than(fundamentals['quick_ratio'], c.getfloat('quick_ratio', 'bm1'), c.getfloat('quick_ratio', 'bm2'), c.getfloat('quick_ratio', 'bm3'), c.getfloat('quick_ratio', 'bm4'), c.getfloat('quick_ratio', 'bm5')), c.getfloat('quick_ratio', 'weight')),
        'current_ratio': (calculate_score_higher_than(fundamentals['current_ratio'], c.getfloat('current_ratio', 'bm1'), c.getfloat('current_ratio', 'bm2'), c.getfloat('current_ratio', 'bm3'), c.getfloat('current_ratio', 'bm4'), c.getfloat('current_ratio', 'bm5')), c.getfloat('current_ratio', 'weight')),
        'pe_ratio_median': (calculate_score_lower_than(fundamentals['pe_ratio_median'], c.getfloat('pe_ratio_median', 'bm1'), c.getfloat('pe_ratio_median', 'bm2'), c.getfloat('pe_ratio_median', 'bm3'), c.getfloat('pe_ratio_median', 'bm4'), c.getfloat('pe_ratio_median', 'bm5')), c.getfloat('pe_ratio_median', 'weight')),
        'roe_median': (calculate_score_higher_than(fundamentals['roe_median'], c.getfloat('roe_median', 'bm1'), c.getfloat('roe_median', 'bm2'), c.getfloat('roe_median', 'bm3'), c.getfloat('roe_median', 'bm4'), c.getfloat('roe_median', 'bm5')), c.getfloat('roe_median', 'weight')),
        'payout_ratio_median': (calculate_score_lower_than(fundamentals['payout_ratio_median'], c.getfloat('payout_ratio_median', 'bm1'), c.getfloat('payout_ratio_median', 'bm2'), c.getfloat('payout_ratio_median', 'bm3'), c.getfloat('payout_ratio_median', 'bm4'), c.getfloat('payout_ratio_median', 'bm5')), c.getfloat('payout_ratio_median', 'weight')),
    }
    for key in stock_score:
        print(f'fundament: {key} \t\t>>>\t\t score: {stock_score[key]} \t\t>>>\t\t value: {fundamentals[key]}')
    return stock_score


def calculate_score_lower_than(value, bm1, bm2, bm3, bm4, bm5):
    if value == None or value <= 0:
        return (0, 'score-na')
    if value <= bm1:
        return (100, 'score-100')
    if value <= bm2:
        return (80, 'score-80')
    if value <= bm3:
        return (60, 'score-60')
    if value <= bm4:
        return (40, 'score-40')
    if value <= bm5:
        return (20, 'score-20')
    if value > bm5:
        return (0, 'score-na')


def calculate_score_higher_than(value, bm1, bm2, bm3, bm4, bm5):
    if value == None:
        return (0, 'score-na')
    if value >= bm1:
        return (100, 'score-100')
    if value >= bm2:
        return (80, 'score-80')
    if value >= bm3:
        return (60, 'score-60')
    if value >= bm4:
        return (40, 'score-40')
    if value >= bm5:
        return (20, 'score-20')
    if value < bm5:
        return (0, 'score-na')
# endregion Stock Scoring Model

# region Altman Z Score


def altman_z_score(ticker):
    bs = ticker.quarterly_balancesheet
    qf = ticker.quarterly_financials
    qe = ticker.quarterly_earnings
    # A=Working capital/total assets
    # B=Retained earnings/total assets
    # C=Earnings before interest and taxes (EBIT)/total assets
    # D=Market value of equity/book value of total liabilities
    # E=Sales/total assets
    if 'Total Current Assets' in bs and 'Total Current Liabilities' in bs and 'Total Assets' in bs:
        a = (bs.loc['Total Current Assets'][0] - bs.loc['Total Current Liabilities'][0]) / bs.loc['Total Assets'][0]
    else:
        a = 0
    if 'Retained Earnings' in bs:
        b = bs.loc['Retained Earnings'][0] / bs.loc['Total Assets'][0]
    else:
        b = 0
    if 'Ebit' in qf and 'Total Assets' in bs:
        c = qf.loc['Ebit'][0] / bs.loc['Total Assets'][0]
    else:
        c = 0
    if 'Total Liab' in bs:
        d = ticker.info['marketCap'] / bs.loc['Total Liab'][0]
    else:
        d = 0
    if 'Revenue' in qe and 'Total Assets' in bs:
        e = qe['Revenue'].sum() / bs.loc['Total Assets'][0]
    else:
        e = 0
    return (1.2 * a) + (1.4 * b) + (3.3 * c) + (0.6 * d) + (1.0 * e)
# endregion Altman Z Score


# region Piotroski F Score
def piotroski_f_score(ticker):
    f_score = 0
    # Positive net income (1 point)
    if earnings_sum_last_4_quarters(ticker.quarterly_earnings) > 0:
        f_score += 1
    # Positive return on assets (ROA) in the current year (1 point)
    if return_on_assets(ticker) > 0:
        f_score += 1
    # Positive operating cash flow in the current year (1 point)
    if positive_operating_cashflow(ticker):
        f_score += 1
    # Cash flow from operations being greater than net Income (quality of earnings) (1 point)
    if operating_cashflow_greater_than_net_income(ticker):
        f_score += 1
    # Lower amount of long term debt in the current period, compared to the previous year (decreased leverage) (1 point)
    if lower_long_term_debt_than_prev_year(ticker):
        f_score += 1
    # Higher current ratio this year compared to the previous year (more liquidity) (1 point)
    if higher_current_ratio_than_prev_year(ticker):
        f_score += 1
    # No new shares were issued in the last year (lack of dilution) (1 point).
    if ticker.shares is not None:
        if no_new_shares_issued(ticker):
            f_score += 1
    else:
        f_score += 0.5
    # A higher gross margin compared to the previous year (1 point)
    if higher_gross_margin_than_prev_year(ticker):
        f_score += 1
    # A higher asset turnover ratio compared to the previous year (1 point)
    if higher_asset_turnover_ration_than_prev_year(ticker):
        f_score += 1
    return f_score


def return_on_assets(ticker):
    earnings = ticker.quarterly_earnings['Earnings'].sum()
    assets = ticker.quarterly_balancesheet.loc['Total Assets'].sum()
    return earnings / assets


def positive_operating_cashflow(ticker):
    if 'Total Cash From Operating Activities' in ticker.quarterly_cashflow:
        return ticker.quarterly_cashflow.loc['Total Cash From Operating Activities'].sum() > 0
    else:
        return False


def operating_cashflow_greater_than_net_income(ticker):
    if 'Total Cash From Operating Activities' in ticker.quarterly_cashflow:
        operating_cashflow = ticker.quarterly_cashflow.loc['Total Cash From Operating Activities'].sum()
        net_income = ticker.quarterly_cashflow.loc['Net Income'].sum()
        return operating_cashflow > net_income
    else:
        return False


def lower_long_term_debt_than_prev_year(ticker):
    if 'Long Term Debt' in ticker.balancesheet:
        return ticker.balancesheet.loc['Long Term Debt'][0] < ticker.balancesheet.loc['Long Term Debt'][1]
    else:
        return False


def higher_current_ratio_than_prev_year(ticker):
    current_year = ticker.balancesheet.loc['Total Assets'][0] / ticker.balancesheet.loc['Total Liab'][0]
    prev_year = ticker.balancesheet.loc['Total Assets'][1] / ticker.balancesheet.loc['Total Liab'][1]
    return current_year > prev_year


def no_new_shares_issued(ticker):
    return ticker.shares.iloc[-1][0] <= ticker.shares.iloc[-2][0]


def higher_gross_margin_than_prev_year(ticker):
    current_year = ticker.financials.loc['Gross Profit'][0] / ticker.financials.loc['Total Revenue'][0]
    prev_year = ticker.financials.loc['Gross Profit'][1] / ticker.financials.loc['Total Revenue'][1]
    return current_year > prev_year


def higher_asset_turnover_ration_than_prev_year(ticker):
    e = ticker.earnings
    bs = ticker.balancesheet
    try:
        current_year_total_assets = ((bs.loc['Total Assets'][0] + bs.loc['Total Assets'][1]) / 2)
    except IndexError:
        current_year_total_assets = bs.loc['Total Assets'][0]
    try:
        prev_year_total_assets = ((bs.loc['Total Assets'][1] + bs.loc['Total Assets'][2]) / 2)
    except IndexError:
        prev_year_total_assets = bs.loc['Total Assets'][1]
    current_year = e.iloc[-1]['Revenue'] / current_year_total_assets
    prev_year = e.iloc[-2]['Revenue'] / prev_year_total_assets
    return current_year > prev_year
# endregion Piotroski F Score


def shares_outstanding_last_4_yrs(ticker, last_4_fiscal_yrs):
    shares_outstanding = {}
    current_year = date.today().year
    # check if data shares outstanding data is available
    if ticker.shares is None:
        for key in last_4_fiscal_yrs:
            shares_outstanding[key] = ticker.info['sharesOutstanding'] / M
    #  if available, match earnings years with shares outstanding years
    else:
        shares_fiscal_yrs = ticker.shares['BasicShares'].to_dict()
        for key in last_4_fiscal_yrs:
            shares_outstanding[key] = 0
        for key in shares_fiscal_yrs:
            shares_outstanding[key] = shares_fiscal_yrs[key] / M
        # if year of shares outstanding is missing, fill it with year + 1 data
        for key in shares_outstanding:
            if shares_outstanding[key] == 0 and key + 1 in shares_outstanding:
                shares_outstanding[key] = shares_outstanding[key+1] / M
            elif shares_outstanding[key] == 0 and key + 1 not in shares_outstanding:
                shares_outstanding[key] = shares_outstanding[key-1]
    shares_outstanding[current_year] = ticker.info['sharesOutstanding'] / M
    return shares_outstanding


def earnings_per_share_last_4_yrs_in_mil(last_4_fiscal_yrs, earnings_dict, shares_outstanding_overview):
    eps_last_4_yrs = {}
    for year in last_4_fiscal_yrs:
        eps_last_4_yrs[year] = (earnings_dict[year] / shares_outstanding_overview[year]) / M
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
    return tse / shares_outstanding


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


# def candlestick(ticker):
#     df = ticker.history(period="5y")
#     fig = go.Figure(data=[go.Candlestick(x=df.index,
#                                          open=df['Open'],
#                                          high=df['High'],
#                                          low=df['Low'],
#                                          close=df['Close'])])
#     candlestick_div = plot(fig, output_type='div')
#     return candlestick_div
