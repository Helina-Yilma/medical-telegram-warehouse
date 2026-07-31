from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from . import schemas, database

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="API to access analytical insights from medical telegram data.",
    version="1.0.0"
)

@app.get("/api/reports/top-products", response_model=List[schemas.ProductMentions])
def get_top_products(limit: int = 10, db: Session = Depends(database.get_db)):
    """Returns the most frequently mentioned terms/products."""
    query = text("""
        SELECT message_text as product_name, count(*) as mention_count 
        FROM clean.fct_messages
        GROUP BY 1 ORDER BY 2 DESC LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return result

@app.get("/api/channels/{channel_name}/activity", response_model=List[schemas.ChannelActivity])
def get_channel_activity(channel_name: str, db: Session = Depends(database.get_db)):
    """Returns posting activity trends for a specific channel."""
    query = text("""
        SELECT d.full_date as date, COUNT(m.message_id) as message_count
        FROM clean.fct_messages m
        JOIN clean.dim_channels c ON m.channel_key = c.channel_key
        JOIN clean.dim_dates d ON m.date_key = d.date_key
        WHERE c.channel_name = :channel_name
        GROUP BY 1 ORDER BY 1 ASC
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchall()
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found or no activity recorded")
    return result

@app.get("/api/search/messages", response_model=List[schemas.MessageResult])
def search_messages(query: str, limit: int = 20, db: Session = Depends(database.get_db)):
    """Searches for messages containing a specific keyword."""
    search_query = text("""
        SELECT m.message_id, c.channel_name as channel_title, m.message_text, d.full_date as message_date
        FROM clean.fct_messages m
        JOIN clean.dim_channels c ON m.channel_key = c.channel_key
        JOIN clean.dim_dates d ON m.date_key = d.date_key
        WHERE m.message_text ILIKE :search_term
        LIMIT :limit
    """)
    result = db.execute(search_query, {"search_term": f"%{query}%", "limit": limit}).fetchall()
    return result

@app.get("/api/reports/visual-content", response_model=List[schemas.VisualStats])
def get_visual_stats(db: Session = Depends(database.get_db)):
    """Returns statistics about image usage across channels."""
    # We cast the AVG result to ::numeric so ROUND() can process it
    query = text("""
        SELECT 
            image_category, 
            COUNT(*) as total_count, 
            ROUND(AVG(confidence_score)::numeric, 4) as avg_views
        FROM clean.fct_image_detections
        GROUP BY 1
    """)
    result = db.execute(query).fetchall()
    return result