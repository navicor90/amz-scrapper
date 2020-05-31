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
    
def save_soup(soup, file_name):
    with open("soups/"+file_name+".html", "w") as file:
        file.write(str(soup))

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
        getattr(self,'description')#is mandatory
    
    def list_order():
        return ["ref_amz_id",
            "detail_link",
            "brand",
            "description",
            "price",
            "reviews",
            "stars",
            "stock"]
    
    def to_list(self):
        return [getattr(self,a) for a in AmzProduct.list_order()]
