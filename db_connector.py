import mysql.connector
import pandas as pd
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "newpassword",
    "database": "huim_project"
}

def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        return None

def test_connection():
    try:
        conn = get_connection()
        if conn and conn.is_connected():
            conn.close()
            return True
        return False
    except Exception:
        return False

def load_transactions(limit=20000):
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        query = f"SELECT * FROM transactions LIMIT {limit}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

def load_monthly_summary():
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        query = """
            SELECT month_year, SUM(cell_utility) as total_utility 
            FROM transactions 
            GROUP BY month_year 
            ORDER BY month_year
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def load_top_items(top_n=10):
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        query = f"""
            SELECT item_name, SUM(cell_utility) as total_utility 
            FROM transactions 
            GROUP BY item_name 
            ORDER BY total_utility DESC 
            LIMIT {top_n}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_dataset_stats():
    try:
        conn = get_connection()
        if not conn:
            return {}
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_records FROM transactions")
        total_records = cursor.fetchone()['total_records']
        
        cursor.execute("SELECT COUNT(DISTINCT transaction_id) as total_txns FROM transactions")
        total_txns = cursor.fetchone()['total_txns']
        
        cursor.execute("SELECT COUNT(DISTINCT item_name) as total_items FROM transactions")
        total_items = cursor.fetchone()['total_items']
        
        cursor.execute("SELECT MIN(transaction_date) as start_date, MAX(transaction_date) as end_date FROM transactions")
        dates = cursor.fetchone()
        
        conn.close()
        return {
            'records': total_records,
            'transactions': total_txns,
            'items': total_items,
            'start_date': dates['start_date'],
            'end_date': dates['end_date']
        }
    except Exception:
        return {}

def save_mining_results(df):
    try:
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mining_results")
        
        insert_query = """
            INSERT INTO mining_results 
            (itemset, support, utility, itemset_size, category) 
            VALUES (%s, %s, %s, %s, %s)
        """
        
        data_to_insert = [
            (str(row['itemset']), float(row['support']), float(row['utility']), int(row['itemset_size']), str(row['category']))
            for index, row in df.iterrows()
        ]
        
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def load_saved_results(category=None):
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        query = "SELECT * FROM mining_results"
        if category:
            query += f" WHERE category = '{category}'"
        query += " ORDER BY utility DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def load_products():
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        query = "SELECT * FROM products"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def save_upload_record(record_dict):
    try:
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO uploaded_analyses 
            (filename, total_records, total_items, hfhu_count, hflu_count, lfhu_count, execution_time, profit_source) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            record_dict.get('filename'),
            record_dict.get('total_records'),
            record_dict.get('total_items'),
            record_dict.get('hfhu_count'),
            record_dict.get('hflu_count'),
            record_dict.get('lfhu_count'),
            record_dict.get('execution_time'),
            record_dict.get('profit_source')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
