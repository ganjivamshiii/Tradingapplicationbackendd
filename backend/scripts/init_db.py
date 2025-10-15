"""
Initialize the database with tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models.trade import Trade
from app.models.portfolio import Portfolio

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print(f"Tables created: {list(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    init_database()