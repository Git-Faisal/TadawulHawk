"""
Database Manager for Tadawul Hawk.
Handles PostgreSQL operations using SQLAlchemy ORM.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, Boolean, Text, ForeignKey, CheckConstraint, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from contextlib import contextmanager

from config import Config
from utils import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()


# ============================================
# SQLAlchemy Models
# ============================================

class Stock(Base):
    """Stock metadata model."""
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    exchange = Column(String(50), default='Tadawul')
    listing_date = Column(Date)
    currency = Column(String(10), default='SAR')
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    price_history = relationship('PriceHistory', back_populates='stock', cascade='all, delete-orphan')
    quarterly_fundamentals = relationship('QuarterlyFundamental', back_populates='stock', cascade='all, delete-orphan')
    annual_fundamentals = relationship('AnnualFundamental', back_populates='stock', cascade='all, delete-orphan')
    collection_logs = relationship('DataCollectionLog', back_populates='stock', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        CheckConstraint("symbol LIKE '%.SR'", name='chk_symbol_format'),
        CheckConstraint("exchange IN ('Tadawul', 'NOMU')", name='chk_exchange'),
    )

    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', company='{self.company_name}', exchange='{self.exchange}')>"


class PriceHistory(Base):
    """Price history model."""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    data_date = Column(Date, nullable=False)

    # Current/Latest Price
    last_close_price = Column(Numeric(12, 3))

    # Historical Prices
    price_1m_ago = Column(Numeric(12, 3))
    price_3m_ago = Column(Numeric(12, 3))
    price_6m_ago = Column(Numeric(12, 3))
    price_9m_ago = Column(Numeric(12, 3))
    price_12m_ago = Column(Numeric(12, 3))

    # 52-week high/low
    week_52_high = Column(Numeric(12, 3))
    week_52_low = Column(Numeric(12, 3))

    # 3-year high/low
    year_3_high = Column(Numeric(12, 3))
    year_3_low = Column(Numeric(12, 3))

    # 5-year high/low
    year_5_high = Column(Numeric(12, 3))
    year_5_low = Column(Numeric(12, 3))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    stock = relationship('Stock', back_populates='price_history')

    # Constraints
    __table_args__ = (
        UniqueConstraint('stock_id', 'data_date', name='uq_price_stock_date'),
    )

    def __repr__(self):
        return f"<PriceHistory(stock_id={self.stock_id}, date={self.data_date}, price={self.last_close_price})>"


class QuarterlyFundamental(Base):
    """Quarterly fundamentals model."""
    __tablename__ = 'quarterly_fundamentals'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=False)
    quarter_end_date = Column(Date, nullable=False)

    # Financial Metrics
    revenue = Column(Numeric(18, 2))
    gross_profit = Column(Numeric(18, 2))
    net_income = Column(Numeric(18, 2))
    operating_cash_flow = Column(Numeric(18, 2))
    free_cash_flow = Column(Numeric(18, 2))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    stock = relationship('Stock', back_populates='quarterly_fundamentals')

    # Constraints
    __table_args__ = (
        CheckConstraint('fiscal_quarter BETWEEN 1 AND 4', name='chk_fiscal_quarter'),
        UniqueConstraint('stock_id', 'fiscal_year', 'fiscal_quarter', name='uq_quarterly_stock_period'),
    )

    def __repr__(self):
        return f"<QuarterlyFundamental(stock_id={self.stock_id}, year={self.fiscal_year}, quarter=Q{self.fiscal_quarter})>"


class AnnualFundamental(Base):
    """Annual fundamentals model."""
    __tablename__ = 'annual_fundamentals'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    year_end_date = Column(Date, nullable=False)

    # Financial Metrics
    revenue = Column(Numeric(18, 2))
    gross_profit = Column(Numeric(18, 2))
    net_income = Column(Numeric(18, 2))
    operating_cash_flow = Column(Numeric(18, 2))
    free_cash_flow = Column(Numeric(18, 2))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    stock = relationship('Stock', back_populates='annual_fundamentals')

    # Constraints
    __table_args__ = (
        UniqueConstraint('stock_id', 'fiscal_year', name='uq_annual_stock_year'),
    )

    def __repr__(self):
        return f"<AnnualFundamental(stock_id={self.stock_id}, year={self.fiscal_year})>"


class DataCollectionLog(Base):
    """Data collection audit log model."""
    __tablename__ = 'data_collection_log'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    collection_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    records_collected = Column(Integer, default=0)
    error_message = Column(Text)
    collection_timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    stock = relationship('Stock', back_populates='collection_logs')

    # Constraints
    __table_args__ = (
        CheckConstraint("collection_type IN ('price', 'quarterly', 'annual', 'metadata')", name='chk_collection_type'),
        CheckConstraint("status IN ('success', 'failed', 'partial')", name='chk_status'),
    )

    def __repr__(self):
        return f"<DataCollectionLog(stock_id={self.stock_id}, type={self.collection_type}, status={self.status})>"


# ============================================
# Database Manager Class
# ============================================

class DatabaseManager:
    """
    Manages all database operations for Tadawul Hawk.
    Provides connection management, CRUD operations, and query methods.
    """

    def __init__(self):
        """Initialize database manager with connection pool."""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Create SQLAlchemy engine and session factory."""
        try:
            database_url = Config.get_database_url()
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=False  # Set to True for SQL query logging
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        Automatically handles commit/rollback and session cleanup.

        Usage:
            with db_manager.get_session() as session:
                # perform database operations
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def drop_tables(self):
        """Drop all tables from the database (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise

    # ============================================
    # Stock Operations
    # ============================================

    def upsert_stock(self, symbol: str, company_name: Optional[str] = None,
                     sector: Optional[str] = None, industry: Optional[str] = None,
                     exchange: Optional[str] = None, listing_date: Optional[datetime] = None) -> Stock:
        """
        Insert or update stock metadata.

        Args:
            symbol: Stock symbol (e.g., '2222.SR')
            company_name: Company name
            sector: Sector classification
            industry: Industry classification
            exchange: Exchange market ('Tadawul' or 'NOMU')
            listing_date: Date of listing

        Returns:
            Stock object
        """
        with self.get_session() as session:
            stock = session.query(Stock).filter(Stock.symbol == symbol).first()

            if stock:
                # Update existing stock
                if company_name:
                    stock.company_name = company_name
                if sector:
                    stock.sector = sector
                if industry:
                    stock.industry = industry
                if exchange:
                    stock.exchange = exchange
                if listing_date:
                    stock.listing_date = listing_date
                logger.debug(f"Updated stock: {symbol}")
            else:
                # Insert new stock
                stock = Stock(
                    symbol=symbol,
                    company_name=company_name,
                    sector=sector,
                    industry=industry,
                    exchange=exchange or 'Tadawul',
                    listing_date=listing_date
                )
                session.add(stock)
                logger.debug(f"Inserted new stock: {symbol}")

            session.flush()
            session.refresh(stock)
            return stock

    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol."""
        with self.get_session() as session:
            return session.query(Stock).filter(Stock.symbol == symbol).first()

    def get_all_stocks(self, active_only: bool = True) -> List[Stock]:
        """Get all stocks, optionally filtering by active status."""
        with self.get_session() as session:
            query = session.query(Stock)
            if active_only:
                query = query.filter(Stock.is_active == True)
            return query.all()

    # ============================================
    # Price History Operations
    # ============================================

    def upsert_price_history(self, stock_id: int, data_date: datetime, **price_data) -> PriceHistory:
        """
        Insert or update price history.

        Args:
            stock_id: Stock ID
            data_date: Date of price snapshot
            **price_data: Price fields (last_close_price, price_1m_ago, etc.)

        Returns:
            PriceHistory object
        """
        with self.get_session() as session:
            price = session.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.data_date == data_date
            ).first()

            if price:
                # Update existing record
                for key, value in price_data.items():
                    if hasattr(price, key):
                        setattr(price, key, value)
                logger.debug(f"Updated price history for stock_id={stock_id}, date={data_date}")
            else:
                # Insert new record
                price = PriceHistory(stock_id=stock_id, data_date=data_date, **price_data)
                session.add(price)
                logger.debug(f"Inserted price history for stock_id={stock_id}, date={data_date}")

            session.flush()
            session.refresh(price)
            return price

    # ============================================
    # Quarterly Fundamentals Operations
    # ============================================

    def upsert_quarterly_fundamental(self, stock_id: int, fiscal_year: int,
                                     fiscal_quarter: int, quarter_end_date: datetime,
                                     **financial_data) -> QuarterlyFundamental:
        """
        Insert or update quarterly fundamental data.

        Args:
            stock_id: Stock ID
            fiscal_year: Fiscal year
            fiscal_quarter: Fiscal quarter (1-4)
            quarter_end_date: Quarter end date
            **financial_data: Financial metrics (revenue, gross_profit, etc.)

        Returns:
            QuarterlyFundamental object
        """
        with self.get_session() as session:
            quarterly = session.query(QuarterlyFundamental).filter(
                QuarterlyFundamental.stock_id == stock_id,
                QuarterlyFundamental.fiscal_year == fiscal_year,
                QuarterlyFundamental.fiscal_quarter == fiscal_quarter
            ).first()

            if quarterly:
                # Update existing record
                quarterly.quarter_end_date = quarter_end_date
                for key, value in financial_data.items():
                    if hasattr(quarterly, key):
                        setattr(quarterly, key, value)
                logger.debug(f"Updated quarterly fundamental: stock_id={stock_id}, {fiscal_year}Q{fiscal_quarter}")
            else:
                # Insert new record
                quarterly = QuarterlyFundamental(
                    stock_id=stock_id,
                    fiscal_year=fiscal_year,
                    fiscal_quarter=fiscal_quarter,
                    quarter_end_date=quarter_end_date,
                    **financial_data
                )
                session.add(quarterly)
                logger.debug(f"Inserted quarterly fundamental: stock_id={stock_id}, {fiscal_year}Q{fiscal_quarter}")

            session.flush()
            session.refresh(quarterly)
            return quarterly

    # ============================================
    # Annual Fundamentals Operations
    # ============================================

    def upsert_annual_fundamental(self, stock_id: int, fiscal_year: int,
                                  year_end_date: datetime, **financial_data) -> AnnualFundamental:
        """
        Insert or update annual fundamental data.

        Args:
            stock_id: Stock ID
            fiscal_year: Fiscal year
            year_end_date: Fiscal year end date
            **financial_data: Financial metrics (revenue, gross_profit, etc.)

        Returns:
            AnnualFundamental object
        """
        with self.get_session() as session:
            annual = session.query(AnnualFundamental).filter(
                AnnualFundamental.stock_id == stock_id,
                AnnualFundamental.fiscal_year == fiscal_year
            ).first()

            if annual:
                # Update existing record
                annual.year_end_date = year_end_date
                for key, value in financial_data.items():
                    if hasattr(annual, key):
                        setattr(annual, key, value)
                logger.debug(f"Updated annual fundamental: stock_id={stock_id}, year={fiscal_year}")
            else:
                # Insert new record
                annual = AnnualFundamental(
                    stock_id=stock_id,
                    fiscal_year=fiscal_year,
                    year_end_date=year_end_date,
                    **financial_data
                )
                session.add(annual)
                logger.debug(f"Inserted annual fundamental: stock_id={stock_id}, year={fiscal_year}")

            session.flush()
            session.refresh(annual)
            return annual

    # ============================================
    # Data Collection Log Operations
    # ============================================

    def log_collection(self, stock_id: Optional[int], collection_type: str,
                      status: str, records_collected: int = 0,
                      error_message: Optional[str] = None):
        """
        Log a data collection operation.

        Args:
            stock_id: Stock ID (None for general operations)
            collection_type: Type of collection ('price', 'quarterly', 'annual', 'metadata')
            status: Status ('success', 'failed', 'partial')
            records_collected: Number of records collected
            error_message: Error message if failed
        """
        with self.get_session() as session:
            log_entry = DataCollectionLog(
                stock_id=stock_id,
                collection_type=collection_type,
                status=status,
                records_collected=records_collected,
                error_message=error_message
            )
            session.add(log_entry)
            logger.info(f"Logged collection: type={collection_type}, status={status}, records={records_collected}")

    def has_recent_collection(self, stock_id: int, collection_type: str, hours: int = 24) -> bool:
        """
        Check if a stock has been successfully collected recently.

        Args:
            stock_id: Stock ID
            collection_type: Type of collection
            hours: Number of hours to look back

        Returns:
            True if recent successful collection exists
        """
        with self.get_session() as session:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)

            log = session.query(DataCollectionLog).filter(
                DataCollectionLog.stock_id == stock_id,
                DataCollectionLog.collection_type == collection_type,
                DataCollectionLog.status == 'success',
                DataCollectionLog.collection_timestamp >= cutoff_time
            ).first()

            return log is not None

    # ============================================
    # Query Methods for Exports
    # ============================================

    def get_all_data_for_export(self) -> List[Dict[str, Any]]:
        """
        Get all data structured for export.
        Returns a list of dictionaries containing all stock data.
        """
        with self.get_session() as session:
            stocks = session.query(Stock).filter(Stock.is_active == True).all()
            export_data = []

            for stock in stocks:
                stock_data = {
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'sector': stock.sector,
                    'industry': stock.industry,
                    'listing_date': stock.listing_date.isoformat() if stock.listing_date else None,
                    'currency': stock.currency,
                    'price_history': [],
                    'quarterly_fundamentals': [],
                    'annual_fundamentals': []
                }

                # Add price history
                for price in stock.price_history:
                    stock_data['price_history'].append({
                        'data_date': price.data_date.isoformat(),
                        'last_close_price': float(price.last_close_price) if price.last_close_price else None,
                        'price_1m_ago': float(price.price_1m_ago) if price.price_1m_ago else None,
                        'price_3m_ago': float(price.price_3m_ago) if price.price_3m_ago else None,
                        'price_6m_ago': float(price.price_6m_ago) if price.price_6m_ago else None,
                        'price_9m_ago': float(price.price_9m_ago) if price.price_9m_ago else None,
                        'price_12m_ago': float(price.price_12m_ago) if price.price_12m_ago else None,
                        'week_52_high': float(price.week_52_high) if price.week_52_high else None,
                        'week_52_low': float(price.week_52_low) if price.week_52_low else None,
                        'year_3_high': float(price.year_3_high) if price.year_3_high else None,
                        'year_3_low': float(price.year_3_low) if price.year_3_low else None,
                        'year_5_high': float(price.year_5_high) if price.year_5_high else None,
                        'year_5_low': float(price.year_5_low) if price.year_5_low else None
                    })

                # Add quarterly fundamentals
                for quarterly in stock.quarterly_fundamentals:
                    stock_data['quarterly_fundamentals'].append({
                        'fiscal_year': quarterly.fiscal_year,
                        'fiscal_quarter': quarterly.fiscal_quarter,
                        'quarter_end_date': quarterly.quarter_end_date.isoformat(),
                        'revenue': float(quarterly.revenue) if quarterly.revenue else None,
                        'gross_profit': float(quarterly.gross_profit) if quarterly.gross_profit else None,
                        'net_income': float(quarterly.net_income) if quarterly.net_income else None,
                        'operating_cash_flow': float(quarterly.operating_cash_flow) if quarterly.operating_cash_flow else None,
                        'free_cash_flow': float(quarterly.free_cash_flow) if quarterly.free_cash_flow else None
                    })

                # Add annual fundamentals
                for annual in stock.annual_fundamentals:
                    stock_data['annual_fundamentals'].append({
                        'fiscal_year': annual.fiscal_year,
                        'year_end_date': annual.year_end_date.isoformat(),
                        'revenue': float(annual.revenue) if annual.revenue else None,
                        'gross_profit': float(annual.gross_profit) if annual.gross_profit else None,
                        'net_income': float(annual.net_income) if annual.net_income else None,
                        'operating_cash_flow': float(annual.operating_cash_flow) if annual.operating_cash_flow else None,
                        'free_cash_flow': float(annual.free_cash_flow) if annual.free_cash_flow else None
                    })

                export_data.append(stock_data)

            return export_data

    # ============================================
    # Bulk Save Operations
    # ============================================

    def save_collected_data(self, symbol: str, collected_data: Dict[str, Any], exchange: str = 'Tadawul') -> bool:
        """
        Save all data collected by StockCollector in one transaction.

        Args:
            symbol: Stock symbol
            collected_data: Data from StockCollector.collect_all_data()
            exchange: Exchange market ('Tadawul' or 'NOMU')

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # 1. Upsert stock metadata
                stock_info = collected_data.get('stock_info', {})
                stock = session.query(Stock).filter(Stock.symbol == symbol).first()

                if stock:
                    # Update existing
                    if stock_info.get('company_name'):
                        stock.company_name = stock_info['company_name']
                    if stock_info.get('sector'):
                        stock.sector = stock_info['sector']
                    if stock_info.get('industry'):
                        stock.industry = stock_info['industry']
                    if exchange:
                        stock.exchange = exchange
                    logger.debug(f"Updated stock metadata: {symbol}")
                else:
                    # Insert new
                    stock = Stock(
                        symbol=symbol,
                        company_name=stock_info.get('company_name'),
                        sector=stock_info.get('sector'),
                        industry=stock_info.get('industry'),
                        exchange=exchange,
                        currency=stock_info.get('currency', 'SAR')
                    )
                    session.add(stock)
                    logger.info(f"Inserted new stock: {symbol}")

                session.flush()
                stock_id = stock.id

                # 2. Upsert price data
                current_price = collected_data.get('current_price', {})
                historical_prices = collected_data.get('historical_prices', {})
                high_low = collected_data.get('high_low', {})

                if current_price.get('data_date'):
                    from datetime import date
                    data_date = current_price['data_date']
                    if isinstance(data_date, str):
                        data_date = date.fromisoformat(data_date)

                    price_rec = session.query(PriceHistory).filter(
                        PriceHistory.stock_id == stock_id,
                        PriceHistory.data_date == data_date
                    ).first()

                    if price_rec:
                        # Update
                        price_rec.last_close_price = current_price.get('last_close_price')
                        price_rec.price_1m_ago = historical_prices.get(1)
                        price_rec.price_3m_ago = historical_prices.get(3)
                        price_rec.price_6m_ago = historical_prices.get(6)
                        price_rec.price_9m_ago = historical_prices.get(9)
                        price_rec.price_12m_ago = historical_prices.get(12)
                        price_rec.week_52_high = high_low.get('week_52_high')
                        price_rec.week_52_low = high_low.get('week_52_low')
                        price_rec.year_3_high = high_low.get('year_3_high')
                        price_rec.year_3_low = high_low.get('year_3_low')
                        price_rec.year_5_high = high_low.get('year_5_high')
                        price_rec.year_5_low = high_low.get('year_5_low')
                        logger.debug(f"Updated price history for {symbol}")
                    else:
                        # Insert
                        price_rec = PriceHistory(
                            stock_id=stock_id,
                            data_date=data_date,
                            last_close_price=current_price.get('last_close_price'),
                            price_1m_ago=historical_prices.get(1),
                            price_3m_ago=historical_prices.get(3),
                            price_6m_ago=historical_prices.get(6),
                            price_9m_ago=historical_prices.get(9),
                            price_12m_ago=historical_prices.get(12),
                            week_52_high=high_low.get('week_52_high'),
                            week_52_low=high_low.get('week_52_low'),
                            year_3_high=high_low.get('year_3_high'),
                            year_3_low=high_low.get('year_3_low'),
                            year_5_high=high_low.get('year_5_high'),
                            year_5_low=high_low.get('year_5_low')
                        )
                        session.add(price_rec)
                        logger.info(f"Inserted price history for {symbol}")

                # 3. Upsert quarterly fundamentals
                quarterly_data = collected_data.get('quarterly_fundamentals', [])

                # Deduplicate by (fiscal_year, fiscal_quarter), keeping most recent quarter_end_date
                # (Yahoo Finance sometimes returns duplicate quarters)
                seen_quarters = {}
                for quarter in quarterly_data:
                    key = (quarter['fiscal_year'], quarter['fiscal_quarter'])
                    from datetime import date
                    quarter_end = quarter['quarter_end_date']
                    if isinstance(quarter_end, str):
                        quarter_end = date.fromisoformat(quarter_end)

                    if key not in seen_quarters or quarter_end > seen_quarters[key]['quarter_end_date']:
                        quarter['quarter_end_date'] = quarter_end
                        seen_quarters[key] = quarter

                quarterly_data = list(seen_quarters.values())

                for quarter in quarterly_data:
                    from datetime import date
                    quarter_end = quarter['quarter_end_date']
                    if isinstance(quarter_end, str):
                        quarter_end = date.fromisoformat(quarter_end)

                    qf = session.query(QuarterlyFundamental).filter(
                        QuarterlyFundamental.stock_id == stock_id,
                        QuarterlyFundamental.fiscal_year == quarter['fiscal_year'],
                        QuarterlyFundamental.fiscal_quarter == quarter['fiscal_quarter']
                    ).first()

                    if qf:
                        # Update
                        qf.quarter_end_date = quarter_end
                        qf.revenue = quarter.get('revenue')
                        qf.gross_profit = quarter.get('gross_profit')
                        qf.net_income = quarter.get('net_income')
                        qf.operating_cash_flow = quarter.get('operating_cash_flow')
                        qf.free_cash_flow = quarter.get('free_cash_flow')
                    else:
                        # Insert
                        qf = QuarterlyFundamental(
                            stock_id=stock_id,
                            fiscal_year=quarter['fiscal_year'],
                            fiscal_quarter=quarter['fiscal_quarter'],
                            quarter_end_date=quarter_end,
                            revenue=quarter.get('revenue'),
                            gross_profit=quarter.get('gross_profit'),
                            net_income=quarter.get('net_income'),
                            operating_cash_flow=quarter.get('operating_cash_flow'),
                            free_cash_flow=quarter.get('free_cash_flow')
                        )
                        session.add(qf)

                logger.info(f"Saved {len(quarterly_data)} quarterly records for {symbol}")

                # 4. Upsert annual fundamentals
                annual_data = collected_data.get('annual_fundamentals', [])

                # Deduplicate by fiscal_year, keeping most recent year_end_date
                # (Yahoo Finance sometimes returns duplicate fiscal years)
                seen_years = {}
                for year in annual_data:
                    fiscal_year = year['fiscal_year']
                    from datetime import date
                    year_end = year['year_end_date']
                    if isinstance(year_end, str):
                        year_end = date.fromisoformat(year_end)

                    if fiscal_year not in seen_years or year_end > seen_years[fiscal_year]['year_end_date']:
                        year['year_end_date'] = year_end
                        seen_years[fiscal_year] = year

                annual_data = list(seen_years.values())

                for year in annual_data:
                    from datetime import date
                    year_end = year['year_end_date']
                    if isinstance(year_end, str):
                        year_end = date.fromisoformat(year_end)

                    af = session.query(AnnualFundamental).filter(
                        AnnualFundamental.stock_id == stock_id,
                        AnnualFundamental.fiscal_year == year['fiscal_year']
                    ).first()

                    if af:
                        # Update
                        af.year_end_date = year_end
                        af.revenue = year.get('revenue')
                        af.gross_profit = year.get('gross_profit')
                        af.net_income = year.get('net_income')
                        af.operating_cash_flow = year.get('operating_cash_flow')
                        af.free_cash_flow = year.get('free_cash_flow')
                    else:
                        # Insert
                        af = AnnualFundamental(
                            stock_id=stock_id,
                            fiscal_year=year['fiscal_year'],
                            year_end_date=year_end,
                            revenue=year.get('revenue'),
                            gross_profit=year.get('gross_profit'),
                            net_income=year.get('net_income'),
                            operating_cash_flow=year.get('operating_cash_flow'),
                            free_cash_flow=year.get('free_cash_flow')
                        )
                        session.add(af)

                logger.info(f"Saved {len(annual_data)} annual records for {symbol}")

                # 5. Log collection success (using 'price' as type since it covers all data)
                log_entry = DataCollectionLog(
                    stock_id=stock_id,
                    collection_type='price',
                    status='success',
                    records_collected=1 + len(quarterly_data) + len(annual_data)
                )
                session.add(log_entry)

                logger.info(f"Successfully saved all data for {symbol}")
                return True

        except Exception as e:
            logger.error(f"Failed to save data for {symbol}: {e}", exc_info=True)
            return False

    def export_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Export all data for a stock in dictionary format.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with all stock data or None if not found
        """
        try:
            with self.get_session() as session:
                # Get stock
                stock = session.query(Stock).filter(Stock.symbol == symbol).first()

                if not stock:
                    logger.warning(f"Stock {symbol} not found for export")
                    return None

                # Build export data
                export_data = {
                    'stock_info': {
                        'symbol': stock.symbol,
                        'company_name': stock.company_name,
                        'exchange': stock.exchange,
                        'sector': stock.sector,
                        'industry': stock.industry,
                        'currency': stock.currency,
                        'listing_date': stock.listing_date,
                        'created_at': stock.created_at,
                        'updated_at': stock.updated_at
                    },
                    'price_history': [],
                    'quarterly_fundamentals': [],
                    'annual_fundamentals': []
                }

                # Get price history
                prices = session.query(PriceHistory).filter(PriceHistory.stock_id == stock.id).all()
                for price in prices:
                    export_data['price_history'].append({
                        'data_date': price.data_date,
                        'last_close_price': price.last_close_price,
                        'price_1m_ago': price.price_1m_ago,
                        'price_3m_ago': price.price_3m_ago,
                        'price_6m_ago': price.price_6m_ago,
                        'price_9m_ago': price.price_9m_ago,
                        'price_12m_ago': price.price_12m_ago,
                        'week_52_high': price.week_52_high,
                        'week_52_low': price.week_52_low,
                        'year_3_high': price.year_3_high,
                        'year_3_low': price.year_3_low,
                        'year_5_high': price.year_5_high,
                        'year_5_low': price.year_5_low,
                        'created_at': price.created_at,
                        'updated_at': price.updated_at
                    })

                # Get quarterly fundamentals
                quarterlies = session.query(QuarterlyFundamental).filter(
                    QuarterlyFundamental.stock_id == stock.id
                ).order_by(QuarterlyFundamental.fiscal_year.desc(),
                          QuarterlyFundamental.fiscal_quarter.desc()).all()

                for q in quarterlies:
                    export_data['quarterly_fundamentals'].append({
                        'fiscal_year': q.fiscal_year,
                        'fiscal_quarter': q.fiscal_quarter,
                        'quarter_end_date': q.quarter_end_date,
                        'revenue': q.revenue,
                        'gross_profit': q.gross_profit,
                        'net_income': q.net_income,
                        'operating_cash_flow': q.operating_cash_flow,
                        'free_cash_flow': q.free_cash_flow,
                        'created_at': q.created_at,
                        'updated_at': q.updated_at
                    })

                # Get annual fundamentals
                annuals = session.query(AnnualFundamental).filter(
                    AnnualFundamental.stock_id == stock.id
                ).order_by(AnnualFundamental.fiscal_year.desc()).all()

                for a in annuals:
                    export_data['annual_fundamentals'].append({
                        'fiscal_year': a.fiscal_year,
                        'year_end_date': a.year_end_date,
                        'revenue': a.revenue,
                        'gross_profit': a.gross_profit,
                        'net_income': a.net_income,
                        'operating_cash_flow': a.operating_cash_flow,
                        'free_cash_flow': a.free_cash_flow,
                        'created_at': a.created_at,
                        'updated_at': a.updated_at
                    })

                logger.info(f"Exported data for {symbol}: {len(export_data['price_history'])} price records, "
                          f"{len(export_data['quarterly_fundamentals'])} quarterly, "
                          f"{len(export_data['annual_fundamentals'])} annual")

                return export_data

        except Exception as e:
            logger.error(f"Failed to export data for {symbol}: {e}", exc_info=True)
            return None

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False