# step one
import argparse
import os
from tqdm.auto import tqdm
from pathlib import Path
from collections import Counter, defaultdict
from pprint import pprint
from time import sleep
from requests import get, head
# import json
import rapidjson as json

from lxml.etree import iterparse, tostring, XPath
# import slack
# client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])

from utils import (
    extract_full_domain,
    extract_registered_domain,
    extract_suffix,
    SetEncoder
)


def extract(file_path, is_test=False):
    dataset = defaultdict(defaultdict) 
    print("Start extracting.")

    counter = Counter()

    # get_tuv = XPath('child::tuv')
    get_url = XPath('prop[@type="source-document"][1]/text()')
    
    i = 0
    with tqdm(total=36936714) as pbar_items:
        with tqdm(total=67977) as pbar_domains:

            for _, d in iterparse(file_path, tag='tu'):
                if is_test and i == 1000000: # 1 M rows
                    return dataset
                i += 1
                en, de  = d.findall('tuv')


                counter['row_counter'] += 1

                en_url = en.findtext('prop[@type="source-document"]')
                en_segment = en.findtext('seg')

                de_url = de.findtext('prop[@type="source-document"]')
                de_segment = de.findtext('seg')

                if en_url == "unknown" or de_url == "unknown":
                    counter['unkown_url_counter'] += 1
                    continue

                en_domain = extract_full_domain(en_url)
                de_domain = extract_full_domain(de_url)
    
                dataset[de_domain]['en_domain'] = en_domain
                dataset[de_domain]['de_domain'] = de_domain

                if dataset[de_domain].get('items') == None:
                    # print('create - dataset[de_domain][\'items\'] = defaultdict()')
                    dataset[de_domain]['items'] = defaultdict()
                

                dataset[de_domain]['items'][de_url] = { 'corresponding_en_url': en_url }
                
                if dataset[de_domain]['items'][de_url].get('number_of_segment') == None:
                    dataset[de_domain]['items'][de_url]['number_of_segment'] = 0

                dataset[de_domain]['items'][de_url]['number_of_segment'] += 1

                if len(dataset) > counter['domain_counter']:
                    counter['domain_counter'] += 1           
                    pbar_domains.update(1)

                pbar_items.update(1)

                d.clear()
                # break
    return dataset


def save(output_path, dataset):
    print("Save result to:", output_path)
    with open(output_path, 'w', encoding="utf-8") as f:    
        json.dump(dataset, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path', type=str)
    parser.add_argument('output_dir', type=str)
    parser.add_argument('-test', action='store_true')

    
    args = parser.parse_args()

    is_test = args.test
    input_file_path = args.input_path
    input_file_name = Path(input_file_path).stem
    
    dataset = extract(input_file_path, is_test=is_test)

    print('Save file')
    if is_test:
        save(os.path.join(args.output_dir, '{}.v2.test.json'.format(input_file_name)),
             dataset)
    else:
        save(os.path.join(args.output_dir, '{}.v2.json'.format(input_file_name)),
             dataset)
    print('Done.')