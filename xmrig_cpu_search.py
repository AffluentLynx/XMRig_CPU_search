#!/usr/bin/env python3

# Standard Python libraries.
import os
import sys
import time

# Third party Python libraries.
import requests
import json
from tqdm import tqdm
from bs4 import BeautifulSoup

# Custom Python libraries.


__version__ = "1.1.0"


SER_NUM = 50                   #search number- how many search results the search engine return
SLEEPTIME = 10                   #In seconds, provides a pause to avoid rate limiting by search engine
samples_threshold = 100           #samples is the amount of times a benchmark test was submitted
HASHRATE_MAX= 40000
hashrate_threshold= 17000       #Higher Hashrate the better / more expensive
exclude_unbranded_CPUs=True     #unbranded_CPUs are unoffical CPUs that were never released
CPU_FILE = 'XMRig.json'

EXCLUSIVE_VENDORS= [
    'www.ebay.com',
    'www.newegg.com',
    'www.amazon.com']

APPROVED_VENDORS = [
    'www.ebay.com',
    'www.newegg.com',
    'www.amazon.com',
    'www.staples.com',
    "www.officedepot.com",
    'www.microcenter.com',
    'www.walmart.com',
    'www.wiredzone.com',
    'wiredzone.com',
    'www.aliexpress.com',
    's.click.aliexpress.com',
    'www.antonline.com',
    'www.gamepc.com',
    'www.avadirect.com',
    #VVV Does not sell to individual consumers VVV
    'www.cdw.com',
    'www.zones.com']

UNVERIFIED_VENDORS = [
    "www.itcreations.com",
    "www.harddiskdirect.com",
    "harddiskdirect.com",
    "www.allhdd.com",
    "www.networkhardwares.com",
    "bleepbox.com",
    "www.serversupply.com",
    "www.publicsector.shidirect.com",
    "www.shidirect.com",
    "www.shi.com",
    "www.cloudninjas.com",
    "cloudninjas.com",
    "www.sabrepc.com",
    "www.acmemicro.com",
    "www.ipcstore.com",
    "www.govets.com",
    "www.insight.com",
    "ips.insight.com",
    "www.onlogic.com"]

def get_processors_info(print_results=True):
    processors_info = []
    if os.path.exists(CPU_FILE):
        try:
            with open(CPU_FILE, 'r', encoding='utf-8') as file:
                cpu_list = json.load(file)
        except Exception as e:
            print(f"Failed to read JSON file: {e}") 
            exit()
    else:
        try:
            cpu_list = requests.get('https://api.xmrig.com/1/benchmarks', timeout=9)
            cpu_list.raise_for_status()
            with open(CPU_FILE, "w") as file:
                json.dump(cpu_list.json(), file)
        except Exception as e:
            print(f"Failed to fetch or save benchmarks from 'www.xmrig.com'.\nError info: {e}")
            exit()

    for index, row in enumerate(cpu_list):
        processor_info = {
            "rank": index,
            # "name": row['cpu'],
            "hashrate": int(row['hashrate']),
            # "hashrate_1t": int(row['hashrate_1t']),
            "samples": row['count'],
            "name": row['cpu']}
        processors_info.append(processor_info)

    filtered_processors = [processor for processor in processors_info if HASHRATE_MAX>=float(processor['hashrate'])>=hashrate_threshold]
    filtered_processors = [processor for processor in filtered_processors if int(processor['samples']) >= samples_threshold]
    if exclude_unbranded_CPUs: 
        filtered_processors = [processor for processor in filtered_processors if not 
            processor["name"].startswith('AMD Eng Sample') and not processor["name"].startswith('Genuine Intel')]

    if print_results:
        for processor in filtered_processors:
            print(processor)
        print(f"Number of Processors: {len(filtered_processors)}")
        print(f"hashrate range: {hashrate_threshold}-{HASHRATE_MAX}\tsamples_threshold: {samples_threshold}")
        input("\nPress Enter to continue to search") #remove maybe?
    return filtered_processors

def search_processor_price_duckduckgo(processor_name):
    url = "https://api.duckduckgo.com/"
    params = {
        'q': f'{processor_name} price',
        'format': 'json',
        'ia': 'web',
        'iax': 'search'}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        if 'Results' in results:
            # Extract the relevant information from the API response
            # You may need to customize this based on the actual structure of the API response
            price_info = results['Results'][0]['Text']  # Replace this with actual extraction logic
            return price_info
        else:
            print(f"No results found for {processor_name}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Failed to perform a web search: {e}")
        return None

