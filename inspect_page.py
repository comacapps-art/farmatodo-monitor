from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating...")
        page.goto('https://www.farmatodo.com.ve/categorias/cuidado-personal/cuidado-del-cabello', wait_until='domcontentloaded', timeout=60000)
        print("Waiting for JS to render...")
        page.wait_for_timeout(10000)
        # Scroll down a bit to trigger lazy loading if needed
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(5000)
        
        html = page.content()
        with open('category_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Page saved to category_page.html")
        browser.close()

if __name__ == '__main__':
    inspect()
