from datetime import datetime
from typing import Dict
from pydantic import BaseModel

class InsertCrawlData(BaseModel):
    company_id : int
    title : str
    content : str
    url : str
    content_type : str
    meta_data : Dict[str, any]
    published_at : datetime
    created_at : datetime

    model_config = {"from_attributes": True}

class CrawlDataListItem(BaseModel):
    company_id : int
    title : str
    content : str | None
    url : str | None
    content_type : str
    meta_data : Dict[str, any] | None
    published_at : datetime
    created_at : datetime

class CrawlDataListResponse(BaseModel):
    items: list[CrawlDataListItem]
    total: int
    page: int
    page_size: int