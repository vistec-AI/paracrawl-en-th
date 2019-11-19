# step one
import argparse
import os
from pathlib import Path
from collections import Counter, defaultdict
from pprint import pprint
from time import sleep
from requests import get, head
from xmlr import xmlparse, xmliter, XMLParsingMethods


from utils import extract_domain, extract_suffix



def extract(filename):
    dataset = {
        "en": defaultdict(lambda: []),
        "de": defaultdict(lambda: [])
    }
    print("Start extracting.")

    counter = Counter()
    with tqdm(total=204522994) as pbar_items:
        with tqdm(total=67977) as pbar_domains:
            for d in xmliter(filename, 'tu'):
    #             print(d)

                counter['row_counter'] += 1
                en_url = d['tuv'][0]['prop']
                de_url = d['tuv'][1]['prop']

                # print("en_urls", en_url)
                # print("de_urls", de_url)

                if en_url == "unknown" or de_url == "unknown":
                    counter['unkown_url_counter'] += 1
                    continue

                if type(en_url) == list:
                    en_url = en_url[0]
                if type(de_url) == list:
                    de_url = de_url[0]

                if type(en_url) == str:
                    en_domain = extract_domain(en_url)
                    # if not en_domain in dataset['en'].keys():
                        # dataset['en'][en_domain] = []
                    # dataset['en'][en_domain].append(en_url)
                    # else:
                    # if len(dataset['en'][en_domain] ) == 10:
                        # continue
                    dataset['en'][en_domain].append(en_url)

                if type(de_url) == str:
                    de_domain = extract_domain(de_url)

                    # if not de_domain in dataset['de'].keys():
                    #     dataset['de'][de_domain] = []
                    # dataset['de'][de_domain].append(de_url)
                    # else:
                    # if len(dataset['de'][de_domain]) == 10:
                        # continue
                    dataset['de'][de_domain].append(de_url)


                if len(dataset['de'].keys()) > counter['domain_counter']:
                    counter['domain_counter'] += 1           
                    pbar_domains.update(1)
                    
                pbar_items.update(1)

    print("Done.")
    return dataset


def save(output_path, dataset):
    print("Save result to:", output_path)
    with open(output_path, 'w', encoding="utf-8") as f:    
        json.dump(dataset, f, ensure_ascii=False)


if name == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path', type=str)
    parser.add_argument('output_dir', type=str)

    
    args = parser.parse_args()

    input_file_path = args.input
    input_file_name = Path(input_file_path).stem
    
    dataset = extract(filename)
    
    save(os.path.join(output_dir, '{}.json'.format(input_file_name)))
