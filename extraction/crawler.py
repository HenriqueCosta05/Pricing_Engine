import os
import json
import asyncio
import logging
from urllib.parse import urlparse
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from core.config import LLM_PROVIDER, LLM_PROVIDER_FALLBACKS

logger = logging.getLogger(__name__)

def get_domain_key(url: str) -> str:
    domain = urlparse(url).netloc
    return domain.replace("www.", "").replace(".", "_")


def get_product_key(product: str) -> str:
    return "_".join(product.lower().strip().split())

async def scrape_multiple_domains(
    urls: list,
    products: list[str] | None = None,
    max_results: int = 10,
    progress_callback=None,
):
    async def emit(message: str):
        logger.info(message)
        if progress_callback is not None:
            result = progress_callback(message)
            if asyncio.iscoroutine(result):
                await result

    schema_dir = Path("schemas")
    schema_dir.mkdir(exist_ok=True)
    
    data_dir = Path("data_buffer")
    data_dir.mkdir(exist_ok=True)
    
    browser_cfg = BrowserConfig(headless=True)
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    provider = LLM_PROVIDER

    if gemini_api_key:
        os.environ.setdefault("OPENAI_API_KEY", gemini_api_key)
        os.environ.setdefault("GOOGLE_API_KEY", gemini_api_key)

    logger.info(
        "Schema generation config: provider=%s gemini_key_present=%s openai_key_present=%s google_key_present=%s",
        provider,
        bool(gemini_api_key),
        bool(os.getenv("OPENAI_API_KEY")),
        bool(os.getenv("GOOGLE_API_KEY")),
    )
    llm_config = LLMConfig(
        provider=provider,
        api_token=gemini_api_key,
    )

    selected_products = [product for product in (products or []) if product]
    if selected_products:
        await emit(f"Selected products: {', '.join(selected_products)}")

    target_products = selected_products if selected_products else [None]
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for target_product in target_products:
            if target_product:
                await emit(f"Starting product: {target_product}")

            for url in urls:
                domain_key = get_domain_key(url)
                file_suffix = domain_key
                product_focus = ""

                if target_product:
                    product_key = get_product_key(target_product)
                    file_suffix = f"{domain_key}__{product_key}"
                    product_focus = f" matching product: {target_product}"

                schema_path = schema_dir / f"{file_suffix}_schema.json"
                await emit(f"Starting {url}" + (f" for {target_product}" if target_product else ""))
                logger.debug("Schema path: %s, exists: %s", schema_path, schema_path.exists())

                if schema_path.exists():
                    try:
                        with open(schema_path, "r") as f:
                            schema = json.load(f)
                        logger.info("Loaded cached schema from %s", schema_path)
                        await emit(f"Loaded cached schema for {file_suffix}")
                    except Exception as exc:
                        logger.exception("Failed to load cached schema from %s", schema_path)
                        await emit(f"Failed to load cached schema from {file_suffix}: {exc}")
                        continue
                else:
                    await emit(f"Generating schema for {file_suffix}")
                    logger.info("Generating schema for URL=%s suffix=%s provider=%s has_key=%s", url, file_suffix, provider, bool(gemini_api_key))
                    schema = None
                    providers_to_try = [provider] + LLM_PROVIDER_FALLBACKS
                    last_error = None

                    for attempt_provider in providers_to_try:
                        try:
                            query_text = f"Extract the first {max_results} products{product_focus} with fields: title, price, url, and seller."
                            logger.debug("Query: %s", query_text)
                            logger.debug("Attempting schema generation with provider=%s", attempt_provider)
                            
                            attempt_llm_config = LLMConfig(
                                provider=attempt_provider,
                                api_token=gemini_api_key if "gemini" in attempt_provider.lower() else None,
                            )
                            
                            schema = JsonCssExtractionStrategy.generate_schema(
                                url=url,
                                query=query_text,
                                schema_type="css",
                                llm_config=attempt_llm_config
                            )
                            logger.info("Successfully generated schema for %s with provider=%s", file_suffix, attempt_provider)
                            await emit(f"Generated schema for {file_suffix} using {attempt_provider}")
                            break
                        except Exception as e:
                            last_error = e
                            logger.warning("Schema generation failed with provider=%s error=%s", attempt_provider, str(e))
                            await emit(f"Provider {attempt_provider} failed, trying next...")
                            continue

                    if schema is None:
                        logger.exception("All schema generation providers failed for %s", file_suffix)
                        await emit(f"Schema generation failed for {file_suffix}: {last_error}")
                        continue
                    
                    try:
                        with open(schema_path, "w") as f:
                            json.dump(schema, f, indent=2)
                        logger.info("Saved schema to %s", schema_path)
                        await emit(f"Saved schema for {file_suffix}")
                    except Exception as exc:
                        logger.exception("Schema generation failed for URL=%s suffix=%s error=%s", url, file_suffix, str(exc))
                        await emit(f"Schema generation failed for {file_suffix}: {exc}")
                        continue

                strategy = JsonCssExtractionStrategy(schema=schema, verbose=False)
                extraction_cfg = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.BYPASS)

                await emit(f"Crawling {url}" + (f" for {target_product}" if target_product else ""))
                logger.info("Starting crawl with schema for URL=%s suffix=%s", url, file_suffix)
                try:
                    result = await crawler.arun(url=url, config=extraction_cfg)
                    logger.debug("Crawl result for %s: success=%s", url, result.success)
                    
                    if result.success:
                        logger.info("Crawl succeeded for %s", url)
                        data = json.loads(result.extracted_content)
                        if isinstance(data, list):
                            data = data[:max_results]
                        save_path = data_dir / f"{file_suffix}.json"
                        with open(save_path, "w") as f:
                            json.dump(data, f, indent=2)
                        logger.info("Saved %d items to %s", len(data), save_path)
                        await emit(f"Saved {len(data)} items for {file_suffix}")
                    else:
                        logger.warning("Crawl failed for %s: result.success=False", url)
                        await emit(f"Failed to crawl {url}" + (f" for {target_product}" if target_product else ""))
                except Exception as exc:
                    logger.exception("Crawl exception for URL=%s suffix=%s", url, file_suffix)
                    await emit(f"Crawl exception for {file_suffix}: {exc}")

    await emit("Scraping complete")