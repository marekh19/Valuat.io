# If split need to be calculated

split_dict = {}
splits = ticker.splits.to_dict().items()
for split in splits:
    year = split[0].to_pydatetime().year
    coeficient = split[1]
    if year >= last_4_fiscal_yrs[-1]:
        split_dict[year] = coeficient
print('====================')
print('Splits in last 4 fiscal years:')
print(split_dict)
print('====================')

# If there was split this year but this year is not closed fiscal year yet
if datetime.now().year in split_dict.keys() and datetime.now().year not in last_4_fiscal_yrs:
    shares_outstanding_last_4_yrs = {last_4_fiscal_yrs[0]: current_shares_outstanding_in_mil / split_dict[datetime.now().year]}
else:
    shares_outstanding_last_4_yrs = {last_4_fiscal_yrs[0]: current_shares_outstanding_in_mil}

for year in last_4_fiscal_yrs:
    if year not in shares_outstanding_last_4_yrs.keys():
        if year + 1 in split_dict.keys():
            shares_outstanding_last_4_yrs[year] = shares_outstanding_last_4_yrs[year + 1] / split_dict[year + 1]
        if year + 1 not in split_dict.keys():
            shares_outstanding_last_4_yrs[year] = shares_outstanding_last_4_yrs[year + 1]
print('====================')
print('Shares outstanding in last 4 fiscal years:')
print(shares_outstanding_last_4_yrs)
print('====================')

eps_last_4_yrs_in_mil = {}
for year in last_4_fiscal_yrs:
    eps_last_4_yrs_in_mil[year] = (earnings_dict[year] / shares_outstanding_last_4_yrs[year]) / M
print('====================')
print('Earnings per share in last 4 fiscal years:')
print(eps_last_4_yrs_in_mil)
print('====================')

# If there was split this year but this year is not closed fiscal year yet
last_fiscal_year_median_price = ticker.history(period="5y")[str(last_4_fiscal_yrs[0]) + '-01-01':str(last_4_fiscal_yrs[0]) + '-12-31']['Close'].median()

if datetime.now().year in split_dict.keys() and datetime.now().year not in last_4_fiscal_yrs:
    median_price_last_4_yrs = {last_4_fiscal_yrs[0]: last_fiscal_year_median_price * split_dict[datetime.now().year]}
else:
    median_price_last_4_yrs = {last_4_fiscal_yrs[0]: last_fiscal_year_median_price}

for year in last_4_fiscal_yrs:
    if year not in median_price_last_4_yrs.keys():
        if year + 1 in split_dict.keys():
            median_price_last_4_yrs[year] = shares_outstanding_last_4_yrs[year + 1] * split_dict[year + 1]
        if year + 1 not in split_dict.keys():
            shares_outstanding_last_4_yrs[year] = shares_outstanding_last_4_yrs[year + 1]

for year in last_4_fiscal_yrs:
    median_price_last_4_yrs[year] = ticker.history(period="max")[str(year) + '-01-01':str(year) + '-12-31']['Close'].median()
print('====================')
print('Median price in last 4 fiscal years:')
print(median_price_last_4_yrs)
print('====================')
