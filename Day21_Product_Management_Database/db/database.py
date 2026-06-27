from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://sachin:sachin@77.37.45.138:3306/employeedb"

engine = create_engine(
    DATABASE_URL,  # verify the connection is alive before using it
    echo=True          # set True to log every SQL statement SQLAlchemy emits
)


# Base class that all ORM models inherit from
Base = declarative_base()

# A Session is the ORM's "handle" to the database for queries/transactions
Session = sessionmaker(bind=engine)


# FastAPI dependency: open a session per request and always close it
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

