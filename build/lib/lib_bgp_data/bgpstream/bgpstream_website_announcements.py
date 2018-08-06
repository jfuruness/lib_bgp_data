import re
import requests
import bs4
import multiprocessing
from multiprocessing import Process, Queue
import pprint

class BGPStream_Website_Parser:
    def __init__(self, parallel=False, verbose=False, row_limit=None):
        # This regex parses out the AS number and name from a string of both
        self.as_regex = re.compile(r'''
                                   (?P<as_name>.+?)\s\(AS\s(?P<as_number>\d+)\)
                                   |
                                   (?P<as_number2>\d+).*?\((?P<as_name2>.+?)\)
                                   ''', re.VERBOSE
                                   )
        # This regex returns a string that starts and ends with numbers
        self.nums_regex = re.compile(r'(\d[^a-zA-Z\(\)\%]*\d*)')
        # This is for a queue to collect results from multithreaded module
        self.q = Queue()
        self.row_limit = row_limit
        self.verbose = verbose
        # I think you can only do about 100 in parallel then website cuts off
        self.parallel = parallel

    def get_tags(self, url, tag):
        """
        Gets the html of a given url, and returns the selected tags

        Input
            self    class object
            url     str                        url for get request
            tag     str                        type of tag to select
        Output
            tags    list of bs4.element.tag    list of tags from bs4
        """
        response = requests.get(url)
        # Raises an exception if there was an error
        response.raise_for_status()
        # Creates a beautiful soup object from the get request
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        # This is to avoid too many open file erros
        response.close()
        # Create a list of tags from the html and return them
        return [x for x in soup.select(tag)]

    def parse_common_elements(self, row_vals, children):
        """
        Parses html and inputs the parsed values
        into a dictionary to be returned

        Input
            self        class object
            row_vals    dict                       Dictionary in which to
                                                   store parsed values
            children    list of bs4.element.Tag    List of tags to parse
        Output
            row_vals    int                        Dictionary in which parsed
                                                   values are stored
            as_info     list of str                List of strings to parse
            tags        list of bs4.element.Tag    List of tags to parse
        """
        # Must use stripped strings here because the text contains an image
        row_vals["country"] = " ".join(children[3].stripped_strings)
        try:
            # If there is just one string this will work
            as_info = children[5].string.strip()
        except:
            # If there is more than one AS this will work
            stripped = children[5].stripped_strings
            as_info = [x for x in stripped]
        row_vals["start_time"] = children[7].string.strip()
        row_vals["end_time"] = children[9].string.strip()
        row_vals["url"] = children[11].a["href"]
        row_vals["event_number"] = self.nums_regex.search(
            row_vals["url"]).group()
        url = 'https://bgpstream.com' + row_vals["url"]
        return as_info, self.get_tags(url, "td")

    def parse_as_info(self, as_info):
        """
        Performs regex on as_info to return AS number and AS name

        Input
            self         class object
            as_info      str             AS information that contains a number
                                         and a name
        Output
            as_name      str             AS name from as_info
            as_number    str             AS number from as_info
        """
        # Get group objects from a regex search
        as_parsed = self.as_regex.search(as_info)
        # If the as_info is "N/A" and the regex returns nothing
        if as_parsed is None:
            return None, None
        else:
            # This is the first way the string can be formatted:
            if as_parsed.group("as_number") is not None:
                return as_parsed.group("as_name"), as_parsed.group("as_number")
            # This is the second way the string can be formatted:
            else:
                return as_parsed.group("as_name2"),\
                    as_parsed.group("as_number2")

    def parse_outage(self, row_vals, children):
        """
        Parses even_type outage html and inputs the parsed values
        into a dictionary

        Input
            self        class object
            row_vals    dict                       Dictionary in which to
                                                   store parsed values
            children    list of bs4.element.Tag    List of tags to parse
        Output
            None        NoneType
        """

        as_info, extended_children = self.parse_common_elements(row_vals,
                                                                children)
        row_vals["AS_name"], row_vals["AS_number"] = self.parse_as_info(
            as_info)
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        prefix_string = extended_children[
            len(extended_children) - 1].string.strip()
        # Finds all the numbers within a string
        prefix_info = self.nums_regex.findall(prefix_string)
        row_vals["number_of_prefixes_affected"] = prefix_info[0]
        row_vals["percent_of_prefixes_affected"] = prefix_info[1]

    def parse_hijack(self, row_vals, children):
        """
        Parses even_type possible hijack html and inputs the parsed values
        into a dictionary

        Input
            self        class object
            row_vals    dict                       Dictionary in which to
                                                   store parsed values
            children    list of bs4.element.Tag    List of tags to parse
        Output
            None        NoneType
        """

        as_info, extended_children = self.parse_common_elements(row_vals,
                                                                children)
        row_vals["expected_origin_name"], row_vals["expected_origin_number"]\
            = self.parse_as_info(as_info[1])
        row_vals["detected_origin_name"], row_vals["detected_origin_number"]\
            = self.parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        row_vals["expected_prefix"] = self.nums_regex.search(
            extended_children[end - 6].string.strip()).group(1)
        row_vals["more_specific_prefix"] = self.nums_regex.search(
            extended_children[end - 4].string.strip()).group(1)
        row_vals["detected_as_path"] = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        row_vals["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)

    def parse_leak(self, row_vals, children):
        """
        Parses even_type BGP Leak html and inputs the parsed values
        into a dictionary

        Input
            self        class object
            row_vals    dict                       Dictionary in which to
                                                   store parsed values
            children    list of bs4.element.Tag    List of tags to parse
        Output
            None        NoneType                   None
        """
        as_info, extended_children = self.parse_common_elements(row_vals,
                                                                children)
        row_vals["origin_as_name"], row_vals["origin_as_number"] =\
            self.parse_as_info(as_info[1])
        row_vals["leaker_as_name"], row_vals["leaker_as_number"] =\
            self.parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        row_vals["leaked_prefix"] = self.nums_regex.search(
            extended_children[end - 5].string.strip()).group(1)
        leaked_to_info = [x for x in
                          extended_children[end - 3].stripped_strings]
        # We use arrays here because there could be several AS's
        row_vals["leaked_to_number"] = []
        row_vals["leaked_to_name"] = []
        # We start the range at 1 because 0 returns the string: "leaked to:"
        for i in range(1, len(leaked_to_info)):
            name, number = self.parse_as_info(leaked_to_info[i])
            row_vals["leaked_to_number"].append(number)
            row_vals["leaked_to_name"].append(name)
        row_vals["example_as_path"] = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        row_vals["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)

    def parse_row(self, row):
        """
        Parses a row of html into a dictionary

        Input
            self        class object
            row         bs4.element.Tag
        Output
            None        NoneType
        """

        # These are all of the tags within the row
        children = [x for x in row.children]
        row_vals = {"event_type": children[1].string.strip()}
        if row_vals["event_type"] == "Outage":
            self.parse_outage(row_vals, children)
        elif row_vals["event_type"] == "Possible Hijack":
            self.parse_hijack(row_vals, children)
        elif row_vals["event_type"] == "BGP Leak":
            self.parse_leak(row_vals, children)
#        pprint.pprint(row_vals)
        if self.parallel:
            self.q.put(row_vals)
        else:
            return row_vals

    def parallel_parse(self, max_processes=multiprocessing.cpu_count()):
        """
        Parses html into a dictionary in parallel
        Note that we can't use multiprocessing.pool here
        because it can't pickle properly, and pathos.multiprocessing is full
        of bugs. Because of this we impliment our own pool that cannot have
        more than the max amount of processes running at any given time

        Input
            self             class object
            max_processes    int             max number of processes that run
                                             by default, the number of cores
        Output
            None             NoneType
        """

        rows = self.get_tags("https://bgpstream.com", "tr")
        vals = []
        if self.row_limit is None or self.row_limit > (len(rows) - 3):
            # The - 3 is because the last couple of rows in the website are
            # screwed up, probably an html error or something who knows
            self.row_limit = len(rows) - 3
        if self.parallel:
            processes = []
            num_running = latest_unjoined = 0
            if self.verbose:
                print("total number of rows: {}".format(self.row_limit))
            # This is the for loop to start the processes
            for i in range(self.row_limit):
                processes.append(Process(target=self.parse_row, args=(rows[i],)))
                processes[i].start()
                if self.verbose:
                    print("now processing row {}/{}".format(i, self.row_limit))
                num_running += 1
                # This is to make sure we don't have too many processes running
                if num_running > max_processes:
                    processes[latest_unjoined].join()
                    num_running -= 1
                    latest_unjoined += 1
            # After we are done starting processes, we have to join any remaining
            for i in range(latest_unjoined, self.row_limit):
                processes[i].join()
            while(self.q.empty()==False):
                vals.append(self.q.get())
        else:
            for i in range(self.row_limit):
                val = self.parse_row(rows[i])
                if self.verbose:
                    print("now processing row {}/{}".format(i, self.row_limit))
                vals.append(val)
        return vals
#parser = BGPStream_Website_Parser()
#parser.parallel_parse()
