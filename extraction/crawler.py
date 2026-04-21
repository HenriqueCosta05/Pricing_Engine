import os
import json
import asyncio
from urllib.parse import urlparse
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

def get_domain_key(url: str) -> str:
    domain = urlparse(url).netloc
    return domain.replace("www.", "").replace(".", "_")

async def scrape_multiple_domains(urls: list):
    schema_dir = Path("schemas")
    schema_dir.mkdir(exist_ok=True)
    
    data_dir = Path("data_buffer")
    data_dir.mkdir(exist_ok=True)
    
    browser_cfg = BrowserConfig(headless=True)
    llm_config = LLMConfig(
        provider="gemini/gemini-1.5-flash",
        api_token=os.getenv("GEMINI_API_KEY") 
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for url in urls:
            domain_key = get_domain_key(url)
            schema_path = schema_dir / f"{domain_key}_schema.json"
            
            if schema_path.exists():
                with open(schema_path, "r") as f:
                    schema = json.load(f)
            else:
                schema = JsonCssExtractionStrategy.generate_schema(
                    url=url,
                    query="Extract a list of products with fields: title, price, url, and seller.",
                    schema_type="css",
                    llm_config=llm_config
                )
                with open(schema_path, "w") as f:
                    json.dump(schema, f, indent=2)

            strategy = JsonCssExtractionStrategy(schema=schema, verbose=False)
            extraction_cfg = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.BYPASS)
            
            result = await crawler.arun(url=url, config=extraction_cfg)
            if result.success:
                data = json.loads(result.extracted_content)
                save_path = data_dir / f"{domain_key}.json"
                with open(save_path, "w") as f:
                    json.dump(data, f, indent=2)