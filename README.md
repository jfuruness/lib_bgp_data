
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
* [Utils](#utils)
* [Database](#database-submodule)
* [Logging](#logging-submodule)
* [Installation](#installation)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
* [FAQ](#faq)
## Package Description
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
   * [Short Description](#main-short-description)
   * [Long Description](#main-long-description)
   * [Usage](#main-usage)
   * [Table Schema](#main-table-schema)
   * [Design Choices](#main-design-choices)
   * [Possible Future Improvements](#main-possible-future-improvements)
### Main Short description
### Main Long description
### Main Usage
#### In a Script
#### From the Command Line
### Main Table Schema
### Main Design Choices
### Main Possible Future Improvements
## MRT Announcements Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#mrt-announcements-short-description)
   * [Long Description](#mrt-announcements-long-description)
   * [Usage](#mrt-announcements-usage)
   * [Table Schema](#mrt-announcements-table-schema)
   * [Design Choices](#mrt-announcements-design-choices)
   * [Possible Future Improvements](#mrt-announcements-possible-future-improvements)
### MRT Announcements Short description
The purpose of this submodule is to parse MRT files received from https://bgpstream.caida.org/broker/data using bgpscanner to obtain the prefix, origin, time, and AS path, and insert this information into the database.
### MRT Announcements Long description
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
    * bgpscanner is used to parse files because it is the fastest
    * BGP dump scanner for testing
        * By default bgpdump is used because bgpscanner ignores malformed attributes, which AS's should ignore but not all do
        * This is a small portion of announcements, so we ignore them for tests but not for simulations, which is why we use bgpdump for full runs
    * Announcements with malformed attributes are ignored
    * sed is used because it is cross compatible and fast
        * Must use regex parser that can find/replace for array format
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
MRT_Parser().parse_files({"start": 1558974033,
                          "end": 1558974033})
```
To run the MRT Parser with specific time intervals and custom api parameters:

See: [https://bgpstream.caida.org/docs/api/broker](https://bgpstream.caida.org/docs/api/broker) for full listof API Parameters. Note that these params are only added to a dictionary of:
 {'human': True,  'intervals': ["{},{}".format(start, end)]}
In this example we get all RIB files from a specific collector, route-views2
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files({"start": 1558974033,
                          "end": 1558974033,
                          "api_param_mods": {"collector": "route-views2",
                                             "types": ['ribs']}})
```
To run the MRT Parser with specific time intervals and bgpdump:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files({"start": 1558974033,
                          "end": 1558974033,
                          "bgpscanner": False})
```

To run the MRT Parser with specific time intervals and IPV4 and IPV6 data:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files({"start": 1558974033,
                          "end": 1558974033,
                          "IPV4": True,
                          "IPV6": True})
```
To run the MRT Parser with specific time intervals and different number of threads:
```python
from multiprocessing import cpu_count
from lib_bgp_data import MRT_Parser
MRT_Parser().parse_files({"start": 1558974033,
                          "end": 1558974033,
                          "download_threads": cpu_count(),
                          "parse_threads": cpu_count()/4})
```
#### From the Command Line
Coming Soon to a theater near you
### MRT Announcements Table Schema
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
* We only want the first BGP dump
    * Multiple dumps have conflicting announcements
    * Instead, for longer intervals use one BGP dump and updates
* Due to I/O bound downloading:
    * Multithreading is used over multiprocessing for less memory
    * Four times CPUs is used for thread count
* I have a misquito bite that is quite large.
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
* bgpscanner is the fastest BGP dump scanner so it is used for tests
* bgpscanner ignores announcements with malformed attributes
* bgpdump is used for full runs because it does not ignore announcements with malformed attributes, which some ASs don't ignore
* sed is used for regex parsing because it is fast and portable
### MRT Announcements Possible Future Improvements
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
### Relationships Long description
### Relationships Usage
#### In a Script
#### From the Command Line
### Relationships Table Schema
### Relationships Design Choices
### Relationships Possible Future Improvements
## Roas Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#roas-short-description)
   * [Long Description](#roas-long-description)
   * [Usage](#roas-usage)
   * [Table Schema](#roas-table-schema)
   * [Design Choices](#roas-design-choices)
   * [Possible Future Improvements](#roas-possible-future-improvements)
### Roas Short description
### Roas Long description
### Roas Usage
#### In a Script
#### From the Command Line
### Roas Table Schema
### Roas Design Choices
### Roas Possible Future Improvements
## Extrapolator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Extrapolator Short Description](#extrapolator-short-description)
### Extrapolator Short description
The Extrapolator takes as input mrt announcement data from the [MRT Parser](#mrt-announcements-submodule) and relationships data (peer and customer-provider data) from the [Relationships Parser](#relationships-submodule). The Extrapolator then propagates announcements to all appropriate AS's which would receive them, and outputs this data. 

For more in depth documentation please refer to: [https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)
## BGPStream Website Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#bgpstream-website-short-description)
   * [Long Description](#bgpstream-website-long-description)
   * [Usage](#bgpstream-website-usage)
   * [Table Schema](#bgpstream-website-table-schema)
   * [Design Choices](#bgpstream-website-design-choices)
   * [Possible Future Improvements](#bgpstream-website-possible-future-improvements)
### BGPStream Website Short description
### BGPStream Website Long description
### BGPStream Website Usage
#### In a Script
#### From the Command Line
### BGPStream Website Table Schema
### BGPStream Website Design Choices
### BGPStream Website Possible Future Improvements
## RPKI Validator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rpki-validator-short-description)
   * [Long Description](#rpki-validator-long-description)
   * [Usage](#rpki-validator-usage)
   * [Table Schema](#rpki-validator-table-schema)
   * [Design Choices](#rpki-validator-design-choices)
   * [Possible Future Improvements](#rpki-validator-possible-future-improvements)
### RPKI Validator Short description
### RPKI Validator Long description
### RPKI Validator Usage
#### In a Script
#### From the Command Line
### RPKI Validator Table Schema
### RPKI Validator Design Choices
### RPKI Validator Possible Future Improvements
## What if Analysis Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#what-if-analysis-short-description)
   * [Long Description](#what-if-analysis-long-description)
   * [Usage](#what-if-analysis-usage)
   * [Table Schema](#what-if-analysis-table-schema)
   * [Design Choices](#what-if-analysis-design-choices)
   * [Possible Future Improvements](#what-if-analysis-possible-future-improvements)
### What if Analysis  Short description
### What if Analysis  Long description
### What if Analysis  Usage
#### In a Script
#### From the Command Line
### What if Analysis  Table Schema
### What if Analysis  Design Choices
### What if Analysis  Possible Future Improvements
## API Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#api-short-description)
   * [Long Description](#api-long-description)
   * [Usage](#api-usage)
   * [JSON Format](#api-json-format)
   * [Design Choices](#api-design-choices)
   * [Possible Future Improvements](#api-possible-future-improvements)
### API Short Description
### API Long Description
### API Usage
#### In a Script
#### From the Command Line
### API JSON Format
### API Design Choices
### API Possible Future Improvements
## Utils
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#utils-description)
   * [Design Choices](#utils-design-choices)
   * [Possible Future Improvements](#utils-possible-future-improvements)
### Utils Description
### Utils Design Choices
### Utils Possible Future Improvements
## Database Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#database-description)
   * [Usage](#database-usage)
   * [Design Choices](#database-design-choices)
   * [Possible Future Improvements](#database-possible-future-improvements)
### Database Description
### Database Enhancements
### Database  Usage
#### In a Script
#### From the Command Line
### Database Design Choices
unlogged tables
### Database Possible Future Improvements
### Database Installation
PUT LINK HERE TO DB INSTALL INSTRUCTIONS BELOW!!
## Logging Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#logging-description)
   * [Design Choices](#logging-design-choices)
   * [Possible Future Improvements](#logging-possible-future-improvements)
### Logging Description
### Logging Design Choices
### Logging Possible Future Improvements
## Installation
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Installation Instructions](#installation-instructions)
   * [Postgres Installation](#postgres-instructions)
   * [System Requirements](#system-requirements)
### Installation instructions
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
pip3 install lib_bgp_data
```
This will install the package and all of it's python dependencies. 

If you want to install the project for development:
```bash
git clone https://github.com/jfuruness/lib_bgp_data.git
cd lib_bgp_data
pip3 install -r requirements.txt
python3 setup.py sdist bdist_wheel
python3 setup.py develop
```

After this you are going to need a install a couple of other things. bgscanner, bgpdump, and the extrapolator are all automatically installed and moved to /usr/bin. bgpdump must be installed from source because it has bug fixes that are necessary. The RPKI validator (for now) must be manually installed.

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
### System Requirements
## Development/Contributing
   * [lib\_bgp\_data](#lib_bgp_data)
## History
   * [lib\_bgp\_data](#lib_bgp_data)
## Credits
   * [lib\_bgp\_data](#lib_bgp_data)
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
