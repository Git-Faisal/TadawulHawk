// Global data store
let stocksData = null;
let tadawulStocks = [];
let nomuStocks = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadData();
        renderMetadata();
        renderSectorOverview();
        renderIndustryOverview();
        renderStocksTables();
        setupEventListeners();
    } catch (error) {
        console.error('Error initializing app:', error);
        alert('Error loading data. Please check console for details.');
    }
});

// Load JSON data
async function loadData() {
    console.log('Loading data...');
    const response = await fetch('data/stocks_analysis.json');
    console.log('Response:', response);
    stocksData = await response.json();
    console.log('Data loaded:', stocksData);
    console.log('Total stocks:', stocksData.stocks.length);

    // Separate stocks by exchange
    tadawulStocks = stocksData.stocks.filter(s => s.exchange === 'Tadawul');
    nomuStocks = stocksData.stocks.filter(s => s.exchange === 'NOMU');
    console.log('Tadawul:', tadawulStocks.length, 'NOMU:', nomuStocks.length);
}

// Render metadata
function renderMetadata() {
    const metadataEl = document.getElementById('metadata');
    const date = new Date(stocksData.metadata.generated_date).toLocaleString();
    metadataEl.innerHTML = `
        <p>Generated: ${date} | Total Stocks: ${stocksData.metadata.total_stocks}
        (Tadawul: ${stocksData.metadata.tadawul_count}, NOMU: ${stocksData.metadata.nomu_count})</p>
        <p style="font-style: italic;">Created by Faisal Alkhorayef</p>
    `;
}

// Render sector overview table
function renderSectorOverview() {
    const tbody = document.getElementById('sector-body');
    const sectors = Object.entries(stocksData.sector_overview)
        .sort((a, b) => b[1].stock_count - a[1].stock_count);

    tbody.innerHTML = sectors.map(([sector, stats]) => `
        <tr>
            <td><strong>${sector}</strong></td>
            <td>${stats.stock_count}</td>
            <td>${formatNumber(stats.pe_avg)}</td>
            <td>${formatNumber(stats.pe_median)}</td>
            <td>${formatNumber(stats.pb_avg)}</td>
            <td>${formatNumber(stats.pb_median)}</td>
            <td>${formatNumber(stats.ev_fcf_avg)}</td>
            <td>${formatNumber(stats.ev_fcf_median)}</td>
            <td>${formatPercent(stats.revenue_cagr_3y_avg)}</td>
            <td>${formatPercent(stats.revenue_cagr_3y_median)}</td>
            <td>${formatPercent(stats.net_margin_avg)}</td>
            <td>${formatPercent(stats.net_margin_median)}</td>
            <td>${formatNumber(stats.volatility_avg)}</td>
            <td>${formatNumber(stats.volatility_median)}</td>
        </tr>
    `).join('');
}

// Render industry overview table (top 20)
function renderIndustryOverview() {
    const tbody = document.getElementById('industry-body');
    const industries = Object.entries(stocksData.industry_overview)
        .sort((a, b) => b[1].stock_count - a[1].stock_count)
        .slice(0, 20);

    tbody.innerHTML = industries.map(([industry, stats]) => `
        <tr>
            <td><strong>${industry}</strong></td>
            <td>${stats.stock_count}</td>
            <td>${formatNumber(stats.pe_avg)}</td>
            <td>${formatNumber(stats.pe_median)}</td>
            <td>${formatNumber(stats.pb_avg)}</td>
            <td>${formatNumber(stats.pb_median)}</td>
            <td>${formatNumber(stats.ev_fcf_avg)}</td>
            <td>${formatNumber(stats.ev_fcf_median)}</td>
            <td>${formatPercent(stats.revenue_cagr_3y_avg)}</td>
            <td>${formatPercent(stats.revenue_cagr_3y_median)}</td>
            <td>${formatPercent(stats.net_margin_avg)}</td>
            <td>${formatPercent(stats.net_margin_median)}</td>
            <td>${formatNumber(stats.volatility_avg)}</td>
            <td>${formatNumber(stats.volatility_median)}</td>
        </tr>
    `).join('');
}

// Render stock tables
function renderStocksTables() {
    renderStocksTable('tadawul', tadawulStocks);
    renderStocksTable('nomu', nomuStocks);
    populateFilters('tadawul', tadawulStocks);
    populateFilters('nomu', nomuStocks);
}