def search_processor_price_google(processor_name):
    time.sleep(SLEEPTIME) # Introduce a delay to avoid rate limiting
    search_url = f"https://www.google.com/search?q={processor_name}"
    vendors = []

    try:
        # Send a GET request to Google Shopping
        response = requests.get(search_url, 
            # headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            timeout=5, 
            params={"num": SER_NUM}
            )  ##num is used for number of listings
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser') # Parse the HTML content
    except Exception as e:
        if response.status_code == 429:
            print(f'retry after: {response.headers["retry-after"]}\n')
        print(f"Failed to perform a Google Shopping search: {e}")
        return None

    #Extracts deals from online search then adds to 'vendors' list
    listings=soup.find_all('span', string=lambda string: string and '$' in string)
    for fingerprint in listings:
        parent_container = fingerprint.find_parent('div').find_parent('div').find_parent('div').find_parent('div').find_parent('div').find_parent('div').find_parent('div')
        main_container = parent_container.find('a') #Contains website link and listing title. source is also extracted from the link
        link = 'www.google.com' + main_container['href']    #Link Extraction
        price = fingerprint.get_text(strip=True)            #Price Extraction
        title_element = main_container.find('h3')           #Title Extraction
        title = title_element.get_text(strip=True) if title_element else 'Title N/A'         #Title Extraction
        source_start = link[29:]                            #Source Extraction
        source_end = source_start.find('.com')              #Source Extraction
        source = source_start[:source_end+4]                #Source Extraction

        vendors.append({'title': title, 'price': price, 'link': link, 'source': source})      

    #changes price from (str)$1,234.56 -> (int)1234 
    for vendor in vendors:
        try:
            vendor['price'] = int(vendor['price'].split('$')[1].replace(',', '').split(".")[0])
        except ValueError: 
            vendor['price'] = 999999 #Sets the price absurdly high if the algorithm cannot convert original price in to a integer

    vendors.sort(key=lambda x: x['price']) #orginizes list by price

    #Reorginizes vendors so approved ones appear first and unknown ones are filtered out.
    a_vendors = []
    b_vendors = []
    c_vendors = []
    for vendor in vendors:
        if vendor['source'] in APPROVED_VENDORS:
            a_vendors.append(vendor)
        elif vendor['source'] in UNVERIFIED_VENDORS:
            b_vendors.append(vendor)
        else:
            c_vendors.append(vendor)

    return a_vendors, b_vendors, c_vendors

def print_vendor_options(processor_list):
    print("Processor information with search results:")
    for i in processor_list:
        print(f"\n\n\n{i['processors_info']['rank']}. {i['processors_info']['name']}\tHR: {i['processors_info']['hashrate']}")
        if len(i['Avendors']) > 0:
            for listing in i['Avendors']:
                price = "${:<10}".format(listing['price'])
                source = "{:<25}".format(listing['source'])
                title = listing['title']
                print(f"{price}{source}{title}")
        if len(i['Bvendors']) > 0:
            print('   Unverified vendors:')
            for listing in i['Bvendors']:
                price = "${:<10}".format(listing['price'])
                source = "{:<25}".format(listing['source'])
                title = listing['title']
                print(f"{price}{source}{title}")
        if len(i['Cvendors']) > 0:
            print('   Unknown vendors:')
            for listing in i['Cvendors']:
                price = "${:<10}".format(listing['price'])
                source = "{:<25}".format(listing['source'])
                title = listing['title']
                print(f"{price}{source}{title}")
    print()

def idenitfy_optimal_cpu_by_price(processor_list):
    hr2price = []

    for processor in processor_list:
        vendors = processor['approved_vendors']
        vendors = [vendor for vendor in vendors if vendor['source'] in EXCLUSIVE_VENDORS] #Filters out non exclusive vendors

        ratio = int(processor['hashrate']) / vendors[0]['price']
        entry = {'name': processor['name'], 'rating': ratio, 'link': vendors[0]['link']}
        hr2price.append(entry) 
    hr2price.sort(key=lambda x: x['rating'], reverse=True)
    print("Higher Score is better!")
    for i, entry in enumerate(hr2price):
        print(f'{i}. {entry["name"]}\tScore:{round(entry["rating"], 3)}\t{entry["link"]}\n')

def main_search(processors_info):
    processor_list = []
    archive = []   
    for processor in tqdm(processors_info, desc=f"Searching for prices... ", unit="search"):
        # print(f"searching: {processor}") # not compatible with tqdm
        Avendors, Bvendors, Cvendors  = search_processor_price_google(processor["name"])
        
        #Could be used to compare results without preforming search again.
        with open('XCS_results.txt', 'w', encoding='utf-8') as file: 
            file.write(f"{processor['name']} ---\t{str(Avendors)}\n\n") 

        if len(Avendors) == 0 and len(Avendors) == 0:
            print(f'Error! No known vendors found. {len(Cvendors)} Unknown vendors found')
            archive_entry = {'processors_info': processor, 'Avendors': None, 'Bvendors': None, 'Cvendors': Cvendors}
            archive.append(archive_entry)
        elif len(Avendors) == 0:
            print(f'Warning! No approved vendors found! {len(Bvendors)}/{len(Cvendors)} known/unknown vendors found')
            print(f"Skipping {processor['name']} from comparison list.")
            archive_entry = {'processors_info': processor, 'Avendors': None, 'Bvendors': Bvendors, 'Cvendors': Cvendors}
            archive.append(archive_entry)
        else:
            archive_entry = {'processors_info': processor, 'Avendors': Avendors, 'Bvendors': Bvendors, 'Cvendors': Cvendors}
            entry = {'name': processor['name'], 'hashrate': processor['hashrate'], 'approved_vendors': Avendors}
            # input(archive_entry)
            # print('\n')
            # input(entry)
            # print('\n\n\n')
            processor_list.append(entry)
            archive.append(archive_entry)
    return archive, processor_list

if __name__ == "__main__":
    processors_info = get_processors_info()
    archive, processor_list = main_search(processors_info)
    print_vendor_options(archive)
    idenitfy_optimal_cpu_by_price(processor_list)

#EOF


