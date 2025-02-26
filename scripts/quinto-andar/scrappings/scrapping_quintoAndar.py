import re
from time import sleep

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class PropertyDataExtractor:
    """Extrai dados textuais de elementos HTML."""

    @staticmethod
    def extract_value_text(element):
        valor = re.search(r"\d+\.?\d*", element)
        return valor.group() if valor else None

    @staticmethod
    def extract_size_text(element):
        size = re.search(r"\d+\s*m²", element)
        return size.group() if size else None

    @staticmethod
    def extract_rooms_text(element):
        rooms = re.search(r"\d+\s*[Qq]uartos?", element)
        return rooms.group() if rooms else None

    @staticmethod
    def extract_parking_text(element):
        parking = re.search(r"(\d+|0)\s*[Vv]agas?", element)
        return parking.group() if parking else "0 vaga"

    @staticmethod
    def extract_type_text(element):
        house_type = re.search(r'\b(apartamento|casa|studio|kitnet)\b', element, re.IGNORECASE)
        return house_type.group() if house_type else None

    @staticmethod
    def extract_property_data(valor, size, rooms, parking, house_type, description):
        return {
            'description': description,
            'type': house_type,
            'price': valor,
            'size': size,
            'bedrooms': rooms,
            'parking_spaces': parking,
        }

class PropertyScraper:
    """Configura e executa a raspagem de dados do site de propriedades."""

    def __init__(self, base_url, options=None):
        self.base_url = base_url
        self.options = options if options else Options()
        self.data_list = []
        self.options.add_argument('window-size=1400,925')

    def setup_driver(self):
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(self.base_url)

    def close_driver(self):
        self.driver.quit()

    def load_all_properties(self):
        while True:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Ver mais']"))
                )
                button.click()
                sleep(3)
            except Exception as e:
                print("Botão 'Ver mais' não está mais disponível ou erro:", e)
                break

    def scrape_properties(self):
        self.setup_driver()
        self.load_all_properties()

        page_content = self.driver.page_source
        site = BeautifulSoup(page_content, 'html.parser')

        properties = site.find_all('div', attrs={'role': 'presentation', 'class': 'Cozy__CardRow-Container oVdjIf'})
        type_text = site.find_all('h2', attrs={'class': 'CozyTypography UQvm9e xih2fc _72Hu5c _1tBHcU'})
        price_text = site.find_all('div', attrs={'class': 'Cozy__CardTitle-Title hFUhPy'})
        # print(len(price_text))

        for i in range(len(properties)):
            # print(len(properties))
            valor = PropertyDataExtractor.extract_value_text(price_text[i].text)
            size = PropertyDataExtractor.extract_size_text(properties[i].text)
            description = properties[i].find('h2').text if properties[i].find('h2') else None
            house_type = PropertyDataExtractor.extract_type_text(type_text[i].text)
            rooms = PropertyDataExtractor.extract_rooms_text(properties[i].text)
            parking = PropertyDataExtractor.extract_parking_text(properties[i].text)

            property_data = PropertyDataExtractor.extract_property_data(valor, size, rooms, parking, house_type, description)
            self.data_list.append(property_data)

        self.close_driver()
        return self.data_list

class DataHandler:
    """Manipula e salva os dados extraídos em um DataFrame."""

    def __init__(self, data):
        self.data = data

    def create_dataframe(self):
        df = pd.DataFrame(self.data)
        df['bathrooms'] = pd.NA  # Adiciona coluna bathrooms com valores nulos
        df['modo'] = pd.NA  # Adiciona coluna modo com valores nulos
        return df

    def save_to_csv(self, df, filename):
        df.to_csv(filename, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    base_url = 'https://www.quintoandar.com.br/alugar/imovel/brasilia-df-brasil?referrer=home&profiling=true'

    scraper = PropertyScraper(base_url)
    properties_data = scraper.scrape_properties()

    print(f"Imóveis capturados até agora: {len(properties_data)}")

    data_handler = DataHandler(properties_data)
    df = data_handler.create_dataframe()
    data_handler.save_to_csv(df, 'imoveis_df_aluguel.csv')
    print("Dados salvos em 'imoveis_df_aluguel.csv'")
