from db.database import Base, engine

# Import the models so they register themselves on Base.metadata.
# Without these imports the tables are unknown and create_all() does nothing.
from models.product_model import Product
from models.customer_model import Customer

Base.metadata.drop_all(bind=engine)
print("Tables dropped:", list(Base.metadata.tables.keys()))
