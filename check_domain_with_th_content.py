
import argparse
import json
import re, os
import threading
from time import sleep
from collections import Counter, defaultdict
from datetime import datetime
import concurrent
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from random import sample, choice, seed
from functools import partial, reduce

import pandas as pd
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from fake_useragent import UserAgent

import utils


# 1. Load dataset
def load_dataset():
    with open('./data/en-de.bicleaner07.json', 'r', encoding="utf-8") as f:
        dataset = json.load(f)
        return dataset

SUB_LANG_PATTERNS = [
    (r'(lang=)(de)', r'\1th'),
    (r'(/)(de)(/)', r'\1th\3'),
    (r'(/)(de)$', r'\1th'),
    (r'^(de)(\.)', r'th\2'), ## lang id as the sub domain
    (r'^(german|ger|ge)(\.)', r'th\2'), ## lang id as the sub domain
    (r'(/)(german|ger|ge)(/)', r'\1th\3'),
    (r'(lang=)((german|ger|ge))', r'\1th'),
]

CHROMEDRIVER_PATH = 'chromedriver'

# 2. get URLs
def get_sample_urls_match_with_patterns(dataset, patterns):
    counter = Counter()
    examples_urls_in_pattern = defaultdict(list)
    for domain, urls in tqdm(dataset['de'].items()):
        
        for pattern in patterns:
            for url in urls[:1]:
                if re.search(pattern[0], url):
                    counter[pattern[0]] += 1

                    examples_urls_in_pattern[pattern[0]].append(url)

    return examples_urls_in_pattern, counter
    
# 3. call and check

def requests_retry_session(
    retries=0,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


threadLocal = threading.local()
def get_driver(executable_path=CHROMEDRIVER_PATH):
    driver = getattr(threadLocal, 'driver', None)
    if driver is None:
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--no-sandbox")
        chromeOptions.add_argument('--ignore-certificate-errors')
        chromeOptions.add_argument("disable-gpu")

        driver = webdriver.Chrome(executable_path, options=chromeOptions)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": UserAgent().random, "platform":"Linux"})
        setattr(threadLocal, 'driver', driver)
        
    # driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": UserAgent().random, "platform":"Linux"})
    return driver


def get_status(url):
    r = None
    url_correct = url
    
    ua = UserAgent()
    try:
        if 'http://' not in url:
            url_http = 'http://'  + url
                
            r = requests_retry_session().head(url_http)
            url_correct = url_http

            if r == None:
                url_https = 'https://'  + url
                r = requests_retry_session().head(url_https)
                url_correct = url_https
        else:
            r = requests_retry_session().head(url)


        if r == None:
            code= 0
        else:
            code = r.status_code

            # code = 0  # probably bad domain name
    except Exception as e:
        code = 0
    return code, url_correct


def detect_thai_language(text):
    
    pattern = r'[ก-ฮ]'

    if re.search(re.compile(pattern), text):
        return True
    return False

def get_content(url):
    # driver = get_driver()
    # try:
    #     driver.get(url)
    #     text = driver.page_source
    # except Exception as e:
        
    #     print('exception: get_content()')
    #     print('url:', url)
    #     print(e)
    #     return ''
    # finally:
    #     driver.close()
    ua = UserAgent()
    try:
        r = requests.get(url, headers={'User-Agent': ua.random} )
        r.encoding = r.apparent_encoding
        return r.text # return string
    except Exception as e:
        print('e', e)
        return ''
    return ''
    # return r.content

urls_with_status = defaultdict(defaultdict)
pattern_counter = defaultdict(Counter)

def substitue_lang_worker(match, replace, url):
    
    
    modified_url = re.sub(match, replace, url)
    status, url_modified_correct = get_status(modified_url)

    is_thai = None
    if int(status) == 200:
      
        is_thai = detect_thai_language(get_content(url_modified_correct))
        if is_thai:
            print('{}, modifield_url: {} , is_thai: {}'.format(status, url_modified_correct, is_thai))

            
    result = (is_thai, status, match, url_modified_correct)
    return result

# def substitute_lang_worker_callback(results):
#     print('type(results):', type(results))
#     assert type(results) == list
#     for result in results:
#         is_thai, status, match, modified_url = result
#         print('callback result', result)

#         pattern_counter[match][status] += 1
# #         print(pattern_counter)
#         full_domain = utils.extract_full_domain(modified_url)

#         urls_with_status[status][full_domain] = {
#             "is_thai": is_thai,
#             "example_modified_url": [modified_url],
#             "pattern": match,
#         }

def run(examples_urls_in_pattern, is_test=False, n_workers=8):
    for pattern, urls in examples_urls_in_pattern.items():
      
        for sub_pattern in SUB_LANG_PATTERNS:
            if pattern == sub_pattern[0]:
                match, replace = sub_pattern[0], sub_pattern[1]
                break

        print('')
        print('Pattern:', pattern, 'replace with:', replace)
        print('Number of urls for this pattern:', len(urls))
        print('')

        _substitue_lang_worker = partial(substitue_lang_worker, match, replace)
 
        if is_test:
            print('testing: fetch only 10 urls')
            urls = urls[:10]
        
        counter = 0
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            future_to_url = { executor.submit(_substitue_lang_worker, url): url  for url in urls }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_url)):
                url = future_to_url[future]
                
                counter+=1
                if counter % 500 == 0:
                    print('counter: {}'.format(counter))
                if counter == len(urls):
                    print('[ Completed counter: {} ]'.format(counter))
                try:
                    result = future.result()
                    if is_test:
                        print('result:', result)
                    is_thai, status, match, modified_url = result
            
                    pattern_counter[match][status] += 1
                    full_domain = utils.extract_full_domain(modified_url)

                    urls_with_status[status][full_domain] = {
                        "is_thai": is_thai,
                        "example_modified_url": [modified_url],
                        "pattern": match,
                    }
                except Exception as exc:
                    print('e', exc)
                    # print('%r generated an exception: %s' % (url, exc))
                    continue
                    
     

        print('Done.')

def write_to_jspn(urls_with_status):
    
    current = datetime.now().strftime("%d.%m.%Y_%H.%M")

    path = "./data/urls_with_status.{}.json".format(current)
    print(path)
    with open(path, 'w', encoding="utf-8") as f:
    
        json.dump(urls_with_status, f, ensure_ascii=False, indent=4)
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-test', action="store_true")
    parser.add_argument('--n_workers', type=int, default=8)
    parser.add_argument('--chromedriver_path', type=str, default='chromedriver')

    args = parser.parse_args()

    CHROMEDRIVER_PATH = args.chromedriver_path

    print('1. load dataset')
    dataset = load_dataset()

    print('2. get url match pattern dataset')
    examples_urls_in_pattern, counter = get_sample_urls_match_with_patterns(dataset, SUB_LANG_PATTERNS)

    print(counter)

    print('\n\n\n')
    print('3. run the http, lang detect')
    run(examples_urls_in_pattern, is_test=args.test, n_workers=args.n_workers)

    print('\n\n4.writing result to file')
    write_to_jspn(urls_with_status)