// Render a stock table
function renderStocksTable(exchange, stocks) {
    const tbody = document.getElementById(`${exchange}-body`);

    if (stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="13" class="empty-state">No stocks to display</td></tr>';
        return;
    }

    tbody.innerHTML = stocks.map(stock => `
        <tr class="stock-row" data-symbol="${stock.symbol}">
            <td><strong>${stock.symbol}</strong></td>
            <td>${stock.company_name}</td>
            <td>${stock.sector || '-'}</td>
            <td>${stock.industry || '-'}</td>
            <td class="number-value">${formatNumber(stock.price.current)}</td>
            <td class="number-value">${formatNumber(stock.price['52w_ratio'])}</td>
            <td class="number-value">${formatPercent(stock.price.percentile_52w)}</td>
            <td class="number-value">${formatNumber(stock.price.volatility)}</td>
            <td class="number-value">${formatNumber(stock.valuation.pe_ltm)}</td>
            <td class="number-value">${formatNumber(stock.valuation.pb)}</td>
            <td class="number-value">${formatNumber(stock.valuation.ev_fcf)}</td>
            <td class="number-value">${formatNumber(stock.valuation.peg)}</td>
            <td><button class="btn-detail" data-symbol="${stock.symbol}" data-exchange="${exchange}">Details</button></td>
        </tr>
    `).join('');

    // Add click handlers
    tbody.querySelectorAll('.btn-detail').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const symbol = btn.dataset.symbol;
            const exchange = btn.dataset.exchange;
            toggleDetails(symbol, exchange);
        });
    });

    tbody.querySelectorAll('.stock-row').forEach(row => {
        row.addEventListener('click', () => {
            const symbol = row.dataset.symbol;
            toggleDetails(symbol, exchange);
        });
    });
}

// Toggle stock details
function toggleDetails(symbol, exchange) {
    const tbody = document.getElementById(`${exchange}-body`);
    const stockRow = tbody.querySelector(`tr[data-symbol="${symbol}"]`);
    const existingDetailRow = tbody.querySelector(`tr.detail-row[data-symbol="${symbol}"]`);

    if (existingDetailRow) {
        // Close details
        existingDetailRow.remove();
        stockRow.classList.remove('expanded');
    } else {
        // Open details
        const stock = (exchange === 'tadawul' ? tadawulStocks : nomuStocks)
            .find(s => s.symbol === symbol);
        const detailRow = createDetailRow(stock);
        stockRow.after(detailRow);
        stockRow.classList.add('expanded');
    }
}

