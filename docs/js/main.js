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
    const response = await fetch('data/stocks_analysis.json');
    stocksData = await response.json();

    // Separate stocks by exchange
    tadawulStocks = stocksData.stocks.filter(s => s.exchange === 'Tadawul');
    nomuStocks = stocksData.stocks.filter(s => s.exchange === 'NOMU');
}

// Render metadata
function renderMetadata() {
    const metadataEl = document.getElementById('metadata');
    const date = new Date(stocksData.metadata.generated_date).toLocaleString();
    metadataEl.innerHTML = `
        <p>Generated: ${date} | Total Stocks: ${stocksData.metadata.total_stocks}
        (Tadawul: ${stocksData.metadata.tadawul_count}, NOMU: ${stocksData.metadata.nomu_count})</p>
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

    return clone;
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
    document.getElementById('tadawul-clear-filters').addEventListener('click', () => clearFilters('tadawul'));
    document.getElementById('tadawul-export-csv').addEventListener('click', () => exportToCSV('tadawul'));

    // NOMU filters
    document.getElementById('nomu-sector-filter').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-industry-filter').addEventListener('change', () => filterStocks('nomu'));
    document.getElementById('nomu-search').addEventListener('input', () => filterStocks('nomu'));
    document.getElementById('nomu-clear-filters').addEventListener('click', () => clearFilters('nomu'));
    document.getElementById('nomu-export-csv').addEventListener('click', () => exportToCSV('nomu'));

    // Sorting
    setupSorting('tadawul');
    setupSorting('nomu');
}

// Filter stocks
function filterStocks(exchange) {
    const sectorFilter = document.getElementById(`${exchange}-sector-filter`).value;
    const industryFilter = document.getElementById(`${exchange}-industry-filter`).value;
    const searchText = document.getElementById(`${exchange}-search`).value.toLowerCase();

    const allStocks = exchange === 'tadawul' ? tadawulStocks : nomuStocks;

    const filtered = allStocks.filter(stock => {
        const matchSector = !sectorFilter || stock.sector === sectorFilter;
        const matchIndustry = !industryFilter || stock.industry === industryFilter;
        const matchSearch = !searchText ||
            stock.symbol.toLowerCase().includes(searchText) ||
            stock.company_name.toLowerCase().includes(searchText);

        return matchSector && matchIndustry && matchSearch;
    });

    renderStocksTable(exchange, filtered);
}

// Clear filters
function clearFilters(exchange) {
    document.getElementById(`${exchange}-sector-filter`).value = '';
    document.getElementById(`${exchange}-industry-filter`).value = '';
    document.getElementById(`${exchange}-search`).value = '';
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

    // Re-render with sorted data
    renderStocksTable(exchange, sorted);

    // Apply filters if any are active
    const sectorFilter = document.getElementById(`${exchange}-sector-filter`).value;
    const industryFilter = document.getElementById(`${exchange}-industry-filter`).value;
    const searchText = document.getElementById(`${exchange}-search`).value;

    if (sectorFilter || industryFilter || searchText) {
        filterStocks(exchange);
    }
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

// Helper: Format number
function formatNumber(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return value;
}

// Helper: Format percentage
function formatPercent(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        return value.toFixed(2) + '%';
    }
    return value;
}

// Helper: Format large number
function formatLargeNumber(value) {
    if (value == null) return '-';
    if (typeof value === 'number') {
        if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B';
        if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M';
        if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K';
        return value.toFixed(2);
    }
    return value;
}
