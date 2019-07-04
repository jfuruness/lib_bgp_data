
# lib\_bgp\_data
This package contains multiple submodules that are used to gather and manipulate real data in order to simulate snapshots of the internet. The purpose of this is to test different security policies to determine their accuracy, and hopefully find ones that will create a safer, more secure, internet as we know it.

* [lib\_bgp\_data](#lib_bgp_data)
* [Description](#package-description)
* [Main Submodule](#main-submodule)
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
* [Database](#database-submodule)
* [Logging](#logging-submodule)
* [Installation](#installation)
* [Adding a Submodule](#adding-a-submodule)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
* [FAQ](#faq)
## Package Description
* [lib\_bgp\_data](#lib_bgp_data)
This README is split up into several subsections for each of the submodules included in this package. Each subsection has it's own descriptions, usage instructions, etc. The main (LINK HERE) subsection details how all of the submodules combine to completely simulate the internet. For an overall view of how the project will work, see below:

**![](https://docs.google.com/drawings/u/0/d/sx3R9HBevCu5KN2luxDuOzw/image?w=864&h=650&rev=1621&ac=1&parent=1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc)**
Picture link: https://docs.google.com/document/d/1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc/edit?usp=sharing

Please note: These steps are not necessarily linear, as much of this is done in parallel as possible. For more details please view the [Main Submodule](#main-submodule)
1. The project first starts by using the [MRT Parser](#mrt-announcements-submodule) to collect all announcements sent over the internet for a specific time interval. 
2. The [Roas Parser](#roas-submodule) also downloads all the roas for that time interval.
3. A new table is formed with all mrt announcements that have roas. 
4. The relationships data [Relationships Parser](#relationships-submodule) is also gathered in order to be able to simulate the connections between different AS's on the internet. 
5. Each of these data sets gets fed into the [Extrapolator](#extrapolator-submodule) which then creates a graph of the internet and propagates announcements through it. After this stage is complete, there is a graph of the internet, with each AS having all of it's announcements that was propagated to it (with the best announcement for each prefix saved based on gao rexford).
6. At this point we also run the [RPKI Validator](#rpki-validator-submodule), to get the validity of these announcements. With this data we can know whether an announcement that arrived at a particular AS (from the [Extrapolator](#extrapolator-submodule) and whether or not that announcement would have been blocked by standard ROV. 
7. We also download all data from bgpstream.com with the [BGPStream Website Parser](#bgpstream-website-submodule). Using this data we can know whether an announcement is actually hijacked or not.
8.  Using the bgpstream.com data from the [BGPStream Website Parser](#bgpstream-website-submodule) and the [RPKI Validator](#rpki-validator-submodule) data we can tell is an announcement would have been blocked or not, and whether or not that announcement would have been blocked correctly. This calculation is done in the last submodule, the [What if Analysis](#what-if-analysis-submodule). The output of this data is for each as, a table of how many announcements have been blocked correctly, blocked incorrectly, not blocked correctly, and not blocked incorrectly.
9. the [What if Analysis](#what-if-analysis-submodule) data as well as the [Extrapolator](#extrapolator-submodule) data is then available to query form a web interface through the [API](#api-submodule), the last last submodule. All of these steps are done in the submodule called [Main](#main-submodule), in which many of these steps are done in parallel for efficiency. These results are then displayed on our website at [https://bgpforecast.uconn.edu/](https://bgpforecast.uconn.edu/)

## Main Submodule
* [lib\_bgp\_data](#lib_bgp_data)
* [Short Description](#main-short-description)
* [Long Description](#main-long-description)
* [Usage](#main-usage)
* [Table Schema](#main-table-schema)
* [Design Choices](#main-design-choices)
* [Possible Future Improvements](#main-possible-future-improvements)
### Main Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
### Main Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
-make sure to include about how much time each one takes, and how bgpstream.com takes a lot longer the first run through but then afterwards is extremely fast
### Main Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
#### In a Script
#### From the Command Line
### Main Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
### Main Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
### Main Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Main Submodule](#main-submodule)
## MRT Announcements Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#mrt-announcements-short-description)
   * [Long Description](#mrt-announcements-long-description)
   * [Usage](#mrt-announcements-usage)
   * [Table Schema](#mrt-announcements-table-schema)
   * [Design Choices](#mrt-announcements-design-choices)
   * [Possible Future Improvements](#mrt-announcements-possible-future-improvements)
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
                         api_param_mods={"collector": "route-views2",
                                         "types": ['ribs']})
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

* This table contains information on the MRT Announcements retrieved from the https://bgpstream.caida.org/broker/data
* Unlogged tables are used for speed
* prefix: The prefix of an AS *(CIDR)*
* as\_path: An array of all the AS numbers in the AS Path (*bigint ARRAY)*
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

* Add functionality to download and parse updates?
    * This would allow for a longer time interval
    * After the first dump it is assumed this would be faster?
    * Would need to make sure that all updates are gathered, not just the first in the time interval to the api, as is the norm
* Test again for different thread numbers now that bgpscanner is used
* Test different regex parsers other than sed for speed?
* Add test cases
## Relationships Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#relationships-short-description)
   * [Long Description](#relationships-long-description)
   * [Usage](#relationships-usage)
   * [Table Schema](#relationships-table-schema)
   * [Design Choices](#relationships-design-choices)
   * [Possible Future Improvements](#relationships-possible-future-improvements)
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
* Add test cases
* Possibly take out date checking for cleaner code?
    * Saves very little time
* Move unzip_bz2 to this file? Nothing else uses it anymore
* Possibly change the name of the table to provider_customers
    * That is the order the data is in, it is like that in all files

## Roas Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#roas-short-description)
   * [Long Description](#roas-long-description)
   * [Usage](#roas-usage)
   * [Table Schema](#roas-table-schema)
   * [Design Choices](#roas-design-choices)
   * [Possible Future Improvements](#roas-possible-future-improvements)
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
> The default params for the Roas Collector are:
> name = self.\_\_class\_\_.\_\_name\_\_  # The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers.
> path = "/tmp/bgp_{}".format(name)  # This is for the roa files
> CSV directory = "/dev/shm/bgp_{}".format(name) # Path for CSV files, located in RAM
> logging stream level = logging.INFO  # Logging level for printing
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
Coming Soon to a theater near you
#### From the Command Line
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
* Add test cases
## Extrapolator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Extrapolator Short Description](#extrapolator-short-description)
   * [Long Description](#extrapolator-long-description)
   * [Usage](#extrapolator-usage)
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
(coming soon)
To run the rovpp extrapolator:
> The params for the rovpp extrapolator function are:
> attacker_asn: The asn of the attacker
> victim_asn: The asn of the victim
> victim_prefix: This is misleading and should really be fixed in the extrapolator. This is the attackers prefix.

To initialize Extrapolator and run the rovpp version:
```python
from lib_bgp_data import Extrapolator
Extrapolator().run_rovpp(attacker_asn, victim_asn, more_specific_prefix)
```                                                            
## BGPStream Website Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#bgpstream-website-short-description)
   * [Long Description](#bgpstream-website-long-description)
   * [Usage](#bgpstream-website-usage)
   * [Table Schema](#bgpstream-website-table-schema)
   * [Design Choices](#bgpstream-website-design-choices)
   * [Possible Future Improvements](#bgpstream-website-possible-future-improvements)
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
| path         | ```"/tmp/bgp_{}".format(name)```     | This is for the mrt files                                                                                         |
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
from lib_bgp_data import MRT_Parser
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
MRT_Parser().parse_files(start=1558974033,
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
* Add test cases
* Request of make bgpstream.com an api for faster request time?
    * It would cause less querying to their site
* Multithread the first hundred results?
    * If we only parse new info this is the common case
## RPKI Validator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rpki-validator-short-description)
   * [Long Description](#rpki-validator-long-description)
   * [Usage](#rpki-validator-usage)
   * [Table Schema](#rpki-validator-table-schema)
   * [Design Choices](#rpki-validator-design-choices)
   * [Possible Future Improvements](#rpki-validator-possible-future-improvements)
### RPKI Validator Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


### RPKI Validator Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


### RPKI Validator Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


#### In a Script
#### From the Command Line
### RPKI Validator Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


### RPKI Validator Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


### RPKI Validator Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)


## What if Analysis Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#what-if-analysis-short-description)
   * [Long Description](#what-if-analysis-long-description)
   * [Usage](#what-if-analysis-usage)
   * [Table Schema](#what-if-analysis-table-schema)
   * [Design Choices](#what-if-analysis-design-choices)
   * [Possible Future Improvements](#what-if-analysis-possible-future-improvements)
### What if Analysis  Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)


### What if Analysis  Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)


### What if Analysis  Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)


#### In a Script
#### From the Command Line
### What if Analysis  Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)

* [What if Analysis Table Schema](#what-if-analysis-table-schema)
### What if Analysis  Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)


### What if Analysis  Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [What if Analysis Submodule](#what-if-analysis-submodule)


## API Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#api-short-description)
   * [Long Description](#api-long-description)
   * [Usage](#api-usage)
   * [JSON Format](#api-json-format)
   * [Design Choices](#api-design-choices)
   * [Possible Future Improvements](#api-possible-future-improvements)
### API Short Description
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


### API Long Description
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


### API Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


#### In a Script
#### From the Command Line
### API JSON Format
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


### API Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


### API Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [API Submodule](#api-submodule)


## ROVPP Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rovpp-short-description)
   * [Long Description](#rovpp-long-description)
   * [Usage](#rovppusage)
   * [Table Schema](#rovpp-table-schema)
   * [Design Choices](#rovpp-design-choices)
   * [Possible Future Improvements](#rovpp-possible-future-improvements)
### ROVPP Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)

This module was created to simulate ROV++ over the topology of the internet for a hotnets paper. Due to numerous major last minute changes hardcoding was necessary to meet the deadline, and this submodule quickly turned into garbage. Hopefully we will revisit this and make it into a much better test automation script once we know how we want to run our tests. Due to this, I am not going to write documentation on this currently.
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


### ROVPP  Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [ROVPP Submodule](#rovpp-submodule)


## Utils
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#utils-description)
   * [Design Choices](#utils-design-choices)
   * [Possible Future Improvements](#utils-possible-future-improvements)
### Utils Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)

### Utils Features
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)


### Utils Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)


### Utils Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Utils](#utils)


## Database Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#database-description)
   * [Usage](#database-usage)
   * [Design Choices](#database-design-choices)
   * [Possible Future Improvements](#database-possible-future-improvements)
### Database Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


### Database Enhancements
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


### Database  Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


#### In a Script
#### From the Command Line
### Database Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


unlogged tables
### Database Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


### Database Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


PUT LINK HERE TO DB INSTALL INSTRUCTIONS BELOW!!
## Logging Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#logging-description)
   * [Error Catcher](#error-catcher)
   * [Design Choices](#logging-design-choices)
   * [Possible Future Improvements](#logging-possible-future-improvements)
### Logging Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)


### Error Catcher
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)


### Logging Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)


### Logging Possible Future Improvements
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)


## Installation
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Installation Instructions](#installation-instructions)
   * [Postgres Installation](#postgres-instructions)
   * [System Requirements](#system-requirements)
   * [Installation Class Details](#installation-class-details)
### Installation instructions
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


First you need some dependencies. Run
```bash
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
```
Then install postgres 11 (see [Postgres Installation](#postgres-installation)

If you are on a machine that has SELinux, you are going to need to run this in a python environment. On Ubuntu, the steps are as follows
```bash
sudo apt-get install python3-pip
sudo pip3 install virtualenv 
```

On Redhat the steps can be found here:
[https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/](https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/)

Once you have virtualenv installed, run 
```bash
python3 -m venv env
source ./env/bin/activate
```
You now have a python virtual environment where you do not need sudo to install packages. Then run:
```bash
pip3 install wheel --upgrade
pip3 install lib_bgp_data --upgrade
```
This will install the package and all of it's python dependencies. 

If you want to install the project for development:
```bash
git clone https://github.com/jfuruness/lib_bgp_data.git
cd lib_bgp_data
pip3 install wheel --upgrade
pip3 install -r requirements.txt --upgrade
python3 setup.py sdist bdist_wheel
python3 setup.py develop
```

After this you are going to need a install a couple of other things. bgscanner, bgpdump, and the extrapolator are all automatically installed and moved to /usr/bin. bgpdump must be installed from source because it has bug fixes that are necessary. The RPKI validator (for now) must be manually installed.
>bgpscanner manual install link:
>[https://gitlab.com/Isolario/bgpscanner](https://gitlab.com/Isolario/bgpscanner)
>bgpdump manual install link:
>[https://bitbucket.org/ripencc/bgpdump/wiki/Home](https://bitbucket.org/ripencc/bgpdump/wiki/Home)
>extrapolator manual install link:
>[https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)

To run the automatic install process, make a script called install.py with:
```python
from lib_bgp_data import Install, MRT_Parser
Install().install()
```
If you have already installed a database and config and don't need a fresh install, do:
```python
from lib_bgp_data import Install, MRT_Parser
Install().install(fresh_install=False)
```
This will automate the installation process, and from here you should be ready to go
### Postgres Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


For this, you are going to need postgres 11. You need this because it allows for parallel query execution, which significantly speeds up processing time. For installing postgres on your machine, see:
Ubuntu Install:
[https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/](https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/)

or redhat install:

[https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/](https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/)

After the database is installed, we are going to need to make a couple of changes. First, we need to start the database. To do this run:
```bash
sudo systemctl start postgresql@11-main.service
```
To check to see if it is running:
```bash
sudo systemctl status postgresql@11-main.service
```

### RPKI Validator Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


### System Requirements
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


### Installation Class Details
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


#### Installation Class Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


#### Installation Class Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


#### Installation Class Future Extensions
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Submodule](#installation-submodule)


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
   add note here about how to add a submodule and stuff
## History
   * [lib\_bgp\_data](#lib_bgp_data)
## Credits
   * [lib\_bgp\_data](#lib_bgp_data)
    Make sure to credit everyone in the files, profs, stack overflow posts, and bgpscaner team for helping out
## License
   * [lib\_bgp\_data](#lib_bgp_data)
## TODO/Possible Future Improvements
   * [lib\_bgp\_data](#lib_bgp_data)
command line args
automate the database installation process
remove all in person crap like we from the readme you idjiout
(if something is from a submodule, post a link to that specific possible future improvements? say that this is a summary of stuff?)
## FAQ
   * [lib\_bgp\_data](#lib_bgp_data)
