import re, os
import tldextract


def extract_suffix(url):
    obj = tldextract.extract(url)
    return obj.suffix

def extract_domain(url):
    # t = urlparse(url)
    ext = tldextract.extract(url)
    return '.'.join(part for part in ext[:3] if part)
