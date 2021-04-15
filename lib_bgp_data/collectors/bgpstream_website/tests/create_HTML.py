#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module pulls HTML from bgpstream.com, randomly generates new
info, and changes it in the HTML. The modified HTML is saved in the
test_HTML directory.

The events class attribute is a list of dictionaries that contains
many pieces of event information necessary for parsing/testing each event.

url_to_files helps with mapping for open_custom_HTML which is used for
patching over utils.get_tags

Usage of this module is in conftest.py
"""

import os
from bs4 import BeautifulSoup as Soup, NavigableString
import requests
from ..event_types import BGPStream_Website_Event_Types
from ....utils import utils
import re
from random import getrandbits, choices, randrange
from ipaddress import IPv4Address, IPv6Address
from string import ascii_uppercase
from time import strftime, gmtime, time
from itertools import product


########################
### Helper functions ###
########################

def random_IP(v: int):
    if v == 4:
        return str(IPv4Address(getrandbits(32))) + '/32'
    elif v == 6:
        return str(IPv6Address(getrandbits(128))) + '/128'

def random_string(n: int):
    """Returns a n-length random string of letters"""
    return ''.join(choices(ascii_uppercase, k=n))

def random_name():
    """Return a randomly generated origin name in the format
       ******* - *******, **
    """
    return random_string(7) +' - '+ random_string(7) +', '+ random_string(2)

def random_number():
    return str(randrange(100, 1000000))

def colon_split_replace(original, new_text):
    """Replaces text after a colon in original bs4 tag with new_text
       E.g. original.string = AS Number: 123
            new_text = 456
            
            original.string will be changed to AS Number: 456"""
    original.string = original.string.split(':')[0] + ': ' + new_text

def square_to_curly(l):
    """Convenience function that converts a list to a string,
       then replaces the square brackets with curly braces."""
    return str(l).replace('[', '{').replace(']', '}')

def remove_list_format(l):
    """Removes brackets, and quotes"""
    return str(l).replace("'", '')[1:-1]


class HTML_Creator:

    def __init__(self, path):
        """arg path -- a pytest temporary directory, passed from conftest.py"""
        self.bgpstream_url = 'https://bgpstream.com'
        self.html_dir = path
        # maps urls to paths where HTML is written
        self.url_to_file = {self.bgpstream_url: self.html_dir + 'page.html'}
        # list of all events created
        self.events = []

    def get_event_tag(self, event):
        response = requests.get(self.bgpstream_url)
        response.raise_for_status()
        # 'BGP Leak ' and 'Outage ' both have an extra space
        if event == BGPStream_Website_Event_Types.LEAK.value or event == BGPStream_Website_Event_Types.OUTAGE.value:
            event += ' '
        tag = Soup(response.text, 'html.parser').find(string=event).parent.parent
        response.close()
        return tag

    def get_url_tag(self, url):
        response = requests.get(self.bgpstream_url + url)
        response.raise_for_status()
        tag = Soup(response.text, 'html.parser')
        response.close()
        return tag


    def change_common_info(self, event_type, save_dict, no_as): 
        """Hijacks and leaks have 2 lines of AS info, outages have 1.
           Outages can have N/A for as info
           Returns the tags and new url for further processing"""
        tag = self.get_event_tag(event_type)

        asn = tag.find(class_='asn')

        if event_type == BGPStream_Website_Event_Types.HIJACK.value:
            # Pieces of AS info that Hijacks have
            keys = ['expected_origin_name', 'expected_origin_number',
                    'detected_origin_name', 'detected_origin_number']
            save_dict['country'] = ''
            save_dict['end_time'] = ''

        if event_type == BGPStream_Website_Event_Types.LEAK.value:
            keys = ['origin_as_name', 'origin_as_number',
                    'leaker_as_name', 'leaker_as_number']
            save_dict['country'] = ''
            save_dict['end_time'] = ''

        if event_type == BGPStream_Website_Event_Types.OUTAGE.value:
            keys = ['as_name', 'as_number']

        # these will serve as the new AS names and AS numbers
        names_numbers = [random_name(), random_number(),
                         random_name(), random_number()]

        # save them to the dict so they can be recalled for testing
        for key, value in zip(keys, names_numbers):
            save_dict[key] = value

        # change the HTML for hijacks/leaks
        if len(keys) == 4:
            # formats the generated AS names and numbers
            first_AS = names_numbers[0] + ' (AS ' + names_numbers[1] + ')'
            second_AS = names_numbers[2] + ' (AS ' + names_numbers[3] + ')'

            # the asn tag has children tags that should be preserved
            # e.g. <i>Expected Origin AS:</i>
            asn.contents[2].replace_with(NavigableString(first_AS))
            asn.contents[6].replace_with(NavigableString(second_AS))

            # as_info is the 1st return value of parse_common_elements
            save_dict['as_info'] = [x for x in asn.stripped_strings]
            # these 2 are returned by parse_as_info
            save_dict['parsed_as_info1'] = (names_numbers[0], names_numbers[1])
            save_dict['parsed_as_info2'] = (names_numbers[2], names_numbers[3])

        # outages can have no AS info
        elif no_as:
            save_dict['as_name'] = None
            save_dict['as_number'] = None
            save_dict['as_info'] = 'N/A'
            save_dict['parsed_as_info1'] = (None, None)
            asn.string = 'N/A'
        else:
            asn.string = names_numbers[0] + ' (AS ' + names_numbers[1] + ')'
            save_dict['as_info'] = asn.string
            save_dict['parsed_as_info1'] = (names_numbers[0], names_numbers[1])

        # save and change start time
        start = strftime('%Y-%m-%d %H:%M:%S', gmtime(time()))
        save_dict['start_time'] = start
        tag.find(class_='starttime').string = start

        # get the <a> tag and extract the old url
        url_tag = tag.find('a')
        old_url = url_tag['href']

        # change the url and event number to something new
        event_number = random_number()
        new_url = '/event/' + event_number
        save_dict['url'] = new_url
        save_dict['event_number'] = event_number
        url_tag['href'] = new_url

        # save tag as a row that can be used for parse_common_elements
        save_dict['row'] = tag
        save_dict['event_type'] = event_type
        return tag, self.get_url_tag(url=old_url), new_url

    def save_and_write(self, save_dict, tds, file_name, event_type,
                       extra_page, new_url):
            # save extended children to the dict
            save_dict['extended_children'] = tds
            # save the dict to events
            self.events.append(save_dict)
            # add to the event_info_keys for this type
            #self.event_info_keys[event_type].append(file_name)
            # write out and make open_custom_HTML able to open this file
            file_path = self.html_dir + file_name + '.html'
            self.url_to_file[self.bgpstream_url + new_url] = file_path

            # append the front page row HTML
            with open(self.url_to_file[self.bgpstream_url], 'a') as f:
                f.write(save_dict['row'].prettify())

            # write the specific event's webpage HTML
            with open(file_path, 'w') as f:
                f.write(str(extra_page))


    def write_hijack(self):

        hijack_info = {}

        for i in [4, 6]:
            tag, hijack_page, new_url = self.change_common_info(
                   BGPStream_Website_Event_Types.HIJACK.value, hijack_info, False)

            # generate new info
            ip = random_IP(i)
            detected_as_path = remove_list_format([random_number() 
                                            for i in range(randrange(3, 10))])
            detected_by_bgpmon_peers = random_number()

            # saving them
            hijack_info['expected_prefix'] = ip
            hijack_info['more_specific_prefix'] = ip
            # as path is formatted with curly braces
            hijack_info['detected_as_path'] = '{' + detected_as_path + '}'
            hijack_info['detected_by_bgpmon_peers'] = detected_by_bgpmon_peers

            # put it in the HTML
            tds =  hijack_page('td')

            colon_split_replace(tds[1], ip)
            colon_split_replace(tds[3], ip)
            # No colon here. Comma is removed.
            tds[5].string = 'Detected AS Path ' + detected_as_path.replace(',','')
            colon_split_replace(tds[6], detected_by_bgpmon_peers)

            file_name = 'hijack' + str(i)
            self.save_and_write(hijack_info, tds, file_name, 'hijack',
                                hijack_page, new_url)

    def write_leak(self):
        leak_info = {}

        tag, leak_page, new_url = self.change_common_info(
                                  BGPStream_Website_Event_Types.LEAK.value, leak_info, False)
        tds =  leak_page('td')
        leaked_to_list = tds[-3]('li')

        # generate new info
        ip = random_IP(4)

        # casting to int here because no quotes are desired
        leaked_to_number = [int(random_number()) 
                            for i in range(len(leaked_to_list))]

        leaked_to_name = [random_name() for i in range(len(leaked_to_list))]

        example_as_path = remove_list_format([random_number() 
                                          for i in range(randrange(10, 30))])

        detected_by_bgpmon_peers = random_number()
      
        # saving them
        leak_info['leaked_prefix'] = ip
        leak_info['leaked_to_number'] = square_to_curly(leaked_to_number)
        leak_info['leaked_to_name'] = square_to_curly(leaked_to_name)
        leak_info['example_as_path'] = '{' + example_as_path + '}'
        leak_info['detected_by_bgpmon_peers'] = detected_by_bgpmon_peers

        # changing the HTML
        colon_split_replace(tds[1], ip + '(AS' + leak_info['origin_as_number']
                            + ' ' + leak_info['origin_as_name'])

        for i in range(len(leaked_to_list)):
            # modifying the HTML for every item of the list
            leaked_to_list[i].string = str(leaked_to_number[i]) +\
                                           ' (' + leaked_to_name[i] + ')'

        colon_split_replace(tds[4], example_as_path.replace(',',''))
        colon_split_replace(tds[5], detected_by_bgpmon_peers)

        self.save_and_write(leak_info, tds, 'leak', 'leak', leak_page, new_url)

    def write_outage(self):
        for no_as, end, country in list(product([True, False], repeat=3)):
            f_name = 'outage'
            if no_as:
                f_name += '_no_as'
            outage_info = {}

            tag, outage_page, new_url = self.change_common_info(
                                 BGPStream_Website_Event_Types.OUTAGE.value, outage_info, no_as)

            if end:
                f_name += '_end'
                end = strftime('%Y-%m-%d %H:%M:%S', gmtime(time()))
                outage_info['end_time'] = end
                tag.find(class_='endtime').string = end
            else:
                outage_info['end_time'] = ''
                tag.find(class_='endtime').string = ''

            if country:
                f_name += '_country'
                country_name = random_name()[-2:]
                # it's best to create new country tag by hand
                # because of variability in the HTML pulled
                country_tag = Soup(features='html.parser').new_tag('td',
                                                        class_='country')
                img_tag = Soup(features='html.parser').new_tag('img',
                    src='https://portal.bgpmon.net/images/flags/' +\
                    country_name.lower() + '.gif')
                country_tag.append(country_name)
                country_tag.append(img_tag)
                tag.find(class_='country').replace_with(country_tag)
                outage_info['country'] = country_name
            else:
                outage_info['country'] = ''
                tag.find(class_='country').string = ''

            tds = outage_page('td')

            num_prefixes = random_number()
            # make the random number a percent
            percent_prefixes = str(int(random_number()) % 100)

            outage_info['number_prefixes_affected'] = num_prefixes                    
            outage_info['percent_prefixes_affected'] = percent_prefixes

            colon_split_replace(tds[-1],
                                num_prefixes + ' (' + percent_prefixes + '%)') 
                   
            self.save_and_write(outage_info, tds, f_name, 'outage',
                                outage_page, new_url)


    def setup(self):
        # clears the file first
        open(self.url_to_file[self.bgpstream_url], 'w').close()
        self.write_hijack()
        self.write_leak()
        self.write_outage()
        # adding 10 "corrupted rows" that will be removed during parsing
        with open(self.url_to_file[self.bgpstream_url], 'a') as f:
            for i in range(10):
                f.write('<tr>Corrupted</tr>')

    def open_custom_HTML(self, url: str, tag: str):
        """Function used for patching utils.get_tags()."""
        with open(self.url_to_file[url], 'r') as f:
            return [x for x in Soup(f.read(), 'html.parser').select(tag)]



