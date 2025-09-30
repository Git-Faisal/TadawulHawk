"""
Debug script to inspect raw yfinance data.
Shows exact quarters and annual periods being returned.
"""

import yfinance as yf
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils import setup_logger

logger = setup_logger('debug_yfinance', level='DEBUG')

print("="*70)
print("YFINANCE DATA INSPECTION - Saudi Aramco (2222.SR)")
print("="*70)

ticker = yf.Ticker('2222.SR')

# Get quarterly financials
print("\n[QUARTERLY FINANCIALS]")
print("-" * 70)
quarterly_income = ticker.quarterly_financials
quarterly_cashflow = ticker.quarterly_cashflow

if quarterly_income is not None and not quarterly_income.empty:
    print(f"\nColumns (dates): {len(quarterly_income.columns)}")
    for i, col in enumerate(quarterly_income.columns):
        print(f"\n  Quarter {i+1}: {col.date()} (Year: {col.year}, Month: {col.month})")

        # Calculate quarter number from month
        quarter_num = (col.month - 1) // 3 + 1
        print(f"    Calculated Quarter: Q{quarter_num} {col.year}")

        # Get key metrics
        revenue = quarterly_income.loc['Total Revenue', col] if 'Total Revenue' in quarterly_income.index else None
        net_income = quarterly_income.loc['Net Income', col] if 'Net Income' in quarterly_income.index else None
        gross_profit = quarterly_income.loc['Gross Profit', col] if 'Gross Profit' in quarterly_income.index else None

        print(f"    Revenue: {revenue:,.0f}" if revenue else "    Revenue: None")
        print(f"    Gross Profit: {gross_profit:,.0f}" if gross_profit else "    Gross Profit: None")
        print(f"    Net Income: {net_income:,.0f}" if net_income else "    Net Income: None")

# Get annual financials
print("\n\n[ANNUAL FINANCIALS]")
print("-" * 70)
annual_income = ticker.financials
annual_cashflow = ticker.cashflow

if annual_income is not None and not annual_income.empty:
    print(f"\nColumns (dates): {len(annual_income.columns)}")
    for i, col in enumerate(annual_income.columns):
        print(f"\n  Year {i+1}: {col.date()} (Year: {col.year}, Month: {col.month})")

        # Get key metrics
        revenue = annual_income.loc['Total Revenue', col] if 'Total Revenue' in annual_income.index else None
        net_income = annual_income.loc['Net Income', col] if 'Net Income' in annual_income.index else None
        gross_profit = annual_income.loc['Gross Profit', col] if 'Gross Profit' in annual_income.index else None

        print(f"    Revenue: {revenue:,.0f}" if revenue else "    Revenue: None")
        print(f"    Gross Profit: {gross_profit:,.0f}" if gross_profit else "    Gross Profit: None")
        print(f"    Net Income: {net_income:,.0f}" if net_income else "    Net Income: None")

# Manual calculation for each year
print("\n\n[QUARTERLY SUM vs ANNUAL COMPARISON]")
print("-" * 70)

if quarterly_income is not None and annual_income is not None:
    # Check for 2024, 2023, 2022
    for check_year in [2024, 2023, 2022]:
        print(f"\n{'='*70}")
        print(f"YEAR {check_year}")
        print('='*70)

        # Get all quarters for this year
        quarters_year = [col for col in quarterly_income.columns if col.year == check_year]

        print(f"\nFound {len(quarters_year)} quarters for {check_year}:")
        q_revenue_sum = 0
        q_gross_sum = 0
        q_net_sum = 0
        quarters_with_data = 0

        for col in quarters_year:
            quarter_num = (col.month - 1) // 3 + 1
            revenue = quarterly_income.loc['Total Revenue', col] if 'Total Revenue' in quarterly_income.index else None
            gross = quarterly_income.loc['Gross Profit', col] if 'Gross Profit' in quarterly_income.index else None
            net = quarterly_income.loc['Net Income', col] if 'Net Income' in quarterly_income.index else None

            # Check for NaN
            import pandas as pd
            revenue_valid = revenue is not None and pd.notna(revenue)
            gross_valid = gross is not None and pd.notna(gross)
            net_valid = net is not None and pd.notna(net)

            print(f"\n  Q{quarter_num} {check_year} (ending {col.date()}):")
            print(f"    Revenue: {revenue:,.0f}" if revenue_valid else "    Revenue: NaN/None")
            print(f"    Gross Profit: {gross:,.0f}" if gross_valid else "    Gross Profit: NaN/None")
            print(f"    Net Income: {net:,.0f}" if net_valid else "    Net Income: NaN/None")

            if revenue_valid:
                q_revenue_sum += revenue
            if gross_valid:
                q_gross_sum += gross
            if net_valid:
                q_net_sum += net

            if revenue_valid or gross_valid or net_valid:
                quarters_with_data += 1

        # Get annual data for this year
        annual_year = [col for col in annual_income.columns if col.year == check_year]

        if annual_year:
            col = annual_year[0]
            a_revenue = annual_income.loc['Total Revenue', col] if 'Total Revenue' in annual_income.index else None
            a_gross = annual_income.loc['Gross Profit', col] if 'Gross Profit' in annual_income.index else None
            a_net = annual_income.loc['Net Income', col] if 'Net Income' in annual_income.index else None

            import pandas as pd
            a_revenue_valid = a_revenue is not None and pd.notna(a_revenue)
            a_gross_valid = a_gross is not None and pd.notna(a_gross)
            a_net_valid = a_net is not None and pd.notna(a_net)

            print(f"\n  Annual {check_year} (ending {col.date()}):")
            print(f"    Revenue: {a_revenue:,.0f}" if a_revenue_valid else "    Revenue: NaN/None")
            print(f"    Gross Profit: {a_gross:,.0f}" if a_gross_valid else "    Gross Profit: NaN/None")
            print(f"    Net Income: {a_net:,.0f}" if a_net_valid else "    Net Income: NaN/None")

            print(f"\n  COMPARISON ({quarters_with_data}/4 quarters have data):")
            if a_revenue_valid and q_revenue_sum > 0:
                diff_pct = ((q_revenue_sum - a_revenue) / a_revenue) * 100
                print(f"    Revenue: Quarterly sum = {q_revenue_sum:,.0f}, Annual = {a_revenue:,.0f} (Diff: {diff_pct:.1f}%)")
            else:
                print(f"    Revenue: Cannot compare (missing data)")

            if a_gross_valid and q_gross_sum > 0:
                diff_pct = ((q_gross_sum - a_gross) / a_gross) * 100
                print(f"    Gross Profit: Quarterly sum = {q_gross_sum:,.0f}, Annual = {a_gross:,.0f} (Diff: {diff_pct:.1f}%)")
            else:
                print(f"    Gross Profit: Cannot compare (missing data)")

            if a_net_valid and q_net_sum > 0:
                diff_pct = ((q_net_sum - a_net) / a_net) * 100
                print(f"    Net Income: Quarterly sum = {q_net_sum:,.0f}, Annual = {a_net:,.0f} (Diff: {diff_pct:.1f}%)")
            else:
                print(f"    Net Income: Cannot compare (missing data)")
        else:
            print(f"\n  No annual data found for {check_year}")

print("\n" + "="*70)
print("INSPECTION COMPLETE")
print("="*70)
