"""
CAPP 30122: Course Search Engine Part 1

EGEMEN PAMUKCU
"""
# DO NOT REMOVE THESE LINES OF CODE
# pylint: disable-msg=invalid-name, redefined-outer-name, unused-argument, unused-variable

import queue
import json
import sys
import csv
import re
import bs4
import util
import copy

INDEX_IGNORE = set(['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be',
                    'but', 'by', 'course', 'for', 'from', 'how', 'i',
                    'ii', 'iii', 'in', 'include', 'is', 'not', 'of',
                    'on', 'or', 's', 'sequence', 'so', 'social', 'students',
                    'such', 'that', 'the', 'their', 'this', 'through', 'to',
                    'topics', 'units', 'we', 'were', 'which', 'will', 'with',
                    'yet'])


def get_links_from(source, follow_links):
    '''
    Crawls the urls starting from a source url.

    Inputs:
        sourec: string showing the source url to be started with.
        follow_links: cumulative list of links to be appended.

    Outputs:
        list of strings containing urls.
    '''
    limiting_domain = "classes.cs.uchicago.edu"
    resp = util.get_request(source)
    html = util.read_request(resp)
    soup = bs4.BeautifulSoup(html, "html5lib")
    links = []
    for a in soup.find_all('a'):
        if a.has_attr('href'):
            links.append(a['href'])
    for link in links:
        fin_url = util.remove_fragment(util.convert_if_relative_url(source, link))
        if util.is_url_ok_to_follow(fin_url, limiting_domain) and fin_url not in follow_links:
            follow_links.append(fin_url)
    return follow_links

def json_to_dict(path):
    '''
    Creates a dictionary from a json file.

    Inputs:
        path: a string indicating the path of the json file

    Outputs:
        a dictionary converted from a json file.
    '''
    with open(path) as f:
        data = json.load(f)
    return data

def get_codes_words(urls, code_to_id):
    '''
    Creates a list of tuples containing unique course IDs and a word used in the
    course description or title.

    Inputs:
        urls: list of strings containing urls to be looked at.
        code_to_id: dictionary that contains the mapping course codes to course
            identifiers

    Outputs:
        List of length 2 tuples with unique course IDs and a corresponding word.
    '''
    id_word = []
    for url in urls:
        s = bs4.BeautifulSoup(util.read_request(util.get_request(url)), 'html5lib')
        divs = s.find_all('div', class_='courseblock main')
        divs += s.find_all('div', class_='courseblock subsequence')
        for div in divs:
            words = []
            p_title = div.find_all('p', class_='courseblocktitle')
            for p in p_title:
                splits = p.text.strip('. ').split('.')
                code = splits[0]
                title = splits[0] + splits[1]
                words += re.findall(r"\b[a-zA-Z]+\w*", title.lower())
                split_title = re.findall(r'\w+', code)
                codes = []
                for number in split_title[1:]:
                    codes.append(split_title[0] + ' ' + number)
            p_desc = div.find_all('p', class_='courseblockdesc')
            for p in p_desc:
                words += re.findall(r"\b[a-zA-Z]+\w*", p.text.lower())
            for code in codes:
                for word in words:
                    if word not in INDEX_IGNORE:
                        id_word.append((code_to_id[code], word))
    return list(set(id_word))


def go(num_pages_to_crawl, course_map_filename, index_filename):
    '''
    Crawl the college catalog and generates a CSV file with an index.

    Inputs:
        num_pages_to_crawl: the number of pages to process during the crawl
        course_map_filename: the name of a JSON file that contains the mapping
          course codes to course identifiers
        index_filename: the name for the CSV of the index.

    Outputs:
        CSV file of the index index.
    '''

    code_to_id = json_to_dict(course_map_filename)
    starting_url = ("http://www.classes.cs.uchicago.edu/archive/2015/winter"
                    "/12200-1/new.collegecatalog.uchicago.edu/index.html")
    limiting_domain = "classes.cs.uchicago.edu"
    initial_set = get_links_from(starting_url, [])
    final_set = copy.deepcopy(initial_set)
    for url in initial_set:
        final_set = get_links_from(url, final_set)

    ids_words = get_codes_words(final_set[:num_pages_to_crawl], code_to_id)
    with open(index_filename, mode='w') as index:
        index_writer = csv.writer(index, delimiter='|')
        for pair in ids_words:
            index_writer.writerow(pair)




if __name__ == "__main__":
    usage = "python3 crawl.py <number of pages to crawl>"
    args_len = len(sys.argv)
    course_map_filename = "course_map.json"
    index_filename = "catalog_index.csv"
    if args_len == 1:
        num_pages_to_crawl = 1000
    elif args_len == 2:
        try:
            num_pages_to_crawl = int(sys.argv[1])
        except ValueError:
            print(usage)
            sys.exit(0)
    else:
        print(usage)
        sys.exit(0)

    go(num_pages_to_crawl, course_map_filename, index_filename)
