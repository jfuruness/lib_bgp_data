#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Detailed_File.

The Detailed_File class contains the functionality to load and parse
mrt files. It's an extention of MRT_File but with a few changes in
regex to also get update type, if necessary.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino", "Nicholas Shpetner"]
__credits__ = ["Justin Furuness", "Matt Jaccino", "Cameron Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import os
import logging
# HEY, LISTEN! TAKE OUT SHUTIL WHEN PUSHING!
from shutil import copyfile
from ..base_classes import File
from .detailed_tables import MRT_Detailed_Table
from ..utils import utils


class Detailed_MRT_File(File):
    """Converts MRT files to CSVs and then inserts them into a database.

    In depth explanation in README.
    """

    __slots__ = ['path', 'csv_dir', 'url', 'start', 'end', 'num', 'csv_name']

    def __init__(self,
                 path: str,
                 csv_dir: str,
                 url: str,
                 start: int,
                 end: int,
                 num: int = 1):
        self.start = start
        self.end = end

        # added this
        self.path = path

        super().__init__(path, csv_dir, url, num)

    def parse_file(self, bgpscanner=True):
        """Parses a downloaded file and inserts it into the database

        if bgpscanner is set to True, bgpscanner is used to parser files
        which is faster, but ignores malformed announcements. While
        these malformed announcements are few and far between, bgpdump
        does not ignore them and should be used for full data runs. For
        testing however, bgpscanner is much faster and has almost all
        data required. More in depth explanation at the top of the file

        Note that when tested for speed, logging doesn't slow down parse_files
        Or it does, and I just turned it off wrong.
        """
        # Sets CSV path
        self.csv_name = f"{self.csv_dir}/{os.path.basename(self.path)}.csv"
        # Parses the MRT file into a csv file
        print("Paths set, converting dump")
        self._convert_dump_to_csv(bgpscanner)
        print("Inserted file from " + self.url)
        dst = "/new_hires/nicholas/lib_bgp_mrt_detailed/lib_bgp_data/lib_bgp_data/mrt_parser/tests/test.txt"
        copyfile(self.csv_name, dst)
        #  Inserts the csv file into the MRT_Detailed Table
        try:
            utils.csv_to_db(MRT_Detailed_Table, self.csv_name)
        except:
            print("DOWNLOAD THIS FILE: ", self.url)
            #copyfile(self.path, "/new_hires/nicholas/lib_bgp_mrt_detailed/lib_bgp_data/lib_bgp_data/mrt_parser/tests/error_before_parsing.txt")
            copyfile(self.csv_name, "/new_hires/nicholas/lib_bgp_mrt_detailed/lib_bgp_data/lib_bgp_data/mrt_parser/tests/err.txt")
            raise

        #utils.csv_to_db(MRT_Detailed_Table, self.csv_name)  
        # Deletes all old files
        utils.delete_paths([self.path, self.csv_name])
        utils.incriment_bar(logging.root.level)


########################
### Helper Functions ###
########################

    def _convert_dump_to_csv(self, bgpscanner=True):
        """Parses MRT file into a CSV

        This function uses bgpscanner to first be able to read
        the MRT file. This is because BGPScanner is the fastest tool to
        use for this task. The drawback of bgpscanner is that it ignores
        malformed announcements. There aren't a lot of these, and it's
        much faster, but for a full data set the slower tool bgpdump
        should be used. Then the sed commands parse the file and
        format the data for a CSV. Then this is stored as a tab
        delimited CSV file, and the original is deleted. For a more in
        depth explanation see top of file. For parsing spefics, see each
        function listed below.
        """

        args = self._bgpscanner_args() if bgpscanner else self._bgpdump_args()
        args += '> ' + self.csv_name
        print("Arg set 1 complete, as:\n" + args)
        # writes to the temp txt
        utils.run_cmds(args)
        print("Argset 1 ran")
        logging.debug(f"Wrote {self.csv_name}\n	From {self.url}")
        utils.delete_paths(self.path)

    def _bgpscanner_args(self):
        """Parses MRT file into a CSV using bgpscanner

        For a more in depth explanation see _convert_dump_to_csv. For
        explanation on specifics of the parsing, see below.
        """
        # TODO: Type, prefix, time first seen, time of update itself, ASN for updates, ribs stay as is
        # TODO: Check if updates == announcements
        # I know this may seem unmaintanable, that's because this is a
        # Fast way to to this. Please, calm down.
        # Turns out not fast - idk if other regexes are faster

        # bgpscanner outputs this format:
        # TYPE|SUBNETS|AS_PATH|NEXT_HOP|ORIGIN|ATOMIC_AGGREGATE|
        # AGGREGATOR|COMMUNITIES|SOURCE|TIMESTAMP|ASN 32 BIT
        # Example: =|1.23.250.0/24|14061 6453 9498 45528 45528|
        # 198.32.160.170|i|||
        # 6453:50 6453:1000 6453:1100 6453:1113 14061:402 14061:2000
        # 14061:2002 14061:4000 14061:4002|198.32.160.170 14061|
        # 1545345848|1

        # Also please note: sed needs escape characters, so if something
        # is escaped once it is for sed. If it is escaped twice, it is
        # to escape something in sed, and a second escape for the python
        # Below are the things that need to be escaped:
        # Parenthesis are escaped because they are sed capture groups
        # + is escaped to get sed's special plus (at least one)
        # . is escaped for sed to recognize it as a period to match
        # / is escaped for sed to match the actual forward slash

        # performs bgpdump on the file
        bash_args = 'bgpscanner '
        bash_args += self.path
        # Cuts out columns we don't need
        bash_args += ' | cut -d "|" -f1,2,3,10'
        # Now we have TYPE|SUBNETS|AS_PATH|TIMESTAMP
        # Ex: =|1.23.250.0/24|14061 6453 9498 45528 45528|1545345848

        # This is where my (nicholas) modifications start. We want to
        # keep the update type here:
        bash_args += ' | sed "s/'
        # Then we continue with the original code for a bit
        # Now we focus on SUBNETS|AS_PATH|TIMESTAMP
        # Ex: 1.23.250.0/24|14061 6453 9498 45528 45528|1545345848
        # Gets three capture groups.
        # The first capture group is the prefix
        # Captures chars normally in IPV4 or IPV6 prefixes
        bash_args += '\([0|1|2|3|4|5|6|7|8|9|%|\.|\:|a|b|c|d|e|f|/]\+\)|'

        # I left this old code here in case someone can figure it out
        # https://unix.stackexchange.com/questions/145402/
        # It appears sed doesn't support this kind of alternation
        # It appears you cannot perform alternation with char classes
        # So while it is slower to use ^, that is the way it will run
        # until someone can figure out a crazier sed command. And even
        # if you could, it would appear that it wouldn't be cross
        # platform compatable, so it probably shouldn't be done anyways
        # The regex for prefix is done in this way instead of non
        # greedy matching because sed doesn't have non greedy matching
        # so instead the | must be excluded which is slower than this
        # bash_args += '\([[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+'
        # bash_args += '\.[[:digit:]]\+\/[[:digit:]]\+|'
        # Now we match for ipv6 prefixes
        # bash_args += '[0|1|2|3|4|5|6|7|8|9|%|\:|\.|a|b|c|d|e|f]*]\)|'

        # Now we focus on AS_PATH|TIMESTAMP
        # Ex: 14061 6453 9498 45528 45528|1545345848
        # Second capture group is as path except for the last number
        bash_args += '\([^{]*[[:space:]]\)*'

        # Now we have all but the last number
        # Ex: 45528|1545345848
        # Third capture group is the origin
        bash_args += '\([^{]*\)'

        # Now we have just the time
        # Example: |1545345848
        # Fourth capture group is the time
        # Don't capture anything after a decimal, we want an int
        bash_args += '|\([[:digit:]]*\)'
        # Replacement with the capture groups
        # Must double escape here or python freaks out
        bash_args += '/\\1\\t{\\2\\3}\\t\\3\\t\\4/g" | '
        # Replaces spaces in array to commas
        # Need to pipe to new sed because you need the -n -p args
        # to make sed not output the full string if it doesn't match
        # And you cannot add -e args after that
        bash_args += 'sed "s/ /, /g" '
        bash_args += '| sed "s/|/\	/g" |'
        # Since this is also a detailed mrt file, we gotta add
        # the interval timestamp.
        bash_args += 'sed -e "s/$/\	' + str(int(self.start)) + '\	' + str(int(self.end)) + '/"'
        # For various reasons, we also need to swap the columns around
        # for input into the table:
        bash_args += " | awk '{print $7,$6,$5,$4,$2,$3,$1}' FS='\	' OFS='\	'"

        """
        # Finally, a bit more sed magic to fix some malformed arrays
        # We do this by first inserting a { in front of element 0
        bash_args += " | sed 's/\	\([[:digit:]]\+,\s\)/\	{\\1/' "
        # Then we remove the second { from the line
        bash_args += " | sed 's/{//2'"
        # We do the same for the right side
        bash_args += " | sed -e 's/,\s\([[:digit:]]\+\)\	/, \\1}\	/'"
        bash_args += " | sed 's/},/, /' "
        # Just in case:
        bash_args += " | sed -e 's/\	{\([[:digit:]]\+\)\	/{\\1}\	/' "
        bash_args += " | sed -e 's/\(\/[[:digit:]]\+\){/\\1\	{/' "
        bash_args += " | sed -e 's/\	\([[:digit:]]\+\)\.\([[:digit:]]\+\)\	/\	\\1\	\\2\	/' "
        bash_args += " | sed -e 's/\([[:digit:]]\+\)\s\([[:digit:]]\+\)\s\([[:digit:]]\+\)\s\([[:digit:]]\+\)[[:blank:]]\+[[:digit:]]\+[[:blank:]]\+/\\1\	\\2\	\\3\	\\4\	/' "
        bash_args += " | sed 's/\([[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\/[[:digit:]]\+,\)//2g' "
        bash_args += " | sed 's/\([[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\/[[:digit:]]\+\)//2g' " 
        # TODO: duped prefixes: makes mutiple announcements with different prefix
        #bash_args += " | sed -e 's/\(\/[[:digit:]]\+\)\s\+/\\1\	/' "
        bash_args += " | sed -e 's/\(\/[[:digit:]]\+\)[[:blank:]]\+/\\1\	/' "
        bash_args += " | sed -e 's/\(\/[[:digit:]]\+\),/\\1/' "
        #bash_args += " | sed -e 's/\(\/[[:digit:]]\+\)	\+/\\1\	/' "

        # is the extra whitespace actually just a null value?
        #bash_args += " | sed 's/[[:blank:]]\+/\	/g' "
        #bash_args += " | sed 's/,\	/, /g' "

        # bash_args += " | sed 's/\(\/[[:digit:]]\+\),/\\1/' "
        # bash_args += " | sed -r 's/\\(^[0123456789\.:abcde\\/]+\\)[[:space:]]*/\\1\	/'"
        bash_args += " | sed 's/\/\([[:digit:]]\+\)\s\+/\/\\1\	{/' "
        bash_args += " | sed 's/{//2g' "
        # Add quotes around type:

        """
        #bash_args += """ | sed -e 's/\([+|=|-]\)/'"'"'\\1'"'"'/' """
        """
        #bash_args += " | sed 's/\	\+/\	/' "
        # And we also gotta check for spaces in arrays with 1 AS
        #bash_args += " | sed 's/{ /{/g' "
        bash_args += " | sed 's/{[[:space:]]/{/g' "
        # remove extra origin?
        bash_args += " | sed 's/\	[[:digit:]]\+\	//3' "
        bash_args += " | sed 's/^[ \	]*//g' "
        """

        # cut down the multiple prefixes
        bash_args += " | sed -e 's/\(\/[[:digit:]]\+\)[[:blank:]]\+/\\1\	/'"
        bash_args += " | sed -e 's/\(\/[[:digit:]]\+\),/\\1/'"

        bash_args += " | sed 's/{/\"{/g'"
        bash_args += " | sed 's/}/}\"/g'"

        # tabify
        bash_args += " | sed 's/[\	][\	][\	]*/\	/g' "

        """
        # for some reason, the fourth column is missing sometimes
        # this should band-aid it, but I need to figure out why this is the case

        # Added a -z flag for new line character
        bash_args += " | sed -z 's/^\(\\n[[:digit:]]\+\	[[:digit:]]\+\	[[:digit:]]\+\)\	\([[:digit:]]\+\.\)/\\1\	0000\	\\2/' "
        bash_args += " | sed 's/{[[:blank:]]\+/{/'"
        """

        return bash_args

    def _bgpdump_args(self):
        """Parses MRT file into a CSV using bgpdump

        For a more in depth explanation see _convert_dump_to_csv. For
        explanation on specifics of the parsing, see below. Also note,
        you must use the updated bgpdump tool, not the apt repo.
        """

        # performs bgpdump on the file
        bash_args = 'bgpdump -q -m -t change '
        bash_args += self.path
        # Cuts out columns we don't need
        bash_args += ' | cut -d "|" -f2,6,7 '
        # Deletes any announcements with as sets
        bash_args += '|sed -e "/{.*}/d" '
        # Performs regex matching with sed and adds brackets to as_path
        bash_args += '-e "s/\(.*|.*|\)\(.*$\)/\\1{\\2}/g" '
        # Replaces pipes and spaces with commas for csv insertion
        # leaves out first one: -e "s/, / /"
        bash_args += '-e "s/ /, /g" -e "s/|/	/g" '
        # Adds a column for the origin
        bash_args += '-e "s/\([[:digit:]]\+\)}/\\1}	\\1/g"'
        # Rearrange columns to match for csv_to_db
        bash_args += '| awk \'BEGIN {FS="	"};{OFS="	"};{ print '
        bash_args += '$2, $3, $4, $1}\''
        return bash_args
