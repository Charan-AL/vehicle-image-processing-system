"""
Create database tables from SQLAlchemy models.
This script creates the Image and AnalysisResult tables in PostgreSQL.

Usage:
    python create_tables.py

IMPORTANT:
- Run this AFTER confirming database connection (test_db_connection.py)
- This creates tables based on current models in app/models.py
- Safe to run multiple times (idempotent)
"""

from app.database import engine, Base
from app.models import Image, AnalysisResult

def create_tables():
    """Create all tables defined in models."""
    print("=" * 70)
    print("Creating Database Tables")
    print("=" * 70)
    
    try:
        # Base.metadata.create_all() creates all tables from models
        # It only creates tables that don't exist (idempotent)
        print("\n[Step 1] Creating tables from models...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        print("[Step 2] Verifying tables...")
        with engine.connect() as connection:
            # Get list of all tables in the database
            inspector = __import__('sqlalchemy').inspect(engine)
            tables = inspector.get_table_names()
            
            if "images" in tables:
                print("✓ 'images' table created successfully")
                print(f"  Columns: {[col['name'] for col in inspector.get_columns('images')]}")
            else:
                print("✗ 'images' table not found")
                return False
            
            if "analysis_results" in tables:
                print("✓ 'analysis_results' table created successfully")
                print(f"  Columns: {[col['name'] for col in inspector.get_columns('analysis_results')]}")
            else:
                print("✗ 'analysis_results' table not found")
                return False
        
        print("\n" + "=" * 70)
        print("All tables created successfully! ✓")
        print("=" * 70)
        
        print("\nTable Summary:")
        print("-" * 70)
        print("TABLE: images")
        print("  - id (PRIMARY KEY)")
        print("  - filename")
        print("  - filepath")
        print("  - status")
        print("  - created_at")
        print()
        print("TABLE: analysis_results")
        print("  - id (PRIMARY KEY)")
        print("  - image_id (FOREIGN KEY → images.id)")
        print("  - blur_score")
        print("  - brightness_score")
        print("  - plate_text")
        print("  - plate_valid")
        print("  - duplicate")
        print("  - remarks")
        print("  - completed_at")
        print("-" * 70)
        
        print("\nRelationship:")
        print("  One Image → One AnalysisResult")
        print("  (One-to-One relationship, though structure allows One-to-Many)")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"Error creating tables: {str(e)}")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env is correct")
        print("3. Ensure database 'vehicle_db' exists")
        print("4. Run: python test_db_connection.py")
        return False

if __name__ == "__main__":
    success = create_tables()
    exit(0 if success else 1)
