import requests
import time
from bs4 import BeautifulSoup
from django.utils import timezone
from panel.models import Proxy

def scrape_sslproxies(limit=50):
    """
    Scrapes fresh proxies from sslproxies.org and stores them in the Django database.
    """
    url = "https://www.sslproxies.org/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    proxies_created = 0
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for the primary proxy list textarea or table
        proxy_table = soup.find("table", id="proxylisttable")
        if not proxy_table:
            # Fallback to general tables
            proxy_table = soup.find("table")
            
        if proxy_table:
            tbody = proxy_table.find("tbody")
            rows = tbody.find_all("tr") if tbody else proxy_table.find_all("tr")[1:]
            
            for row in rows[:limit]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port_str = cols[1].text.strip()
                    try:
                        port = int(port_str)
                    except ValueError:
                        continue
                    
                    proto = "http"
                    if len(cols) >= 7:
                        proto = "https" if cols[6].text.strip().lower() == "yes" else "http"
                    
                    # Create or update in database
                    proxy_obj, created = Proxy.objects.get_or_create(
                        ip=ip,
                        port=port,
                        defaults={
                            'protocol': proto,
                            'is_active': True,
                            'last_checked': timezone.now()
                        }
                    )
                    if created:
                        proxies_created += 1
                        
        print(f"[SCRAPER] Successfully scraped and created {proxies_created} proxies.")
    except Exception as e:
        print(f"[SCRAPER] Error scraping sslproxies: {e}")
        
    return proxies_created

def test_proxy(proxy):
    """
    Tests proxy connection speed and active status against instagram.com.
    Updates the database row.
    """
    auth_part = f"{proxy.username}:{proxy.password}@" if proxy.username and proxy.password else ""
    proxy_url = f"{proxy.protocol}://{auth_part}{proxy.ip}:{proxy.port}"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    start_time = time.time()
    try:
        # Use a short timeout to prevent blocking worker threads
        response = requests.get("https://www.instagram.com", proxies=proxies, timeout=7)
        if response.status_code == 200:
            proxy.speed = round(time.time() - start_time, 2)
            proxy.is_active = True
        else:
            proxy.is_active = False
    except Exception:
        proxy.is_active = False
        
    proxy.last_checked = timezone.now()
    proxy.save()
    return proxy.is_active