// Create detail row
function createDetailRow(stock) {
    const template = document.getElementById('stock-detail-template');
    const clone = template.content.cloneNode(true);
    const tr = clone.querySelector('tr');
    tr.dataset.symbol = stock.symbol;
    tr.classList.add('visible');

    // Populate data fields
    populateDetailField(clone, 'price.current', formatNumber(stock.price.current));
    populateDetailField(clone, 'price.52w_high', formatNumber(stock.price['52w_high']));
    populateDetailField(clone, 'price.52w_low', formatNumber(stock.price['52w_low']));
    populateDetailField(clone, 'price.position_momentum', formatPercent(stock.price.position_momentum));

    populateDetailField(clone, 'valuation.market_cap', formatLargeNumber(stock.valuation.market_cap));
    populateDetailField(clone, 'valuation.enterprise_value', formatLargeNumber(stock.valuation.enterprise_value));
    populateDetailField(clone, 'valuation.total_debt', formatLargeNumber(stock.valuation.total_debt));
    populateDetailField(clone, 'valuation.total_cash', formatLargeNumber(stock.valuation.total_cash));
    populateDetailField(clone, 'valuation.balance_sheet_date', stock.valuation.balance_sheet_date || 'N/A');
    populateDetailField(clone, 'valuation.pe_ltm', formatNumber(stock.valuation.pe_ltm));
    populateDetailField(clone, 'valuation.pb', formatNumber(stock.valuation.pb));
    populateDetailField(clone, 'valuation.ev_fcf', formatNumber(stock.valuation.ev_fcf));
    populateDetailField(clone, 'valuation.peg', formatNumber(stock.valuation.peg));

    populateDetailField(clone, 'growth.revenue_cagr_3y', formatPercent(stock.growth.revenue_cagr_3y));
    populateDetailField(clone, 'growth.revenue_cagr_4y', formatPercent(stock.growth.revenue_cagr_4y));
    populateDetailField(clone, 'growth.revenue_yoy', formatPercent(stock.growth.revenue_yoy));
    populateDetailField(clone, 'growth.net_income_cagr_3y', formatPercent(stock.growth.net_income_cagr_3y));
    populateDetailField(clone, 'growth.fcf_cagr_3y', formatPercent(stock.growth.fcf_cagr_3y));

    populateDetailField(clone, 'margins.gross_ltm', formatPercent(stock.margins.gross_ltm));
    populateDetailField(clone, 'margins.gross_trend', stock.margins.gross_trend, true);
    populateDetailField(clone, 'margins.net_ltm', formatPercent(stock.margins.net_ltm));
    populateDetailField(clone, 'margins.net_trend', stock.margins.net_trend, true);
    populateDetailField(clone, 'margins.ocf_ltm', formatPercent(stock.margins.ocf_ltm));
    populateDetailField(clone, 'margins.ocf_trend', stock.margins.ocf_trend, true);
    populateDetailField(clone, 'margins.fcf_ltm', formatPercent(stock.margins.fcf_ltm));
    populateDetailField(clone, 'margins.fcf_trend', stock.margins.fcf_trend, true);

    populateDetailField(clone, 'quality.net_income_consistency', formatNumber(stock.quality.net_income_consistency));
    populateDetailField(clone, 'quality.fcf_consistency', formatNumber(stock.quality.fcf_consistency));

    // Populate annual history table
    const annualTable = clone.querySelector('[data-field="historical.annual"]');
    if (annualTable && stock.historical && stock.historical.annual) {
        annualTable.innerHTML = createHistoryTable(stock.historical.annual, 'annual');
    }

    // Populate quarterly history table
    const quarterlyTable = clone.querySelector('[data-field="historical.quarterly"]');
    if (quarterlyTable && stock.historical && stock.historical.quarterly) {
        quarterlyTable.innerHTML = createHistoryTable(stock.historical.quarterly, 'quarterly');
    }

    return clone;
}

// Create history table HTML (transposed: periods as columns)
function createHistoryTable(data, type) {
    if (!data || data.length === 0) {
        return '<tr><td colspan="6" class="empty-state">No data available</td></tr>';
    }

    // Sort data by period (oldest to newest for left-to-right reading)
    const sortedData = [...data].sort((a, b) => {
        if (type === 'annual') {
            return a.fiscal_year - b.fiscal_year;
        } else {
            // For quarterly: sort by year, then quarter
            if (a.fiscal_year === b.fiscal_year) {
                return a.fiscal_quarter - b.fiscal_quarter;
            }
            return a.fiscal_year - b.fiscal_year;
        }
    });

    // Create period labels
    const periods = sortedData.map(row => {
        return type === 'annual'
            ? `FY${row.fiscal_year}`
            : `FY${row.fiscal_year} Q${row.fiscal_quarter}`;
    });

    // Build header row
    const headerRow = '<tr><th>Metric</th>' + periods.map(p => `<th>${p}</th>`).join('') + '</tr>';

    // Build metric rows with margins
    const metrics = [
        { label: 'Revenue', field: 'revenue', showMargin: false },
        { label: 'Gross Profit', field: 'gross_profit', showMargin: true },
        { label: 'Net Income', field: 'net_income', showMargin: true },
        { label: 'OCF', field: 'operating_cash_flow', showMargin: true },
        { label: 'CapEx', field: 'capital_expenditure', showMargin: false },
        { label: 'FCF', field: 'free_cash_flow', showMargin: true }
    ];

    const metricRows = metrics.map(metric => {
        // Main metric row
        const values = sortedData.map(row => {
            const formattedValue = formatLargeNumber(row[metric.field]);
            const isNegative = formattedValue.startsWith('(');
            return `<td class="number-value ${isNegative ? 'negative' : ''}">${formattedValue}</td>`;
        }).join('');
        let rows = `<tr><td><strong>${metric.label}</strong></td>${values}</tr>`;

        // Add margin row if applicable
        if (metric.showMargin) {
            const marginValues = sortedData.map(row => {
                const metricValue = row[metric.field];
                const revenue = row['revenue'];
                if (metricValue != null && revenue != null && revenue !== 0) {
                    const margin = (metricValue / revenue * 100).toFixed(1);
                    return `<td class="number-value margin-row">${margin}%</td>`;
                } else {
                    return `<td class="number-value margin-row">-</td>`;
                }
            }).join('');
            rows += `<tr><td style="padding-left: 20px; font-style: italic; color: #888; font-size: 0.85em;">margin</td>${marginValues}</tr>`;
        }

        return rows;
    }).join('');

    return `<thead>${headerRow}</thead><tbody>${metricRows}</tbody>`;
}

