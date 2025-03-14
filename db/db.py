"""
Database utility module for MySQL operations.
"""
import pymysql
from pymysql.cursors import DictCursor

class DBManager:
    """
    Database manager class for handling MySQL connections and operations.
    """
    def __init__(self, host='localhost', port=0, user='root', password='', database='adify_db'):
        """
        Initialize the database connection parameters.
        
        Args:
            host (str): MySQL host address
            user (str): MySQL username
            password (str): MySQL password
            database (str): Database name
        """
        self.database = database
        self.password = password
        self.user = user
        self.host = host
        self.port = port

    def get_connection(self):
        """
        Create and return a new database connection.
        
        Returns:
            Connection: MySQL database connection
        """
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=DictCursor
        )
    
    def fetch_all(self, query, params=None):
        """
        Execute a query and fetch all results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: List of dictionaries with query results
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            connection.close()
    
    def fetch_one(self, query, params=None):
        """
        Execute a query and fetch one result.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            dict: Dictionary with query result
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        finally:
            connection.close()
    
    def execute(self, query, params=None):
        """
        Execute a query without returning results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Number of affected rows
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                result = cursor.execute(query, params)
                connection.commit()
                return result
        finally:
            connection.close()
    
    def execute_insert(self, query, params=None):
        """
        Execute an insert query and return the last inserted ID.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Last inserted ID
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    def batch_execute_insert(self, query, params=None):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 批量执行
                cursor.executemany(query, params)
                connection.commit()
                return cursor.rowcount
        finally:
            connection.close()