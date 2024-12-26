import requests
import json
import time
import os
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from RedisConnection import RedisConnection

URL = "https://dentalstall.com/"

class Abstractclass(ABC):
    @abstractmethod
    def update(self, message: str):
        pass

class Printnotifications(Abstractclass):
    def update(self, message):
        print("Notification:->",message)

class Notifications:
    def __init__(self):
        self._observers = []
        self.scraped_products = 0
        self.updated_products = 0

    def add_observer(self, observer: Abstractclass):
        self._observers.append(observer)

    def remove_observer(self, observer: Abstractclass):
        self._observers.remove(observer)

    def notify_observers(self):
        message = f"Scraped {self.scraped_products} products and updated {self.updated_products} in the database."
        for observer in self._observers:
            observer.update(message)

    def scrape(self):
        self.notify_observers()

class ProductScraper:
    def __init__(self, pages_to_scrape, proxy=None):
        self.pages_to_scrape = pages_to_scrape
        self.proxy = proxy
        self.scraped_data = []
        self.cache = {}  #assuming cache as a redis.. 
    
    def request_with_retry(self, url: str, retries: int = 3, delay: int = 2, token: str = None) -> str:

        """
        Note: I am added a proxy server just need to ensure we not get blocked by target server with same IP address
        as for now proxy is None, as no restriction on target but in real world scenario we can use proxy server to avoid facing 
        blocking/throttling from target end.

        For authroization using STATIC_TOKEN as None just for showing the real use cases 
        """

        STATIC_TOKEN = None
        if token != STATIC_TOKEN:
            raise Exception("Unauthorized: Invalid or missing token, Please try with Valid Token")

        for retry in range(retries):
            try:
                proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                response = requests.get(
                    url,
                    proxies=proxies,
                    headers={"Authorization": f"Bearer {token}"} if token else None
                )
                response.raise_for_status()
                return response.text

            except requests.exceptions.RequestException as e:
                print('Error while fetching data from URL & retry count is: {}, {}, {}'.format(url, e, retry))
                time.sleep(delay) 

        raise Exception("Failed to fetch data from url: {} and error is: {}".format(url, e))


    def scrape_page(self, url: str):

        """
            - finding all products card
            - fetching title, price & image_url from scrapped data
            - Doing cache operations
        """

        html = self.request_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')

        products = []
        product_cards = soup.select('div[class*="product"]') 
   
        for card in product_cards:

            title = card.find('h3', class_='product-title').text.strip() if card.find('h3', class_='product-title') else "No title"
            price = card.find('span', class_='product-price').text.strip().replace('$', '').replace(',', '') if card.find('span', class_='product-price') else "0"
            image_url = card.find('img')['src'] if card.find('img') else ""

            image_name = image_url.split('/')[-1] if image_url else ""
            image_path = os.path.join('images', image_name)
    
            cached_price = self.cache.get(title)


            #cache operations
            if cached_price and float(cached_price) == float(price):
                print('Skipping update in cache as title:{} and price:{} remains same'.format(title, price))
            else:
                self.cache[title] = price 
                print('Product updated with title: {} and new price: {}'.format(title, price))

            products.append({
                "product_title": title,
                "product_price": float(price),
                "path_to_image": image_path
            })

        return products

    def save_to_json(self, data, filename='atyls_assignment_scapping.json'):

        """
           Saving daa to json file name atyls_assignment_scapping.json
        """

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def scrape(self):

        """
           This is a scrape function to call URL, scrape and notifications service.
        """

        current_page = 1
        all_products = []

        while current_page <= self.pages_to_scrape:
            url = f"{URL}shop/page/{current_page}/"
            products = self.scrape_page(url)
            all_products.extend(products)

            current_page += 1
            time.sleep(2)  # sleep time = 2 seconds

        self.save_to_json(all_products)


        Notifications().scraped_products = len(all_products)
        Notifications().updated_products = len(all_products) 
        Notifications().notify_observers()
        return all_products


if __name__ == "__main__":
    pages_to_scrape = 5
    scraper = ProductScraper(pages_to_scrape)
    console_observer = Printnotifications()
    Notifications().add_observer(console_observer)
    try:
        scraped_data = scraper.scrape()
        print(f"Scraping completed. Total products scraped: {len(scraped_data)}")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