// Populate detail field
function populateDetailField(clone, fieldPath, value, isTrend = false) {
    const el = clone.querySelector(`[data-field="${fieldPath}"]`);
    if (el) {
        if (isTrend) {
            el.textContent = value || '';
            el.className = `trend ${value}`;
        } else {
            el.textContent = value;
            // Apply color coding for numbers
            if (typeof value === 'string' && value.includes('%')) {
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    if (numValue > 0) el.classList.add('positive');
                    else if (numValue < 0) el.classList.add('negative');
                    else el.classList.add('neutral');
                }
            }
        }
    }
}

// Populate filter dropdowns
function populateFilters(exchange, stocks) {
    const sectorFilter = document.getElementById(`${exchange}-sector-filter`);
    const industryFilter = document.getElementById(`${exchange}-industry-filter`);

    // Get unique sectors and industries
    const sectors = [...new Set(stocks.map(s => s.sector).filter(Boolean))].sort();
    const industries = [...new Set(stocks.map(s => s.industry).filter(Boolean))].sort();

    // Populate sectors
    sectors.forEach(sector => {
        const option = document.createElement('option');
        option.value = sector;
        option.textContent = sector;
        sectorFilter.appendChild(option);
    });

    // Populate industries
    industries.forEach(industry => {
        const option = document.createElement('option');
        option.value = industry;
        option.textContent = industry;
        industryFilter.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Tadawul filters
    document.getElementById('tadawul-sector-filter').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-industry-filter').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-search').addEventListener('input', () => filterStocks('tadawul'));
    document.getElementById('tadawul-52w-filter').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-filter-ni-positive').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-filter-ni-growing').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-filter-fcf-positive').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-filter-fcf-growing').addEventListener('change', () => filterStocks('tadawul'));
    document.getElementById('tadawul-clear-filters').addEventListener('click', () => clearFilters('tadawul'));
    document.getElementById('tadawul-export-csv').addEventListener('click', () => exportToCSV('tadawul'));

    // NOMU filters
    document.getElementById('nomu-sector-filter').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-industry-filter').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-search').addEventListener('input', () => filterStocks('nomu'));
    document.getElementById('nomu-52w-filter').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-filter-ni-positive').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-filter-ni-growing').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-filter-fcf-positive').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-filter-fcf-growing').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-clear-filters').addEventListener('click', () => clearFilters('nomu'));
    document.getElementById('nomu-export-csv').addEventListener('click', () => exportToCSV('nomu'));

    // Sorting
    setupSorting('tadawul');
    setupSorting('nomu');
}

// Quality filter helper functions
function checkNetIncomeAlwaysPositive(stock) {
    if (!stock.historical || !stock.historical.annual || stock.historical.annual.length === 0) {
        return false;
    }
    return stock.historical.annual.every(year =>
        year.net_income != null && year.net_income > 0
    );
}

function checkNetIncomeGrowing(stock) {
    if (!stock.historical || !stock.historical.annual || stock.historical.annual.length < 2) {
        return false;
    }
    const sorted = [...stock.historical.annual].sort((a, b) => a.fiscal_year - b.fiscal_year);
    const oldest = sorted[0].net_income;
    const newest = sorted[sorted.length - 1].net_income;
    return oldest != null && newest != null && oldest > 0 && newest > oldest;
}

function checkFCFAlwaysPositive(stock) {
    if (!stock.historical || !stock.historical.annual || stock.historical.annual.length === 0) {
        return false;
    }
    return stock.historical.annual.every(year =>
        year.free_cash_flow != null && year.free_cash_flow > 0
    );
}

