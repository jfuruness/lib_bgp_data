import re
import requests
import bs4
import urllib.request
import shutil
import os
import bz2
import pprint

class Caida_AS_Relationships_Parser:

    def __init__(self, path="/tmp/bgp"):
        """
        Initializes urls, regexes, and path variables

        Input
            self    class object
            path    string          path for all files
        Output
            None    NoneType
        """

        # Path to where all files will go. It does not have to exist
        self.path = path
        self.unzipped_path = os.path.join(self.path + "unzipped")
        # URLs fom the caida websites to pull data from
        url_1 = 'http://data.caida.org/datasets/as-relationships/serial-1/'
        url_2 = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        self.urls = [url_1, url_2]
        # Parse based on ^|, space, or newline
        self.divisor = re.compile(r'([^|\n\s]+)')

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
        # Create a list of tags from the html and return them
        return [x for x in soup.select(tag)]

    def get_file_names(self, path):
        """
        Gets the file names in a given path

        Input
            self     class object
            path     string          path for files
        Output
            files    list of str     list of file_names
        """

        # This may look too small to be a function, but outside a function
        # it becomes a couple lines longer
        for (_, _, files) in os.walk(path):
            return files

    def download_files(self):
        """
        Downloads all .bz2 files from caida websites into self.path

        Input
            self    class object
        Output
            None    NoneType
        """

        # Create directory if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        for url in self.urls:
            elements = [x for x in self.get_tags(url, 'a')]
            for i in range(len(elements)):
                # There are some files we don't want, so we exlude them
                if "bz2" in elements[i]["href"]:
                    # os.path.join is neccessary
                    # for cross platform compatability
                    temp_path = os.path.join(self.path, elements[i]["href"])
                    with urllib.request.urlopen(url + elements[i]["href"])\
                            as response, open(temp_path, 'wb') as out_file:
                        # Copy the file into the specified file_path
                        shutil.copyfileobj(response, out_file)
                        print("{} / {} downloaded".format(i + 1,
                                                          len(elements)))

    def unzip_files(self):
        """
        Unzips all .bz2 files from caida websites into self.path_unzipped

        Input
            self    class object
        Output
            None    NoneType
        """

        # Create the path if ut doesn't exist
        if not os.path.exists(self.unzipped_path):
            os.mkdir(self.unzipped_path)
        files = self.get_file_names(self.path)
        for i in range(len(files)):
            print("{} / {} unzipped".format(i + 1, len(files)))
            # os.path.join is needed for cross platform compatability
            filepath = os.path.join(self.path, files[i])
            newfilepath = os.path.join(self.unzipped_path,
                                       files[i][:-4] + '.decompressed')
            # Unzips .bz2 into a new file
            with open(newfilepath, 'wb') as new_file,\
                    bz2.BZ2File(filepath, 'rb') as file:
                for data in iter(lambda: file.read(100 * 1024), b''):
                    new_file.write(data)

    def parse_ppdc(self, file_name):
        """
        Parses ppdc files for data

        Input
            self         class object
            file_name    string          name of the file
        Output
            None         NoneType
        """

        temp_file = open(os.path.join(self.unzipped_path, file_name), "r")
        data = []
        
        # For all lines without a comment:
        for line in [x for x in temp_file.readlines() if "#" not in x]:
            # Format of a ppdc file:
            # <cone_as> <customer_as_1>...<customer_as_n>
            nums = self.divisor.findall(line)
            temp = {"cone_as": nums[0], "customer_as": nums[1:]}
#            pprint.pprint(temp)
            data.append(temp)
        temp_file.close()
        return data

    def parse_as_rel(self, file_name):
        """
        Parses as_rel files for data

        Input
            self         class object
            file_name    string          name of the file
        Output
            None         NoneType
        """

        temp_file = open(os.path.join(self.unzipped_path, file_name), "r")
        data = []

        # For all lines without comments
        for line in [x for x in temp_file.readlines() if "#" not in x]:
            # Format of as-rel file:
            # <provider_as> | <customer_as> | -1
            # <peer_as> | <peer_as> | 0
            nums = self.divisor.findall(line)
            classifier = nums[2]
            if classifier == '-1':
                temp = {"provider_as": nums[0], "customer_as": nums[1]}
            elif classifier == '0':
                temp = {"peer_as_1": nums[0], "peer_as_2": nums[1]}
            else:
                raise Exception("classifier unknown: {}".format(classifier))
#            pprint.pprint(temp)
            data.append(temp)
        temp_file.close()
        return data

    def parse_as_rel2(self, file_name):
        """
        Parses as_rel2 files for data

        Input
            self         class object
            file_name    string          name of the file
        Output
            None         NoneType
        """

        temp_file = open(os.path.join(self.unzipped_path, file_name), "r")
        data = []

        # For all lines without comments
        for line in [x for x in temp_file.readlines() if "#" not in x]:
            # Format of as-rel2:
            # <provider_as> | <customer_as> | -1
            # <peer_as> | <peer_as> | 0 | <source>
            groups = self.divisor.findall(line)
            classifier = groups[2]
            if classifier == '-1':
                temp = {"provider_as": groups[0], "customer_as": groups[1]}
            elif classifier == '0':
                temp = {"peer_as_1": groups[0],
                        "peer_as_2": groups[1],
                        "source": groups[3]}
            else:
                raise Exception("classifier unknown: {}".format(classifier))
#            pprint.pprint(temp)
            data.append(temp)
        temp_file.close()
        return data

    def parse_files(self):
        """
        Parses files from caida websites for data on AS relationships

        Input
            self    class object
        Output
            None    NoneType
        """
        data = []

        # for all files in self.path_unzipped
        for file_name in self.get_file_names(self.unzipped_path):
            if "ppdc" in file_name:
                data.extend(self.parse_ppdc(file_name))
            elif "as-rel.txt" in file_name:
                data.extend(self.parse_as_rel(file_name))
            elif "as-rel2.txt" in file_name:
                data.extend(self.parse_as_rel2(file_name))
        return data

    def clean_up(self):
        """
        Permanently deletes all the files in paths specified

        Input
            self    class object
        Output
            None    NoneType
        """

        if os.path.exists(self.path):
            # rm -rf self.path
            shutil.rmtree(self.path)
        if os.path.exists(self.unzipped_path):
            # rm -rf self.unzipped_path
            shutil.rmtree(self.unzipped_path)


#parser = Caida_AS_Relationships_Parser()
#parser.download_files()
#parser.unzip_files()
#parser.parse_files()
