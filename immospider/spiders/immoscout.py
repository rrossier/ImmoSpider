# -*- coding: utf-8 -*-
import scrapy
import json
from immospider.items import ImmoscoutItem


class ImmoscoutSpider(scrapy.Spider):
    name = "immoscout"
    allowed_domains = ["immobilienscout24.de"]
    # start_urls = ['https://www.immobilienscout24.de/Suche/S-2/Wohnung-Miete/Berlin/Berlin']
    # start_urls = ['https://www.immobilienscout24.de/Suche/S-2/Wohnung-Miete/Berlin/Berlin/Lichterfelde-Steglitz_Nikolassee-Zehlendorf_Dahlem-Zehlendorf_Zehlendorf-Zehlendorf/2,50-/60,00-/EURO--800,00/-/-/']

    # The immoscout search results are stored as json inside their javascript. This makes the parsing very easy.
    # I learned this trick from https://github.com/balzer82/immoscraper/blob/master/immoscraper.ipynb .
    script_xpath = './/script[contains(., "IS24.resultList")]'
    next_xpath = '//div[@id = "pager"]/div/a/@href'

    def start_requests(self):
        yield scrapy.Request(self.url)

    def parse(self, response):

        print(response.url)

        for line in response.xpath(self.script_xpath).extract_first().split('\n'):
            if line.strip().startswith('resultListModel'):
                immo_json = line.strip()
                immo_json = json.loads(immo_json[17:-1])

                #TODO: On result pages with just a single result resultlistEntry is not a list, but a dictionary.
                #TODO: So extracting data will fail.
                for result in immo_json["searchResponseModel"]["resultlist.resultlist"]["resultlistEntries"][0]["resultlistEntry"]:

                    item = ImmoscoutItem()

                    # print(data)

                    data = result["resultlist.realEstate"]

                    item['immo_id'] = data['@id']
                    item['url'] = response.urljoin("/expose/" + str(data['@id']))
                    item['title'] = data['title']
                    address = data['address']
                    try:
                        item['address'] = address['street'] + " " + address['houseNumber']
                    except:
                        item['address'] = None    
                    item['city'] = address['city']
                    item['zip_code'] = address['postcode']
                    item['district'] = address['quarter']
                    try:
                        item['lat'] = address['wgs84Coordinate']['latitude']
                        item['lng'] = address['wgs84Coordinate']['longitude']
                    except Exception as e:
                        # print(e)
                        item['lat'] = None
                        item['lng'] = None

                    item["rent"] = data["price"]["value"]
                    item["livingSpace"] = data["livingSpace"]
                    item["rooms"] = data["numberOfRooms"]
                    item["brokerage"] = data["courtage"]["hasCourtage"]

                    if "calculatedPrice" in data:
                        item["extra_costs"] = (data["calculatedPrice"]["value"] - data["price"]["value"])
                    if "builtInKitchen" in data:
                        item["kitchen"] = data["builtInKitchen"]
                    if "balcony" in data:
                        item["balcony"] = data["balcony"]
                    if "garden" in data:
                        item["garden"] = data["garden"]
                    if "privateOffer" in data:
                        item["private"] = data["privateOffer"]
                    if "plotArea" in data:
                        item["area"] = data["plotArea"]
                    if "cellar" in data:
                        item["cellar"] = data["cellar"]
                    if "guestToilet" in data:
                        item["guestToilet"] = data["guestToilet"]

                    if "@publishDate" in result:
                        item["publishDate"] = result["@publishDate"]

                    try:
                        contact = data['contactDetails']
                        item['contact_name'] = contact['firstname'] + " " + contact["lastname"]
                    except:
                        item['contact_name'] = None

                    try:
                        item['media_count'] = len(data['galleryAttachments']['attachment'])
                    except:
                        item['media_count'] = 0


               
                    yield item

        next_page_list = response.xpath(self.next_xpath).extract()
        if next_page_list:
            next_page = next_page_list[-1]
            print("Scraping next page", next_page)
            if next_page:
                next_page = response.urljoin(next_page)
                yield scrapy.Request(next_page, callback=self.parse)
