import time
import datetime
import urllib.parse
import pandas as pd
import time
import datetime
import urllib.parse
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

async def _async_scrape(url: str, headless: bool):
    products_data = []
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"products_{timestamp}.csv"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        # Optimización extrema de memoria: Bloquear imágenes, fuentes y videos usando regex estricto
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,map}", lambda r: r.abort())
        
        print(f"Navigating to {url} ...")
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            
            print("Scrolling down and loading all products...")
            previous_count = 0
            attempts = 0
            
            while True:
                await page.evaluate("""
                    () => {
                        window.scrollBy(0, 800);
                        const btn = document.querySelector('#group-view-load-more') || 
                                    Array.from(document.querySelectorAll('button')).find(b => /ver m[aá]s|cargar m[aá]s/i.test(b.textContent));
                        if (btn && btn.offsetParent !== null) btn.click();
                    }
                """)
                await page.wait_for_timeout(1200)
                
                current_count = await page.evaluate("() => document.querySelectorAll('.product-card').length")
                
                if current_count == previous_count:
                    attempts += 1
                    if attempts >= 3:
                        break
                else:
                    attempts = 0
                    
                previous_count = current_count

            print("Scroll complete. Extracting all products at once...")
            js_extract = """
            () => {
                let results = [];
                document.querySelectorAll('.product-card').forEach(card => {
                    try {
                        let title = card.querySelector('.product-card__title')?.innerText.trim() || "";
                        let brand = card.querySelector('.product-card__brand')?.innerText.trim() || "";
                        let price = card.querySelector('.product-card__price-value')?.innerText.trim() || "";
                        let linkNode = card.querySelector('a.product-card__info-link');
                        let href = linkNode ? linkNode.getAttribute('href') : "";
                        let link = href ? "https://www.farmatodo.com.ve" + href : "";
                        let sku = "";
                        if (href && href.includes('/producto/')) {
                            sku = href.split('/producto/')[1].split('-')[0];
                        }
                        let oldPrice = card.querySelector('.product-card__price-offer')?.innerText.trim() || "";
                        let imgNode = card.querySelector('img.product-image__image');
                        let image = imgNode ? imgNode.getAttribute('src') : "";
                        let discount = card.querySelector('.offer .text')?.innerText.trim() || "";
                        
                        if (title && price) {
                            results.push({
                                Brand: brand, Title: title, Price: price, Link: link,
                                SKU: sku, OldPrice: oldPrice, Image: image, Discount: discount
                            });
                        }
                    } catch(e) {}
                });
                return results;
            }
            """
            
            products_chunk = await page.evaluate(js_extract)
            unique_products = {}
            for p in products_chunk:
                unique_id = p.get("SKU") if p.get("SKU") else p.get("Title")
                unique_products[unique_id] = p

            print("Extracting products...")
            products_data = list(unique_products.values())
            print(f"Extracted {len(products_data)} unique products.")
            
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            await browser.close()

    if products_data:
        try:
            df = pd.DataFrame(products_data)
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Successfully saved {len(products_data)} products to {output_file}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            output_file = None
    else:
        print("No products found.")
        output_file = None
        
    return products_data, output_file

def scrape_farmatodo(query: str, headless: bool = False):
    if query.startswith('http'):
        url = query
    else:
        encoded_query = urllib.parse.quote(query.upper())
        url = f"https://www.farmatodo.com.ve/buscar?product={encoded_query}&departamento=Todos&filtros="
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        products, output_file = loop.run_until_complete(_async_scrape(url, headless))
    finally:
        loop.close()
        
    return products, output_file

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Farmatodo Web Scraper')
    parser.add_argument('url', help='URL of the Farmatodo category or product search')
    
    args = parser.parse_args()
    products, f = scrape_farmatodo(args.url, headless=True)
    print(f"Found {len(products)} products.")
