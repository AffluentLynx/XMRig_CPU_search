#!/usr/bin/env python3

# Standard Python libraries.
import sys
import time

# Third party Python libraries.
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

# Custom Python libraries.


__version__ = "1.0.0"


sleeptime = 5                   #In seconds, provides a pause to avoid rate limiting by search engine
samples_threshold = 3           #samples is the amount of times a benchmark test was submitted
hashrate_threshold= 12000       #Higher Hashrate the better / more expensive
exclude_unbranded_CPUs=True     #unbranded_CPUs are unoffical CPUs that were never released

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


def get_processors_info(from_file=False, file_path=None, print_results=True):
    processors_info = []
    if from_file and file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
        except Exception as e:
            print(f"Failed to read HTML file: {e}") 
            return None

    elif from_file and not file_path:
        print('Error!')
        return None

    else: #from_file == False
        try:
            # Send a GET request to XMRig.com/benchmark
            html_content = requests.get('www.xmrig.com/benchmark', timeout=9)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch benchmarks from 'www.xmrig.com'. Please try saving the page as an HTML, named 'XMRig.html', in the same directory as this script.\nError info: {e}")
            return None

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        print(f"Failed to parse processors info: {e}")
        return None

    table = soup.find('table', class_='table')

        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                columns = row.find_all(['td', 'th'])
                processor_info = {
                    "rank": columns[0].get_text(strip=True),
                    "name": columns[1].find('span').get_text(strip=True),
                    "hashrate": columns[2].find('span').get_text(strip=True),
                    "samples": columns[4].find('span').get_text(strip=True)}
                processors_info.append(processor_info)

            #Filter out enrties that do not meet the search thresholds
            filtered_processors = [processor for processor in processors_info if float(processor['hashrate']) >= hashrate_threshold]
            filtered_processors = [processor for processor in filtered_processors if int(processor['samples']) >= samples_threshold]
            if exclude_unbranded_CPUs: 
                filtered_processors = [processor for processor in filtered_processors if not 
                    processor["name"].startswith('AMD Eng Sample') and not processor["name"].startswith('Genuine Intel')]

        if print_results:
            for processor in filtered_processors:
                print(processor)
            print(f"Number of Processors: {len(filtered_processors)}")
            print(f"hashrate_threshold: {hashrate_threshold}\tsamples_threshold: {samples_threshold}")
            input("\nPress Enter to continue to search") #remove maybe?

    except Exception as e:
        print(f"Failed to parse processors info: {e}")

    return filtered_processors

def print_vendor_options(processor_list):
    print("Processor information with search results:")
    for i in processor_list:
        print(f"\n\n\n{processor['rank']}. {processor['name']}\tHR: {processor['hashrate']}")
        if len(i['Avendors']) > 0:
            for listing in i['Avendors']:
                print(f"{listing['source']} \t\t\t ${listing['price']} \t {listing['title']}")
        if len(i['Bvendors']) > 0:
            print('\n Unverified vendors:')
            for listing in i['Bvendors']:
                print(f"{listing['source']} \t\t\t ${listing['price']} \t {listing['title']}")
        if len(i['Cvendors']) > 0:
            print('\n Unknown vendors:')
            for listing in i['Cvendors']:
                print(f"{listing['source']} \t\t\t ${listing['price']} \t {listing['title']}")

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
    time.sleep(sleeptime) # Introduce a delay to avoid rate limiting
    search_url = f"https://www.google.com/search?q={processor_name}"
    vendors = []

    try:
        # Send a GET request to Google Shopping
        response = requests.get(search_url, timeout=5, params={"num": 50})  ##num is used for number of listings
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser') # Parse the HTML content
    
    except Exception as e:
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

def idenitfy_optimal_cpu_by_price(processor_list):
    hr2price = []

    for processor in processor_list:
        vendors = processor['approved_vendors']
        vendors = [vendor for vendor in vendors if vendor['source'] in EXCLUSIVE_VENDORS] #Filters out non exclusive vendors

        ratio = int(processor['hashrate'].split('.')[0]) / vendors[0]['price']
        entry = {'name': processor['name'], 'rating': ratio, 'link': vendors[0]['link']}
        hr2price.append(entry) 
    hr2price.sort(key=lambda x: x['rating'], reverse=True)
    print("Higher Score is better!")
    for i, entry in enumerate(hr2price):
        print(f'{i}. Processor: {entry["name"]}\tScore: {entry["rating"]}\tLink: {entry["link"]}')

if __name__ == "__main__":
    if os.path.exists('XMRig.html'): 
        processors_info = get_processors_info_from_file(True, 'XMRig.html')
    else:
        processors_info = get_processors_info_from_file(False)

    if not processors_info:
        print('get_processors_info_from_file() Failed. Terminating script.')
        exit()

    # processors_info = processors_info[0:26] #Limits the search to savetime/avoid request caps
     
    processor_list = []
    achive = []   
    i = -1
    for processor in tqdm(processors_info, desc=f"Searching for prices... ", unit="lookup"):
        # print(f"searching: {processor}") # not compatible with tqdm
        i += 1
        Avendors, Bvendors, Cvendors  = search_processor_price_google_shopping(processor["name"])
        
        # with open('XCS_results.txt', 'w', encoding='utf-8') as file: file.write(f"{processor['name']} ---\t{str(Avendors)}\n\n") #Could be used to compare results without preforming search again.

        if len(Avendors) == 0 and len(Avendors) == 0:
            print(f'Error! No known vendors found. {len(Cvendors)} Unknown vendors found')
            archive_entry = {'processors_info': processors_info, 'Avendors': None, 'Bvendors': None, 'Cvendors': Cvendors}
            achive.append(archive_entry)
            exit()
        elif len(Avendors) == 0:
            print(f'Warning! No approved vendors found! {len(Bvendors)}/{len(Cvendors)} known/unknown vendors found')
            print(f"Skipping {processor['name']} from comparison list.")
            archive_entry = {'processors_info': processors_info, 'Avendors': None, 'Bvendors': Bvendors, 'Cvendors': Cvendors}
            achive.append(archive_entry)
            continue
        else:
            archive_entry = {'processors_info': processors_info, 'Avendors': Avendors, 'Bvendors': Bvendors, 'Cvendors': Cvendors}
            entry = {'name': processor['name'], 'hashrate': processor['hashrate'], 'approved_vendors': Avendors}
            processor_list.append(entry)
            achive.append(archive_entry)

    print_vendor_options(achive)
    idenitfy_optimal_cpu_by_price(processor_list)

#EOF


