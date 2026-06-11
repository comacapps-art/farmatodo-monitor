import urllib.parse
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(headless=True)
page = browser.new_page()
page.goto('https://www.farmatodo.com.ve/buscar?product=NOVEX&departamento=Todos&filtros=', wait_until='domcontentloaded')
page.wait_for_timeout(5000)

unique_skus = set()

attempts = 0
prev = 0
while True:
    load_more = page.locator('button:has-text("Cargar más")')
    if load_more.count() > 0:
        try:
            if load_more.first.is_visible():
                load_more.first.click()
                page.wait_for_timeout(3000)
        except:
            pass

    # Extract currently visible
    cards = page.locator('.product-card').all()
    for card in cards:
        link_loc = card.locator('.product-card__info-link')
        if link_loc.count() > 0:
            href = link_loc.first.get_attribute('href')
            unique_skus.add(href)

    curr = page.evaluate('document.body.scrollHeight')
    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    page.wait_for_timeout(2500)
    
    if curr == prev:
        attempts += 1
        if attempts >= 3:
            break
    else:
        attempts = 0
    prev = curr

print(f"Total unique products found: {len(unique_skus)}")

browser.close()
p.stop()
