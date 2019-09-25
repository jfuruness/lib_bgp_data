# lib\_bgp\_data
This package contains multiple submodules that are used to gather and manipulate real data in order to simulate snapshots of the internet. The purpose of this is to test different security policies to determine their accuracy, and hopefully find ones that will create a safer, more secure, internet as we know it.

*disclaimer: If a submodule is in development, that means that it unit tests are in the process of being written*

*Another disclaimer: Long story short, our system has a lot of weird permissions, so I've made a lot of commits to this repo as root. They are all me, Justin Furuness. Oops.*

* [lib\_bgp\_data](#lib_bgp_data)
* [Description](#package-description)
* Submodules:
	* [Forecast Submodule](#forecast-submodule)
	* [MRT Announcements Submodule](#mrt-announcements-submodule)
	* [Relationships Submodule](#relationships-submodule)
	* [Roas Submodule](#roas-submodule)
	* [Extrapolator Submodule](#extrapolator-submodule)
	* [BGPStream Website Submodule](#bgpstream-website-submodule)
	* [RPKI Validator Submodule](#rpki-validator-submodule)
	* [What if Analysis Submodule](#what-if-analysis-submodule)
	* [API Submodule](#api-submodule)
	* [ROVPP Submodule](#rovpp-submodule)
	* [Utils](#utils)
	* [Config](#config-submodule)
	* [Database](#database-submodule)
	* [Logging](#logging-submodule)
* [Installation](#installation)
* [Testing](#testing)
* [Adding a Submodule](#adding-a-submodule)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
* [FAQ](#faq)
## Package Description
* [lib\_bgp\_data](#lib_bgp_data)
This README is split up into several subsections for each of the submodules included in this package. Each subsection has it's own descriptions, usage instructions, etc. The [Forecast Submodule](#forecast-submodule) subsection details how all of the submodules combine to completely simulate the internet. For an overall view of how the project will work, see below:

**![](https://docs.google.com/drawings/u/0/d/sx3R9HBevCu5KN2luxDuOzw/image?w=864&h=650&rev=1621&ac=1&parent=1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc)**
Picture link: https://docs.google.com/document/d/1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc/edit?usp=sharing

Please note: These steps are not necessarily linear, as much of this is done in parallel as possible. For more details please view the [Forecast Submodule](#forecast-submodule)
1. The project first starts by using the [MRT Parser](#mrt-announcements-submodule) to collect all announcements sent over the internet for a specific time interval. This usually takes around 15-20 minutes on our machine and results in approximately 40-100 GB of data.
2. The [Roas Parser](#roas-submodule) also downloads all the ROAs for that time interval. This usually takes a couple of seconds.
3. A new table is formed with all mrt announcements that have ROAs. This join is done by checking whether or not the prefixes of the MRT announcements are a subset of the prefixes in the ROAs table. Because this is an expensive operation, and is done on a 40GB+ table, this takes an hour or two on our machine.
4. The relationships data [Relationships Parser](#relationships-submodule) is also gathered in order to be able to simulate the connections between different AS's on the internet. This takes a couple of seconds.
5. Each of these data sets gets fed into the [Extrapolator](#extrapolator-submodule) which then creates a graph of the internet and propagates announcements through it. After this stage is complete, there is a graph of the internet, with each AS having all of it's announcements that was propagated to it (with the best announcement for each prefix saved based on gao rexford). The [Extrapolator](#extrapolator-submodule) itself takes around 5-6 hours on our machine, and results in a table around 10 GB large. This is also because we invert the results. This means that instead of storing the RIB for each AS, which results in a table that is 300GB+ large, we store what is not in the RIB for each AS. This allows us to save space, and it also saves time because joins we do on this table take less time.
6. At this point we also run the [RPKI Validator](#rpki-validator-submodule), to get the validity of these announcements. With this data we can know whether an announcement that arrived at a particular AS (from the [Extrapolator](#extrapolator-submodule) and whether or not that announcement would have been blocked by standard ROV. This usually takes 10-20 minutes the first time, or about 1 minute every time thereafter, on our machine.
7. We also download all data from bgpstream.com with the [BGPStream Website Parser](#bgpstream-website-submodule). Using this data we can know whether an announcement is actually hijacked or not. This takes about 2-3 hours the first time, and then about 1-5 minutes every time after on our machine. This takes a while because querying the website takes a while.
8.  Using the bgpstream.com data from the [BGPStream Website Parser](#bgpstream-website-submodule) and the [RPKI Validator](#rpki-validator-submodule) data we can tell if an announcement would have been blocked or not, and whether or not that announcement would have been blocked correctly. For example, if the rpki validator says that a prefix origin pair is invalid by asn, that means it would be blocked (for the invalid by asn policy). If that announcement also occurs in bgpstream.com as a hijacking, then we know that the prefix origin pair is a hijacking, and then we add one point to the hijacked and blocked column. That is an over simplification, but this calculation is done in the last submodule, the [What if Analysis](#what-if-analysis-submodule). The output of this data is for each AS, a table of how many announcements have been blocked and were hijacks, blocked and were not hijacks, not blocked but were hijacks, and not blocked and were not hijacks. This does joins on massive tables, and takes 1-10 minutes on our server.
9. The [What if Analysis](#what-if-analysis-submodule) data as well as the [Extrapolator](#extrapolator-submodule) data is then available to query form a web interface through the [API](#api-submodule), the last last submodule. All of these steps are done in the submodule called [Main](#main-submodule), in which many of these steps are done in parallel for efficiency. These results are then displayed on our website at [https://sidr.engr.uconn.edu/](https://sidr.engr.uconn.edu/)
10. The purpose of this is to determine the effect that these security policies would have on the internet and blocking hijacks (attacks). Now from the API it is possible to see what attacks (hijacks) where blocked correctly and incorrectly. It's also possible to see if other announcements where treated as a hijack and were incorrectly blocked. Using this it is possible to see how different security policies would affect your specific ASN

## Forecast Submodule
* [lib\_bgp\_data](#lib_bgp_data)
* [Short Description](#forecast-short-description)
* [Long Description](#forecast-long-description)
* [Usage](#forecast-usage)
* [Table Schema](#forecast-table-schema)
* [Design Choices](#forecast-design-choices)
* [Possible Future Improvements](#forecast-possible-future-improvements)

Status: Development
### Forecast Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)

This submodule runs all of the parsers to get a days worth of data for the ROV forecast.
### Forecast Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)

This submodule basically follows the steps in the  [Package Description](#package-description) except for a couple of minor variations.

1. If fresh_install is passed in as True, then a fresh install is installed.
2. If test is passed in as true, the MRT announcements are filtered down to just one prefix to make it easier to test the package.
3. db.vacuum_analyze_checkpoint is called 3 times. Once before joining the mrt announcements with roas, once before running the what if analysis, and at the end of everything. The purpose of this is to save storage space, create statistics on all of the tables, and write to disk. This helps the query planner when planning table joins and massively decreases runtime.

Other than that, please refer to the [Package Description](#package-description)

### Forecast Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)
#### In a Script
Initializing the Forecast:


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize Forecast with default values:
```python
from lib_bgp_data import Forecast
parser = Forecast()
```                 
To initialize Forecast with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import Forecast
parser = Forecast({"path": "/my_custom_path",
                                   "csv_dir": "/my_custom_csv_dir",
                                   "stream_level": DEBUG})
```
Running the Forecast:

| Parameter  | Default                    | Description                                                                                        |
|------------|----------------------------|----------------------------------------------------------------------------------------------------|
| start      | 7 days ago, epoch time     | epoch time, for the start of when to look for the desired event type in subtables that get created |
| end        | 6 days ago, epoch time     | epoch time, for the end of when to look for the desired event type in subtables that get created   |
| fresh_install  | False                       | Install everything from scratch if True                           |
| mrt_args       | {}                       | args passed to init the mrt parser                                                                |
| mrt_parse_args       | {}                      | args passed to run the mrt parser                                    |
| rel_args | {} | args passed to init the relationships parser                                                 |
| rel_parse_args    | {}                      | args passed to run the relationships parser                           |
| rel_parse_args    | {}                      | args passed to run the relationships parser                           |
| roas_args    | {}                      | args passed to init the roas collector                           |
| web_args    | {}                      | args passed to run the bgpstream_website_parser                           |
| web_parse_args    | {}                      | args passed to run the bgpstream_website_parser parser                           |
| exr_args    | {}                      | args passed to init the extrapolator submodule                           |
| rpki_args    | {}                      | args passed to init the RPKI Validator                           |
| what_if_args    | {}                      | args passed to init the what if analysis                           |
| test    | False                      | If true, limit mrt announcements to one prefix for time and space savings                           |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To run the Forecast with defaults:
```python
from lib_bgp_data import Forecast
Forecast().run_forecast()
```
To run the Forecast with specific time intervals:
```python
from lib_bgp_data import Forecast
Forecast().run_forecast(start=1558974033, end=1558974033)
```
To run the run_forecast with specific time intervals and a fresh install:
```python
from lib_bgp_data import Forecast
Forecast().run_forecast(start=1558974033,
                         end=1558974033,
                         fresh_install=True)
```
To run the Forecast with specific mrt parser args and a start and end time:
```python
from lib_bgp_data import Forecast
mrt_parser_args = {"api_param_mods"={"collectors[]":  ["route-views2",  "rrc03"}}
Forecast().run_forecast(start=1558974033,
                        end=1558974033,
                        mrt_args=mrt_parse_args)
```

To run the Forecast with a simple test, a start and end, and a fresh install:
```python
from lib_bgp_data import Forecast
Forecast().run_forecast(start=1558974033,
                         end=1558974033,
                         fresh_install=True,
                          test=True)
```
#### From the Command Line
Coming soon to a theater near you
### Forecast Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)

See: [MRT Announcements Table Schema](#mrt-announcements-table-schema)
	* Create Table SQL: 

	```
	    CREATE UNLOGGED TABLE IF NOT EXISTS
	        mrt_announcements (
	            prefix cidr,
	            as_path bigint ARRAY,
	            origin bigint,
	            time bigint
	        );```


### Forecast Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)
	* There are no indexes on the mrt_w_roas table because they are never used
	* Nothing is multithreaded for simplicity, and since each parser either takes up all threads or <1 minute. 
	* The database is vacuum analyzed and checkpointed before big joins to help the query planner choose the right query plan
	* When testing only one prefix is used to speed up the extrapolator and reduce data size
### Forecast Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Forecast Submodule](#forecast-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Unit tests
	* cmd line args
	* docs for unit tests and cmd line args
	* Once in dev push to pypi
	* Potentially multithread?
	* Restart at the end of the full run
## MRT Announcements Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#mrt-announcements-short-description)
   * [Long Description](#mrt-announcements-long-description)
   * [Usage](#mrt-announcements-usage)
   * [Table Schema](#mrt-announcements-table-schema)
   * [Design Choices](#mrt-announcements-design-choices)
   * [Possible Future Improvements](#mrt-announcements-possible-future-improvements)
 
Status: Development
### MRT Announcements Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

The purpose of this submodule is to parse MRT files received from https://bgpstream.caida.org/broker/data using bgpscanner to obtain the prefix, origin, time, and AS path, and insert this information into the database.
### MRT Announcements Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

This submodule downloads and parses MRT Files. This is done through a series of steps.
1. Make an api call to https://bgpstream.caida.org/broker/data
    * Handled in _get_mrt_urls function
    * This will return json for rib files which contain BGP announcements
    * From this we parse out urls for the BGP dumps
    * This only returns the first dump for the time interval given
        * However, we only want one dump, multiple dumps would have data that conflicts with one another
        * For longer intervals use one BGP dump then updates
2. Then all the mrt files are downloaded in parallel
    * Handled in MRT_Parser class
    * This instantiates the MRT_File class with each url
        * utils.download_file handles downloading each particular file
    * Four times the CPUs is used for thread count since it is I/O bound
        * Mutlithreading with GIL lock is better than multiprocessing since this is just intensive I/O in this case
    * Downloaded first so that we parse the largest files first
    * In this way, more files are parsed in parallel (since the largest files are not left until the end)
3. Then all mrt_files are parsed in parallel
    * Handled in the MRT_Parser class
    * The mrt_files class handles the actual parsing of the files
    * CPUs - 1 is used for thread count since this is a CPU bound process
    * Largest files are parsed first for faster overall parsing
    * bgpscanner is the fastest BGP dump scanner so it is used for tests
    * bgpdump used to be the only parser that didn't ignore malformed announcements, but now with a change bgpscanner does this as well
        * This was a problem because some ASes do not ignore these errors
    * sed is used because it is cross compatible and fast
        * Must use regex parser that can find/replace for array format
        * AS Sets are not parsed because they are unreliable
    * Possible future extensions:
        * Use a faster regex parser?
        * Add parsing updates functionality?
4. Parsed information is stored in csv files, and old files are deleted
    * This is handled by the MRT_File class
    * This is done because there is thirty to one hundred gigabytes
        * Fast insertion is needed, and bulk insertion is the fastest
    * CSVs are chosen over binaries even though they are slightly slower
        * CSVs are more portable and don't rely on postgres versions
        * Binary file insertion relies on specific postgres instance
    * Old files are deleted to free up space
5. CSV files are inserted into postgres using COPY, and then deleted
    * This is handled by MRT_File class
    * COPY is used for speedy bulk insertions
    * Files are deleted to save space
    * Duplicates are not deleted because this is an intensive process
        * There are not a lot of duplicates, so it's not worth the time
        * The overall project takes longer if duplicates are deleted
        * A duplicate has the same AS path and prefix
6. VACUUM ANALYZE is then called to analyze the table for statistics
    * An index is never created on the mrt announcements because when the announcements table is intersected with roas table, only a parallel sequential scan is used
### MRT Announcements Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

#### In a Script
Initializing the MRT Parser:
> The default params for the mrt parser are:
> name = self.\_\_class\_\_.\_\_name\_\_  # The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers.
> path = "/tmp/bgp_{}".format(name)  # This is for the mrt files
> CSV directory = "/dev/shm/bgp_{}".format(name) # Path for CSV files, located in RAM
> logging stream level = logging.INFO  # Logging level for printing
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize MRT_Parser with default values:
```python
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser()
```                 
To initialize MRT_Parser with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser({"path": "/my_custom_path",
                         "csv_dir": "/my_custom_csv_dir",
                         "stream_level": DEBUG})
```
Running the MRT Parser:
> The default params for the mrt parser's parse_files are:
> start = 7 days ago in epoch,  # Start of the received time interval from which to get MRT Announcements
> end = 6 day ago in epoch,  # End of received time interval from which to get MRT announcements
> api_params_mods = None  # custom parameters to API for mrt files, by default gets all announcements within a time interval with so: {'human': True,  # This value cannot be changed
'intervals': ["{},{}".format(start, end)],  # This value cannot be changed
'types': ['ribs']
}
> download_threads = Number of CPU cores * 4  # Number of threads used to download MRT Files
> parse_threads = Number of CPU cores  # Number of threads to parse MRT Files
> IPV4  = True  # Whether or not to include IPV4 data
> IPV6 = False  # Whether or not to include IPV6 data
> bgpscanner = True  # Uses bgpscanner to parse mrt files
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To run the MRT Parser with defaults:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files()
```
To run the MRT Parser with specific time intervals:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files(start=1558974033,
                         end=1558974033)
```
To run the MRT Parser with specific time intervals and custom api parameters:

See: [https://bgpstream.caida.org/docs/api/broker](https://bgpstream.caida.org/docs/api/broker) for full listof API Parameters. Note that these params are only added to a dictionary of:
 {'human': True,  'intervals': ["{},{}".format(start, end)]}
In this example we get all RIB files from a specific collector, route-views2
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files(start=1558974033,
                         end=1558974033,
                         api_param_mods={"collectors[]": ["route-views2", "rrc03"]})
```
To run the MRT Parser with specific time intervals and bgpdump:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files(start=1558974033,
                         end=1558974033,
                         bgpscanner=False)
```

To run the MRT Parser with specific time intervals and IPV4 and IPV6 data:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files(start=1558974033,
                         end=1558974033,
                         IPV4=True,
                         IPV6=True)
```
To run the MRT Parser with specific time intervals and different number of threads:
```python
from multiprocessing import cpu_count
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files(start=1558974033,
                         end=1558974033,
                         download_threads=cpu_count(),
                         parse_threads=cpu_count()/4)
```
#### From the Command Line
Coming Soon to a theater near you
### MRT Announcements Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

	* This table contains information on the MRT 	Announcements retrieved from the https://bgpstream.caida.org/broker/data
	* Unlogged tables are used for speed
	* prefix: The prefix of an AS *(CIDR)*
	* as\_path: An array of all the AS numbers in the 	AS Path (*bigint ARRAY)*
	* origin: The origin AS *(bigint)*
	* time: Epoch Time that the announcement was first seen *(bigint)*
	* Create Table SQL:
	    ```
	    CREATE UNLOGGED TABLE IF NOT EXISTS
	        mrt_announcements (
	            prefix cidr,
	            as_path bigint ARRAY,
	            origin bigint,
	            time bigint
	        );
	    ```
### MRT Announcements Design Choices 
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

* We only want the first BGP dump
    * Multiple dumps have conflicting announcements
    * Instead, for longer intervals use one BGP dump and updates
* Due to I/O bound downloading:
    * Multithreading is used over multiprocessing for less memory
    * Four times CPUs is used for thread count
* Downloading is done and completed before parsing
    * This is done to ensure largest files get parsed first
    * Results in fastest time
* Downloading completes 100% before parsing because synchronization primitives make the program slower if downloading is done until threads are available for parsing
* Largest files are parsed first because due to the difference in file size there is more parallelization achieved when parsing largest files first resulting in a faster overall time
* CPUs - 1 is used for thread count since the process is CPU bound
    * For our machine this is the fastest, feel free to experiment
* Data is bulk inserted into postgres
    * Bulk insertion using COPY is the fastest way to insert data into postgres and is neccessary due to massive data size
* Parsed information is stored in CSV files
    * Binary files require changes based on each postgres version
    * Not as compatable as CSV files
* Duplicates are not deleted to save time, since there are very few
    * A duplicate has the same AS path and prefix
* bgpscanner is the fastest BGP dump scanner so it is used
* bgpdump used to be the only parser that didn't ignore malformed announcements, but now with a change bgpscanner does this as well
    * This was a problem because some ASes do not ignore these errors
* sed is used for regex parsing because it is fast and portable
* AS Sets are not parsed because they are unreliable
### MRT Announcements Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Add functionality to download and parse updates?
	    * This would allow for a longer time interval
	    * After the first dump it is assumed this would be 	faster?
	    * Would need to make sure that all updates are gathered, not just the first in the time interval to the api, as is the norm
	* Test again for different thread numbers now that bgpscanner is used
	* Test different regex parsers other than sed for speed?
	* Add test cases
	* Add cmd line args
	* Log properly for different levels
	* Put underscores in front of all private variables
	* Add: 	[https://www.isolar.io/Isolario_MRT_data/Alderaan/2019_07/](https://www.isolar.io/Isolario_MRT_data/Alderaan/2019_07/)
	* Update all docs about bgpscanner and fix it
	* Change parameter docs to be tables
	* Update docs on cmd line args and unit tests
	* Include in docs as set percentage is ~.05%
	* Make regex faster?
	* Potentially fixed the bug where pools could not be created twice - take this out of unit tests
	* Once in dev push to pypi
	* Potentially partition table for speedup??
## Relationships Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#relationships-short-description)
   * [Long Description](#relationships-long-description)
   * [Usage](#relationships-usage)
   * [Table Schema](#relationships-table-schema)
   * [Design Choices](#relationships-design-choices)
   * [Possible Future Improvements](#relationships-possible-future-improvements)

Status: Development
### Relationships Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)

The purpose of this submodule is to parse Relationship files received from http://data.caida.org/datasets/as-relationships/serial-2/, converting this file into csvs with customer provider and peer relationships, and inserting this data into the database.
### Relationships Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)

The purpose of this class is to download relationship files and insert the data into a database. This is done through a series of steps.

1. Make an API call to:
    * http://data.caida.org/datasets/as-relationships/serial-2/
    * Handled in _get_url function
    * This will return the URL of the file that we need to download
    * In that URL we have the date of the file, which is also parsed out
    * The serial 2 data set is used because it has multilateral peering
    * which appears to be the more complete data set
2. Then check if the file has already been parsed before
    * Handled in parse_files function
    * If the URL date is less than the config file date do nothing
    * Else, parse
    * This is done to avoid unneccesarily parsing files
4. Then the Relationships_File class is then instantiated
5. The relationship file is then downloaded
    * This is handled in the utils.download_file function
6. Then the file is unzipped
    * handled by utils _unzip_bz2
7. The relationship file is then split into two
    * Handled in the Relationships_File class
    * This is done because the file contains both peers and customer_provider data.
    * The file itself is a formatted CSV with "|" delimiters
    * Using grep and cut the relationships file is split and formatted
    * This is done instead of regex because it is faster and simpler
8. Then each CSV is inserted into the database
    * The old table gets destroyed first
    * This is handleded in the utils.csv_to_db function
    * This is done because the file comes in CSV format
    * Optionally data can be inserted into ROVPP tables for the ROVPP simulation
9. The config is updated with the last date a file was parsed

### Relationships Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)

#### In a Script

Initializing the Relationships Parser:
> The default params for the Relationships parser are:
> name = self.\_\_class\_\_.\_\_name\_\_  # The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers.
> path = "/tmp/bgp_{}".format(name)  # This is for the relationship files
> CSV directory = "/dev/shm/bgp_{}".format(name) # Path for CSV files, located in RAM
> logging stream level = logging.INFO  # Logging level for printing
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize Relationships_Parser with default values:
```python
from lib_bgp_data import Relationships_Parser
relationships_parser = Relationships_Parser()
```                 
To initialize Relationships_Parser with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import Relationships_Parser
relationships_parser = Relationships_Parser({"path": "/my_custom_path",
                                             "csv_dir": "/my_custom_csv_dir",
                                             "stream_level": DEBUG})
```
Running the Relationships_Parser:
> The default params for the relationships parser's parse_files are:
> rovpp = False #  By default store in the normal tables
> url = None  # If rovpp is set to true, the specified URL will be used for downloads

To run the Relationships Parser with defaults:
```python
from lib_bgp_data import Relationships_Parser
Relationships_Parser().parse_files()
```
To run the Relationships Parser for ROVPP with a specific URL:
```python
from lib_bgp_data import Relationships_Parser
Relationships_Parser().parse_files(rovpp=True,
                                   url="my_specific_url")
```
#### From the Command Line
Coming Soon to a theater near you
### Relationships Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)
* [customer_providers Table Schema](#customer_providers-table-schema)
* [peers Table Schema](#peers-table-schema)
* [rovpp_customer_providers Table Schema](#rovpp_customer_providers-table-schema)
* [rovpp_peers Table Schema](#rovpp_peers-table-schema)
* [rovpp_as_connectivity Table Schema](#rovpp_as_connectivity-table-schema)

* These tables contains information on the relationship data retrieved from http://data.caida.org/datasets/as-relationships/serial-2/
* Unlogged tables are used for speed
#### customer_providers Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for customer provider pairs
* provider_as: Provider ASN *(bigint)*
* customer_as: Customer ASN (*bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        customer_providers (
            provider_as bigint,
            customer_as bigint
        );
    ```
#### peers Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for peer pairs
* peer_as_1: An ASN that is a peer *(bigint)*
* peer_as_2: An ASN that is another peer *(bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        peers (
            peer_as_1 bigint,
            peer_as_2 bigint
        );
    ```
##### ROVPP Tables:
###### rovpp_customer_providers Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for customer provider pairs
* provider_as: Provider ASN *(bigint)*
* customer_as: Customer ASN (*bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        rovpp_customer_providers (
            provider_as bigint,
            customer_as bigint
        );
    ```
###### rovpp_peers Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for peer pairs
* peer_as_1: An ASN that is a peer *(bigint)*
* peer_as_2: An ASN that is another peer *(bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        rovpp_peers (
            peer_as_1 bigint,
            peer_as_2 bigint
        );
    ```
###### rovpp_as_connectivity Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains connectivity information for all ASes
* asn: An ASes ASN *(bigint)*
* connectivity: number of customers + number of peers *(integer)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
              rovpp_as_connectivity AS (
              SELECT ases.asn AS asn,
              COALESCE(cp.connectivity, 0) + 
                COALESCE(p1.connectivity, 0) + 
                COALESCE(p2.connectivity, 0)
                  AS connectivity
              FROM rovpp_ases ases
              LEFT JOIN (SELECT cp.provider_as AS asn,
                         COUNT(cp.provider_as) AS connectivity
                         FROM rovpp_customer_providers cp
                         GROUP BY cp.provider_as) cp
              ON ases.asn = cp.asn
              LEFT JOIN (SELECT p.peer_as_1 AS asn,
                         COUNT(p.peer_as_1) AS connectivity
                         FROM rovpp_peers p GROUP BY p.peer_as_1) p1
              ON ases.asn = p1.asn
              LEFT JOIN (SELECT p.peer_as_2 AS asn,
                         COUNT(p.peer_as_2) AS connectivity
                         FROM rovpp_peers p GROUP BY p.peer_as_2) p2
              ON ases.asn = p2.asn
              );
    ```
### Relationships Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)
* CSV insertion is done because the relationships file is a CSV
* Dates are stored and checked to prevent redoing old work
* An enum was used to make the code cleaner in relationship_file
    * Classes are more messy in this case

### Relationships Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Add test cases
	* Reach out to Caida say to use RIPE and isolario data
	* Ask if you can see the code they use to generate the graphs
	* Missing asn and multihomed preferences improvements
	* Instead of filling stuff in - use SQL and caida path to replicate and make it better!
	* get ixps and s to s???
	* Check if disconnected like rovpp
	* Optimize for shortest path always?
	* Use this metric to check for poor graphs
	* use deep learning to recreate for ourselves
	* use caida as ground truth???
		* Then apply to larger sets?
	* Add cmd line args
	* Add docs on tests and cmd line args
	* Change parameter docs to be tables in docs
	* Possibly take out date checking for cleaner code?
	    * Saves very little time
	* Move unzip_bz2 to this file? Nothing else uses it 	anymore
	* Possibly change the name of the table to 	provider_customers
	    * That is the order the data is in, it is like that in all files
	* Post connectivity table in the stack overflow and ask how to combine into a better query
	* Once in prod push to pypi

## Roas Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#roas-short-description)
   * [Long Description](#roas-long-description)
   * [Usage](#roas-usage)
   * [Table Schema](#roas-table-schema)
   * [Design Choices](#roas-design-choices)
   * [Possible Future Improvements](#roas-possible-future-improvements)

Status: Production

### Roas Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)
The purpose of this submodule is to parse Roa data received from https://rpki-validator.ripe.net/api/export.json, converting this data into csvs and inserting this data into the database.
### Roas Long Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)

The purpose of this parser is to download ROAs from rpki and insert them into a database. This is done through a series of steps.

1. Clear the Roas table
   * Handled in the parse_roas function
2. Make an API call to https://rpki-validator.ripe.net/api/export.json
   * Handled in the _get_json_roas function
   * This will get the json for the roas
3. Format the roa data for database insertion
   * Handled in the _format_roas function
4. Insert the data into the database
   * Handled in the utils.rows_to_db
    * First converts data to a csv then inserts it into the database
    * CSVs are used for fast bulk database insertion
5. An index is created on the roa prefix
    * The purpose of this is to make the SQL query faster when joining with the mrt announcements

### Roas Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)
#### In a Script
Initializing the Roas Collector:


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize ROAs_Collector with default values:
```python
from lib_bgp_data import ROAs_Collector
roas_parser = ROAs_Collector()
```                 
To initialize ROAs_Collector with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import ROAs_Collector
roas_parser = ROAs_Collector({"path": "/my_custom_path",
                              "csv_dir": "/my_custom_csv_dir",
                              "stream_level": DEBUG})
```
To run the ROAs_Collector with defaults (there are no optional parameters):
```python
from lib_bgp_data import ROAs_Collector
ROAs_Collector().parse_roas()
```

#### From the Command Line
Depending on the permissions of your system, and whether or not you pip installed the package with sudo, you might be able to run the ROAs Parser with:

```roas_collector```

or a variety of other possible commands, I've tried to make it fairly idiot proof with the capitalization and such.

The other way you can run it is with:
```python3 -m lib_bgp_data --roas_collector```

### Roas Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)
* This table contains information on the ROAs retrieved from the https://rpki-validator.ripe.net/api/export.json
* Unlogged tables are used for speed
* asn: The ASN of an AS *(bigint)*
* prefix: The prefix of an AS *(CIDR)*
* max_length: Max length specified by roa (*bigint)*

* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        roas (
            asn bigint
            prefix cidr,
            max_length integer
        );
    ```
### Roas Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)
* CSVs are used for fast database bulk insertion
* An index on the prefix is created on the roas for fast SQL joins
### Roas Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Roas Submodule](#roas-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* None as of yet, production code

## Extrapolator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Extrapolator Short Description](#extrapolator-short-description)
   * [Long Description](#extrapolator-long-description)
   * [Usage](#extrapolator-usage)
   * [Possible Future Improvements](#extrapolator-possible-future-improvements)

Status: Development
### Extrapolator Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)
The Extrapolator takes as input mrt announcement data from the [MRT Parser](#mrt-announcements-submodule) and relationships data (peer and customer-provider data) from the [Relationships Parser](#relationships-submodule). The Extrapolator then propagates announcements to all appropriate AS's which would receive them, and outputs this data. This submodule is a simple wrapper to make it easier for a python script to run the extrapolator. It can run the rovpp version of the extrapolator or the forecast version of the extrapolator. Details other than how to run the wrapper are not included because up to date information should be found on the actual github page.

For more in depth documentation please refer to: [https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)
### Extrapolator Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)
#### In a Script
To run the forecast extrapolator:
> The params for the forecast extrapolator function are:

| Parameter   | Default | Description                                                                                                        |
|-------------|---------|--------------------------------------------------------------------------------------------------------------------|
| input_table | None    | Announcements table the extrapolator will pull data from, if it is none the default is the mrt_announcements table |

To initialize Extrapolator and run the forecast version:
```python
from lib_bgp_data import Extrapolator
Extrapolator().run_forecast(input_table="mrt_w_roas")
```                                                            
To initialize the Extrapolator and run the rovpp version:
> The params for the rovpp extrapolator function are:

| Parameter            | Default | Description                                                                                                                                                   |
|----------------------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| attacker_asn         | N/A     | Attacker's asn                                                                                                                                                |
| victim_asn           | N/A     | Victim's asn                                                                                                                                                  |
| more_specific_prefix | N/A     | The more specific prefix, or attackers prefix, that is doing the hijack. For example, if the victims prefix was 1.2.0.0/16, the attackers would be 1.2.3.0/24. The extrapolator calls this victim_prefix, this is misleading and should really be changed. |

To initialize Extrapolator and run the rovpp version:
```python
from lib_bgp_data import Extrapolator
Extrapolator().run_rovpp(attacker_asn, victim_asn, more_specific_prefix)
```
### Extrapolator Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Unit tests
	* Update docs with unit tests                                                            
	* Once in prod push to pypi
## BGPStream Website Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#bgpstream-website-short-description)
   * [Long Description](#bgpstream-website-long-description)
   * [Usage](#bgpstream-website-usage)
   * [Table Schema](#bgpstream-website-table-schema)
   * [Design Choices](#bgpstream-website-design-choices)
   * [Possible Future Improvements](#bgpstream-website-possible-future-improvements)

Status: Development
### BGPStream Website Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)

The purpose of this submodule is to parse information received from https://bgpstream.com to obtain information about real BGP hijacks, leaks, and outages that actually occurred.
### BGPStream Website Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)

This submodule parses through the html of bgpstream.com and formats the data for actual hjacks, leaks, and outages into a CSV for later insertion into a database. This is done through a series of steps.

1. Initialize the three different kinds of data classes.                                            
   * Handled in the \_\_init\_\_ function in the BGPStream\_Website\_Parser class
   * This class mainly deals with accessing the website, the data classes deal with parsing the information. These data classes inherit from the parent class Data and are located in the data_classes file
2. All rows are received from the main page of the website                                          
    * This is handled in the utils.get_tags function                                                 
    * This has some initial data for all bgp events                                                  
3. The last ten rows on the website are removed
    * This is handled in the parse function in the BGPStream_Website_Parser
    * There is some html errors there, which causes errors when parsing                              
4. The row limit is set so that it is not too high                                                  
    * This is handled in the parse function in the BGPStream_Website_Parser
    * This is to prevent going over the maximum number of rows on website                            
5. Rows are iterated over until row_limit is reached                                                
    * This is handled in the parse function in the BGPStream_Website_Parser
6. For each row, if that row is of a datatype passed in the parameters,                             
   and the row is new (by default) add that to the self.data dictionary                             
    * This causes that row to be parsed as well
    * Rows are parsed into CSVs and inserted into the database                                       
7. Call the db_insert funtion on each of the data classes in self.data                              
    * This will parse all rows and insert them into the database                                     
    * This formats the tables as well
        * Unwanted IPV4 or IPV6 prefixes are removed                                                 
        * Indexes are created if they don't exist
        * Duplicates are deleted
        * Temporary tables that are subsets of the data are created                                  
### BGPStream Website Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)

#### In a Script
Initializing the BGPStream_Website_Parser:


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize BGPStream_Website_Parser with default values:
```python
from lib_bgp_data import BGPStream_Website_Parser
parser = BGPStream_Website_Parser()
```                 
To initialize BGPStream_Website_Parser with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import BGPStream_Website_Parser
parser = BGPStream_Website_Parser({"path": "/my_custom_path",
                                   "csv_dir": "/my_custom_csv_dir",
                                   "stream_level": DEBUG})
```

Running the BGPStream_Website_Parser:


| Parameter  | Default                    | Description                                                                                        |
|------------|----------------------------|----------------------------------------------------------------------------------------------------|
| start      | 7 days ago, epoch time     | epoch time, for the start of when to look for the desired event type in subtables that get created |
| end        | 6 days ago, epoch time     | epoch time, for the end of when to look for the desired event type in subtables that get created   |
| row_limit  | None                       | Purely for testing, limits the number of rows to parse through for speed                           |
| IPV4       | True                       | Whether or not to include IPV4 data                                                                |
| IPV6       | False                      | Whether or not to include IPV6 data                                                                |
| data_types | [Event_Types.HIJACK.value] | This is used to determine types of events to parse                                                 |
| refresh    | False                      | If this is true, parse rows regardless of whether we've seen them or not                           |


> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To run the BGPStream_Website_Parser with defaults:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse()
```
To run the BGPStream_Website_Parser with specific time intervals for subtables:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse(start=1558974033,
                                 end=1558974033)
```
To run the BGPStream_Website_Parser with specific time intervals and custom row_limit (parses 10 rows):
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse_files(start=1558974033,
                         end=1558974033,
                         row_limit=10)
```
To run the BGPStream_Website_Parser with specific time intervals and get all outages:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse(start=1558974033,
                                 end=1558974033,
                                 data_types=[Event_Types.OUTAGE.value])
```

To run the BGPStream_Website_Parser with specific time intervals and IPV4 and IPV6 data:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse(start=1558974033,
                                 end=1558974033,
                                 IPV4=True,
                                 IPV6=True)
```
To run the BGPStream Website Parser with specific time intervals and new data regardless of whether or not it exists in the database:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().parse(start=1558974033,
                                 end=1558974033,
                                 refresh=True)
```
#### From the Command Line
Coming Soon to a theater near you
### BGPStream Website Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)

* These tables contains information on the relationship data retrieved from bgpstream.com
* Unlogged tables are used for speed
* Note that explanations are not provided because these fields are chosen by bgpstream.com
#### hijack Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for hijack events
* hijack_id: *(serial PRIMARY KEY)*
* country: Two letter country abbreviation *(varchar (50))*
* detected_as_path: detected_as_path of the hijack *(bigint ARRAY)*
* detected_by_bgpmon_peers: *(integer)*
* detected_origin_name: *(varchar (200))*
* detected_origin_number: *(bigint)*
* start_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* end_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* event_number: *(integer)*
* event_type: *(varchar (50))*
* expected_origin_name: *(varchar (200))*
* expected_origin_number: *(bigint)*
* expected_prefix: *(cidr)*
* more_specific_prefix: *(cidr)*
* url: *(varchar (250))*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS hijack (
              hijack_id serial PRIMARY KEY,
              country varchar (50),
              detected_as_path bigint ARRAY,
              detected_by_bgpmon_peers integer,
              detected_origin_name varchar (200),
              detected_origin_number bigint,
              start_time timestamp with time zone,
              end_time timestamp with time zone,
              event_number integer,
              event_type varchar (50),
              expected_origin_name varchar (200),
              expected_origin_number bigint,
              expected_prefix cidr,
              more_specific_prefix cidr,
              url varchar (250)
              );
    ```
##### hijack_temp Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for hijack events within a certain time frame
* prefix: Previously more specific prefix, aka the attackers prefix *(cidr)*
* origin: Previously the detected_origin_number *(bigint)*
* start_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* end_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* url: *(varchar (250))*
* expected_prefix: *(cidr)*
* expected_origin_number: *(bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE hijack_temp AS
        (SELECT h.more_specific_prefix AS prefix,
        h.detected_origin_number AS origin,
        h.start_time,
        COALESCE(h.end_time, now()) AS end_time,
        h.url,
        h.expected_prefix,
        h.expected_origin_number
    FROM hijack h
    WHERE
        (h.start_time, COALESCE(h.end_time, now())) OVERLAPS
        (%s::timestamp with time zone, %s::timestamp with time zone)
    );
    ```
##### subprefix_hijack_temp Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for subprefix hijack events within a certain time frame
* more_specific_prefix: The attackers prefix *(cidr)*
* attacker: Previously the detected_origin_number *(bigint)*
* url: *(varchar (250))*
* expected_prefix: *(cidr)*
* victim: Previously expected_origin_number *(bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE hijack_temp AS
        (SELECT h.more_specific_prefix AS prefix,
        h.detected_origin_number AS origin,
        h.start_time,
        COALESCE(h.end_time, now()) AS end_time,
        h.url,
        h.expected_prefix,
        h.expected_origin_number
    FROM hijack h
    WHERE
        (h.start_time, COALESCE(h.end_time, now())) OVERLAPS
        (%s::timestamp with time zone, %s::timestamp with time zone)
    );
    ```
#### leak Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for leak events
* leak_id: *(serial PRIMARY KEY)*
* country: Two letter country abbreviation *(varchar (50))*
* detected_by_bgpmon_peers: *(integer)*
* start_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* end_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* event_number: *(integer)*
* event_type: *(varchar (50))*
* example_as_path: *(bigint ARRAY)*
* leaked_prefix: *(cidr)*
* leaked_to_name: *(varchar (200) ARRAY)*
* leaked_to_number: *(bigint ARRAY)*
* leaker_as_name: *(varchar (200))*
* leaker_as_number: *(bigint)*
* origin_as_name: *(varchar (200))*
* origin_as_number: *(bigint)*
* url: *(varchar (250))*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS Leak (
        leak_id serial PRIMARY KEY,
        country varchar (50),
        detected_by_bgpmon_peers integer,
        start_time timestamp with time zone,
        end_time timestamp with time zone,
        event_number integer,
        event_type varchar (50),
        example_as_path bigint ARRAY,
        leaked_prefix cidr,
        leaked_to_name varchar (200) ARRAY,
        leaked_to_number bigint ARRAY,
        leaker_as_name varchar (200),
        leaker_as_number bigint,
        origin_as_name varchar (200),
        origin_as_number bigint,
        url varchar (250)
    );
    ```
#### outage Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for outage events
* outage_id: *(serial PRIMARY KEY)*
* as_name: *(varchar (200))*
* as_number: *(bigint)*
* country: Two letter country abbreviation *(varchar (50))*
* start_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* end_time: *(timestamp with time zone)* - Note that the server and website are set to UTC
* event_number: *(integer)*
* event_type: *(varchar (50))*
* number_prefixes_affected: *(integer)*
* percent_prefixes_affected: *(smallint)*
* url: *(varchar (250))*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS outage (
        outage_id serial PRIMARY KEY,
        as_name varchar (200),
        as_number bigint,
        country varchar (25),
        start_time timestamp with time zone,
        end_time timestamp with time zone,
        event_number integer,
        event_type varchar (25),
        number_prefixes_affected integer,
        percent_prefixes_affected smallint,
        url varchar(150)
    );
    ```
### BGPStream Website Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)
* The last ten rows of the website are not parsed due to html errors                             
* Only the data types that are passed in as a parameter are parsed                               
    * This is because querying each individual events page for info takes a long time
    * Only new rows by default are parsed for the same reason                                    
* Multithreading isn't used because the website blocks the requests                              
* Parsing is done from the end of the page to the top                                            
    * The start of the page is not always the same                                               
### BGPStream Website Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Remove unnessecary indexes
	* Should not use bare except in files
	* Filter bgpstream.com data using hurricane api
	* Email all asns and ISPs about bgpstream.com data and ask other questions (how long do they last and how often, how important are blocking hijackings to you, use our tool?)
	* Once we have ground truth use deep learning with historical data to improve upon hijacking dataset
	* cmd line args
	* Add test cases
	* Update docs on cmd line args, test cases, and indexes
	* Is there a paid version of an API for this?
	* Multithread the first hundred results?
	    * If we only parse new info this is the common case
	    * Maybe this is unnessecary though and would complicate the code
	* Once in prod push to pypi
## RPKI Validator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rpki-validator-short-description)
   * [Long Description](#rpki-validator-long-description)
   * [Usage](#rpki-validator-usage)
   * [Table Schema](#rpki-validator-table-schema)
   * [Design Choices](#rpki-validator-design-choices)
   * [Possible Future Improvements](#rpki-validator-possible-future-improvements)

Status: Development
### RPKI Validator Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
The purpose of this class is to obtain the validity data for all of the prefix origin pairs in our announcements data, and insert it into a database.

### RPKI Validator Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
The purpose of this class is to obtain the validity data for all of the
prefix origin pairs in our announcements data, and insert it into a
database. This is done through a series of steps.

1. Write the validator file.
   * Handled in the _write_validator_file function
   * Normally the RPKI Validator pulls all prefix origin pairs from the internet, but those will not match old datasets
    * Instead, our own validator file is written
    * This file contains a placeholder of 100
        * The RPKI Validator does not observe anything seen by 5 or less
         peers
2. Host validator file
    * Handled in _serve_file decorator
    * Again, this is a file of all prefix origin pairs from our MRT announcements table
3. Run the RPKI Validator
    * Handled in run_validator function
4. Wait for the RPKI Validator to load the whole file
    * Handled in the _wait_for_validator_load function
    * This usually takes about 10 minutes
5. Get the json for the prefix origin pairs and their validity
    * Handled in the _get_ripe_data function
    * Need to query IPV6 port because that's what it runs on
6. Convert all strings to int's
    * Handled in the format_asn function
    * Done to save space and time when joining with later tables
7. Parsed information is stored in csv files, and old files are deleted
    * CSVs are chosen over binaries even though they are slightly slower
        * CSVs are more portable and don't rely on postgres versions
        * Binary file insertion relies on specific postgres instance
    * Old files are deleted to free up space
9. CSV files are inserted into postgres using COPY, and then deleted
    * COPY is used for speedy bulk insertions
    * Files are deleted to save space


### RPKI Validator Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)

Initializing the RPKI Validator:
> The default params for the RPKI Validator are:
> name = self.\_\_class\_\_.\_\_name\_\_  # The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers.
> path = "/tmp/bgp_{}".format(name)  # This is for the roa files
> CSV directory = "/dev/shm/bgp_{}".format(name) # Path for CSV files, located in RAM
> logging stream level = logging.INFO  # Logging level for printing
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize RPKI_Validator with default values:
```python
from lib_bgp_data import RPKI_Validator
roas_parser = RPKI_Validator()
```                 
To initialize RPKI_Validator with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import RPKI_Validator
roas_parser = RPKI_Validator({"path": "/my_custom_path",
                              "csv_dir": "/my_custom_csv_dir",
                              "stream_level": DEBUG})
```
To run the RPKI_Validator with defaults (there are no optional parameters):
```python
from lib_bgp_data import RPKI_Validator
RPKI_Validator().run_validator()
```

#### From the Command Line
Coming Soon to a theater near you
### RPKI Validator Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
#### Unique_Prefix_Origins Table Schema
* This table contains information on the Unique Prefix Origins from the MRT Announcements
*  Unlogged tables are used for speed
* origin: The ASN of an AS *(bigint)*
* prefix: The prefix of an AS *(CIDR)*
* placeholder: 100 used for RPKI Validator seen by peers (doesn't count rows with less than 5) (*bigint)*

* Create Table SQL:
    ```
	CREATE UNLOGGED TABLE unique_prefix_origins AS
                 SELECT DISTINCT origin, prefix, 100 as placeholder
                 FROM mrt_w_roas ORDER BY prefix ASC;
    ```
#### ROV_Validity Table Schema
* This table contains the validity of all prefix origin pairs according to ROV
*  Unlogged tables are used for speed
* origin: The ASN of an AS *(bigint)*
* prefix: The prefix of an AS *(CIDR)*
* validity: 1 for known, 0 unknown, -1 invalid_length, -2, invalid_asn (*bigint)*

* Create Table SQL:
    ```
	CREATE UNLOGGED TABLE IF NOT EXISTS rov_validity (
                 origin bigint,
                 prefix cidr,
                 validity smallint);
    ```
### RPKI Validator Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
    * Indexes are not created because they are not ever used
    * We serve our own file for the RPKI Validator to be able to use old prefix origin pairs
    * Data is bulk inserted into postgres
        * Bulk insertion using COPY is the fastest way to insert data into postgres and is neccessary due to massive data size
    * Parsed information is stored in CSV files
        * Binary files require changes based on each postgres version
        * Not as compatable as CSV files

### RPKI Validator Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
    * Move the file serving functions into their own class
        * Improves readability?
    * Attempt to unhinge the db and get these values with sql queries similar to:
	    * ```SELECT * FROM mrt INNER JOIN ON m_prefix << roas_prefix AND MASKLEN(m_prefix) <= roas_max_length ```
	    * ```SELECT * FROM unique_prefix_origins u INNER JOIN roas r ON u.prefix <<= r.prefix AND MASKLEN(u.prefix) > r.max_length;```
	    * ```SELECT * FROM unique_prefix_origins u INNER JOIN roas r ON u.prefix <<= r.prefix AND u.origin != r.asn;```
	    * Update rpki docs and stuff

    * Add test cases
    * Reduce total information in the headers
    * Change paramaters to be tables in README
    * Allow validator to be able to take non mrt_w_roas table
    * put underscores in front of all private variables
    * Add command line args
    * Reduce total amount of information in headers
    * Take out hardcoded file paths
    * refactor
    * Update file comments and docs on changes
        * Such as killing port 8080, deleting dirs, Popen vs check_call, etc
    * Move file serving functions to their own class?
	    * Improves readability?
	* Update docs for cmd line args, tests, etc.
	* Once in prod push to pypi
	* Have this just output roas since we have our own db??
		* Eventually do this ourselves? simply sign and validate roas?
    * 

## What if Analysis Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#what-if-analysis-short-description)
   * [Long Description](#what-if-analysis-long-description)
   * [Usage](#what-if-analysis-usage)
   * [Table Schema](#what-if-analysis-table-schema)
   * [Design Choices](#what-if-analysis-design-choices)
   * [Possible Future Improvements](#what-if-analysis-possible-future-improvements)

Status: Development
### What if Analysis  Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
The purpose of this class is to determine the effect that security policies would have on each AS.

### What if Analysis  Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
The purpose of this class is to determine the effect that security
policies would have on each AS. This is done through a series of steps.

1. We have hijack tables and the ROV validity table. We first need to permute these tables, to get every possible combination of hijack, policy, and blocked or not blocked. This is done in the split_validitity_table sql queries.
2. We then combine each of these permutations with the output of the prefix origin pairs from the extrapolator. Remember, the extrapolator has inverse results. In other words, normally the extrapolator contains the local RIB for each ASN. Instead, it now contains everything BUT the local RIB for each ASN (discluding all prefix origin pairs not covered by a ROA). Now, because of this, when we combine each permuation of tables from step 1, we are getting all the data from that table that the ASN did not keep. Knowing this information, we must count the total of things which we did not keep, and subtract them from the total of everything in that category. For example: when we combine the invalid_asn_blocked_hijacked tables with the extrapolation results, we are getting all invalid_asn_blocked_hijacks that the ASN did NOT keep in their local RIB. So we must count these rows, i.e. the total number of invalid_asn_blocked_hijacked that the ASN did not keep, and subtract that number from the total number of invalid_asn_blocked_hijacked to get the total number of invalid_asn_blocked_hijacked that the AS did keep. This idea can be seen in each SQL query in the all_sql_queries. Hard to wrap your head around? I feel you. There's no easy way to explain it. Inverting the extrapolator results makes this process very complex and hard to understand, and I still have trouble thinking about it even though I wrote the code.
3. Simply run all of these sql queries to get data.
   Again, apologies for the insufficient explanation. I simply do not know how to write about it any better, and whoever modifies this code after me will probably only be able to understand it with a thorough in person explanation. Good luck.


### What if Analysis Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
#### In a Script
Initializing the What_If_Analysis:


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |


> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize What_If_Analysis with default values:
```python
from lib_bgp_data import What_If_Analysis
parser = What_If_Analysis()
```                 
To initialize What_If_Analysis with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import What_If_Analysis
parser = What_If_Analysis({"path": "/my_custom_path",
                           "csv_dir": "/my_custom_csv_dir",
                           "stream_level": DEBUG})
```
Running the What_If_Analysis (There are no optional parameters):

To run the What_If_Analysis with defaults:
```python
from lib_bgp_data import What_If_Analysis
What_If_Analysis().run_rov_policy()
```
#### From the Command Line
Coming Soon to a theater near you
### What if Analysis Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
* These tables contain statistics for different policies
* Unlogged tables are used for speed
* Because this whole module creates these tables, the table creation sql is omitted.
* Output Tables: invalid_asn, invalid_length, rov:
  * parent_asn: The ASN of the parent AS (stubs not included) *(bigint)*
  * blocked_hijacked: The total number of prefix origin pairs blocked and hijacked by that policy *(bigint)*
  * not_blocked_hijacked: The total number of prefix origin pairs not blocked and hijacked by that policy *  (bigint)*
  * blocked_not_hijacked: The total number of prefix origin pairs blocked and not hijacked by that policy *  (bigint)*
  * not_blocked_not_hijacked: The total number of prefix origin pairs not blocked and not hijacked by that   policy *(bigint)*
  * percent_blocked_hijacked_out_of_total_hijacks: self explanatory *(numeric)*
  * percent_not_blocked_hijacked_out_of_total_hijacks: self explanatory *(numeric)*
  * percent_blocked_not_hijacked_out_of_total_prefix_origin_pairs *(numeric)*

### What if Analysis Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
    * We permute the hijacks with each policy and blocked or not blocked
     to make the sql queries easier when combining with the extrapolator
     results.
    * We subtract the combination of any hijack table with the
     extrapolation results from the total to get what each AS actually
     had (explained above).
    * We invert extrapolation results to save space and time when doing
     what if analysis queries. This is because each AS keeps almost all
     of the announcements sent out over the internet.
    * If an index is not included it is because it was never used

### What if Analysis Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
    * Aggregate what if analysis:
        * what if analysis for treating multiple asns as a single AS
    * Add test cases
    * Multithreading
    * Make the sql queries into sql files
    * unhinge db for this, test speedup
    * Add command line args
    * Add docs on cmd line args and testing
    * split data into hijacks and subprefix hijacks
    * simple time heuristic!! (update api as well)
    * Allow for storage of multiple days worth of announcements
    * Unhinge the database for these queries?
	* Once in prod push to pypi
    * Must fix problem when performing statistics on inverted results
        * Turns out that the extrapolation inverse results table has zero entries if it keeps all of it's announcements recieved. This is a problem because we do not perform statistics on these.
        * Probably doesn't affect normally - only when running smaller subsets
## API Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#api-short-description)
   * [Usage](#api-usage)
   * [Design Choices](#api-design-choices)
   * [Possible Future Improvements](#api-possible-future-improvements)

Status: Development
### API Short Description
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)
The API includes endpoints for:
	* Every variation of hijack data
	* ROAs data
	* Relationship data for specific ASNs
	* Extrapolator data for specific ASNs
	* Policy statistics for specific ASNs and policies
		* Includes aggregate averages for ASNs
	* Average policy statistics
	* RPKI Validity results

NOTE: These might still not yet be up on the website, in order to be compatible with the UI it takes a bit longer

I could go into further details here, but it seems silly to write documentation twice, and there are flasgger docs and explanations in each file for each endpoint. To see examples of output and explanations, go to the usage examples and see the flasgger documentation.

### API Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)
To view the API and use it, go to localhost:5000/api_docs in a web browser.

To create and run the API on localhost:5000:
(NOTE: This method should not be used in production)
#### In a Script
```python
from lib_bgp_data import create_app
create_app()
```
#### From the Command Line
Coming soon to a theater near you
### API Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)
	* Some API endpoints are not done for all ASes in advance because it would take a significant amount of time and add a significant amount of data.
	* Flasgger docs are used to provide an easy web interface
	* All relationship data was not returned due to time constraints
	* Separate blueprints are used for code readability

### API Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Have better logging - record all queries and alert all errors
	* Convert all stubs to parent ASNs at once
	* Add cmd line args
	* Add unit tests
	* Update docs about cmd line args and unit tests
	* Move the API to the sidr website
	* Add documentation on how to add a new API endpoint
	* Add api endpoints for not hijacked but blocked
	* Create indexes for api stuff and record and have a list of them
	* Add historical data
	* Once in prod push to pypi

## ROVPP Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rovpp-short-description)
   * [Long Description](#rovpp-long-description)
   * [Usage](#rovppusage)
   * [Table Schema](#rovpp-table-schema)
   * [Design Choices](#rovpp-design-choices)
   * [Possible Future Improvements](#rovpp-possible-future-improvements)

Status: Development
### ROVPP Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)

This module was created to simulate ROV++ over the topology of the internet for a hotnets paper. Due to numerous major last minute changes hardcoding was necessary to meet the deadline, and this submodule quickly became a mess. Hopefully we will revisit this and make it into a much better test automation script once we know how we want to run our tests. Due to this, I am not going to write documentation on this currently.
### ROVPP Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)


### ROVPP  Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)


#### In a Script
#### From the Command Line
### ROVPP  Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)

* [ROVPP Table Schema](#rovpp-table-schema)
### ROVPP  Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)


### ROVPP Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Aside from rewriting the script:
		* Making multiple tiers of ASNs and percent adoptions
		* geographical adoption
		* Split up results between each tier of ASes
		* Due to new ROVPP policy, must traceback to known AS, blackhole, hijacker, or victim
		* Deadline for paper in january
		* Link to paper here
		* geographical adoption
		* Real data with bgpstream.com
		* unit tests
		* cmd line args
		* take out version metadata
		* add python metadata/headers
		* write documentation
	* Once in prod push to pypi

## Utils
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#utils-description)
   * [Possible Future Improvements](#utils-possible-future-improvements)

Status: Development
### Utils Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)
The utils folder contains a utils file that has many useful functions used across multiple files and submodules.
### Utils Features
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)
Below is a quick list of functions that might be helpful. For more in depth explanations please view the utils file and the functions themselves:
* Pool: A Context manager for multiprocessing pathos pools
* run_parser: A decorator for running the main parser functions that has useful features like deleting files and printing start and end times
* now: Returns current time
* get_default_start: Gets the default start time
* get_default_end: Gets default end time
* set_common_init_args: Sets paths and logger
* download_file: Downloads a file after waiting x seconds
* delete_paths: Deletes anything, dir_path or file_path, or lists of either, that is passed to this function
* clean_paths: Deletes paths and recreates them
* end_parser: Prints end data for parser
* unzip_bz2: Unzips a bz2 file
* write_csv: Writes a csv file
* csv_to_db: Copies a csv into the database
* rows_to_db: Inserts data into a csv and then the database
* get_tags: Gets html tags
* get_json: Gets json with url and headers specified

### Utils Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Possibly move functions that are only used in one file out of the utils folder - find out what these are
	* Refactor - shouldn't need much though
	* Unit tests for some functions
	* Put underscores in front of private variables
	* Write docs on unit tests
	* Once in prod push to pypi

## Config Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#config-submodule-description)
   * [Design Choices](#config-submodule-design-choices)
   * [Possible Future Improvements](#config-submodule-possible-future-improvements)

Status: Development
### Config Submodule Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Config Submodule](#config-submodule)

This module contains a config class that creates and parses a config file. To avoid outdated documentation to see the config format, please view the create_config function in utils/config.py

### Config Submodule Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Config Submodule](#config-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Unit tests
	* Add docs on unit tests
	* Once in prod push to pypi

## Database Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#database-description)
   * [Usage](#database-usage)
   * [Design Choices](#database-design-choices)
   * [Possible Future Improvements](#database-possible-future-improvements)

Status: Development
### Database Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)
This module contains class Database and context manager db_connection

The Database class can interact with a database. It can also be inherited to allow for its functions to be used for specific tables in the database. Other Table classes inherit the database class to be used in utils functions that write data to the database. To do this, the class that inherits the database must be named the table name plus _Table. For more information on how to do this, see the README on how to
add a submodule.

Fucntionality also exists to be able to unhinge and rehinge the database. When the database is unhinged, it becomes as optimized as possible. Checkpointing (writing to disk) is basically disabled, and must be done manually with checkpoints and db restarts. We use this for massive table joins that would otherwise take an extremely long amount of time.

db_connection is used as a context manager to be able to connect to the database, and have the connection close properly upon leaving

### Database Enhancements
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)

Rather than repeat documentation, please view the Install Script to see all sql queries that alter the database. In addition, see the unhinge_db function, for when the database is unhinged. These are extensive lists of sql queries and the reasons why we use them in order to improve database performance.

Note that we NEVER alter the config file for the database. We only ever use the ALTER SYSTEM command so that we can always have the default config to be able to go back to.

### Database  Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


#### In a Script
Initializing the Database using db_connection (which should always be used):


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| table | Database | What gets initialized |
| logger         | ```Thread_Safe_Logger()```     | Logger used to log information |
| clear | ```False``` | Clear table upon initialization. Leave for normal db usage | 
| cursor_factory         | ```RealDictCursor```     | Format for how data is returned                                                                                         |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize Database with default values using db_connection:
```python
from lib_bgp_data import Database, db_connection
with db_connection(Database) as db:
    pass
```                 
To initialize the Database with logger on debug using db_connection:
```python
from logging import DEBUG
from lib_bgp_data import Database, db_connection, Thread_Safe_Logger as Logger
with db_connection(Database, Logger({"stream_level": DEBUG)) as db:
    pass
```
To initialize the Database with a custom cursor factory other than RealDictCursor and custom logging:
```python
from logging import DEBUG
from psycopg2.extras import NamedTupleCursor
from lib_bgp_data import Database, db_connection, Thread_Safe_Logger as Logger
with db_connection(Database,
                   Logger({"stream_level": DEBUG),
                   cursor_factory=NamedTupleCursor) as db:
    pass
```
To get data from a query:
```python
from lib_bgp_data import Database, db_connection
with db_connection(Database) as db:
    data = db.execute("SELECT * FROM my_table WHERE my_val=%s", [1])
```
To execute multiple sql queries at once:
```python
from lib_bgp_data import Database, db_connection
with db_connection(Database) as db:
	sqls = ["SELECT * FROM my_table", "SELECT * FROM my_table2"]
    data = db.multiprocess_execute(sqls)
```
To unhinge/rehinge database (disable writing to disk, then reenable it):
```python
from lib_bgp_data import Database, db_connection
with db_connection(Database) as db:
	db.unhinge_db()
	# do intensive queries
	db.rehinge_db()
```
#### From the Command Line
Coming Soon to a theater near you
### Database Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)
	* RealDictCursor is used as the default cursor factory because it is more OO and using a dictionary is very intuitive.
	* Unlogged tables are used for speed
	* Most safety measures for corruption and logging are disabled to get a speedup since our database is so heavily used with such massive amounts of data

### Database Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Move unhinge and rehinge db to different SQL files
	* Perform unit tests
	* Add cmd line args
	* Add docs on unit tests and cmd line args
	* Fix bare except on line 101
	* Move the _run_sql file from install.py to a utils folder and use it for unhinge and rehinge db along with the delete_files decorator
	* Take away the unhinging thing for db
	* Once in prod push to pypi

### Database Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)

See: [Installation Instructions](#installation-instructions)

## Logging Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#logging-description)
   * [Error Catcher](#error-catcher)
   * [Design Choices](#logging-design-choices)
   * [Possible Future Improvements](#logging-possible-future-improvements)

Status: Development
### Logging Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)
The Logger class used to be the logging class that was used. This class
sets a logging level for printing and for writing to a file. However,
it turns out that the logging module is insanely bad for multithreading.
So insane, that you cannot even import the dang thing without having it
deadlock on you. Crazy, I know. So therefore, I created another logging
class called Thread_Safe_Logger. This class basically emulates a logger
except that it only prints, and never writes to a file. It also never
deadlocks.

There is also a nice decorator called error_catcher. The point of this
was supposed to be to catch any errors that occur and fail nicely with
good debug statements, which is especially useful when multithreading.
However with unit testing, it needs to be able fail really horribly,
so that has become disabled as well. Still, eventually it will be
fixed, so all functions that have self should be contained within the
error catcher.

For an explanation on how logging works:
logging has different levels. If you are below the set logging level,
nothing gets recorded. The levels are, in order top to bottom:

        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        logging.NOTSET

### Error Catcher
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)
A decorator to be used in all class functions that catches errors and fails nicely with good debug information

### Logging Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)
	* Logger class is not used because logging deadlocks just on import
	* Thread_Safe_Logger is used because it does not deadlock
	* error_catcher is used so that functions fail nicely

### Logging Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Fix the error catcher
	* Possibly use the Logger class to log all things in the API?
	* Figure out how to use this class while multithreading
	* Figure out how to exit nicely and not ruin my unit tests
	* Put underscores in front of private vars/funcs
	* Fix to never be printing function that runs func
	* Once in prod push to pypi

## Installation
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Installation Instructions](#installation-instructions)
   * [Postgres Installation](#postgres-instructions)
   * [System Requirements](#system-requirements)
   * [Installation Submodule](#installation-submodule)

Status: Development

### Installation instructions
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)


First you need some dependencies. Run
```bash
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
```
Then install postgres 11 (see [Postgres Installation](#postgres-installation))

If you are on a machine that has SELinux, you are going to need to run this in a python environment. On Ubuntu, the steps are as follows
```bash
sudo apt-get install python3-pip
sudo pip3 install virtualenv 
```

On Redhat the steps can be found here:
[https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/](https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/)
NOTE: If you are installing it on an OS other than ubuntu, I do not think the install script will work. Good luck doing it all manually.

Note: if you are using our machine ahlocal, there are some very weird permission errors. Due to SE Linux and the gateway, etc, sudo cannot access your home directory. I have tried using ```export HOME=/root``` and other solutions to no avail. No one seems to be able to figure it out. No one seems to care either, and I have told the higher ups and coding is the priority. To run this I would install it in a top level directory like /ext and install it by using ```sudo su``` and continuing from there. I'm sure this is not completely secure so hopefully this will get fixed in the future but no one seems to know how to do that lol.

Once you have virtualenv installed, run 
```bash
python3 -m venv env
source ./env/bin/activate
```
You now have a python virtual environment where you do not need sudo to install packages. 
Then, if you are not installing for development, run:
```bash
pip3 install wheel --upgrade
pip3 install lib_bgp_data --upgrade --force
```
This will install the package and all of it's python dependencies.

If you want to install the project for development:
```bash
git clone https://github.com/jfuruness/lib_bgp_data.git
cd lib_bgp_data
pip3 install wheel --upgrade
pip3 install -r requirements.txt --upgrade
python3 setup.py sdist bdist_wheel
python3 setup.py develop --force
```

After this you are going to need a install a couple of other things to be able to use most features. bgscanner, bgpdump, and the extrapolator are all automatically installed and moved to /usr/bin. bgpdump must be installed from source because it has bug fixes that are necessary. The RPKI validator is installed and move to /var/lib.
>bgpscanner manual install link:
>[https://gitlab.com/Isolario/bgpscanner](https://gitlab.com/Isolario/bgpscanner)
>bgpdump manual install link:
>[https://bitbucket.org/ripencc/bgpdump/wiki/Home](https://bitbucket.org/ripencc/bgpdump/wiki/Home)
>extrapolator manual install link:
>[https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)
>RPKI Validator manual install link:
>[https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources](https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources)

To run the automatic install process, make a script called install.py with the script below.
WARNING: THIS WILL OVERWRITE ALL PREVIOUS DB AND OTHER CONFIGURATIONS:
```python
from lib_bgp_data import Install
Install().install()
```
If you have already installed a database and config and don't need a fresh install, do:
```python
from lib_bgp_data import Install
Install().install(fresh_install=False)
```
This will automate the installation process, and from here you should be ready to go.

Note that now that you have installed every part of lib_bgp_data, you can test it if you'd like. You can run:

```pip3 install lib_bgp_data --upgrade --force --install-option test```

to test the install. To test the development package, cd into the root directory and run:

```python3 setup.py develop test```
### Postgres Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)


For this, you are going to need postgres 11. You need this because it allows for parallel query execution, which significantly speeds up processing time. For installing postgres on your machine, see:
Ubuntu Install:
[https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/](https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/)

or redhat install:

[https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/](https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/)

After the database is installed, we are going to need to make a couple of changes. First, we need to start the database. To do this run:
```bash
sudo systemctl start postgresql@11-main.service
# or maybe
sudo systemctl start postgresql
```
To check to see if it is running:
```bash
sudo systemctl status postgresql@11-main.service
# or maybe
sudo systemctl status postgresql
```

### System Requirements
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)

For storage, you are going to want at least 100 GB, probably more, for the database. If you ever want to perform an uninverted extrapolation run, you will need at least 500GB worth of space, maybe more depending on how large the MRT announcements are. My personal recommendation just to be save would be to have 1000GB worth of storage space. And that is just for one run. To do multiple runs, and just in case, I'd have double or triple that, or at some point if you try to add on future extensions, you might be hurting for space.

For the database, an SSD is best. RAID 1 or RAID 10 is the fastest. We are using RAID 1 because who the heck wants to buy 10 SSDs, and data corruption doesn't matter. You might be able to get away without an SSD, but the large majority of every parser, including the extrapolator, is spent writing to the database. So while you might not need an SSD, everything will take much longer.

For the number of cores, the more the merrier. The MRT parser is multithreaded, but more importantly so is the database, and there are some queries we have that are using 8+ threads on our server that take 1-3 hours (specifically when the MRT announcements are joined with the ROAs). Our machine I believe has 12 cores. We've used a VM that had 36 cores, but I don't think postgres ever used more than 8 cores at once, although I could be wrong.

For the amount of RAM, I think this also largely depends on the extrapolator, which needs A LOT of RAM to run. How much, I don't know, that is not part of this package and you should refer to their github here: [https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator). If they don't have it written down perhaps they don't know either. This also matters a lot for the database. We have about 80GB of RAM in our machine, so many massive table joins can be done entirely in RAM, which makes the database a heck of a lot faster. You don't need RAM for the database, but without at least 50GB most joins will have to be written to disk which will slow queries down.


### Installation Submodule
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)
* [Installation Submodule Description](#installation-submodule-description)
* [Installation Submodule Design Choices](#installation-submodule-design-choices)
* [Installation Submodule Possible Future Extensions](#installation-submodule-possible-future-extensions)

#### Installation Submodule Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)


The Install class contains the functionality to create through a script
everything that is needed to be used for the program to run properly.
This is done through a series of steps.

1. Create the config file. This is optional in case a config was created
	* This is handled by the config class
    * The fresh_install arg is by default set to true for a new config
2. Install the new database and database users. This is optional.
    * This is handled by _create_database
    * If a new config is created, a new database will be created
3. Then the database is modified.
    * This is handled by modify_database
    * If unhinged argument is passed postgres won't write to disk
        * All writing to disk must be forced with vaccuum
        * If data isn't written to disk then memory will be leaked
4. Then the extrapolator is installed
    * Handled in the _install_forecast_extrapolator and _install_rovpp_extrapolator function
    * The rov and forecast versions of the extrapolator are isntalled
    * The extrapolators are copied into /usr/bin for later use
5. Then bgpscanner is installed
    * Handled in the _install_bgpscanner function
    * Once it is isntalled it is copied into /usr/bin for later use
6. Then bgpdump is installed
    * Handled in the _install_bpdump function
    * Must be installed from source due to bug fixes
    * Copied to /usr/bin for later use
7. Then the rpki validator is installed
    * Handled in the _install_rpki_validator functions
    * Config files are swapped out for our own
    * Installed in /var/lib
   
#### Installation Submodule Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)
    * Database modifications increase speed
        * Tradeoff is that upon crash corruption occurs
        * These changes are made at a cluster level
            * (Some changes affect all databases)
    * bgpdump must be installed from source due to bug fixes


#### Installation Submodule Possible Future Extensions
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
	* Add test cases
    * Move install scripts to different files, or SQL files, or to their respective submodules
    * I shouldn't have to change lines in the extrapolator to get it to run
    * Add cmd line args
    * Add docs on cmd line args and tests
    * Make install script have less output for different tasks and have this as an option for initing in docs
    * Add to docs how to use your own password for the install script
	* Once in prod push to pypi
## Testing
   * [lib\_bgp\_data](#lib_bgp_data)

Run tests on install by doing:
```pip3 install lib_bgp_data --force --install-option test```
This will install the package, force the command line arguments to be installed, and run the tests
NOTE: You might need sudo to install command line arguments when doing this

You can test the package if in development by moving/cd into the directory where setup.py is located and running:
```python3 setup.py test```

To test a specific submodule, cd into that submodule and run:
```pytest```


## Adding a Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [How to Add a Submodule](#how-to-add-a-submodule)
### How to Add a Submodule
To explain this easier we will look at the roas collector submodule. Do not use this submodule. Instead, copy it and all of it's contents into another directory. If you have access to a bash terminal you can accomplish this by copying doing:
```bash
cp -R roas_collector my_submodule
```
Then you can manipulate this submodule to do what you want. If you want to look at a very simple submodule for another example, the relationships_parser is also fairly straightforward.

Let's first look at the \_\_init\_\_.py file inside this new submodule. For formatting of all python files, I looked it up and the proper way to do it is to have a shebang at the top defining that it is python and that the coding is in utf8, as you can see. Then there is usually a docstring containing all the information you would need about the file. For a normal file someone should be able to read it and obtain a thorough understanding of what's in the file. For the \_\_init\_\_.py file a user should be able to read it and obtain a thorough understanding of the whole submodule. I like to split these docstrings into a series of parts. The first line, as is specified by pep8, is a short description. Then a new line, and then a slightly longer description. Then I like to list out the steps that my file will perform. After that there is a design choices section, which should summarize design choices from above. This section is important because you can clearly detail why certain decisions where made for future users. There is also a future extensions section, which should contain all possible future work for the current file, or, in the case of the \_\_init\_\_.py file, all the future work for the current submodule. Then we are going to include some python headers with some metadata. This data should be kept up to date, and make sure to give credit where credit is due. Another thing, for the love of god please make your files pep8 compliant. There are numerous tools to do this automatically that exist for many different text editors.

If you are not familiar with the \_\_init\_\_.py file, this is a file in python that the package manager will look at to determine what is inside of a folder. That is a very short explanation, a much better explanation can be found at:
google.com
just kidding lol.  I thought I had a good tutorial but I couldn't find it. However, some of this python code is not basic stuff, if you are ever confused I suggest searching the problem with "Corey Shafer" on youtube, his tutorials are usually pretty good.
All classes, functions, etc. that will be used outside of your submodule should be imported in \_\_init\_\_.py . Similar import statements should again occur at the top level \_\_init\_\_.py file. Only the programs that are in the top level \_\_init\_\_.py file can be easily accessed in a script. Also notice how my submodule name, my file in the submodule that contains the most important class required to run that will be imported above, and the class that will be imported to upper level folders are almost all the same name. This will let a user know what the main files are in a program.

Before you continue, you should try to get your new submodule to run. Make sure that you have imported it correctly in both the \_\_init\_\_.py file that is located within your submodules folder, and also the \_\_init\_\_.py file located in the folder above. Then try to import it from lib_bgp_data in a script and run it. Note that to get the traceback from errors, you should pass in as an argument to the initialization of your class {"stream_level": logging.DEBUG}. Good luck! Let me know if you have any problems!

Now lets take a look at the roas_collector. Aside from the stuff at the top which is similar to the \_\_init\_\_.py file, the imports are very different. You'll notice that normal packages import normally, such as the re function. To import classes from files outside of your current folder (in the folder above) you need to do 
```python
from ..<above folder> import <stuff you want to import>
```
You can see this as an example in the line:
```python
from ..utils import utils, error_catcher, db_connection
```
This imports the utils file, error_catcher, and db_connection from the utils folder, which is outside of our current folder. To import classes and other things from the current folder, do the same as above but with one less period. Example below.
```python
from .tables import ROAs_Table
```
After that we have the class. Notice all the docstrings and comments throughout the code. If the information is included in the docstring at the top of the file, just say for a more in depth explanation refer to the top of the file. Also notice the use of \_\_slots\_\_. This is not required, but turns the class almost like into a named tuple. Attributes that are not included in the \_\_slots\_\_ cannot be added. It decreases the reference time for a value significantly, I think by about a third. You probably won't need this, and it can cause lots of errors if you don't understand it, so probably just delete it.

In the \_\_init\_\_ method the utils.set_common_init_args is called. You can view this function in the utils file, but in short this initializes the logger, the path for files, and the csv directory. Leaving these as the default is usually fine.

Also notice the @error_catcher decorator. This catches any errors that occur. For a better explanation, view [Error Catcher](#error-catcher). In short, this is a nice convenient way to log errors.

Then we have the parse_roas function. Notice the decorator for the run_parser. This decorator runs the parser, logs all errors, and records the start and end time of the parser.

Inside this function we have a db_connection context manager. This will open a connection to the database with the table specified and also create that table. 

After this function we have a helper functions sign. This is usually if you have a long list of functions, and want to group them somehow. Helper functions just means that they are private. Notice these functions, and all other variables that should be private (hopefully I do that soon, forgot to do all the variables, oops!) have an underscore underneath them. 

Lets take a look at the file tables.py. This file typically contains all the database interactions side of things. All the tables that get generated. The names of these classes are important and are used in the program. The name of the class should be the name of the table followed by _Table. They inherit from a database class. When this class is initialized it connects to the database, and calls the _create_tables function. This function should create whatever table you are trying to create. Another function, clear_table, should be included in whatever class you created. This is the function that is called whenever db_connection is initiated, to drop whatever previous data was there before. For SQL all table names should be hardcoded in. The \_\_slots\_\_ is empty here because it inherits from the database class. The real dict cursor is used to make all return values into a list of dictionaries, to make it easier to use. Note that this is not the most effective memory wise, and other cursor factories should be used if memory consumption is a problem.

There you have it. Please let me know any questions you might have. Take a look at the [Utils](#utils) section for things you may want to use in your submodule.
## Development/Contributing
   * [lib\_bgp\_data](#lib_bgp_data)

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request
6. Email me at jfuruness@gmail.com because idk how to even check those messages

To add your own submodule: [How to Add a Submodule](#how-to-add-a-submodule)

## History
   * [lib\_bgp\_data](#lib_bgp_data)
   * 0.2.2 - Automated full run
   * 0.2.3 - Fixed bugs found in the RPKI Validator, MRT Parser. Various other bug fixes. Added pytest for roas_collector.

## Credits
   * [lib\_bgp\_data](#lib_bgp_data)

This is a massive python package, and it obviously would not have been possible without lots of help.

First of all, thanks to Comcast for funding such amazing research. It had really been a pleasure working with you guys and this research is yielding some pretty incredible results.

Thanks to Dr. Amir Herzberg and Dr. Bing Wang with all the help for leading the development team and for all of their knowledge on this subject, and for employing me to work on this.

Thanks to Cameron Morris for his help writing the RPKI Validator submodule, and configuring the RPKI Validator to run off of our own file. Also thanks for pointing out other bugs throughout development. And pulling numerous all nighters with me to push for getting the forecast up and running for deadlines for demonstrations. Definitely MVP.

Thanks to James for looking into the mrt_w_roas join duplication bug and the numerous bugs that were discovered in Caida's API, and communicating with them and debugging some SQL queries

Thanks to Luke Malinowski for help in debugging some SQL queries.

Thanks to Reynaldo Morris for his help for showing me how to configure the API to use flasgger docs and writing the first YAML file. Thanks also for writing the first draft of the traceback function used in the ROVPP submodule.

Thanks to Cameron, Reynaldo, and James for connecting the API to the website

There is also all  of the tools that we use:
Thanks to the bgpscanner team. The tool is amazing, it is much faster than bgpdump. They also helped me out to modify their script, and were very responsive to emails.
[https://gitlab.com/Isolario/bgpscanner](https://gitlab.com/Isolario/bgpscanner)

Thanks to the people behind the RPKI Validator. It is an extremely useful and fast tool.
[https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources](https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources)

Thanks to the people behind bgpdump. This tool was what we originally used and has had consistent updates. 
[https://bitbucket.org/ripencc/bgpdump/wiki/Home](https://bitbucket.org/ripencc/bgpdump/wiki/Home)

Thanks to Caida for their MRT and Relationship data, which is extremely useful:
[http://www.caida.org/home/](http://www.caida.org/home/)

Thanks to ISOlario for their MRT data, which we have not yet integrated but will soon:
[https://www.isolar.io/](https://www.isolar.io/)

Thanks to bgpstream.com for their information on hijackings:
[https://bgpstream.com/](https://bgpstream.com/)

Thanks to the amazing team behind the extrapolator:
[https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)

Thanks to all of these blogs, stack overflow posts, etc. for their help in solving various issues:
* https://stackoverflow.com/a/28822227
* https://unix.stackexchange.com/questions/145402/
* https://github.com/uqfoundation/pathos/issues/111
* https://www.2ndquadrant.com/en/blog/
* https://www.postgresql.org/docs/current/
* https://dba.stackexchange.com/a/18486
* https://severalnines.com/blog/
* https://www.postgresql.org/docs/9.1/runtime-config-resource.html
* https://stackoverflow.com/questions/21127360/
* https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/
* https://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script/1321345#1321345
* https://stackoverflow.com/questions/14441955/how-to-perform-custom-build-steps-in-setup-py
* [https://stackoverflow.com/questions/6943208/](https://stackoverflow.com/questions/6943208/)
* [https://stackoverflow.com/a/20691431](https://stackoverflow.com/a/20691431)
* https://www.geeksforgeeks.org/python-difference-between-two-dates-in-minutes-using-datetime-timedelta-method/
* 

## License
   * [lib\_bgp\_data](#lib_bgp_data)

MIT License

## TODO/Possible Future Improvements
   * [lib\_bgp\_data](#lib_bgp_data)

Working on at the moment:
* ROVPP project
* Game theory economics paper
* Time heuristic
* Caida relationship improvements
* Verification if necessary
* Unit tests
* Email Tony when big submodules are stable
	* Offer assistance when installing


* Configure database on website server to be faster

Medium Term:
* [Forecast TODO](#forecast-possible-future-improvements)
* [MRT Submodule TODO](#mrt-announcements-possible-future-improvements)
* [Relationships Submodule TODO](#relationships-possible-future-improvements)
* [ROAs Submodule TODO](#roas-possible-future-improvements)
* [Extrapolator Submodule TODO](#extrapolator-possible-future-improvements)
* [BGPStream Website Submodule TODO](#bgpstream-website-possible-future-improvements)
* [RPKI Validator Submodule TODO](#rpki-validator-possible-future-improvements)
* [What If Analysis Submodule TODO](#what-if-analysis-possible-future-improvements)
* [API Submodule TODO](#api-possible-future-improvements)
* [ROVPP Submodule TODO](#rovpp-possible-future-improvements)
* [Utils TODO](#utils-possible-future-improvements)
* [Config TODO](#config-submodule-possible-future-improvements)
* [Database TODO](#database-possible-future-improvements)
* [Logging TODO](#logging-possible-future-improvements)
* [Installation Submodule TODO](#installation-submodule-possible-future-extensions)
* Add the simple time heuristic
* Add \_\_slots\_\_ if they do not exist in certain classes
* Change all SQL queries to use string formatting to be more dynamic
* Format all SQL queries properly
* Make readme an html page or something with dropdowns for easier use
* time heuristic
* optimizations
	* Only include prefixes that are hijacked or invalid
	* Use this to run bgp forecaster
	* create extra columns (covered and not covered by roas)
	* Non roas: successful hijacks and 
* Message limit has been reached in slack - make a tool to delete messages using api and get everyone to delete all old messages but say last couple of hundred
* Change everything that has ```__eq__(self, other)``` to have: ```return isinstance(other, self.__class__) and self.a == other.a and self.b == other.b```
* See if can utilize mydict.get(1) to mydict.get(1, something else)
* Look into parser class that has an init to replace inits
	* Move some stuff from utils into this?
* include in docs legacy funcs such as rpki val and bgpdump (user for test cases)
* Update docs to pull ripe data closer to current time
* New source of MRT Announcements (inherit from mrt parser)

Long term:
* Automate a script to dump tables that the API uses to the forecast website server
	* Add indexes on all of these tables for the API
* Add a chron job and run this everyday
* Add ability to have multiple days worth of data
* Email statistics automatically?
* For each part modify the work mem and other db confs
* Add history generator to the massive package
* Have a graph viz func that would return an AS and all of it's peers, customers, and providers, and all of their peers, customers, and providers out to a certain level
* Potentially make other submodules for relationship data for the different sources, and compare them to Cadia?
	* Write a paper about this?
* Check out [https://github.com/FORTH-ICS-INSPIRE/artemis](https://github.com/FORTH-ICS-INSPIRE/artemis)
	* Possible alternate source of hiajcks?
	* Reynaldo took a look and said it uses bgpstream.com
* Another graphviz script for propogation visualizations for extrapolator or rovpp?
* Fix BGP leaks problem and publish a paper on this
	* incentivized due to more customers wanting your AS
* Fix origin hijackings and publish a paper on this
	* Path end validation - read Dr. Herzbergs paper
* Extend forecast project to be for all announcements
* Deep learning with bgp leaks and everything else?
	* Not sure if this makes sense since this would be opaque
* Publish a paper on statistical analysis on the selection of nodes for the deployment of ROV, etc.
	* Revisit old works and perform statistical analysis on them
	* 75% of the nodes are transit nodes
	* Should be selected in such a way to have little variance for less testing
	* Determing the weightings on each kind of as (num peers, customers, providers, overall connectivity, etc)
* Extend forecast to run on updates?
	* incrimental updates for the mrt parser and why we decided not to do it – about 60k announcements per update vs 5 million for rib. that’s 80x speedup but cannot do in parallel – that’s now a 7x speedup – but if we consider that it must only take the thing where certain things equal other things, then it becomes negligable. However, the rest of our code must run this way.
## FAQ
   * [lib\_bgp\_data](#lib_bgp_data)

Q: What? WHAT???

A: Read these, and become more confused:
* [https://www.cs.bu.edu/~goldbe/papers/survey.pdf](https://www.cs.bu.edu/~goldbe/papers/survey.pdf)
* [https://www.nsf.gov/awardsearch/showAward?AWD_ID=1840041&HistoricalAwards=false](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1840041&HistoricalAwards=false)
	* Feel free to email Dr. Amir Herzberg for this paper
* [https://www.cs.princeton.edu/~jrex/papers/sigmetrics00.pdf](https://www.cs.princeton.edu/~jrex/papers/sigmetrics00.pdf)
* [https://www.ideals.illinois.edu/bitstream/handle/2142/103896/Deployable%20Internet%20Routing%20Security%20-%20Trusted%20CI%20Webinar.pdf?sequence=2&isAllowed=y](https://www.ideals.illinois.edu/bitstream/handle/2142/103896/Deployable%20Internet%20Routing%20Security%20-%20Trusted%20CI%20Webinar.pdf?sequence=2&isAllowed=y)
* RPKI/ROV Forecast web proposal - email Dr. Amir Herzberg for this paper
* ROVPP Hotnets paper: email Dr. Amir Herzberg for this paper

Q: What is the fastest way to dump these tables?

A: ```pgdump bgp | pigz -p <numthreads> > jdump.sql.gz``` I have tested all of the different possibilities, and this is the fastest for dumping and reuploading for our tables. Note that indexes do not get dumped and must be recreated.
