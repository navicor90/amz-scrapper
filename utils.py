from bs4 import BeautifulSoup
import pandas as pd
import re
import pickle
import sys
sys.setrecursionlimit(50000)

def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def soup_content_from_url(driver, url):
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content,features="lxml")
    return soup


def elements_from_soup_bestsellers_web(soup):
    descriptions = []
    badges = []
    prices = []
    links = []
    products_html_lists = soup.findAll('li',attrs={'class':'zg-item-immersion','role':'gridcell'})
    for i,p in enumerate(products_html_lists):
        badge = p.find('span',attrs={'class':'zg-badge-text'})
        a = p.find('a',href=True, attrs={'class':'a-link-normal'})
        href = a['href']
        desc = a.find('div', attrs={'class':'p13n-sc-truncated'})
        price = p.find('span',attrs={'class':'p13n-sc-price'})
        if badge and desc and price and href:
            badges.append(badge.text)
            descriptions.append(desc.text)
            links.append(href)
            prices.append(price.text.replace("€",""))
    return pd.DataFrame({'Badge':badges,'Product':descriptions,'Price':prices,'Link':links})


def subcategories_from_bestsellers_web(soup):
    subcategories = []
    subcategories_tree_ul = soup.find('ul',attrs={'id':'zg_browseRoot'})
    tree_options = subcategories_tree_ul.findAll('a',href=True)
    for l in tree_options:
        subcategories.append({'name':l.text,'url':l['href']})
    return subcategories

def detail_dict_from_product_page(soup,url):
    detail = {}
    def get_label_value_table(detailhtml):
        detail = {}
        tables = detailhtml.findAll('table')
        for t in tables:
            labels = t.findAll('td', attrs={'class':'label'})
            values = t.findAll('td', attrs={'class':'value'})
            for k,v in zip(labels,values):
                detail[k.text] = v.text.replace("\n","")
        return detail
    
    def get_bucket_content_table(detailhtml):
        detail = {}
        li_elems = detailhtml.find('td', attrs={'class':'bucket'}).findAll('li')
        for li in li_elems:
            if li.has_attr('class'):
                continue
            if len(li.text.split(':')) < 2:
                continue
            label = li.text.split(':')[0]
            value = li.text.split(':')[1]
            detail[label] = value.replace("\n","")
        return detail
    
    
    detailhtml = soup.find('div', attrs={'id': 'prodDetails'})
    print(detailhtml)
    if detailhtml:
        detail = get_label_value_table(detailhtml)
    else:
        detailhtml = soup.find('div', attrs={'id': 'detail_bullets_id'})
        if detailhtml:
            detail = get_bucket_content_table(detailhtml)
        else:
            detailhtml = soup.find('div',attrs={'id':'detail_bullets_id'})
            print('fail looking:' + url)
    # There is different flavors about sellers info, and in each one have a different id
    sellers_div_ids = ['olp-upd-new-freeshipping-threshold','olp-upd-new-freeshipping','olp-new',
                       'olp-upd-new-used-freeshipping-threshold']
    for div_id in sellers_div_ids:
        sellers_div = soup.find('div', attrs={'id':div_id})
        if sellers_div:
            s = sellers_div.text.replace("\n","")
            detail['sellers'] = s[s.find("(")+1:s.find(")")]
            break
    
    return detail



class AmzProduct: 
    ref_amz_id = None
    detail_link = None
    brand = None
    description = None
    price = None
    reviews = None
    stars = None
    stock = None
    
    def __init__(self,amz_data_dict):
        for k,v in amz_data_dict.items():
            if isinstance(k,str):
                setattr(self,k,v)

class ProductSerch:
    ref_local_id = None
    provider_name = None
    amz_related_products = []


def amz_products_with_soup(soup):
    def search_results(soup):
        return (soup.find('span',attrs={'data-component-type':'s-search-results'})
                   .findAll('div',attrs={'class':'s-result-item'}))
    
    def data_from_div_result(div_result):
        def text_elements(item_div_result):
            inner_elements = item_div_result.contents
            while len(inner_elements) == 1:
                inner_elements = inner_elements[0].contents
                # Cleaning contents
                for i,e in enumerate(inner_elements):
                    if len(str(e).strip()) == 0 or e.text.strip() is "":
                        inner_elements.remove(e)
            return inner_elements
        
        def data_dict_from_elements(elements):
            data = {}
            for i,e in enumerate(elements):
                if 'estrellas' in str(e):
                    stars = e.find('span',string=re.compile('estrellas'))
                    data['stars'] = str(stars.text).strip()
                elif 'h2' in str(e):
                    link = e.find('a')
                    data['description'] = str(e.text).strip()
                    data['link'] = link.get("href")
                elif 'a-price' in str(e).strip():
                    whole_price = e.find('span',attrs={'class':'a-price-whole'}).text
                    symbol = e.find('span',attrs={'class':'a-price-symbol'}).text
                    data['price'] = str(whole_price)+symbol
                elif 'stock' in str(e):
                    stock = e.find('span',string=re.compile('stock'))
                    data['stock'] = str(stock.text).strip()
                else:
                    #data[i] = str(e.text).strip()
                    pass
            return data
        elements = text_elements(div_result)
        return data_dict_from_elements(elements)
    print("Splitting results...")
    div_results = search_results(soup)
    products = []
    print(f'{len(div_results)} elements found. \nConverting to AmzProduct objects...')
    for dr in div_results:
        amz_data = data_from_div_result(dr)
        products.append(AmzProduct(amz_data))
    print('Ready!.')
    return products
        
