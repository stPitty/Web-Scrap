import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm

from keywords import KEYWORDS


class Habr:

    def __init__(self, keywords, pages=1):
        self.url = 'https://habr.com'
        self.keywords = keywords
        self.result = []
        self.pages = pages

    def _get_response(self, page):
        response = requests.get(url=self.url + '/ru/all/page' + str(page),
                                headers={'User-Agent': 'Chrome/70.0.3538.77'}
                                )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, features='html.parser')
        news = soup.find_all('article', class_='tm-articles-list__item')
        return news

    def find_preview(self):
        for page in range(self.pages):
            news = self._get_response(page + 1)
            for article in tqdm(news,
                                desc=f'Ищем информацию в превью, стр: {page + 1}',
                                colour='Yellow'):
                text = article.find('div', class_='article-formatted-body article-formatted-body_version-1')
                if text is None:
                    text = article.find('div', class_='article-formatted-body article-formatted-body_version-2')
                link = article.find('a', class_='tm-article-snippet__title-link')
                if link is not None:
                    find_words = set(text.text.split())
                    self._compare(find_words, link, article)

    def find_all_post(self):
        for page in range(self.pages):
            news = self._get_response(page + 1)
            for article in tqdm(news,
                                desc=f'Сканируем целый пост, стр: {page + 1}',
                                colour='green'):
                link = article.find('a', class_='tm-article-snippet__title-link')
                if link is not None:
                    href = self.url + link.attrs.get('href')
                    response = requests.get(href)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, features='html.parser')
                    text = soup.find('div', id='post-content-body')
                    find_words = set(text.text.split())
                    self._compare(find_words, link, article)

    def find_hubs(self):
        for page in range(self.pages):
            news = self._get_response(page + 1)
            for article in tqdm(news,
                                desc=f'Проверяем хабы на соответствие, стр: {page + 1}',
                                colour='MAGENTA'):
                link = article.find('a', class_='tm-article-snippet__title-link')
                if link is not None:
                    text = article.find_all('span', class_='tm-article-snippet__hubs-item')
                    find_words = {hub.text.strip() for hub in text}
                    self._compare(find_words, link, article)

    def _compare(self, find_words, link, article):
        if self.keywords & find_words:
            key = ', '.join(list((self.keywords & find_words)))
            title = link.find('span').text
            href = self.url + link.attrs.get('href')
            posting_time = article.find('time').attrs.get('title')
            self.result.append({'title': title,
                                'posting_time': posting_time,
                                'url': href,
                                'keywords': key
                                })
            return self.result


def save_json(content, file_name):
    file_name += '.json'
    with open(file_name, 'w+') as file:
        json.dump(content, file, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    one = Habr(KEYWORDS, pages=5)
    one.find_all_post()
    one.find_hubs()
    one.find_preview()
    save_json(one.result, 'result')
