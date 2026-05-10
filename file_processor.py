import pandas as pd
import numpy as np
import io

class FileProcessor:
    COLUMN_MAP = {
        'transaction_id': [
            'tid','trans_id','order_id','bill_no','invoice_id',
            'txn_id','receipt_no','id','sno','sr_no','s_no',
            'bill_number','order_number','invoice_number'
        ],
        'item_name': [
            'item','product','product_name','name','description',
            'goods','commodity','article','sku','product_desc',
            'item_desc','product_code','material'
        ],
        'quantity': [
            'qty','amount','count','units','no_of_items',
            'pieces','nos','volume','number','qty_sold',
            'units_sold','quantity_sold'
        ],
        'unit_profit': [
            'profit','price','unit_price','margin','revenue',
            'value','cost','rate','unit_cost','selling_price',
            'mrp','sp','profit_per_unit','unit_margin'
        ],
        'transaction_date': [
            'date','trans_date','order_date','bill_date',
            'purchase_date','datetime','time','created_at',
            'sale_date','invoice_date','transaction_dt'
        ]
    }

    def load_file(self, uploaded_file):
        name = uploaded_file.name.lower()
        try:
            if name.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except Exception:
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_csv(uploaded_file, encoding='latin-1')
                    except Exception:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=';')
            elif name.endswith('.xlsx') or name.endswith('.xls'):
                df = pd.read_excel(uploaded_file)
            else:
                return None, "Unsupported file format. Please upload CSV, XLSX, or XLS."
            
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_').str.replace('.', '_')
            return df, None
        except Exception as e:
            return None, f"Could not read the file. Error details: {str(e)}"

    def detect_columns(self, df):
        result = {}
        for standard_name, aliases in self.COLUMN_MAP.items():
            if standard_name in df.columns:
                result[standard_name] = {'found': True, 'original': standard_name, 'action': 'exact match'}
            else:
                for alias in aliases:
                    if alias in df.columns:
                        result[standard_name] = {'found': True, 'original': alias, 'action': f'renamed from {alias}'}
                        break
                else:
                    result[standard_name] = {'found': False, 'original': None, 'action': 'will auto-fix'}
        return result

    def validate_and_fix(self, df, profit_map=None, user_column_selections=None):
        df_clean = df.copy()
        col_report = self.detect_columns(df_clean)
        
        rename_map = {}
        for std_name, info in col_report.items():
            if info['found'] and info['original'] != std_name:
                rename_map[info['original']] = std_name
        df_clean.rename(columns=rename_map, inplace=True)
        
        if not col_report['item_name']['found']:
            if user_column_selections and 'item_name' in user_column_selections:
                sel_col = user_column_selections['item_name'].strip().lower().replace(' ', '_').replace('-', '_').replace('.', '_')
                df_clean.rename(columns={sel_col: 'item_name'}, inplace=True)
                col_report['item_name']['found'] = True
                col_report['item_name']['action'] = 'user selected'
            else:
                raise ValueError("Cannot identify item/product column. Please select which column contains product names.")

        original_rows = len(df_clean)
        
        if 'transaction_id' not in df_clean.columns:
            df_clean['transaction_id'] = ['T' + str(i+1).zfill(6) for i in range(len(df_clean))]
            col_report['transaction_id']['action'] = 'auto-generated'
            
        if 'transaction_date' not in df_clean.columns:
            df_clean['transaction_date'] = pd.Timestamp.today()
            col_report['transaction_date']['action'] = 'set to today'
        else:
            try:
                df_clean['transaction_date'] = pd.to_datetime(df_clean['transaction_date'], dayfirst=True, format='mixed', errors='coerce')
                if df_clean['transaction_date'].isna().all():
                    df_clean['transaction_date'] = pd.Timestamp.today()
                else:
                    df_clean['transaction_date'] = df_clean['transaction_date'].fillna(pd.Timestamp.today())
            except Exception:
                df_clean['transaction_date'] = pd.Timestamp.today()

        if 'quantity' not in df_clean.columns:
            df_clean['quantity'] = 1
            col_report['quantity']['action'] = 'set to 1'
        else:
            if df_clean['quantity'].dtype == 'object':
                df_clean['quantity'] = df_clean['quantity'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df_clean['quantity'] = pd.to_numeric(df_clean['quantity'], errors='coerce')
            df_clean['quantity'] = df_clean['quantity'].fillna(1).abs().clip(lower=1).astype(int)

        if 'unit_profit' not in df_clean.columns and profit_map is None:
            df_clean['unit_profit'] = 1.0
            col_report['unit_profit']['action'] = 'set to 1 (equal weight)'
            profit_source = 'equal_weight'
        elif profit_map is not None:
            df_clean['unit_profit'] = df_clean['item_name'].map(profit_map).fillna(1.0)
            profit_source = 'user_provided'
            if 'unit_profit' not in df_clean.columns:
                df_clean['unit_profit'] = 1.0
        else:
            if df_clean['unit_profit'].dtype == 'object':
                df_clean['unit_profit'] = df_clean['unit_profit'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df_clean['unit_profit'] = pd.to_numeric(df_clean['unit_profit'], errors='coerce')
            median_val = df_clean['unit_profit'].median()
            if pd.isna(median_val):
                median_val = 1.0
            df_clean['unit_profit'] = df_clean['unit_profit'].fillna(median_val).abs().clip(lower=0.01)
            profit_source = 'from_file'

        df_clean = df_clean.dropna(subset=['item_name'])
        df_clean = df_clean[df_clean['item_name'].astype(str).str.strip() != '']
        df_clean['item_name'] = df_clean['item_name'].astype(str).str.strip()
        
        df_clean = df_clean.drop_duplicates().reset_index(drop=True)
        cleaned_rows = len(df_clean)
        
        orig_name_col = col_report['item_name']['original'] if col_report['item_name']['original'] else 'item_name'
        if orig_name_col in df.columns:
            valid_orig_rows = len(df.dropna(subset=[orig_name_col]))
        else:
            valid_orig_rows = original_rows
            
        duplicates_removed = original_rows - cleaned_rows - (original_rows - valid_orig_rows)
        if duplicates_removed < 0: duplicates_removed = 0
        
        data_quality = {
            'original_rows': original_rows,
            'cleaned_rows': cleaned_rows,
            'nulls_fixed': df.isna().sum().sum(),
            'duplicates_removed': duplicates_removed,
            'columns_renamed': [v['original'] for k, v in col_report.items() if v['found'] and v['original'] != k],
            'columns_generated': [k for k, v in col_report.items() if not v['found']],
            'profit_source': profit_source
        }
        
        return df_clean, col_report, data_quality

    def needs_profit_input(self, df):
        col_report = self.detect_columns(df)
        if col_report['unit_profit']['found']:
            col_name = col_report['unit_profit']['original']
            sample = pd.to_numeric(df[col_name].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
            if sample.isna().sum() / len(sample) < 0.5:
                return False
        return True

    def get_unique_items(self, df):
        col_report = self.detect_columns(df)
        if col_report['item_name']['found']:
            col_name = col_report['item_name']['original']
            return sorted(df[col_name].astype(str).str.strip().unique().tolist())
        return []

    def generate_sample_template(self):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data = {
                'transaction_id': ['T001', 'T001', 'T002', 'T003', 'T003'],
                'item_name': ['Milk', 'Bread', 'Eggs', 'Milk', 'Butter'],
                'quantity': [2, 1, 12, 1, 1],
                'unit_profit': [3.5, 2.0, 5.0, 3.5, 4.0],
                'transaction_date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-03']
            }
            pd.DataFrame(data).to_excel(writer, sheet_name='Data', index=False)
            
            instructions = {
                'Column': ['transaction_id', 'item_name', 'quantity', 'unit_profit', 'transaction_date'],
                'Description': ['Unique ID for each purchase/basket', 'Name of the product', 'Number of items bought', 'Profit per unit (optional)', 'Date of transaction (optional)'],
                'Accepted Names': [', '.join(self.COLUMN_MAP['transaction_id'][:5]), 
                                   ', '.join(self.COLUMN_MAP['item_name'][:5]),
                                   ', '.join(self.COLUMN_MAP['quantity'][:5]),
                                   ', '.join(self.COLUMN_MAP['unit_profit'][:5]),
                                   ', '.join(self.COLUMN_MAP['transaction_date'][:5])]
            }
            pd.DataFrame(instructions).to_excel(writer, sheet_name='Instructions', index=False)
            
            accepted = []
            for k, v in self.COLUMN_MAP.items():
                for alias in v:
                    accepted.append({'Standard Column': k, 'Accepted Variation': alias})
            pd.DataFrame(accepted).to_excel(writer, sheet_name='Accepted Names', index=False)
            
        return output.getvalue()