function checkFCFGrowing(stock) {
    if (!stock.historical || !stock.historical.annual || stock.historical.annual.length < 2) {
        return false;
    }
    const sorted = [...stock.historical.annual].sort((a, b) => a.fiscal_year - b.fiscal_year);
    const oldest = sorted[0].free_cash_flow;
    const newest = sorted[sorted.length - 1].free_cash_flow;
    return oldest != null && newest != null && oldest > 0 && newest > oldest;
}

// Filter stocks
function filterStocks(exchange) {
    const sectorFilter = document.getElementById(`${exchange}-sector-filter`).value;
    const industryFilter = document.getElementById(`${exchange}-industry-filter`).value;
    const searchText = document.getElementById(`${exchange}-search`).value.toLowerCase();
    const percentile52wFilter = document.getElementById(`${exchange}-52w-filter`).value;

    // Quality filters
    const filterNIPositive = document.getElementById(`${exchange}-filter-ni-positive`).checked;
    const filterNIGrowing = document.getElementById(`${exchange}-filter-ni-growing`).checked;
    const filterFCFPositive = document.getElementById(`${exchange}-filter-fcf-positive`).checked;
    const filterFCFGrowing = document.getElementById(`${exchange}-filter-fcf-growing`).checked;

    const allStocks = exchange === 'tadawul' ? tadawulStocks : nomuStocks;

    const filtered = allStocks.filter(stock => {
        const matchSector = !sectorFilter || stock.sector === sectorFilter;
        const matchIndustry = !industryFilter || stock.industry === industryFilter;
        const matchSearch = !searchText ||
            stock.symbol.toLowerCase().includes(searchText) ||
            stock.company_name.toLowerCase().includes(searchText);

        // 52W percentile filter
        let match52w = true;
        if (percentile52wFilter) {
            const percentile = stock.price.percentile_52w;
            if (percentile != null) {
                const [min, max] = percentile52wFilter.split('-').map(Number);
                match52w = percentile >= min && percentile <= max;
            } else {
                match52w = false;
            }
        }

        // Quality filter checks
        const matchNIPositive = !filterNIPositive || checkNetIncomeAlwaysPositive(stock);
        const matchNIGrowing = !filterNIGrowing || checkNetIncomeGrowing(stock);
        const matchFCFPositive = !filterFCFPositive || checkFCFAlwaysPositive(stock);
        const matchFCFGrowing = !filterFCFGrowing || checkFCFGrowing(stock);

        return matchSector && matchIndustry && matchSearch && match52w &&
               matchNIPositive && matchNIGrowing && matchFCFPositive && matchFCFGrowing;
    });

    renderStocksTable(exchange, filtered);
}

// Clear filters
function clearFilters(exchange) {
    document.getElementById(`${exchange}-sector-filter`).value = '';
    document.getElementById(`${exchange}-industry-filter`).value = '';
    document.getElementById(`${exchange}-search`).value = '';
    document.getElementById(`${exchange}-52w-filter`).value = '';
    document.getElementById(`${exchange}-filter-ni-positive`).checked = false;
    document.getElementById(`${exchange}-filter-ni-growing`).checked = false;
    document.getElementById(`${exchange}-filter-fcf-positive`).checked = false;
    document.getElementById(`${exchange}-filter-fcf-growing`).checked = false;
    filterStocks(exchange);
}

// Setup sorting
function setupSorting(exchange) {
    const table = document.getElementById(`${exchange}-table`);
    const headers = table.querySelectorAll('th[data-sort]');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.dataset.sort;
            sortStocks(exchange, sortKey);
        });
    });
}

// Sort stocks
let currentSort = { tadawul: null, nomu: null };
function sortStocks(exchange, sortKey) {
    const stocks = exchange === 'tadawul' ? tadawulStocks : nomuStocks;

    // Toggle sort direction
    const isAscending = currentSort[exchange] === sortKey;
    currentSort[exchange] = isAscending ? null : sortKey;

    const sorted = [...stocks].sort((a, b) => {
        const aVal = getNestedValue(a, sortKey);
        const bVal = getNestedValue(b, sortKey);

        // Handle null/undefined
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;

        // Compare
        if (typeof aVal === 'string') {
            return isAscending ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        } else {
            return isAscending ? bVal - aVal : aVal - bVal;
        }
    });

    // Update the source array with sorted data
    if (exchange === 'tadawul') {
        tadawulStocks = sorted;
    } else {
        nomuStocks = sorted;
    }

    // Always re-apply filters to maintain filter state
    filterStocks(exchange);
}

