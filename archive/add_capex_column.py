"""
Add capital_expenditure column to quarterly_fundamentals and annual_fundamentals tables.
"""

from database.db_manager import DatabaseManager
from sqlalchemy import text

def add_capex_columns():
    """Add capital_expenditure column to both fundamentals tables."""
    db = DatabaseManager()

    with db.engine.connect() as conn:
        # Add capital_expenditure to quarterly_fundamentals
        print("Adding capital_expenditure column to quarterly_fundamentals...")
        try:
            conn.execute(text("""
                ALTER TABLE quarterly_fundamentals
                ADD COLUMN IF NOT EXISTS capital_expenditure NUMERIC(18, 2);
            """))
            conn.commit()
            print("✓ Added capital_expenditure to quarterly_fundamentals")
        except Exception as e:
            print(f"Error adding to quarterly_fundamentals: {e}")

        # Add capital_expenditure to annual_fundamentals
        print("Adding capital_expenditure column to annual_fundamentals...")
        try:
            conn.execute(text("""
                ALTER TABLE annual_fundamentals
                ADD COLUMN IF NOT EXISTS capital_expenditure NUMERIC(18, 2);
            """))
            conn.commit()
            print("✓ Added capital_expenditure to annual_fundamentals")
        except Exception as e:
            print(f"Error adding to annual_fundamentals: {e}")

    print("\nMigration complete!")

if __name__ == '__main__':
    add_capex_columns()
