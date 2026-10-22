import os
from sqlalchemy.pool import QueuePool

HOST = os.environ.get("DB_HOST", "localhost")
PORT = os.environ.get("DB_PORT", "3306")
DATABASE = os.environ.get("DB_NAME", "omicairn")
USERNAME = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")

SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': QueuePool,
    'max_overflow': 2,   # max extra connections that can be created beyond the pool size
    'pool_size': 3,  # connection pool size
    'pool_timeout': 5,  # max time a thread waits for a connection when the pool is full before raising an error
    'pool_recycle': 1200,  # interval after which pooled connections are recycled (reset); -1 = never recycle
    'pool_pre_ping': True
}

DB_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8mb4".format(
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
