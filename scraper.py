import time
import datetime
import urllib.parse
import pandas as pd
from playwright.sync_api import sync_playwright

def scrape_farmatodo(query: str, headless: bool = False):
    products_data = []
    
    # Format URL if it's a keyword instead of a full link
    if query.startswith('http'):
        url = query
    else:
        # Encode keyword for URL
        encoded_query = urllib.parse.quote(query.upper())
        url = f"https://www.farmatodo.com.ve/buscar?product={encoded_query}&departamento=Todos&filtros="
        
    # Generate unique output file to avoid Permission Denied
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"products_{timestamp}.csv"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Optimización extrema de memoria: Bloquear imágenes, fuentes y videos
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
        
        print(f"Navigating to {url} ...")
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        
        # Wait a bit for initial dynamic content to load
        page.wait_for_timeout(5000)
        
        # Scroll and extract products continuously to handle virtual scrolling
        print("Scrolling down and loading all products...")
        previous_height = 0
        attempts = 0
        
        unique_products = {}
        
        while True:
            # Look for "Cargar más" button and click it if visible
            load_more = page.locator('button:has-text("Cargar más")')
            if load_more.count() > 0:
                try:
                    if load_more.first.is_visible():
                        load_more.first.click()
                        page.wait_for_timeout(3000)
                except Exception as e:
                    pass

            # Extract currently visible products
            cards = page.locator('.product-card').all()
            for card in cards:
                try:
                    title_loc = card.locator('.product-card__title')
                    title = title_loc.inner_text().strip() if title_loc.count() > 0 else ""
                    
                    brand_loc = card.locator('.product-card__brand')
                    brand = brand_loc.inner_text().strip() if brand_loc.count() > 0 else ""
                    
                    price_loc = card.locator('.product-card__price-value')
                    price = price_loc.inner_text().strip() if price_loc.count() > 0 else ""
                    
                    # Extract link and SKU
                    link_loc = card.locator('.product-card__info-link')
                    link = ""
                    sku = ""
                    if link_loc.count() > 0:
                        href = link_loc.first.get_attribute('href')
                        if href:
                            link = f"https://www.farmatodo.com.ve{href}"
                            try:
                                sku = href.split('/producto/')[1].split('-')[0]
                            except:
                                pass
                                
                    # Extract Old Price
                    old_price_loc = card.locator('.product-card__price-offer')
                    old_price = old_price_loc.inner_text().strip() if old_price_loc.count() > 0 else ""
                    
                    # Extract Image
                    img_loc = card.locator('img.product-image__image')
                    image_url = img_loc.first.get_attribute('src') if img_loc.count() > 0 else ""
                    
                    # Extract Discount Percentage
                    discount_loc = card.locator('.offer .text')
                    discount = discount_loc.inner_text().strip() if discount_loc.count() > 0 else ""
                    
                    if title and price:
                        unique_id = sku if sku else title
                        unique_products[unique_id] = {
                            "Brand": brand,
                            "Title": title,
                            "Price": price,
                            "Link": link,
                            "SKU": sku,
                            "OldPrice": old_price,
                            "Image": image_url,
                            "Discount": discount
                        }
                except Exception as e:
                    pass

            current_height = page.evaluate('document.body.scrollHeight')
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2500) # Espera a que carguen los nuevos
            
            if current_height == previous_height:
                attempts += 1
                if attempts >= 3: # Si después de 3 intentos no carga más, ya terminó
                    break
            else:
                attempts = 0
            
            previous_height = current_height

        print("Extracting products...")
        products_data = list(unique_products.values())
        print(f"Extracted {len(products_data)} unique products.")

        browser.close()

    if products_data:
        try:
            df = pd.DataFrame(products_data)
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Successfully saved {len(products_data)} products to {output_file}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            output_file = None
    else:
        print("No products found. Make sure the URL is correct and the page has products.")
        output_file = None
        
    return products_data, output_file

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Farmatodo Web Scraper')
    parser.add_argument('url', help='URL of the Farmatodo category or product search')
    
    args = parser.parse_args()
    scrape_farmatodo(args.url)
