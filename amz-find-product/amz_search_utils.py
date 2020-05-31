from bs4 import BeautifulSoup
import re


def read_soup(filename):
    with open("soups/"+filename+".html", "r") as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'lxml')
        return soup


class AmazonProductSearch(object):
    soup = None

    class SearchItem(object):
        item_div_result = None

        def __init__(self, item_div_result):
            self.item_div_result = item_div_result

        def to_dict(self):
            e = self.item_div_result
            data = {}
            if 'estrellas' in str(e):
                stars = e.find('span', string=re.compile('estrellas'))
                data['stars'] = str(stars.text).strip()
            if 'h2' in str(e):
                link = e.find('a')
                data['description'] = str(e.find('h2').text).strip()
                data['link'] = link.get("href")
            if 'a-price' in str(e).strip():
                whole_price = e.find('span', attrs={'class': 'a-price-whole'}).text
                symbol = e.find('span', attrs={'class': 'a-price-symbol'}).text
                data['price'] = str(whole_price) + symbol
            if 'stock' in str(e):
                stock = e.find('span', string=re.compile('stock'))
                data['stock'] = str(stock.text).strip()
            return data

    def __init__(self, soup):
        self.soup = soup

    def _search_results(self):
        results = (self.soup.find('span', attrs={'data-component-type': 's-search-results'})
                   .findAll('span', attrs={'cel_widget_id': 'MAIN-SEARCH_RESULTS'}))
        return results

    def _cleaned_search_results(self):
        results = self._search_results()
        cleaned_results = []
        for r in results:
            is_publicity = 'template=SAFE_FRAME' in str(r)
            is_help_frame = 'template=FEEDBACK' in str(r)
            is_message = 'template=TOP_BANNER_MESSAGE' in str(r)
            if not (is_publicity or is_help_frame or is_message):
                cleaned_results.append(r)
        return cleaned_results

    def searchItems(self):
        results = []
        for r in self._cleaned_search_results():
            results.append(AmazonProductSearch.SearchItem(r))
        return results



