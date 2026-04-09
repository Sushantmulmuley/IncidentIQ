from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# This creates a file called incidentiq.db in your project folder
# Think of it like an Excel file but for code
DATABASE_URL = "sqlite:///./incidentiq.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Base is the parent class all our tables inherit from
Base = declarative_base()

# This is our incidents TABLE — like a spreadsheet with columns
class Incident(Base):
    __tablename__ = "incidents"

    id           = Column(Integer, primary_key=True)  # auto number: 1, 2, 3...
    service_name = Column(String)   # which service broke e.g. "orders-service"
    severity     = Column(String)   # "high", "medium", "low"
    raw_logs     = Column(Text)     # the original log text
    root_cause   = Column(Text)     # what AI said caused it
    action_items = Column(Text)     # what AI said to fix it
    created_at   = Column(DateTime, default=datetime.utcnow)  # when it happened

# Create the actual table in the database file
Base.metadata.create_all(bind=engine)

# SessionLocal is how we open and close database connections
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Open a database connection, use it, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_incident(db, service, severity, raw_logs, root_cause, action_items):
    """Save one incident to the database."""
    incident = Incident(
        service_name = service,
        severity     = severity,
        raw_logs     = raw_logs,
        root_cause   = root_cause,
        action_items = action_items,
    )
    db.add(incident)
    db.commit()
    return incident

def find_similar(db, service_name):
    """
    Look up past incidents for the same service.
    This is the MEMORY feature — has this happened before?
    """
    return db.query(Incident)\
             .filter(Incident.service_name == service_name)\
             .order_by(Incident.created_at.desc())\
             .limit(3)\
             .all()