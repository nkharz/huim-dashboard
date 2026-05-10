import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

def generate_fallback_data(num_records=5000):
    products = {
        "Rice": 5, "Wheat Flour": 4, "Cooking Oil": 8, "Mustard Oil": 10,
        "Sugar": 3, "Jaggery": 6, "Tea": 12, "Coffee": 18, "Biscuits": 4,
        "Chips": 7, "Milk": 3, "Butter": 14, "Cheese": 20, "Salt": 2,
        "Turmeric": 5, "Chilli Powder": 6, "Soap": 9, "Shampoo": 22,
        "Toothpaste": 11, "Detergent": 8
    }
    categories = {
        "Rice": "Grocery", "Wheat Flour": "Grocery", "Cooking Oil": "Grocery", 
        "Mustard Oil": "Grocery", "Sugar": "Grocery", "Jaggery": "Grocery", 
        "Tea": "Beverages", "Coffee": "Beverages", "Biscuits": "Snacks",
        "Chips": "Snacks", "Milk": "Dairy", "Butter": "Dairy", 
        "Cheese": "Dairy", "Salt": "Grocery", "Turmeric": "Spices", 
        "Chilli Powder": "Spices", "Soap": "Personal Care", 
        "Shampoo": "Personal Care", "Toothpaste": "Personal Care", "Detergent": "Home Care"
    }

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    days_between = (end_date - start_date).days

    data = []
    transaction_id_counter = 1
    
    items_list = list(products.keys())
    weights = [np.random.randint(1, 10) for _ in items_list]

    records_created = 0
    while records_created < num_records:
        txn_id = f"T{transaction_id_counter:06d}"
        
        num_items = random.randint(2, 7)
        txn_items = random.choices(items_list, weights=weights, k=num_items)
        txn_items = list(set(txn_items)) # unique items
        
        random_days = random.randint(0, days_between)
        txn_date = start_date + timedelta(days=random_days)
        
        for item in txn_items:
            if records_created >= num_records:
                break
                
            qty = random.randint(1, 5)
            profit = products[item]
            
            data.append({
                "transaction_id": txn_id,
                "item_name": item,
                "quantity": qty,
                "unit_profit": profit,
                "category": categories[item],
                "transaction_date": txn_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            records_created += 1
            
        transaction_id_counter += 1

    df = pd.DataFrame(data)
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    df.to_csv(os.path.join(os.path.dirname(__file__), "data", "transactions.csv"), index=False)
    print(f"Generated {len(df)} records in data/transactions.csv")

if __name__ == "__main__":
    generate_fallback_data()
