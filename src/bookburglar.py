#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Downloads and saves to disk an online book from O'Reilly OFPS.

All chapters are concatenated into a single HTML file. The file isn't guaranteed to be
valid HTML.

For book example see http://ofps.oreilly.com/titles/9780596155957 .

@author: eis
Created on 09/12/11
"""
import os
import urllib2
import re
from lxml import etree
import urlparse

RE_REMOVE_ENCODING = re.compile(r'<\?xml(.+?)encoding=(.+?)\?>')

XPATH_CHAPTER_HTML = r"//div[@id='main_content']//div[@class='chapter']"
XPATH_FIRST_PAGE_HTML = r"//div[@id='main_content']//div[@class='book']"
XPATH_TOC = r"//div[@id='main_content']//div[@class='toc']/dl/dt/span/a"
XPATH_BOOK_TITLE = r"//div[@id='main_content']//div[@class='book']//h1[@class='title']"

def fetch_html(url):
    """Downloads HTML at `url` and removes the <?xml ... ?> tag.
    lxml can't parse HTMLs with <?xml encoding=... ?>, so we have to remove it.
    """
    print('...%s' % url)

    connection = urllib2.urlopen(url)
    encoding = connection.headers.getparam('charset')

    return RE_REMOVE_ENCODING.sub('', connection.read().decode(encoding), count=1)

def elements_at_xpath(html, xpath):
    """Parses `html` and returns elements that match `xpath`.
    """
    parser = etree.HTMLParser(recover=True)
    doc = etree.fromstring(html, parser)

    return doc.xpath(xpath)

def html_at_xpath(html, xpath):
    """Parses `html` and returns HTML representation of elements that match `xpath`.
    """
    return ''.join([etree.tostring(e) for e in elements_at_xpath(html, xpath)])

def get_chapter_html(html):
    """Extracts effective chapter content from `html`.
    """
    return html_at_xpath(html, XPATH_CHAPTER_HTML)

def get_toc_urls(html):
    """Parses title page in `html` and returns list of URLs from table of contents
    on that page.
    """
    return [a.attrib['href'] for a in elements_at_xpath(html, XPATH_TOC)]

def steal_a_chapter(chapter_url):
    """Downloads chapter at `chapter_url` and returns effective content.
    """
    return get_chapter_html(fetch_html(chapter_url))

def steal_a_book(root_url, index_page='index.html', save_path=None, save_to='.'):
    """Downloads an online book and saves it to HTML file.

    Saves the resulting HTML at `save_path` if defined; otherwise saves the result to
    <book title>.html in `save_to` folder (current folder is default).
    """
    if not root_url.endswith('/'): root_url += '/'

    print("Downloading a book at %s" % root_url)

    index_html = fetch_html(urlparse.urljoin(root_url, index_page))
    book_title = elements_at_xpath(index_html, XPATH_BOOK_TITLE)[0].text
    first_page = html_at_xpath(index_html, XPATH_FIRST_PAGE_HTML)

    print('Title: "%s"' % book_title)
    print('Extracting chapters...')

    chapters = [
        steal_a_chapter(urlparse.urljoin(root_url, chapter_url))
            for chapter_url in get_toc_urls(index_html)
    ]

    book = ''.join([first_page] + chapters)

    print('Saving...')
    save_path = save_path or os.path.join(save_to, re.sub(r'[^a-zA-Z0-9_\-.() ]+', '', book_title) + '.html')
    with open(save_path, 'w') as outfile:
        outfile.write(book)

    print('All done!')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])

    parser.add_argument('book_url', type=str, default=None,
        help='''Target book URL. Has to be one of those O'Reilly OFPS books. See http://ofps.oreilly.com/titles/9780596155957 for an example.''')
    parser.add_argument('output_file', nargs='?', type=str, default=None,
        help='''Output path. If not specified the book is saved to <book_title>.html in current directory.''')

    args = parser.parse_args()

    steal_a_book(args.book_url, save_path=args.output_file)
