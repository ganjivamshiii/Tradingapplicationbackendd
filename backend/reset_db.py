"""
reset_db.py

Drops all tables and recreates them based on current SQLAlchemy models.
Use this in development. WARNING: This will delete all existing data.
"""

from app.database import Base, engine

# Drop all tables
print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

# Create tables based on models
print("Creating tables...")
Base.metadata.create_all(bind=engine)

print("Database reset complete!")
