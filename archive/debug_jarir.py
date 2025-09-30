"""
Debug script to inspect Jarir Bookstore (4190.SR) data from yfinance.
"""

import yfinance as yf
import pandas as pd
import datetime

print("="*70)
print("JARIR BOOKSTORE (4190.SR) DATA INSPECTION")
print("="*70)

ticker = yf.Ticker('4190.SR')
info = ticker.info

print("\n[COMPANY INFO]")
print(f"Company: {info.get('longName') or info.get('shortName')}")
print(f"Sector: {info.get('sector')}")
print(f"Industry: {info.get('industry')}")

epoch_ms = info.get('firstTradeDateMilliseconds')
if epoch_ms:
    dt = datetime.datetime.fromtimestamp(epoch_ms/1000)
    print(f"Listed: {dt.strftime('%Y-%m-%d')}")

# Get quarterly financials
print("\n\n[QUARTERLY FINANCIALS]")
print("-" * 70)
quarterly_income = ticker.quarterly_financials

if quarterly_income is not None and not quarterly_income.empty:
    print(f"Available quarters: {len(quarterly_income.columns)}")
    for i, col in enumerate(quarterly_income.columns):
        quarter_num = (col.month - 1) // 3 + 1
        revenue = quarterly_income.loc['Total Revenue', col] if 'Total Revenue' in quarterly_income.index else None
        revenue_valid = revenue is not None and pd.notna(revenue)

        print(f"  Q{quarter_num} {col.year} ({col.date()}): Revenue = {revenue:,.0f}" if revenue_valid else f"  Q{quarter_num} {col.year} ({col.date()}): Revenue = NaN/None")
else:
    print("No quarterly data available")

# Get annual financials
print("\n\n[ANNUAL FINANCIALS]")
print("-" * 70)
annual_income = ticker.financials

if annual_income is not None and not annual_income.empty:
    print(f"Available years: {len(annual_income.columns)}")
    for i, col in enumerate(annual_income.columns):
        revenue = annual_income.loc['Total Revenue', col] if 'Total Revenue' in annual_income.index else None
        revenue_valid = revenue is not None and pd.notna(revenue)

        print(f"  {col.year} ({col.date()}): Revenue = {revenue:,.0f}" if revenue_valid else f"  {col.year} ({col.date()}): Revenue = NaN/None")
else:
    print("No annual data available")

# Detailed comparison for years with all 4 quarters
print("\n\n[QUARTERLY vs ANNUAL COMPARISON]")
print("-" * 70)

if quarterly_income is not None and annual_income is not None:
    # Group quarters by year
    years_available = sorted(list(set([col.year for col in quarterly_income.columns])), reverse=True)

    for year in years_available[:3]:  # Check last 3 years
        quarters = [col for col in quarterly_income.columns if col.year == year]

        print(f"\n{year}:")
        print(f"  Quarters available: {len(quarters)}")

        q_revenue_sum = 0
        q_count = 0

        for col in quarters:
            quarter_num = (col.month - 1) // 3 + 1
            revenue = quarterly_income.loc['Total Revenue', col] if 'Total Revenue' in quarterly_income.index else None
            revenue_valid = revenue is not None and pd.notna(revenue)

            if revenue_valid:
                q_revenue_sum += revenue
                q_count += 1
                print(f"    Q{quarter_num}: {revenue:,.0f}")
            else:
                print(f"    Q{quarter_num}: NaN/None")

        # Get annual
        annual_year = [col for col in annual_income.columns if col.year == year]
        if annual_year:
            col = annual_year[0]
            a_revenue = annual_income.loc['Total Revenue', col] if 'Total Revenue' in annual_income.index else None
            a_revenue_valid = a_revenue is not None and pd.notna(a_revenue)

            if a_revenue_valid:
                print(f"  Annual: {a_revenue:,.0f}")

                if q_count == 4 and q_revenue_sum > 0:
                    diff_pct = ((q_revenue_sum - a_revenue) / a_revenue) * 100
                    print(f"  Quarterly sum: {q_revenue_sum:,.0f}")
                    print(f"  Difference: {diff_pct:.1f}%")
                    print(f"  Status: {'PASS (within 2%)' if abs(diff_pct) <= 2 else 'FAIL (outside 2%)'}")
                else:
                    print(f"  Quarterly sum: {q_revenue_sum:,.0f} ({q_count}/4 quarters)")
                    print(f"  Status: Cannot validate (incomplete quarters)")
            else:
                print(f"  Annual: NaN/None")
        else:
            print(f"  Annual: Not available")

print("\n" + "="*70)
print("INSPECTION COMPLETE")
print("="*70)
