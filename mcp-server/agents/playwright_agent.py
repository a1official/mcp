"""
Playwright Agent - Web Automation Tools
Provides web browsing, screenshots, and scraping capabilities
"""

import os
import json
from playwright.async_api import async_playwright


def register_playwright_tools(mcp):
    """Register all Playwright-related tools with the MCP server"""
    
    @mcp.tool()
    async def browse_website(url: str, wait_for_selector: str = None) -> str:
        """
        Browse a website and get its content, title, and text.
        Uses stealth mode to avoid bot detection.
        
        Args:
            url: The URL to browse
            wait_for_selector: Optional CSS selector to wait for before extracting content
        
        Returns:
            JSON with page title, text content, and metadata
        """
        async with async_playwright() as p:
            # Launch with stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context with realistic user agent and viewport
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            
            page = await context.new_page()
            
            # Remove webdriver detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for optional selector
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=10000)
                
                title = await page.title()
                text_content = await page.inner_text("body")
                
                # Limit text content to avoid huge responses
                if len(text_content) > 5000:
                    text_content = text_content[:5000] + "... (truncated)"
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": text_content
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def screenshot_website(url: str, filename: str = "screenshot.png") -> str:
        """
        Take a screenshot of a website.
        
        Args:
            url: The URL to screenshot
            filename: Output filename (default: screenshot.png)
        
        Returns:
            JSON with screenshot path and status
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Take screenshot
                screenshot_path = f"screenshots/{filename}"
                os.makedirs("screenshots", exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "screenshot_path": screenshot_path,
                    "message": f"Screenshot saved to {screenshot_path}"
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def extract_links(url: str) -> str:
        """
        Extract all links from a webpage.
        
        Args:
            url: The URL to extract links from
        
        Returns:
            JSON with list of links found on the page
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Extract all links
                links = await page.evaluate("""
                    () => {
                        const anchors = Array.from(document.querySelectorAll('a'));
                        return anchors.map(a => ({
                            text: a.innerText.trim(),
                            href: a.href
                        })).filter(link => link.href && link.href.startsWith('http'));
                    }
                """)
                
                await browser.close()
                
                # Limit to first 50 links
                if len(links) > 50:
                    links = links[:50]
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "link_count": len(links),
                    "links": links
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def search_google(query: str) -> str:
        """
        Search Google and get the top results.
        
        Args:
            query: Search query
        
        Returns:
            JSON with search results (titles, links, snippets)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Go to Google
                await page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded", timeout=30000)
                
                # Wait for results
                await page.wait_for_selector("div#search", timeout=10000)
                
                # Extract search results
                results = await page.evaluate("""
                    () => {
                        const items = [];
                        const resultDivs = document.querySelectorAll('div.g');
                        
                        for (let i = 0; i < Math.min(10, resultDivs.length); i++) {
                            const div = resultDivs[i];
                            const titleEl = div.querySelector('h3');
                            const linkEl = div.querySelector('a');
                            const snippetEl = div.querySelector('div[data-sncf]');
                            
                            if (titleEl && linkEl) {
                                items.push({
                                    title: titleEl.innerText,
                                    link: linkEl.href,
                                    snippet: snippetEl ? snippetEl.innerText : ''
                                });
                            }
                        }
                        
                        return items;
                    }
                """)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "result_count": len(results),
                    "results": results
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def scrape_products(url: str, product_selector: str = None) -> str:
        """
        Scrape product information from e-commerce websites.
        Uses advanced stealth techniques to avoid bot detection.
        
        Args:
            url: The URL to scrape
            product_selector: Optional CSS selector for product containers
        
        Returns:
            JSON with extracted product data
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            )
            
            page = await context.new_page()
            
            # Enhanced anti-detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
            """)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
                await page.wait_for_timeout(2000)
                
                # Extract products
                if product_selector:
                    products = await page.evaluate(f"""
                        () => {{
                            const items = document.querySelectorAll('{product_selector}');
                            return Array.from(items).slice(0, 20).map(item => ({{
                                text: item.innerText.trim(),
                                html: item.innerHTML.substring(0, 500)
                            }}));
                        }}
                    """)
                else:
                    products = await page.evaluate("""
                        () => {
                            const selectors = [
                                '[data-product]', '.product', '.product-item',
                                '[class*="product"]', '[class*="Product"]'
                            ];
                            
                            for (const selector of selectors) {
                                const items = document.querySelectorAll(selector);
                                if (items.length > 0) {
                                    return Array.from(items).slice(0, 20).map(item => ({
                                        text: item.innerText.trim().substring(0, 200),
                                        classes: item.className
                                    }));
                                }
                            }
                            return [];
                        }
                    """)
                
                page_title = await page.title()
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "title": page_title,
                    "products_found": len(products),
                    "products": products
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "suggestion": "Website may have bot protection. Consider using official APIs."
                })

    @mcp.tool()
    async def search_duckduckgo(query: str, max_results: int = 10) -> str:
        """
        Search DuckDuckGo for privacy-focused results.
        Great for finding product information across multiple sites.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 10)
        
        Returns:
            JSON with search results
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                await page.goto(f"https://duckduckgo.com/?q={query}", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector('article[data-testid="result"]', timeout=10000)
                
                results = await page.evaluate(f"""
                    () => {{
                        const items = [];
                        const resultArticles = document.querySelectorAll('article[data-testid="result"]');
                        
                        for (let i = 0; i < Math.min({max_results}, resultArticles.length); i++) {{
                            const article = resultArticles[i];
                            const titleEl = article.querySelector('h2');
                            const linkEl = article.querySelector('a[data-testid="result-title-a"]');
                            const snippetEl = article.querySelector('[data-result="snippet"]');
                            
                            if (titleEl && linkEl) {{
                                items.push({{
                                    title: titleEl.innerText,
                                    link: linkEl.href,
                                    snippet: snippetEl ? snippetEl.innerText : ''
                                }});
                            }}
                        }}
                        
                        return items;
                    }}
                """)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "result_count": len(results),
                    "results": results,
                    "source": "DuckDuckGo"
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def search_products_smart(product_name: str, site: str = None) -> str:
        """
        Smart product search that uses DuckDuckGo to find products across e-commerce sites.
        Avoids direct scraping by searching for product information.
        
        Args:
            product_name: Product name to search for
            site: Optional site to search within (e.g., "blinkit.com", "amazon.in")
        
        Returns:
            JSON with product search results from multiple sources
        """
        # Build search query
        if site:
            search_query = f"site:{site} {product_name}"
        else:
            search_query = f"{product_name} buy online india"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                await page.goto(f"https://duckduckgo.com/?q={search_query}", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector('article[data-testid="result"]', timeout=10000)
                
                results = await page.evaluate("""
                    () => {
                        const items = [];
                        const resultArticles = document.querySelectorAll('article[data-testid="result"]');
                        
                        for (let i = 0; i < Math.min(15, resultArticles.length); i++) {
                            const article = resultArticles[i];
                            const titleEl = article.querySelector('h2');
                            const linkEl = article.querySelector('a[data-testid="result-title-a"]');
                            const snippetEl = article.querySelector('[data-result="snippet"]');
                            
                            if (titleEl && linkEl) {
                                const link = linkEl.href;
                                const domain = new URL(link).hostname;
                                
                                items.push({
                                    title: titleEl.innerText,
                                    link: link,
                                    snippet: snippetEl ? snippetEl.innerText : '',
                                    domain: domain
                                });
                            }
                        }
                        
                        return items;
                    }
                """)
                
                await browser.close()
                
                # Group by domain
                by_domain = {}
                for result in results:
                    domain = result['domain']
                    if domain not in by_domain:
                        by_domain[domain] = []
                    by_domain[domain].append(result)
                
                return json.dumps({
                    "success": True,
                    "product": product_name,
                    "site_filter": site,
                    "total_results": len(results),
                    "results_by_domain": by_domain,
                    "all_results": results,
                    "tip": "Use the links to visit product pages directly. This avoids bot detection."
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
