from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io

from modules.huim_engine import HUIMEngine, AprioriMiner
from modules.db_connector import (
    test_connection, load_transactions, get_dataset_stats, 
    load_top_items, load_monthly_summary, save_upload_record
)
from modules.file_processor import FileProcessor

app = FastAPI(title="HUIM API", version="2.0.0")

@app.get("/")
def read_root():
    return {"message": "HUIM API v2.0.0 is running"}

@app.get("/health")
def health_check():
    db_ok = test_connection()
    return {"status": "online", "mysql_ok": db_ok, "version": "2.0.0"}

@app.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    fp = FileProcessor()
    content = await file.read()
    file_like = io.BytesIO(content)
    file_like.name = file.filename
    
    raw_df, error = fp.load_file(file_like)
    if error:
        return {"error": error}
        
    cleaned_df, col_report, data_quality = fp.validate_and_fix(raw_df)
    
    engine = HUIMEngine(cleaned_df)
    results = engine.run_full_pipeline(max_combo_size=2)
    
    if test_connection():
        save_upload_record({
            'filename': file.filename,
            'total_records': len(cleaned_df),
            'total_items': cleaned_df['item_name'].nunique(),
            'hfhu_count': len(results['results_df'][results['results_df']['category'] == 'HFHU']),
            'hflu_count': len(results['results_df'][results['results_df']['category'] == 'HFLU']),
            'lfhu_count': len(results['results_df'][results['results_df']['category'] == 'LFHU']),
            'execution_time': results['execution_time'],
            'profit_source': data_quality['profit_source']
        })
        
    return {
        "filename": file.filename,
        "records": len(cleaned_df),
        "column_report": col_report,
        "quality_report": data_quality,
        "thresholds": results['thresholds'],
        "results": results['results_df'].to_dict(orient="records"),
        "lfhu_items": results['results_df'][results['results_df']['category'] == 'LFHU'].to_dict(orient="records"),
        "monthly_trends": results['monthly_df'].to_dict(orient="records"),
        "execution_time": results['execution_time'],
        "profit_source": data_quality['profit_source']
    }

@app.get("/dataset-summary")
def get_dataset_summary():
    return get_dataset_stats()

@app.get("/top-utility-items")
def get_top_utility_items(limit: int = 10):
    df = load_top_items(limit)
    return df.to_dict(orient="records")

@app.get("/monthly-trends")
def get_monthly_trends():
    df = load_monthly_summary()
    return df.to_dict(orient="records")

@app.get("/download-template")
def download_template():
    fp = FileProcessor()
    template_bytes = fp.generate_sample_template()
    return StreamingResponse(
        io.BytesIO(template_bytes),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": "attachment; filename=huim_template.xlsx"}
    )
