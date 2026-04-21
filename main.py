from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from services.intelligence import get_pricing_intelligence
from services.ingestion import ingest_scraped_data
from extraction.crawler import scrape_multiple_domains
import asyncio

app = FastAPI(title="CommerceOS API", version="1.0.0")

class PricingRequest(BaseModel):
    product_name: str
    similarity_threshold: float = 0.4

class ScrapeRequest(BaseModel):
    urls: list[str]

@app.post("/api/v1/intelligence/pricing")
async def analyze_pricing(request: PricingRequest):
    results = get_pricing_intelligence(request.product_name, request.similarity_threshold)
    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
    return results

@app.post("/api/v1/pipeline/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Triggers the Crawl4AI scraper in the background."""
    background_tasks.add_task(scrape_multiple_domains, request.urls)
    return {"message": f"Scraping started in background for {len(request.urls)} domains."}

@app.post("/api/v1/pipeline/ingest")
async def trigger_ingestion():
    """Reads the data_buffer folder and inserts vectors into Postgres."""
    result = ingest_scraped_data()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)