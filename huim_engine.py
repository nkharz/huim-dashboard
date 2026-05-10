import pandas as pd
import numpy as np
from itertools import combinations
import time

class HUIMEngine:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.data['transaction_date'] = pd.to_datetime(self.data['transaction_date'])
        self.data['month_year'] = self.data['transaction_date'].dt.strftime('%Y-%m')
        self.data['cell_utility'] = self.data['quantity'] * self.data['unit_profit']

    def build_utility_matrix(self):
        matrix = pd.pivot_table(
            self.data, 
            index='transaction_id', 
            columns='item_name',
            values='cell_utility', 
            aggfunc='sum', 
            fill_value=0
        )
        return matrix

    def compute_support_and_utility(self):
        matrix = self.build_utility_matrix()
        total_transactions = len(matrix)
        
        support_dict = {}
        utility_dict = {}
        
        for item in matrix.columns:
            support = (matrix[item] > 0).sum() / total_transactions
            utility = matrix[item].sum()
            support_dict[item] = support
            utility_dict[item] = utility
            
        return support_dict, utility_dict, matrix

    def compute_dynamic_thresholds(self, support_dict, utility_dict):
        sv = sorted(list(support_dict.values()))
        m = len(sv)
        if m == 0:
            return {'Sth': 0, 'Uth': 0, 'Smean': 0, 'Umean': 0, 'Smax': 0, 'Umax': 0}
            
        Smean = np.mean(sv)
        Smax = max(sv) if max(sv) > 0 else 1
        Ps = (Smean / Smax) * 100
        Poss = int(np.ceil((Ps / 100) * (m + 1)) - 1)
        Poss = max(0, min(Poss, m - 1))
        Sth = sv[Poss]

        uv = sorted(list(utility_dict.values()))
        Umean = np.mean(uv)
        Umax = max(uv) if max(uv) > 0 else 1
        Pu = (Umean / Umax) * 100
        Posu = int(np.ceil((Pu / 100) * (m + 1)) - 1)
        Posu = max(0, min(Posu, m - 1))
        Uth = uv[Posu]

        return {
            'Sth': Sth, 'Uth': Uth,
            'Smean': Smean, 'Umean': Umean,
            'Smax': Smax, 'Umax': Umax
        }

    def _classify(self, support, utility, Sth, Uth):
        if support == 0:
            return "Discarded"
        if support >= Sth and utility >= Uth:
            return "HFHU"
        if support >= Sth and utility < Uth:
            return "HFLU"
        if support < Sth and utility >= Uth:
            return "LFHU"
        return "Low-Low"

    def classify_single_items(self, support_dict, utility_dict, Sth, Uth):
        results = []
        for item, support in support_dict.items():
            utility = utility_dict[item]
            category = self._classify(support, utility, Sth, Uth)
            results.append({
                'itemset': item,
                'support': support,
                'utility': utility,
                'itemset_size': 1,
                'category': category
            })
        return results

    def generate_and_classify_combinations(self, matrix, valid_items, max_size, Sth, Uth):
        total_transactions = len(matrix)
        results = []
        
        for size in range(2, max_size + 1):
            for combo in combinations(valid_items, size):
                combo_list = list(combo)
                mask = (matrix[combo_list] > 0).all(axis=1)
                matching_count = mask.sum()
                if matching_count == 0:
                    continue
                
                support = matching_count / total_transactions
                utility = matrix.loc[mask, combo_list].sum().sum()
                
                category = self._classify(support, utility, Sth, Uth)
                if category != "Discarded" and category != "Low-Low":
                    results.append({
                        'itemset': ", ".join(sorted(combo_list)),
                        'support': support,
                        'utility': utility,
                        'itemset_size': size,
                        'category': category
                    })
        return results

    def monthly_analysis(self):
        monthly = self.data.groupby(['month_year', 'transaction_id'])['cell_utility'].sum().reset_index()
        monthly_summary = monthly.groupby('month_year')['cell_utility'].sum().reset_index()
        monthly_summary.rename(columns={'cell_utility': 'total_utility'}, inplace=True)
        
        monthly_summary = monthly_summary.sort_values('month_year')
        monthly_summary['delta'] = monthly_summary['total_utility'].diff()
        monthly_summary['growth_pct'] = (monthly_summary['delta'] / monthly_summary['total_utility'].shift(1)) * 100
        monthly_summary['growth_pct'] = monthly_summary['growth_pct'].fillna(0)
        
        return monthly_summary

    def run_full_pipeline(self, max_combo_size=3):
        start_time = time.time()
        
        support_dict, utility_dict, matrix = self.compute_support_and_utility()
        thresholds = self.compute_dynamic_thresholds(support_dict, utility_dict)
        
        single_results = self.classify_single_items(
            support_dict, utility_dict, thresholds['Sth'], thresholds['Uth']
        )
        
        valid_items = [r['itemset'] for r in single_results if r['category'] != 'Discarded']
        
        combo_results = self.generate_and_classify_combinations(
            matrix, valid_items, max_combo_size, thresholds['Sth'], thresholds['Uth']
        )
        
        all_results = single_results + combo_results
        results_df = pd.DataFrame(all_results)
        if not results_df.empty:
            results_df = results_df[results_df['category'] != 'Discarded']
            results_df = results_df.sort_values('utility', ascending=False).reset_index(drop=True)
        else:
            results_df = pd.DataFrame(columns=['itemset', 'support', 'utility', 'itemset_size', 'category'])
            
        monthly_df = self.monthly_analysis()
        
        category_summary = results_df['category'].value_counts().to_dict() if not results_df.empty else {}
        
        execution_time = time.time() - start_time
        
        return {
            'thresholds': thresholds,
            'results_df': results_df,
            'monthly_df': monthly_df,
            'category_summary': category_summary,
            'utility_matrix': matrix,
            'execution_time': execution_time,
            'db_scans': 1,
            'patterns_found': len(results_df)
        }

class AprioriMiner:
    def __init__(self, data, min_support=0.3):
        self.data = data
        self.min_support = min_support
        self.transactions = data.groupby('transaction_id')['item_name'].apply(list).tolist()
        self.total_transactions = len(self.transactions)
        self.db_scans = 0

    def _support(self, itemset):
        self.db_scans += 1
        itemset_set = set(itemset)
        count = sum(1 for txn in self.transactions if itemset_set.issubset(txn))
        return count / self.total_transactions if self.total_transactions > 0 else 0

    def run(self, max_size=3):
        start_time = time.time()
        
        items = self.data['item_name'].unique()
        valid_items = []
        results = []
        
        for item in items:
            sup = self._support([item])
            if sup >= self.min_support:
                valid_items.append(item)
                results.append({
                    'itemset': item,
                    'support': sup,
                    'size': 1
                })
        
        for size in range(2, max_size + 1):
            for combo in combinations(valid_items, size):
                sup = self._support(list(combo))
                if sup >= self.min_support:
                    results.append({
                        'itemset': ", ".join(sorted(list(combo))),
                        'support': sup,
                        'size': size
                    })
                    
        execution_time = time.time() - start_time
        patterns_found = len(results)
        
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('support', ascending=False).reset_index(drop=True)
            
        return {
            'results_df': df,
            'execution_time': execution_time,
            'patterns_found': patterns_found,
            'db_scans': self.db_scans
        }
