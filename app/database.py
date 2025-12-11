import mysql.connector
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password", 
        database="flights"
    )
