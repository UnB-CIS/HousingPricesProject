#' @title: Web Scrapping DFimoveis
#' @author: Luiz Paulo Tavares 

import pandas as pd
import requests
import time
import os
import re
import random
import concurrent.futures
from utils.data_handler import DataHandler
from bs4 import BeautifulSoup

HEADERS = {
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'
}

class PropertyScraper:
    def __init__(self, base_url, property_type="imoveis", headers=HEADERS):
        self.base_url = base_url.format(property_type=property_type)
        self.headers = headers
        self.property_type = property_type

    def extract_property_data(self, property_soup):

        """Extracts relevant data from a property listing HTML element."""
        # Import re at the function level so it's available for all nested functions
        import re

        def get_text_or_none(element, selector):
            selected_element = element.select_one(selector)
            return selected_element.get_text(strip=True) if selected_element else None

        # Descrição \* 

        description = get_text_or_none(property_soup, 'h2.new-title.phrase')
        
        # Tipo de imóvel \* 
        
        type_property_full = get_text_or_none(property_soup, 'h3.new-desc.phrase')
        
        # Extract clean property type from the full description
        property_type = self.property_type  # Default to the property_type used in the URL
        
        # If we have type_property_full, try to extract cleaner value
        if type_property_full and isinstance(type_property_full, str):
            type_property_full = type_property_full.lower()
            # Check each property type and see if it's in the description
            for p_type in PROPERTY_TYPES:
                if p_type.lower() in type_property_full:
                    property_type = p_type
                    break
        
        # Preço do imóvel \* 
        
        price_raw = get_text_or_none(property_soup, 'div.new-price span')
        
        # Clean price value (extract numeric part)
        price = None
        if price_raw:
            if 'Sob Consulta' in price_raw:
                price = ''  # Empty string for 'Sob Consulta'
            else:
                # Extract numeric part using regex, even if it has 'A partir de'
                numeric_match = re.search(r'(\d+(?:[.,]\d+)?)', price_raw)
                if numeric_match:
                    price_value = numeric_match.group(1)
                    # Remove dots from thousands separators and replace comma with dot for decimal
                    price_value = price_value.replace('.', '').replace(',', '.')
                    try:
                        price = float(price_value)
                    except:
                        price = price_raw
                else:
                    price = ''
        
        # Tamanho do imóvel em m² \* 

        size_m2_element = property_soup.find('span', string = lambda x: x and "m²" in x)
        size_m2_raw = size_m2_element.get_text(strip = True) if size_m2_element else None
        
        # Clean size value (remove 'm²' and convert to numeric)
        size_m2 = None
        if size_m2_raw:
            # Handle ranges like "64 a 219 m²" - take the first number
            if 'a' in size_m2_raw:
                size_m2_raw = size_m2_raw.split('a')[0].strip()
            
            # Extract numeric part
            numeric_match = re.search(r'(\d+(?:[.,]\d+)?)', size_m2_raw)
            if numeric_match:
                size_value = numeric_match.group(1)
                # Replace comma with dot for decimal values
                size_value = size_value.replace(',', '.')
                try:
                    size_m2 = float(size_value)
                except:
                    size_m2 = size_value
        
        # Nº de quartos \* 

        bedroom_element = property_soup.find('span', string = lambda x: x and re.search(r'\b(quartos?|Quartos?)\b', x))
        bedroom_raw = bedroom_element.get_text(strip = True) if bedroom_element else None
        
        # Clean bedroom value (extract numeric part)
        bedroom = None
        if bedroom_raw:
            # Handle ranges like "2 a 3 quartos" - take the first number
            if 'a' in bedroom_raw:
                bedroom_raw = bedroom_raw.split('a')[0].strip()
            
            # Extract numeric part
            numeric_match = re.search(r'(\d+)', bedroom_raw)
            if numeric_match:
                try:
                    bedroom = int(numeric_match.group(1))
                except:
                    bedroom = bedroom_raw
        
        # Nº de vagas de carragem \* 

        car_spaces_element = property_soup.find('span', string = lambda x: x and re.search(r'\b(Vaga?|Vagas?)\b', x))
        car_spaces_raw = car_spaces_element.get_text(strip = True) if car_spaces_element else None
        
        # Clean parking spaces value (extract numeric part)
        car_spaces = None
        if car_spaces_raw:
            # Extract numeric part
            numeric_match = re.search(r'(\d+)', car_spaces_raw)
            if numeric_match:
                try:
                    car_spaces = int(numeric_match.group(1))
                except:
                    car_spaces = car_spaces_raw

        return {
            'description': description,
            'address': "",
            'property_type': property_type,
            'price': price,
            'size': size_m2,
            'bedrooms': bedroom,
            'bathrooms': '',
            'parking_spaces': car_spaces
        }

    def scrape_page(self, page_number, max_retries=3):
        """Scrapes a single page for property listings with retry logic."""

        retries = 0
        backoff_factor = 2
        base_wait_time = 2  # Starting with 2 seconds delay

        while retries <= max_retries:
            try:
                url = f"{self.base_url}{page_number}"
                
                # Add jitter to appear more human-like
                jitter = random.uniform(0.5, 1.5)
                wait_time = base_wait_time * (backoff_factor ** retries) * jitter
                
                if retries > 0:
                    print(f"Retry #{retries} for page {page_number} - waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    site = BeautifulSoup(response.text, "html.parser")
                    properties = site.find_all('div', class_='new-info')
                    
                    # Check if we got properties or empty results
                    if properties:
                        return [self.extract_property_data(property_soup) for property_soup in properties], 200
                    else:
                        # This might be the last page with no more results
                        print(f"Página {page_number} não contém propriedades.")
                        return [], 204  # Using 204 to indicate no content but successful request
                
                # Handle specific error codes
                if response.status_code == 429:  # Too Many Requests
                    print(f"Rate limit atingido na página {page_number}. Esperando antes de tentar novamente...")
                    retries += 1
                    continue
                    
                if response.status_code >= 500:  # Server errors
                    print(f"Erro de servidor na página {page_number}. Tentando novamente...")
                    retries += 1
                    continue
                    
                # Other client errors that aren't worth retrying
                if response.status_code >= 400 and response.status_code < 500:
                    print(f"Erro de cliente na página {page_number}. Status code: {response.status_code}")
                    return [], response.status_code
                    
            except requests.RequestException as e:
                print(f"Erro de conexão na página {page_number}: {str(e)}")
                retries += 1
                continue
                
        print(f"Número máximo de tentativas atingido para a página {page_number}")
        return [], 503  # Service Unavailable after retries

    def scrape_all_pages(self, max_pages=None, workers=1, batch_size=10, batch_delay=30, save_each_batch=True, category='venda', property_type='imoveis', output_dir=None, append=True):
        """Scrapes all pages until no more data is available or an error occurs.
        
        Args:
            max_pages: Maximum number of pages to scrape, None for unlimited
            workers: Number of concurrent workers
            batch_size: Number of pages to process before taking a longer pause
            batch_delay: Seconds to pause between batches
            save_each_batch: Whether to save data after each batch
            category: Contract type (venda/aluguel)
            property_type: Type of property being scraped
            output_dir: Directory to save batch data
            append: Whether to append to existing files
        """
        all_properties = []
        empty_page_count = 0
        page = 1
        current_batch = 1
        consecutive_empty_pages_threshold = 2  # Stop after this many consecutive empty pages
        
        # Calculate batches if max_pages is specified
        total_batches = None
        if max_pages:
            total_batches = (max_pages + batch_size - 1) // batch_size
            print(f"Scraping will be performed in {total_batches} batches of {batch_size} pages each.")
        
        while True:
            batch_properties = []
            batch_start_page = page
            print(f"\n--- Starting batch {current_batch} (pages {batch_start_page} to {batch_start_page + batch_size - 1}) ---")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                # Process one batch of pages
                batch_page_count = 0
                futures = []
                
                # Submit batch of pages to the executor
                for i in range(min(batch_size, workers)):
                    if max_pages and page > max_pages:
                        break
                        
                    print(f"Raspando a página {page}...")
                    futures.append(executor.submit(self.scrape_page, page))
                    page += 1
                    batch_page_count += 1
                
                # Process initial results
                empty_in_batch = 0
                for future in concurrent.futures.as_completed(futures):
                    properties, status_code = future.result()
                    
                    # Handle different status codes
                    if status_code == 204:  # No content but success
                        empty_in_batch += 1
                        empty_page_count += 1
                        if empty_page_count >= consecutive_empty_pages_threshold:
                            print(f"Encontradas {consecutive_empty_pages_threshold} páginas vazias consecutivas. Assumindo fim dos resultados.")
                            return all_properties
                    elif status_code != 200:
                        print(f"Erro ao acessar página. Status code: {status_code}")
                        # Don't stop completely on errors, just skip this page
                    else:  # 200 with properties
                        empty_page_count = 0  # Reset counter when we find properties
                        batch_properties.extend(properties)
                
                # Submit remaining pages for this batch if needed
                while batch_page_count < batch_size:
                    if max_pages and page > max_pages:
                        break
                        
                    print(f"Raspando a página {page}...")
                    future = executor.submit(self.scrape_page, page)
                    page += 1
                    batch_page_count += 1
                    
                    properties, status_code = future.result()
                    if status_code == 204:  # No content but success
                        empty_in_batch += 1
                        empty_page_count += 1
                        if empty_page_count >= consecutive_empty_pages_threshold:
                            print(f"Encontradas {consecutive_empty_pages_threshold} páginas vazias consecutivas. Assumindo fim dos resultados.")
                            return all_properties
                    elif status_code != 200:
                        print(f"Erro ao acessar página. Status code: {status_code}")
                    else:  # 200 with properties
                        empty_page_count = 0  # Reset counter
                        batch_properties.extend(properties)
            
            # Add batch properties to the total
            batch_property_count = len(batch_properties)
            all_properties.extend(batch_properties)
            
            # Status report for this batch
            print(f"\n--- Batch {current_batch} completed ---")
            print(f"Pages processed: {batch_page_count}")
            print(f"Empty pages: {empty_in_batch}")
            print(f"Properties found: {batch_property_count}")
            print(f"Total properties so far: {len(all_properties)}")
            
            # If we've hit max_pages, stop
            if max_pages and page > max_pages:
                print(f"Atingido o número máximo de páginas: {max_pages}")
                break
            
            # Save data after each completed batch if requested
            if save_each_batch and batch_properties and output_dir:
                print(f"Saving data from batch {current_batch}...")
                # Process batch data
                batch_data_handler = DataHandler(batch_properties)
                batch_df = batch_data_handler.create_dataframe(category)
                
                # Use simplified file naming - one file per contract type (venda/aluguel)
                excel_filename = f'imoveis_df_{category}.xlsx'
                csv_filename = f'imoveis_df_{category}.csv'
                
                # Save with append=True to keep adding to the same files
                batch_data_handler.save_to_excel(batch_df, excel_filename, output_dir=output_dir, append=append)
                batch_data_handler.save_to_csv(batch_df, csv_filename, output_dir=output_dir, append=append)
                
                print(f"Batch {current_batch} data for {property_type} saved to {output_dir}/{excel_filename}")
            
            # Take a longer pause between batches
            actual_delay = batch_delay + random.uniform(-5, 5)  # Add some randomness
            print(f"Pausando por {actual_delay:.1f} segundos antes do próximo lote...")
            time.sleep(actual_delay)
            current_batch += 1
            
        print(f"\nRaspagem concluída. Total de propriedades coletadas: {len(all_properties)}")
        return all_properties

# URL Base constants - will be formatted with property_type
BASE_URL_ALUGUEL = "https://www.dfimoveis.com.br/aluguel/df/todos/{property_type}?pagina="
BASE_URL_VENDA = "https://www.dfimoveis.com.br/venda/df/todos/{property_type}?pagina="

# Available property types from the DF Imoveis website
PROPERTY_TYPES = [
    "apartamento",
    "casa",
    "casa-condominio",
    "galpao",
    "garagem", 
    "hotel-flat",
    "kitnet",
    "loja",
    "lote",
    "loteamento",
    "ponto-comercial",
    "predio",
    "rural",
    "sala"
]

def run_scraper(category='venda', property_type='imoveis', max_pages=30, workers=3, output_dir=None, append=True, custom_output_files=None, batch_size=30, batch_delay=30, save_each_batch=True):
    """Run the DF Imoveis scraper with the specified parameters.
    
    Args:
        category (str): Type of properties to scrape ('venda' or 'aluguel')
        max_pages (int): Maximum number of pages to scrape
        workers (int): Number of concurrent workers for threading
        output_dir (str): Directory to save output files
        append (bool): Whether to append to existing files
        custom_output_files (dict): Custom file paths for output (excel_path, csv_path)
        batch_size (int): Number of pages per batch to process before pausing
        batch_delay (int): Seconds to wait between batches
    """
    # Select the base URL based on the scraping mode
    base_url = BASE_URL_ALUGUEL if category == 'aluguel' else BASE_URL_VENDA
    
    # Initialize scraper and perform scraping
    scraper = PropertyScraper(base_url=base_url, property_type=property_type)
    properties_data = scraper.scrape_all_pages(
        max_pages=max_pages, 
        workers=workers, 
        batch_size=batch_size, 
        batch_delay=batch_delay,
        save_each_batch=save_each_batch,
        category=category,
        property_type=property_type,
        output_dir=output_dir,
        append=append
    )
    
    # Process scraped data
    
    data_handler = DataHandler(properties_data)
    df = data_handler.create_dataframe(category)
    
    # Save the data to files if output_dir is provided
    if output_dir is not None:
        # Check if custom output files are specified
        if custom_output_files and 'excel_path' in custom_output_files and 'csv_path' in custom_output_files:
            # Use the standardized file paths from the orchestrator
            excel_path = custom_output_files['excel_path']
            csv_path = custom_output_files['csv_path']
            
            # Save directly to specified paths
            data_handler.save_to_excel(df, excel_path, append=append)
            data_handler.save_to_csv(df, csv_path, append=append)
            
            print(f"Excel data saved to {excel_path}")
            print(f"CSV data saved to {csv_path}")
        else:
            # Use simplified file naming - one file per contract type (venda/aluguel)
            excel_filename = f'imoveis_df_{category}.xlsx'
            csv_filename = f'imoveis_df_{category}.csv'
            
            data_handler.save_to_excel(df, excel_filename, output_dir=output_dir, append=append)
            data_handler.save_to_csv(df, csv_filename, output_dir=output_dir, append=append)
            
            print(f"Excel data saved to {output_dir}/{excel_filename}")
            print(f"CSV data saved to {output_dir}/{csv_filename}")
    
    return df

# This allows the script to be run directly for testing
def run_all_scrapers(max_pages=30, workers=3, output_dir=None, append=True, batch_size=30, batch_delay=30, save_each_batch=True):
    """Run all scrapers for all contract types and property types.
    
    Args:
        max_pages (int): Maximum number of pages to scrape per combination
        workers (int): Number of concurrent workers for threading
        output_dir (str): Directory to save output files
        append (bool): Whether to append to existing files
        batch_size (int): Number of pages per batch
        batch_delay (int): Seconds to wait between batches
    """
    contract_types = ['aluguel']
    all_dataframes = []
    
    for contract_type in contract_types:
        for property_type in PROPERTY_TYPES:
            print(f"\n\nScraping {contract_type} - {property_type}...")
            df = run_scraper(
                category=contract_type,
                property_type=property_type,
                max_pages=max_pages,
                workers=workers,
                output_dir=output_dir,
                append=append,
                batch_size=batch_size,
                batch_delay=batch_delay,
                save_each_batch=save_each_batch
            )
            all_dataframes.append(df)
            
            # Give the server some rest between different property types
            time.sleep(30)
    
    return all_dataframes

if __name__ == "__main__":
    # Example usage when running the script directly
    # df = run_scraper(
    #     category='venda',
    #     property_type='apartamento',
    #     max_pages=30,
    #     workers=3,
    #     output_dir="scripts/df-imoveis/dataset",
    #     append=True,
    #     batch_size=30,
    #     batch_delay=30,
    #     save_each_batch=True
    # )
    
    all_dfs = run_all_scrapers(
        max_pages=None,
        workers=3,
        output_dir="scripts/df-imoveis/dataset",
        append=True,
        batch_size=40,
        batch_delay=20,
        save_each_batch=True
    )
