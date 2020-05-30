from bs4 import BeautifulSoup
import pandas as pd
from enum import Enum
from datetime import datetime
import locale
# $ sudo locale-gen es_ES
# $ sudo locale-gen es_ES.UTF-8
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

class PropertyType(Enum):
    LAND='land'
    APARTMENT='apartment'
    HOUSE='house'

    
class Property(object):    
    
    def __init__(self,house_dict):
        # Initialize all public attributes in None
        for k in Property.attributes_order():
            setattr(self,k,None)
        self.scrapped_date = datetime.now()
        
        for k in house_dict.keys():
            setattr(self,k,house_dict[k])
        
        mandatory_attrs = ['source_web','recent_id','scrapped_date','url','totalArea','district']
        for a in mandatory_attrs:
            if not getattr(self,a):
                raise Exception(f'Error creating house: {a} is needed')
        
    def attributes_order():
        return ['ref_id',
                'neighborhood',
                'district',
                'province',
                'currency',
                'amount',
                'price',
                'url',
                'description',
                'property_type',
                'owner',
                'source_web',
                'recent_id',
                'scrapped_date',
                'totalArea',
                'floorArea',# superficie cubierta
                'bedrooms',
                'bathrooms',
                'garage',
                'has_gas',
                'has_water',
                'has_electricity']
    
    def to_list(self):
        return [getattr(self, a) for a in Property.attributes_order()]
    
    
class InmoclickSearchItem(object):
    html_article = None
    property_type = None
    
    def __init__(self, html_article, property_type : PropertyType):
        self.html_article = html_article
        self.property_type = property_type
        
    
    def ref_id(self):
        return self.html_article.a.get("name").strip()
    
    
    def district(self):
        return self.html_article.find('span',attrs={'itemprop':'addressLocality'}).text.strip()

    
    def neighborhood(self):
        return self.html_article.find('p',attrs={'itemprop':'streetAddress'}).text.strip()

    
    def province(self):
        return self.html_article.find('span',attrs={'itemprop':'addressRegion'}).text.strip()

    
    def price_dict(self):
        price = {}
        price['price'] = self.html_article.get("precio").strip()
        if not 'consultar' in price['price'].lower():
            price['currency'] = price['price'].strip().split(' ')[0]
            price['amount'] = locale.atof(price['price'].strip().split(' ')[1])
        return price

    
    def description(self):
        return (self.html_article.find('div', attrs={'class':'description-hover'})
                            .p.text).strip()

    
    def article_link(self):
        return (self.html_article.find('div', attrs={'class':'description-hover'})
                .a.next_sibling.get('href')).strip()


    def total_area(self):
        return self.html_article.get("sup_t").strip()
        
        
    def covered_area(self):
        return self.html_article.get("sup_c").strip()
            
        
    def bedrooms(self):
        return self.html_article.find('span',attrs={'class':'label-dormitorio'}).text.strip()
    
    
    def bathroom(self):
        return self.html_article.find('span',attrs={'class':'label-banio'}).text.strip()
    
    
    def has_gas(self):
        classes = self.html_article.find('div',attrs={'class':'icon-gas'}).get('class')
        if 'disable' in classes:
            return False
        return True
    
    
    def has_water(self):
        classes = self.html_article.find('div',attrs={'class':'icon-agua'}).get('class')
        if 'disable' in classes:
            return False
        return True
    
    
    def has_electricity(self):
        classes = self.html_article.find('div',attrs={'class':'icon-luz'}).get('class')
        if 'disable' in classes:
            return False
        return True
    
    
    def agency(self):
        agency = None
        owner_div = self.html_article.find('div',attrs={'class':'property-brand'})
        if owner_div.img:
            agency = owner_div.img.get('title')
        else:
            agency = owner_div.p.text
        return agency.strip()
    
    
    def to_dict(self):
        property_dict = {}

        property_dict['ref_id'] = self.ref_id()

        # Property data
        property_dict['neighborhood'] = self.neighborhood()
        property_dict['district'] = self.district()
        property_dict['province'] = self.province()
        property_dict.update(self.price_dict())
        property_dict['url'] = self.article_link()
        property_dict['description'] = self.description()
        property_dict['totalArea'] = self.total_area()
           
        if self.property_type.value in [PropertyType.HOUSE.value, PropertyType.APARTMENT.value]:
            # Property tags
            property_dict['bedrooms'] = self.bedrooms()
            property_dict['bathrooms'] = self.bathrooms()
            property_dict['floorArea'] = self.covered_area()

        if self.property_type.value in [PropertyType.LAND.value]:
            # Property tags
            property_dict['has_water'] = self.has_water()
            property_dict['has_electricity'] = self.has_electricity()
            property_dict['has_gas'] = self.has_gas()

        # Property brand
        property_dict['agency'] = self.agency()
        property_dict['property_type'] = self.property_type

        return property_dict