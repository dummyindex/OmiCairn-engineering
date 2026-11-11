import os
from sqlalchemy.pool import QueuePool

HOST = os.environ.get("MYSQL_IP", "localhost")
PORT = os.environ.get("MYSQL_PORT", "3306")
DATABASE = os.environ.get("MYSQL_DATABASE", "omicairn")
USERNAME = os.environ.get("MYSQL_USER", "root")
PASSWORD = os.environ.get("MYSQL_PASSWORD", "")

SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': QueuePool,
    'max_overflow': 3,   # Max connections that can be created beyond pool_size
    'pool_size': 3,  # Connection pool size
    'pool_timeout': 30,  # Max time a thread waits for a connection when the pool is full before raising an error
    'pool_recycle': 1200,  # Interval after which pooled connections are recycled (reset); -1 means never recycle
    'pool_pre_ping': True
}

DB_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(
    username=USERNAME,
    password=PASSWORD,
    host=HOST,
    port=PORT,
    db=DATABASE
)

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_ECHO = False


##################################################
# upload
##################################################
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024 * 10
