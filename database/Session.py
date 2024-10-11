# To use the "async" version of SQLAlchemy which is non blocking you need to enter in the following
# to your terminal.

# pip install "sqlalchemy[async]"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

# The "create_async_engine" method is used to define the settings for the database you will connect 
# to. The keyword argument of "url" allows us to set the location to the database we want to connect
# to.
engine = create_async_engine(
    url = os.getenv('DATABASE_URL_ASYNC_VERSION')
)

# Think of a session as a temporary holding area where you prepare changes before making them 
# permanent in the database. When we invoke the "async_sessionmaker" method and pass in the engine
# to the keyword argument of "bind" we get returned to us a constructor for making sessions.
Session = async_sessionmaker(
    bind = engine
)