import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import pandas as pd

class PartSelectScraper:
    def __init__(self):
        self.base_url = "https://www.partselect.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_parts = []

    def get_category_urls(self):
        """Get URLs for refrigerator and dishwasher parts categories"""
        categories = {
            'refrigerator': 'https://www.partselect.com/Refrigerator-Parts.htm',
            'dishwasher': 'https://www.partselect.com/Dishwasher-Parts.htm'
        }
        return categories

    def scrape_category_parts(self, category_url, appliance_type, max_parts=50):
        """Scrape parts from a category page"""
        print(f"Scraping {appliance_type} parts from: {category_url}")

        try:
            response = self.session.get(category_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find product links - this will need to be adjusted based on actual HTML structure
            product_links = soup.find_all('a', href=re.compile(r'/[A-Z0-9]+-'))[:max_parts]

            for link in product_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    part_data = self.scrape_part_details(full_url, appliance_type)
                    if part_data:
                        self.scraped_parts.append(part_data)
                        print(f"Scraped: {part_data.get('name', 'Unknown part')}")

                    # Rate limiting
                    time.sleep(1)

        except Exception as e:
            print(f"Error scraping category {category_url}: {e}")

    def scrape_part_details(self, part_url, appliance_type):
        """Scrape detailed information from a part page"""
        try:
            response = self.session.get(part_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract part information - adjust selectors based on actual HTML
            part_data = {
                'url': part_url,
                'appliance_type': appliance_type,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Part name
            name_elem = soup.find('h1') or soup.find('title')
            if name_elem:
                part_data['name'] = name_elem.get_text().strip()

            # Part numbers
            ps_number = soup.find(text=re.compile(r'PS\d+'))
            if ps_number:
                part_data['partselect_number'] = ps_number.strip()

            mfg_number = soup.find(text=re.compile(r'W\d+|[A-Z]\d+'))
            if mfg_number:
                part_data['manufacturer_part_number'] = mfg_number.strip()

            # Price
            price_elem = soup.find(class_=re.compile(r'price'))
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                if price_match:
                    part_data['price'] = float(price_match.group(1))

            # Reviews
            review_elem = soup.find(text=re.compile(r'\d+ Reviews?'))
            if review_elem:
                review_match = re.search(r'(\d+)', review_elem)
                if review_match:
                    part_data['review_count'] = int(review_match.group(1))

            # Rating
            rating_elem = soup.find(class_=re.compile(r'star|rating'))
            if rating_elem:
                # Extract rating logic here
                part_data['rating'] = 4.5  # Placeholder

            # Description
            desc_elem = soup.find('div', class_=re.compile(r'description|product-desc'))
            if desc_elem:
                part_data['description'] = desc_elem.get_text().strip()[:500]

            # Symptoms
            symptoms = []
            symptom_elems = soup.find_all(text=re.compile(r'fixes|symptom', re.I))
            for symptom in symptom_elems:
                symptoms.append(symptom.strip())
            part_data['symptoms'] = symptoms[:5]

            # Installation info
            install_elem = soup.find(text=re.compile(r'\d+\s*-\s*\d+\s*min'))
            if install_elem:
                part_data['installation_time'] = install_elem.strip()

            difficulty_elem = soup.find(text=re.compile(r'Easy|Medium|Hard'))
            if difficulty_elem:
                part_data['difficulty'] = difficulty_elem.strip()

            # Category
            breadcrumb = soup.find(class_=re.compile(r'breadcrumb'))
            if breadcrumb:
                categories = [a.get_text().strip() for a in breadcrumb.find_all('a')]
                part_data['category'] = categories[-1] if categories else 'Unknown'

            return part_data

        except Exception as e:
            print(f"Error scraping part {part_url}: {e}")
            return None

    def scrape_all_parts(self, max_parts_per_category=50):
        """Scrape parts from all categories"""
        categories = self.get_category_urls()

        for appliance_type, url in categories.items():
            self.scrape_category_parts(url, appliance_type, max_parts_per_category)
            print(f"Completed {appliance_type}, total parts: {len(self.scraped_parts)}")

    def save_to_json(self, filename='partselect_parts.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.scraped_parts, f, indent=2)
        print(f"Saved {len(self.scraped_parts)} parts to {filename}")

    def save_to_csv(self, filename='partselect_parts.csv'):
        """Save scraped data to CSV file"""
        if self.scraped_parts:
            df = pd.DataFrame(self.scraped_parts)
            df.to_csv(filename, index=False)
            print(f"Saved {len(self.scraped_parts)} parts to {filename}")

def main():
    scraper = PartSelectScraper()

    print("Starting PartSelect scraping...")
    scraper.scrape_all_parts(max_parts_per_category=25)  # Start small for testing

    # Save results
    scraper.save_to_json('data/partselect_parts.json')
    scraper.save_to_csv('data/partselect_parts.csv')

    print(f"Scraping complete! Total parts collected: {len(scraper.scraped_parts)}")

if __name__ == "__main__":
    main()