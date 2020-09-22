from bs4 import BeautifulSoup
import requests

import csv
import os
import asyncio
import aiohttp

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/83.0.4103.61 Safari/537.36',
           'accept': '*/*'}
FILE = 'ads.csv'


class AvitoParser:

    def __init__(self, url: str, pages=1):
        self.url = url
        if pages == 0:
            raise AttributeError("Attribute pages can't be zero")
        else:
            self.pages = pages

    async def get_html(self, url, params=None):
        """
        Send request with next page and return new html
        :param url: take url
        :param params: take new page
        :return: response of new page
        """
        async with aiohttp.request('get', self.url, params=params) as response:
            return url, await response.text()

    @staticmethod
    def get_pages(html) -> int:
        """
        Find out pagination in current html
        :param html: take new html page
        :return: number of pages
        """
        soup = BeautifulSoup(html, 'html.parser')
        pages = soup.find('div', class_='paginate')
        if pages:
            return int(pages.find_all('a')[-1].get('href').split(',')[-1])
        else:
            return 1

    @staticmethod
    def get_content(content) -> list:
        """
        Collect information from html page
        :param content: list of tuples with two elements
        :return: list of data
        """
        items = []
        for _, html in content:
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all('tr', class_=('odd', 'even'))

        ads = []
        for item in items:
            ads.append({
                'title': item.find('td', class_='text').find_next('a').get('title'),
                'link': item.find('td', class_='text').find_next('a').get('href'),
                'short_description': item.find('td', class_='text').find_next('div', class_='zoznam_desc').get_text(
                    strip=True),
                'country': item.find('td', class_='text').find_next('span', class_='zoznam_country').get_text().replace(
                    ' · ', ''),
                'city': item.find('td', class_='text').find_next('span', class_='zoznam_city').get_text().replace(' · ',
                                                                                                                  ''),
                'price': item.find('div', class_='zoznam_cena round2').get_text(),
            })
        return ads

    @staticmethod
    def save_file(items: list, file_name: str):
        """
        Write new data in csv file
        :param items: list of data
        :param file_name: name of file to write
        """
        with open(file_name, 'w', newline='', encoding='utf8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['title', 'link', 'short_description', 'country', 'city', 'price'])
            for item in items:
                writer.writerow([item['title'], item['link'], item['short_description'],
                                 item['country'], item['city'], item['price']])

    async def parse(self):
        """
        Main parser function
        """
        html = requests.get(self.url)
        if html.status_code == 200:
            ads = []
            tasks = []
            for page in range(1, self.pages + 1):
                print(f'Parse {page} page from {self.pages}')
                task = asyncio.create_task(self.get_html(self.url, params={'iPage': page}))  # create response of new page
                tasks.append(task)
            content = await asyncio.gather(*tasks)  # unpacking tasks
            ads.extend(self.get_content(content))
            self.save_file(ads, FILE)
            print(f'Got {len(ads)} ad(s)')
            os.startfile(FILE)
        else:
            print('No connection')


if __name__ == '__main__':
    avito = AvitoParser(url='https://avitoua.com/search/iPage,', pages=2)
    asyncio.run(avito.parse())
