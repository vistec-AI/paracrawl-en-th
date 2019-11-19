# step one
import argparse
import os
from tqdm.auto import tqdm
from pathlib import Path
from collections import Counter, defaultdict
from pprint import pprint
from time import sleep
from requests import get, head
from xmlr import xmlparse, xmliter, XMLParsingMethods
import json

from lxml.etree import iterparse, tostring, XPath
# import slack
# client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])

from utils import (
    extract_full_domain,
    extract_registered_domain,
    extract_suffix,
    SetEncoder
)


def extract(file_path):
    dataset = {
        "en": defaultdict(set),
        "de": defaultdict(set)
    }
    print("Start extracting.")

    counter = Counter()

    # get_tuv = XPath('child::tuv')
    get_url = XPath('prop[@type="source-document"][1]/text()')

    with tqdm(total=36936714) as pbar_items:
        with tqdm(total=67977) as pbar_domains:

            for _, d in iterparse(file_path, tag='tu'):
                en, de  = d.findall('tuv')


                counter['row_counter'] += 1

                en_url = en.findtext('prop[@type="source-document"]')
                de_url = de.findtext('prop[@type="source-document"]')

                if en_url == "unknown" or de_url == "unknown":
                    counter['unkown_url_counter'] += 1
                    continue

                en_domain = extract_full_domain(en_url)
                dataset['en'][en_domain].add(en_url)

                de_domain = extract_full_domain(de_url)
                dataset['de'][de_domain].add(de_url)

                if len(dataset['de']) > counter['domain_counter']:
                    counter['domain_counter'] += 1           
                    pbar_domains.update(1)

                pbar_items.update(1)

                d.clear()
    return dataset


def save(output_path, dataset):
    print("Save result to:", output_path)
    with open(output_path, 'w', encoding="utf-8") as f:    
        json.dump(dataset, f, ensure_ascii=False, cls=SetEncoder)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path', type=str)
    parser.add_argument('output_dir', type=str)

    
    args = parser.parse_args()

    input_file_path = args.input_path
    input_file_name = Path(input_file_path).stem
    
    dataset = extract(input_file_path)

    print('Save file')
    save(os.path.join(args.output_dir, '{}.json'.format(input_file_name)),
         dataset)
    print('Done.')