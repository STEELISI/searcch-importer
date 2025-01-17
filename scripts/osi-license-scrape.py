#!/usr/bin/python3

import bs4
import requests
import sys
import logging
import re

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

license_re = re.compile("^([^\(]+) +\(([^\(]+)\)$")
href_short_name_re = re.compile("^.*/licenses/(.+)$")

def scrape_and_dump():
    r = requests.get("https://opensource.org/licenses/alphabetical")
    soup = bs4.BeautifulSoup(r.content, 'html.parser')
    content = soup.find('div',class_='field-items')
    ul = content.find('ul')
    #print("%r %r" % (ul,ul.text))
    for li in ul.findAll('li'):
        #print("license: %r %r" % (li,li.text))
        a = li.find('a')
        if not a:
            continue
        match = license_re.match(a.text)
        match2 = href_short_name_re.match(a.get("href"))
        if match:
            long_name = match.group(1)
            short_name = match.group(2)
            ld = dict(
                short_name=short_name,
                long_name=long_name,
                url="https://opensource.org/licenses/%s" % (short_name,),
                verified=True)
            print("%r" % (ld,))
        elif match2:
            long_name = a.text
            short_name = match2.group(1)
            ld = dict(
                short_name=short_name,
                long_name=long_name,
                url="https://opensource.org/licenses/%s" % (short_name,),
                verified=True)
            print("%r" % (ld,))
        else:
            LOG.warning("skipping license: %r" % (a.text,))

if __name__ == "__main__":
    scrape_and_dump()
