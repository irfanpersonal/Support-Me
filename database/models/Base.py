from sqlalchemy.orm import declarative_base

# By invoking the "declarative_base" method we can use the returned class to extend from to create
# our database tables.
Base = declarative_base()