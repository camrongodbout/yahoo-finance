#!/usr/bin/env python

"""
Borrowed code from Brad Luicas
Python3 compatible
Multi-attempt cookie getter
"""

__author__ = "Brad Luicas & George Paw"
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "George Paw"
__email__ = "paw.george@gmail.com"
__status__ = "Production"


import re
import sys
import time
import datetime
import requests


def split_crumb_store(v):
    return v.split(':')[2].strip('"')


def find_crumb_store(lines):
    # Looking for
    # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
    for l in lines:
        if re.findall(r'CrumbStore', l):
            return l
    print ("Did not find CrumbStore")


def get_cookie_value(r):
    return {'B': r.cookies['B']}


def get_page_data(symbol):
    url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
    r = requests.get(url)
    cookie = get_cookie_value(r)
    #lines = r.text.encode('utf-8').strip().replace('}', '\n')
    lines = str(r.content).strip().replace('}', '\n')
    return cookie, lines.split('\n')


def get_cookie_crumb(symbol):
    cookie, lines = get_page_data(symbol)
    crumb = split_crumb_store(find_crumb_store(lines))
    # Note: possible \u002F value
    # ,"CrumbStore":{"crumb":"FWP\u002F5EFll3U"
    # FWP\u002F5EFll3U
    #crumb2 = crumb.decode('unicode-escape')
    crumb2 = crumb
    return cookie, crumb2


def get_data(symbol, start_date, end_date, cookie, crumb):
    print (cookie)
    print (crumb)

    filename = '%s.csv' % (symbol)
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, start_date, end_date, crumb)
    response = requests.get(url, cookies=cookie)
    with open (filename, 'w') as handle:
        for block in response.iter_content(1024):
            handle.write(str(block))

def get_data2(symbol, start_date, end_date, cookie, crumb):

    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, start_date, end_date, crumb)
    response = requests.get(url, cookies=cookie)
    data_string = response.text
    return data_string


def get_now_epoch():
    # @see https://www.linuxquestions.org/questions/programming-9/python-datetime-to-epoch-4175520007/#post5244109
    return int(time.mktime(datetime.datetime.now().timetuple()))


def download_quotes(symbol):
    start_date = 0
    end_date = get_now_epoch()
    cookie, crumb = get_cookie_crumb(symbol)
    get_data(symbol, start_date, end_date, cookie, crumb)


def get_hist(symbol, start_date, end_date):
    #sometimes it couldn't get cookie on the first try, try again
    hist = []; retry = 2
    start_date = int(time.mktime(datetime.datetime.strptime(start_date, '%Y-%m-%d').date().timetuple()))
    end_date_real = datetime.datetime.strptime(end_date, '%Y-%m-%d').date() + datetime.timedelta(days=1)    #for some reason the yahoo api is exlcuding the end date, need to pad it with one more day
    end_date = int(time.mktime(end_date_real.timetuple()))
    cookie, crumb = get_cookie_crumb(symbol)
    data_string = get_data2(symbol, start_date, end_date, cookie, crumb)
    while ("cookie" in data_string) and retry > 0:     #run it one more time
        print ("Retrying to get cookie.... {} retries left".format(retry))
        retry = retry - 1
        cookie, crumb = get_cookie_crumb(symbol)
        data_string = get_data2(symbol, start_date, end_date, cookie, crumb)
    data_list = data_string.split('\n')
    keys_string = data_list.pop(0); keys_string = keys_string.replace("Adj Close", "Adj_Close", 1);keys = keys_string.split(',')
    for element in data_list:
        if element is not '':
            zipped = dict(zip(keys,element.split(',')))
            zipped['Symbol'] = symbol       #make it more like yahoo-finance output
            hist.append(zipped)
    return hist


if __name__ == '__main__':
    # If we have at least one parameter go ahead and loop overa all the parameters assuming they are symbols
    if len(sys.argv) == 1:
        print ("\nUsage: get-yahoo-quotes.py SYMBOL\n\n")
    else:
        for i in range(1, len(sys.argv)):
            symbol = sys.argv[i]
            print ("--------------------------------------------------")
            print ("Downloading %s to %s.csv" % (symbol, symbol))
            download_quotes(symbol)
            print ("--------------------------------------------------")

