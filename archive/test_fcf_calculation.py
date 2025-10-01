"""
Test how yfinance calculates Free Cash Flow.
"""

import yfinance as yf
import pandas as pd

def test_fcf_calculation(symbol):
    """Test FCF calculation for a given symbol."""
    print(f"\n{'='*70}")
    print(f"Testing FCF Calculation for {symbol}")
    print('='*70)

    ticker = yf.Ticker(symbol)

    # Get quarterly cash flow
    quarterly_cf = ticker.quarterly_cashflow

    print("\n--- QUARTERLY CASH FLOW STATEMENT ---")
    print("\nAvailable fields:")
    print(quarterly_cf.index.tolist())

    # Get the most recent quarter
    if len(quarterly_cf.columns) > 0:
        recent_quarter = quarterly_cf.columns[0]
        print(f"\n\nMost Recent Quarter: {recent_quarter}")
        print("-" * 70)

        # Look for key fields
        fields_to_check = [
            'Operating Cash Flow',
            'Capital Expenditure',
            'Free Cash Flow',
            'Issuance Of Capital Stock',
            'Issuance Of Debt',
            'Repayment Of Debt',
            'Repurchase Of Capital Stock'
        ]

        for field in fields_to_check:
            if field in quarterly_cf.index:
                value = quarterly_cf.loc[field, recent_quarter]
                if pd.notna(value):
                    print(f"{field:40s}: {value:>20,.0f}")
                else:
                    print(f"{field:40s}: {'N/A':>20}")
            else:
                print(f"{field:40s}: {'NOT FOUND':>20}")

        # Manual calculation
        if 'Operating Cash Flow' in quarterly_cf.index and 'Capital Expenditure' in quarterly_cf.index:
            ocf = quarterly_cf.loc['Operating Cash Flow', recent_quarter]
            capex = quarterly_cf.loc['Capital Expenditure', recent_quarter]

            if pd.notna(ocf) and pd.notna(capex):
                manual_fcf = ocf + capex  # CapEx is usually negative
                print(f"\n{'Manual FCF Calculation:':40s}")
                print(f"{'OCF + CapEx':40s}: {manual_fcf:>20,.0f}")

                if 'Free Cash Flow' in quarterly_cf.index:
                    yf_fcf = quarterly_cf.loc['Free Cash Flow', recent_quarter]
                    if pd.notna(yf_fcf):
                        print(f"{'yfinance FCF':40s}: {yf_fcf:>20,.0f}")
                        diff = manual_fcf - yf_fcf
                        print(f"{'Difference':40s}: {diff:>20,.0f}")

                        if abs(diff) < 1000:  # Within 1000 rounding error
                            print("\n✅ Manual calculation matches yfinance!")
                        else:
                            print("\n⚠️ Discrepancy found!")

    # Test annual cash flow too
    print("\n\n--- ANNUAL CASH FLOW STATEMENT ---")
    annual_cf = ticker.cashflow

    if len(annual_cf.columns) > 0:
        recent_year = annual_cf.columns[0]
        print(f"\n\nMost Recent Year: {recent_year}")
        print("-" * 70)

        for field in fields_to_check:
            if field in annual_cf.index:
                value = annual_cf.loc[field, recent_year]
                if pd.notna(value):
                    print(f"{field:40s}: {value:>20,.0f}")
                else:
                    print(f"{field:40s}: {'N/A':>20}")
            else:
                print(f"{field:40s}: {'NOT FOUND':>20}")

        # Manual calculation for annual
        if 'Operating Cash Flow' in annual_cf.index and 'Capital Expenditure' in annual_cf.index:
            ocf = annual_cf.loc['Operating Cash Flow', recent_year]
            capex = annual_cf.loc['Capital Expenditure', recent_year]

            if pd.notna(ocf) and pd.notna(capex):
                manual_fcf = ocf + capex  # CapEx is usually negative
                print(f"\n{'Manual FCF Calculation:':40s}")
                print(f"{'OCF + CapEx':40s}: {manual_fcf:>20,.0f}")

                if 'Free Cash Flow' in annual_cf.index:
                    yf_fcf = annual_cf.loc['Free Cash Flow', recent_year]
                    if pd.notna(yf_fcf):
                        print(f"{'yfinance FCF':40s}: {yf_fcf:>20,.0f}")
                        diff = manual_fcf - yf_fcf
                        print(f"{'Difference':40s}: {diff:>20,.0f}")

                        if abs(diff) < 1000:
                            print("\n✅ Manual calculation matches yfinance!")
                        else:
                            print("\n⚠️ Discrepancy found!")


if __name__ == '__main__':
    # Test with multiple stocks
    test_stocks = [
        '2222.SR',  # Aramco
        '1120.SR',  # Al Rajhi Bank
        '7010.SR',  # STC
    ]

    for symbol in test_stocks:
        try:
            test_fcf_calculation(symbol)
        except Exception as e:
            print(f"\nError testing {symbol}: {e}")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
