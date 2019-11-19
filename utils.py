import re, os
import tldextract
import json

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
           return list(obj)
        return json.JSONEncoder.default(self, obj)

def extract_suffix(url):
    obj = tldextract.extract(url)
    return obj.suffix

def extract_full_domain(url):
    # t = urlparse(url)
    ext = tldextract.extract(url)
    return '.'.join(part for part in ext[:3] if part)

def extract_registered_domain(url):
    # t = urlparse(url)
    ext = tldextract.extract(url)
    return ext.registered_domain