// Export to CSV
function exportToCSV(exchange) {
    const stocks = exchange === 'tadawul' ? tadawulStocks : nomuStocks;

    const headers = [
        'Symbol', 'Company Name', 'Sector', 'Industry', 'Price', '52W Ratio', '52W %',
        'Volatility', 'P/E', 'P/B', 'EV/FCF', 'PEG', 'Market Cap',
        'Revenue CAGR 3Y', 'Net Income CAGR 3Y', 'FCF CAGR 3Y',
        'Gross Margin', 'Net Margin', 'OCF Margin', 'FCF Margin',
        'Gross Trend', 'Net Trend', 'OCF Trend', 'FCF Trend',
        'Net Income Consistency', 'FCF Consistency', 'Position Momentum'
    ];

    const rows = stocks.map(stock => [
        stock.symbol,
        stock.company_name,
        stock.sector || '',
        stock.industry || '',
        stock.price.current || '',
        stock.price['52w_ratio'] || '',
        stock.price.percentile_52w || '',
        stock.price.volatility || '',
        stock.valuation.pe_ltm || '',
        stock.valuation.pb || '',
        stock.valuation.ev_fcf || '',
        stock.valuation.peg || '',
        stock.valuation.market_cap || '',
        stock.growth.revenue_cagr_3y || '',
        stock.growth.net_income_cagr_3y || '',
        stock.growth.fcf_cagr_3y || '',
        stock.margins.gross_ltm || '',
        stock.margins.net_ltm || '',
        stock.margins.ocf_ltm || '',
        stock.margins.fcf_ltm || '',
        stock.margins.gross_trend || '',
        stock.margins.net_trend || '',
        stock.margins.ocf_trend || '',
        stock.margins.fcf_trend || '',
        stock.quality.net_income_consistency || '',
        stock.quality.fcf_consistency || '',
        stock.price.position_momentum || ''
    ]);

    const csv = [headers, ...rows]
        .map(row => row.map(cell => `"${cell}"`).join(','))
        .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${exchange}_stocks_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

// Helper: Get nested object value
function getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

// Helper: Format number with commas and brackets for negatives
function formatNumber(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        const isNegative = value < 0;
        const absValue = Math.abs(value);
        const fixed = absValue.toFixed(2);
        const [intPart, decPart] = fixed.split('.');
        const withCommas = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        const formatted = `${withCommas}.${decPart}`;
        return isNegative ? `(${formatted})` : formatted;
    }
    return value;
}

// Helper: Format percentage with commas and brackets for negatives
function formatPercent(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        const isNegative = value < 0;
        const absValue = Math.abs(value);
        const fixed = absValue.toFixed(2);
        const [intPart, decPart] = fixed.split('.');
        const withCommas = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        const formatted = `${withCommas}.${decPart}%`;
        return isNegative ? `(${formatted})` : formatted;
    }
    return value;
}

// Helper: Format large number with commas and brackets for negatives
function formatLargeNumber(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        const isNegative = value < 0;
        const absValue = Math.abs(value);

        let formatted;
        if (absValue >= 1e9) {
            formatted = (absValue / 1e9).toFixed(2) + 'B';
        } else if (absValue >= 1e6) {
            formatted = (absValue / 1e6).toFixed(2) + 'M';
        } else if (absValue >= 1e3) {
            formatted = (absValue / 1e3).toFixed(2) + 'K';
        } else {
            formatted = absValue.toFixed(2);
        }

        // Add commas to the number part (before B/M/K suffix)
        const parts = formatted.match(/^([\d.]+)([BMK]?)$/);
        if (parts) {
            const [, num, suffix] = parts;
            const [intPart, decPart] = num.split('.');
            const withCommas = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            formatted = decPart ? `${withCommas}.${decPart}${suffix}` : `${withCommas}${suffix}`;
        }

        return isNegative ? `(${formatted})` : formatted;
    }
    return value;
}
