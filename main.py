from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
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
    products: list[str] = Field(default_factory=list)
    max_results: int = 10

@app.post("/api/v1/intelligence/pricing")
async def analyze_pricing(request: PricingRequest):
    results = get_pricing_intelligence(request.product_name, request.similarity_threshold)
    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
    return results

@app.post("/api/v1/pipeline/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Triggers the Crawl4AI scraper in the background."""
    background_tasks.add_task(scrape_multiple_domains, request.urls, request.products, request.max_results)

    message = f"Scraping started in background for {len(request.urls)} domains."
    if request.products:
        message = f"Scraping started in background for {len(request.urls)} domains and {len(request.products)} products."
    message += f" Limiting to first {request.max_results} results per domain."

    return {"message": message}


@app.post("/api/v1/pipeline/scrape/live")
async def trigger_scrape_live(request: ScrapeRequest):
    """Streams scraping progress back to the client in real time."""

    async def event_stream():
        async def send(message: str):
            yield f"data: {message}\n\n"

        queue = asyncio.Queue()

        async def progress(message: str):
            await queue.put(message)

        scrape_task = asyncio.create_task(
            scrape_multiple_domains(
                request.urls,
                request.products,
                request.max_results,
                progress_callback=progress,
            )
        )

        try:
            while True:
                if scrape_task.done() and queue.empty():
                    break

                message = await queue.get()
                yield f"data: {message}\n\n"

            await scrape_task
            yield "data: Stream closed\n\n"
        except Exception as exc:
            if not scrape_task.done():
                scrape_task.cancel()
            yield f"data: Error: {exc}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/v1/pipeline/ingest")
async def trigger_ingestion():
    """Reads the data_buffer folder and inserts vectors into Postgres."""
    result = ingest_scraped_data()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)