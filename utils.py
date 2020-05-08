from bs4 import BeautifulSoup
import pandas as pd

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
    soup = BeautifulSoup(content)
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
            prices.append(price.text)
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
    
    detailhtml = soup.find('div', attrs={'id':'prodDetails'})
        
    if detailhtml:
        detail = get_label_value_table(detailhtml)
    else:
        detailhtml = soup.find('div',attrs={'id':'detail_bullets_id'})
        detail = get_bucket_content_table(detailhtml)
    
    # SELLERS
    sellers = soup.find('div', attrs={'id':'olp-upd-new-freeshipping-threshold'})
    if sellers:
        detail['sellers'] = sellers.text.replace("\n","")
    else:
        sellers = soup.find('div', attrs={'id':'olp-new'})
        if sellers:
            detail['sellers'] = sellers.text.replace("\n","")
    
    return detail
