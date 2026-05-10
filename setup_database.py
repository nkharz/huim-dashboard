import mysql.connector
import random
from datetime import datetime, timedelta
import sys

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "newpassword"
}

PRODUCTS = {
    "Rice": (5, "Grocery"), "Wheat Flour": (4, "Grocery"), 
    "Cooking Oil": (8, "Grocery"), "Mustard Oil": (10, "Grocery"),
    "Sugar": (3, "Grocery"), "Jaggery": (6, "Grocery"), 
    "Tea": (12, "Beverages"), "Coffee": (18, "Beverages"), 
    "Biscuits": (4, "Snacks"), "Chips": (7, "Snacks"), 
    "Milk": (3, "Dairy"), "Butter": (14, "Dairy"), 
    "Cheese": (20, "Dairy"), "Salt": (2, "Grocery"),
    "Turmeric": (5, "Spices"), "Chilli Powder": (6, "Spices"), 
    "Soap": (9, "Personal Care"), "Shampoo": (22, "Personal Care"),
    "Toothpaste": (11, "Personal Care"), "Detergent": (8, "Home Care")
}

def setup_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating huim_project database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS huim_project")
        cursor.execute("USE huim_project")
        
        print("Creating tables...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
          product_id INT AUTO_INCREMENT PRIMARY KEY,
          item_name VARCHAR(100) NOT NULL UNIQUE,
          unit_profit DECIMAL(10,2) NOT NULL,
          category VARCHAR(50) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
          id INT AUTO_INCREMENT PRIMARY KEY,
          transaction_id VARCHAR(20) NOT NULL,
          item_name VARCHAR(100) NOT NULL,
          quantity INT NOT NULL,
          unit_profit DECIMAL(10,2) NOT NULL,
          cell_utility DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_profit) STORED,
          category VARCHAR(50) NOT NULL,
          transaction_date DATETIME NOT NULL,
          month_year VARCHAR(7) GENERATED ALWAYS AS (DATE_FORMAT(transaction_date,'%Y-%m')) STORED,
          INDEX idx_tid (transaction_id),
          INDEX idx_item (item_name),
          INDEX idx_date (transaction_date),
          INDEX idx_mon (month_year)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mining_results (
          id INT AUTO_INCREMENT PRIMARY KEY,
          itemset VARCHAR(255) NOT NULL,
          support DECIMAL(10,4) NOT NULL,
          utility DECIMAL(12,2) NOT NULL,
          itemset_size INT NOT NULL,
          category VARCHAR(10) NOT NULL,
          mined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_cat (category),
          INDEX idx_util (utility DESC)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_analyses (
          id INT AUTO_INCREMENT PRIMARY KEY,
          filename VARCHAR(255) NOT NULL,
          upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          total_records INT,
          total_items INT,
          hfhu_count INT,
          hflu_count INT,
          lfhu_count INT,
          execution_time DECIMAL(10,4),
          profit_source VARCHAR(50),
          status VARCHAR(20) DEFAULT 'completed'
        )
        """)
        
        print("Inserting products...")
        cursor.execute("DELETE FROM products")
        for item, (profit, cat) in PRODUCTS.items():
            cursor.execute("INSERT INTO products (item_name, unit_profit, category) VALUES (%s, %s, %s)", (item, profit, cat))
        
        print("Inserting 20,000 transactions...")
        cursor.execute("DELETE FROM transactions")
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 12, 31)
        days_between = (end_date - start_date).days
        
        items_list = list(PRODUCTS.keys())
        weights = [random.randint(1, 10) for _ in items_list]
        
        records = []
        txn_id_counter = 1
        
        while len(records) < 20000:
            txn_id = f"T{txn_id_counter:06d}"
            num_items = random.randint(2, 7)
            txn_items = random.choices(items_list, weights=weights, k=num_items)
            txn_items = list(set(txn_items))
            random_days = random.randint(0, days_between)
            txn_date = start_date + timedelta(days=random_days)
            
            for item in txn_items:
                if len(records) >= 20000:
                    break
                qty = random.randint(1, 5)
                profit = PRODUCTS[item][0]
                cat = PRODUCTS[item][1]
                records.append((txn_id, item, qty, profit, cat, txn_date))
                
            txn_id_counter += 1
            
            if len(records) % 500 == 0:
                print(f"Generated {len(records)} records...")
                insert_query = "INSERT INTO transactions (transaction_id, item_name, quantity, unit_profit, category, transaction_date) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.executemany(insert_query, records[-500:])
                conn.commit()

        print("\n" + "="*50)
        print("DATABASE SETUP COMPLETE")
        print("="*50)
        print("Run the following commands:")
        print("1. Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
        print("2. python -m venv venv")
        print("3. venv\\Scripts\\activate")
        print("4. pip install -r requirements.txt")
        print("5. python -m streamlit run app.py")
        print("6. python -m uvicorn api:app --reload")
        
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        print("Make sure MySQL is running and DB_CONFIG password is correct.")

if __name__ == "__main__":
    setup_database()
