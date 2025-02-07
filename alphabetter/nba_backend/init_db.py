from alphabetter.nba_backend.database import engine, Base  # Use relative import
from alphabetter.nba_backend.models import PlayerStats  # Use relative import

# Debug: Print registered tables
print("Registered tables:", Base.metadata.tables.keys())

print("Initializing database...")
Base.metadata.drop_all(bind=engine)  # Drop tables (for development only)
Base.metadata.create_all(bind=engine)  # Create tables

print("Tables after creating:", Base.metadata.tables.keys())

print("Database tables created successfully!")
