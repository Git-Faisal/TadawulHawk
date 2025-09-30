"""
Analysis Engine for Saudi Stock Screener.
Calculates all metrics and generates JSON for website.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional
from collections import defaultdict

class StockAnalyzer:
    """Calculate all metrics for stock screening and analysis."""

    def __init__(self):
        """Initialize analyzer and load data."""
        print("Loading data files...")

        # Load CSV files
        self.stocks_df = pd.read_csv('exports/stocks.csv')
        self.prices_df = pd.read_csv('exports/price_history.csv')
        self.quarterly_df = pd.read_csv('exports/quarterly_fundamentals.csv')
        self.annual_df = pd.read_csv('exports/annual_fundamentals.csv')

        # Load valuation data (check if exists)
        val_path = Path('exports/valuation_data.csv')
        if val_path.exists():
            self.valuation_df = pd.read_csv(val_path)
        else:
            print("Warning: valuation_data.csv not found. Will use None for valuation metrics.")
            self.valuation_df = None

        print(f"Loaded {len(self.stocks_df)} stocks")

    def calculate_ltm(self, symbol: str, metric: str) -> Optional[float]:
        """
        Calculate Last Twelve Months (LTM) value for a metric.

        Args:
            symbol: Stock symbol
            metric: Metric name (revenue, net_income, etc.)

        Returns:
            LTM value or None
        """
        # Get last 4 quarters for this symbol
        stock_quarters = self.quarterly_df[
            self.quarterly_df['symbol'] == symbol
        ].sort_values('quarter_end_date', ascending=False).head(4)

        if len(stock_quarters) < 4:
            return None

        # Sum the metric across 4 quarters
        values = stock_quarters[metric].dropna()
        if len(values) == 0:
            return None

        return values.sum() if len(values) > 0 else None

    def calculate_cagr(self, start_value: float, end_value: float, years: int) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate.

        Args:
            start_value: Starting value
            end_value: Ending value
            years: Number of years

        Returns:
            CAGR as percentage or None
        """
        if not start_value or not end_value or start_value <= 0 or years <= 0:
            return None

        try:
            cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
            return round(cagr, 2)
        except:
            return None

    def calculate_yoy_growth(self, current: float, previous: float) -> Optional[float]:
        """Calculate Year-over-Year growth percentage."""
        if not previous or previous == 0:
            return None

        try:
            growth = ((current - previous) / abs(previous)) * 100
            return round(growth, 2)
        except:
            return None

    def calculate_margin_trend(self, symbol: str, margin_type: str) -> str:
        """
        Calculate margin trend (expanding/flat/contracting).

        Args:
            symbol: Stock symbol
            margin_type: 'gross', 'net', 'ocf', or 'fcf'

        Returns:
            'expanding', 'flat', or 'contracting'
        """
        # Get last 8 quarters
        stock_quarters = self.quarterly_df[
            self.quarterly_df['symbol'] == symbol
        ].sort_values('quarter_end_date', ascending=False).head(8)

        if len(stock_quarters) < 8:
            return 'unknown'

        # Split into recent 4Q and prior 4Q
        recent_4q = stock_quarters.head(4)
        prior_4q = stock_quarters.tail(4)

        # Calculate margins
        if margin_type == 'gross':
            numerator = 'gross_profit'
        elif margin_type == 'net':
            numerator = 'net_income'
        elif margin_type == 'ocf':
            numerator = 'operating_cash_flow'
        elif margin_type == 'fcf':
            numerator = 'free_cash_flow'
        else:
            return 'unknown'

        # Calculate average margins
        recent_margin = (recent_4q[numerator].sum() / recent_4q['revenue'].sum() * 100
                        if recent_4q['revenue'].sum() > 0 else None)
        prior_margin = (prior_4q[numerator].sum() / prior_4q['revenue'].sum() * 100
                       if prior_4q['revenue'].sum() > 0 else None)

        if recent_margin is None or prior_margin is None:
            return 'unknown'

        diff = recent_margin - prior_margin

        if diff > 2:
            return 'expanding'
        elif diff < -2:
            return 'contracting'
        else:
            return 'flat'

    def calculate_consistency(self, symbol: str, metric: str) -> Optional[float]:
        """
        Calculate growth consistency (std dev of quarterly YoY growth rates).
        Lower is better (more consistent).

        Args:
            symbol: Stock symbol
            metric: 'net_income' or 'free_cash_flow'

        Returns:
            Standard deviation or None
        """
        # Get quarterly data sorted by date
        quarters = self.quarterly_df[
            self.quarterly_df['symbol'] == symbol
        ].sort_values('quarter_end_date')

        if len(quarters) < 8:  # Need at least 2 years
            return None

        # Calculate YoY growth for each quarter
        yoy_growths = []
        for i in range(4, len(quarters)):
            current = quarters.iloc[i][metric]
            year_ago = quarters.iloc[i-4][metric]

            if pd.notna(current) and pd.notna(year_ago) and year_ago != 0:
                growth = ((current - year_ago) / abs(year_ago)) * 100
                yoy_growths.append(growth)

        if len(yoy_growths) < 3:
            return None

        return round(np.std(yoy_growths), 2)

    def calculate_52w_position_momentum(self, symbol: str) -> Optional[float]:
        """
        Calculate change in 52-week position over 3 months.

        Returns:
            Change in percentile points (positive = improving)
        """
        price_data = self.prices_df[self.prices_df['symbol'] == symbol].iloc[0]

        # Current percentile
        current_price = price_data['last_close_price']
        high_52w = price_data['week_52_high']
        low_52w = price_data['week_52_low']

        if pd.isna(current_price) or pd.isna(high_52w) or pd.isna(low_52w):
            return None

        if high_52w == low_52w:
            current_percentile = 50
        else:
            current_percentile = ((current_price - low_52w) / (high_52w - low_52w)) * 100

        # 3-month ago percentile
        price_3m = price_data['price_3m_ago']
        if pd.isna(price_3m):
            return None

        if high_52w == low_52w:
            ago_percentile = 50
        else:
            ago_percentile = ((price_3m - low_52w) / (high_52w - low_52w)) * 100

        momentum = current_percentile - ago_percentile
        return round(momentum, 2)

    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze a single stock and calculate all metrics.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with all calculated metrics
        """
        # Get base data
        stock_info = self.stocks_df[self.stocks_df['symbol'] == symbol].iloc[0]
        price_data = self.prices_df[self.prices_df['symbol'] == symbol].iloc[0]

        # Get valuation data if available
        if self.valuation_df is not None:
            val_row = self.valuation_df[self.valuation_df['symbol'] == symbol]
            if not val_row.empty:
                val_data = val_row.iloc[0]
                market_cap = val_data.get('market_cap')
                total_debt = val_data.get('total_debt', 0)
                total_cash = val_data.get('total_cash', 0)
                book_value = val_data.get('book_value')
            else:
                market_cap = None
                total_debt = 0
                total_cash = 0
                book_value = None
        else:
            market_cap = None
            total_debt = 0
            total_cash = 0
            book_value = None

        # Calculate LTM metrics
        ltm_revenue = self.calculate_ltm(symbol, 'revenue')
        ltm_gross_profit = self.calculate_ltm(symbol, 'gross_profit')
        ltm_net_income = self.calculate_ltm(symbol, 'net_income')
        ltm_ocf = self.calculate_ltm(symbol, 'operating_cash_flow')
        ltm_fcf = self.calculate_ltm(symbol, 'free_cash_flow')

        # Get annual data for CAGR calculations
        annual_data = self.annual_df[
            self.annual_df['symbol'] == symbol
        ].sort_values('fiscal_year', ascending=False)

        # Price metrics
        current_price = price_data['last_close_price']
        high_52w = price_data['week_52_high']
        low_52w = price_data['week_52_low']

        # Calculate 52w ratio
        ratio_52w = round(high_52w / low_52w, 2) if (pd.notna(high_52w) and pd.notna(low_52w) and low_52w > 0) else None

        # Calculate price percentile
        if pd.notna(current_price) and pd.notna(high_52w) and pd.notna(low_52w):
            if high_52w != low_52w:
                percentile_52w = round(((current_price - low_52w) / (high_52w - low_52w)) * 100, 2)
            else:
                percentile_52w = 50.0
        else:
            percentile_52w = None

        # Calculate volatility
        if pd.notna(high_52w) and pd.notna(low_52w):
            avg_price = (high_52w + low_52w) / 2
            volatility = round((high_52w - low_52w) / avg_price, 3) if avg_price > 0 else None
        else:
            volatility = None

        # Valuation ratios
        pe_ltm = None
        pb = None
        ev_fcf = None

        if market_cap:
            if ltm_net_income and ltm_net_income > 0:
                pe_ltm = round(market_cap / ltm_net_income, 2)

            if book_value and book_value > 0:
                pb = round(market_cap / book_value, 2)

            if ltm_fcf and ltm_fcf > 0:
                ev = market_cap + total_debt - total_cash
                ev_fcf = round(ev / ltm_fcf, 2)

        # Growth calculations (CAGR)
        growth_metrics = {}

        if len(annual_data) >= 4:
            # 3-year CAGR
            current_year = annual_data.iloc[0]
            year_3_ago = annual_data.iloc[3]

            growth_metrics['revenue_cagr_3y'] = self.calculate_cagr(
                year_3_ago['revenue'], current_year['revenue'], 3)
            growth_metrics['gross_profit_cagr_3y'] = self.calculate_cagr(
                year_3_ago['gross_profit'], current_year['gross_profit'], 3)
            growth_metrics['net_income_cagr_3y'] = self.calculate_cagr(
                year_3_ago['net_income'], current_year['net_income'], 3)
            growth_metrics['ocf_cagr_3y'] = self.calculate_cagr(
                year_3_ago['operating_cash_flow'], current_year['operating_cash_flow'], 3)
            growth_metrics['fcf_cagr_3y'] = self.calculate_cagr(
                year_3_ago['free_cash_flow'], current_year['free_cash_flow'], 3)

        if len(annual_data) >= 5:
            # 4-year CAGR
            current_year = annual_data.iloc[0]
            year_4_ago = annual_data.iloc[4]

            growth_metrics['revenue_cagr_4y'] = self.calculate_cagr(
                year_4_ago['revenue'], current_year['revenue'], 4)
            growth_metrics['gross_profit_cagr_4y'] = self.calculate_cagr(
                year_4_ago['gross_profit'], current_year['gross_profit'], 4)
            growth_metrics['net_income_cagr_4y'] = self.calculate_cagr(
                year_4_ago['net_income'], current_year['net_income'], 4)
            growth_metrics['ocf_cagr_4y'] = self.calculate_cagr(
                year_4_ago['operating_cash_flow'], current_year['operating_cash_flow'], 4)
            growth_metrics['fcf_cagr_4y'] = self.calculate_cagr(
                year_4_ago['free_cash_flow'], current_year['free_cash_flow'], 4)

        if len(annual_data) >= 2:
            # YoY growth
            current_year = annual_data.iloc[0]
            last_year = annual_data.iloc[1]

            growth_metrics['revenue_yoy'] = self.calculate_yoy_growth(
                current_year['revenue'], last_year['revenue'])
            growth_metrics['gross_profit_yoy'] = self.calculate_yoy_growth(
                current_year['gross_profit'], last_year['gross_profit'])
            growth_metrics['net_income_yoy'] = self.calculate_yoy_growth(
                current_year['net_income'], last_year['net_income'])
            growth_metrics['ocf_yoy'] = self.calculate_yoy_growth(
                current_year['operating_cash_flow'], last_year['operating_cash_flow'])
            growth_metrics['fcf_yoy'] = self.calculate_yoy_growth(
                current_year['free_cash_flow'], last_year['free_cash_flow'])

        # PEG ratio
        peg = None
        if pe_ltm and growth_metrics.get('net_income_cagr_3y'):
            if growth_metrics['net_income_cagr_3y'] > 0:
                peg = round(pe_ltm / growth_metrics['net_income_cagr_3y'], 2)

        # Margins (LTM)
        gross_margin = round((ltm_gross_profit / ltm_revenue * 100), 2) if ltm_revenue and ltm_revenue > 0 else None
        net_margin = round((ltm_net_income / ltm_revenue * 100), 2) if ltm_revenue and ltm_revenue > 0 else None
        ocf_margin = round((ltm_ocf / ltm_revenue * 100), 2) if ltm_revenue and ltm_revenue > 0 else None
        fcf_margin = round((ltm_fcf / ltm_revenue * 100), 2) if ltm_revenue and ltm_revenue > 0 else None

        # Margin trends
        gross_trend = self.calculate_margin_trend(symbol, 'gross')
        net_trend = self.calculate_margin_trend(symbol, 'net')
        ocf_trend = self.calculate_margin_trend(symbol, 'ocf')
        fcf_trend = self.calculate_margin_trend(symbol, 'fcf')

        # Quality metrics
        net_income_consistency = self.calculate_consistency(symbol, 'net_income')
        fcf_consistency = self.calculate_consistency(symbol, 'free_cash_flow')

        # Position momentum
        position_momentum = self.calculate_52w_position_momentum(symbol)

        # Compile all metrics
        return {
            'symbol': symbol,
            'company_name': stock_info['company_name'],
            'sector': stock_info['sector'],
            'industry': stock_info['industry'],
            'exchange': stock_info['exchange'],

            'price': {
                'current': float(current_price) if pd.notna(current_price) else None,
                '52w_high': float(high_52w) if pd.notna(high_52w) else None,
                '52w_low': float(low_52w) if pd.notna(low_52w) else None,
                '52w_ratio': ratio_52w,
                'percentile_52w': percentile_52w,
                'volatility': volatility,
                'position_momentum': position_momentum
            },

            'valuation': {
                'market_cap': float(market_cap) if market_cap else None,
                'pe_ltm': pe_ltm,
                'pb': pb,
                'ev_fcf': ev_fcf,
                'peg': peg
            },

            'growth': growth_metrics,

            'margins': {
                'gross_ltm': gross_margin,
                'gross_trend': gross_trend,
                'net_ltm': net_margin,
                'net_trend': net_trend,
                'ocf_ltm': ocf_margin,
                'ocf_trend': ocf_trend,
                'fcf_ltm': fcf_margin,
                'fcf_trend': fcf_trend
            },

            'quality': {
                'net_income_consistency': net_income_consistency,
                'fcf_consistency': fcf_consistency
            }
        }

    def calculate_aggregates(self, stocks_analyzed: List[Dict]) -> Dict[str, Any]:
        """
        Calculate sector and industry aggregates.

        Args:
            stocks_analyzed: List of analyzed stock dicts

        Returns:
            Dict with sector and industry stats
        """
        sector_data = defaultdict(list)
        industry_data = defaultdict(list)

        # Group by sector and industry
        for stock in stocks_analyzed:
            sector = stock['sector']
            industry = stock['industry']

            if sector and sector != 'nan':
                sector_data[sector].append(stock)
            if industry and industry != 'nan':
                industry_data[industry].append(stock)

        # Calculate sector aggregates
        sector_overview = {}
        for sector, stocks in sector_data.items():
            sector_overview[sector] = self._calculate_group_stats(stocks)
            sector_overview[sector]['stock_count'] = len(stocks)

        # Calculate industry aggregates
        industry_overview = {}
        for industry, stocks in industry_data.items():
            industry_overview[industry] = self._calculate_group_stats(stocks)
            industry_overview[industry]['stock_count'] = len(stocks)

        return {
            'sector_overview': sector_overview,
            'industry_overview': industry_overview
        }

    def _calculate_group_stats(self, stocks: List[Dict]) -> Dict[str, float]:
        """Calculate average and median for a group of stocks."""

        def safe_avg(values):
            valid = [v for v in values if v is not None and not np.isnan(v)]
            return round(np.mean(valid), 2) if valid else None

        def safe_median(values):
            valid = [v for v in values if v is not None and not np.isnan(v)]
            return round(np.median(valid), 2) if valid else None

        # Extract all metrics
        pe_values = [s['valuation']['pe_ltm'] for s in stocks]
        pb_values = [s['valuation']['pb'] for s in stocks]
        ev_fcf_values = [s['valuation']['ev_fcf'] for s in stocks]
        revenue_cagr_3y = [s['growth'].get('revenue_cagr_3y') for s in stocks]
        net_margin_values = [s['margins']['net_ltm'] for s in stocks]
        volatility_values = [s['price']['volatility'] for s in stocks]

        return {
            'pe_avg': safe_avg(pe_values),
            'pe_median': safe_median(pe_values),
            'pb_avg': safe_avg(pb_values),
            'pb_median': safe_median(pb_values),
            'ev_fcf_avg': safe_avg(ev_fcf_values),
            'ev_fcf_median': safe_median(ev_fcf_values),
            'revenue_cagr_3y_avg': safe_avg(revenue_cagr_3y),
            'revenue_cagr_3y_median': safe_median(revenue_cagr_3y),
            'net_margin_avg': safe_avg(net_margin_values),
            'net_margin_median': safe_median(net_margin_values),
            'volatility_avg': safe_avg(volatility_values),
            'volatility_median': safe_median(volatility_values)
        }

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run full analysis on all stocks.

        Returns:
            Complete analysis data ready for JSON export
        """
        print(f"\nAnalyzing {len(self.stocks_df)} stocks...")

        analyzed_stocks = []
        success_count = 0
        error_count = 0

        for idx, row in self.stocks_df.iterrows():
            symbol = row['symbol']
            try:
                stock_data = self.analyze_stock(symbol)
                analyzed_stocks.append(stock_data)
                success_count += 1

                if (success_count) % 50 == 0:
                    print(f"  Analyzed {success_count}/{len(self.stocks_df)} stocks...")

            except Exception as e:
                print(f"  Error analyzing {symbol}: {e}")
                error_count += 1

        print(f"\nAnalysis complete: {success_count} success, {error_count} errors")

        # Calculate aggregates
        print("Calculating sector and industry aggregates...")
        aggregates = self.calculate_aggregates(analyzed_stocks)

        # Compile final output
        output = {
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'total_stocks': len(analyzed_stocks),
                'tadawul_count': len([s for s in analyzed_stocks if s['exchange'] == 'Tadawul']),
                'nomu_count': len([s for s in analyzed_stocks if s['exchange'] == 'NOMU'])
            },
            'sector_overview': aggregates['sector_overview'],
            'industry_overview': aggregates['industry_overview'],
            'stocks': analyzed_stocks
        }

        return output

    def export_to_json(self, output_path: str = 'docs/data/stocks_analysis.json'):
        """
        Run analysis and export to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        # Run analysis
        data = self.run_analysis()

        # Create output directory
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Export to JSON
        print(f"\nExporting to {output_path}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Exported successfully!")
        print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
        print(f"  Stocks: {data['metadata']['total_stocks']}")
        print(f"  Sectors: {len(data['sector_overview'])}")
        print(f"  Industries: {len(data['industry_overview'])}")


def main():
    """Main execution."""
    print("="*70)
    print("SAUDI STOCK ANALYSIS ENGINE")
    print("="*70)

    # Initialize analyzer
    analyzer = StockAnalyzer()

    # Run analysis and export
    analyzer.export_to_json()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()