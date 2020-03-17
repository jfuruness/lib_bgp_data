# lib\_bgp\_data
This package contains multiple submodules that are used to gather and manipulate real data in order to simulate snapshots of the internet. The purpose of this is to test different security policies to determine their accuracy, and hopefully find ones that will create a safer, more secure, internet as we know it.

*disclaimer: If a submodule is in development, that means that it unit tests are in the process of being written*

* [lib\_bgp\_data](#lib_bgp_data)
* [Description](#package-description)
* Submodules:
    * [Forecast Parser](#forecast-submodule)
    * [Base Parser](#base-parser)
    * [MRT Announcements Parser](#mrt-announcements-submodule)
    * [Relationships Parser](#relationships-submodule)
    * [Roas Parser](#roas-submodule)
    * [Extrapolator Parser](#extrapolator-submodule)
    * [BGPStream Website Parser](#bgpstream-website-submodule)
    * [RPKI Validator Parser](#rpki-validator-submodule)
    * [What if Analysis Parser](#what-if-analysis-submodule)
    * [API Submodule](#api-submodule)
    * [ROVPP Submodule](#rovpp-submodule)
    * [Utils](#utils)
    * [Database](#database-submodule)
    * [Logging](#logging-submodule)
* [Installation](#installation)
* [Testing](#testing)
* [Adding a Submodule](#adding-a-submodule)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [New Hires](#new-hires)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
* [FAQ](#faq)
## Package Description
* [lib\_bgp\_data](#lib_bgp_data)
This README is split up into several subsections for each of the submodules included in this package. Each subsection has it's own descriptions, usage instructions, etc. The [Forecast Submodule](#forecast-submodule) subsection details how all of the submodules combine to completely simulate the internet. For an overall view of how the project will work, see below:

**![](https://docs.google.com/drawings/u/0/d/sx3R9HBevCu5KN2luxDuOzw/image?w=864&h=650&rev=1621&ac=1&parent=1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc)**
Picture link: https://docs.google.com/document/d/1fh9EhU9yX9X4ylwg_K-izE2T7C7CK--X-Vfk1qqd1sc/edit?usp=sharing

If you'd like more of a laymens perspective, see the [FAQ](#faq)

Please note: These steps are not necessarily linear, as much of this is done in parallel as possible. For more details please view the [Forecast Submodule](#forecast-submodule)
1. The project first starts by using the [MRT Parser](#mrt-announcements-submodule). With the two urls listed in the picture, we can access public announcements from specific collectors. Basically it collects all public announcements sent over the internet for a specific time interval. This usually takes around an hour minutes on our machine and results in approximately 67 GB of data.
2. The [Roas Parser](#roas-submodule) also downloads all the ROAs for that time interval. This usually takes a couple of seconds.
3. A new table is formed with all mrt announcements that have ROAs. This join is done by checking whether or not the prefixes of the MRT announcements are a subset of the prefixes in the ROAs table. Because this is an expensive operation, and is done on a 67GB+ table, this takes an hour or two on our machine. The reason we filter these announcements is to reduce the data that we need to go over for faster execution.
4. The relationships data [Relationships Parser](#relationships-submodule) is also gathered in order to be able to simulate the connections between different AS's on the internet. This takes a couple of seconds. From a laymans perspective, this is how the internet is connected.
5. Each of these data sets gets fed into the [Extrapolator](#extrapolator-submodule) which then creates a graph of the internet and propagates announcements through it. From a laymens point of view, we feed in the public announcements, and the relationship data (internet topology). Then, using some algorithms and heuristics that mostly rely on GOA Rexford, we can "guess" with very high accuracy the private traffic of all the ASes that do not have public data. If you don't know what GOA Rexford is please see [FAQ](#faq). After this stage is complete, there is a graph of the internet, with each AS having all of it's announcements that was propagated to it (with the best announcement for each prefix saved based on gao rexford and other heuristics). The [Extrapolator](#extrapolator-submodule) itself takes around 5-6 hours on our machine, and results in a table around 40 GB large.  The reason this table is not larger is because we can invert the results. What does this mean? Well, if you think about it, all announcements should theoretically be everywhere on the internet. So most ASes traffic will be almost the same and will be very large. Instead, we can just save the traffic that did not propogate to that AS, which will result in much smaller tables (since most announcements will be saved). This means that instead of storing the RIB for each AS, which results in a table that is 300GB+ large, we store what is not in the RIB for each AS. This allows us to save space, and it also saves time because joins we do on this table take less time.
6. At this point we also run the [RPKI Validator](#rpki-validator-submodule), to get the validity of these announcements. With this data we can know whether an announcement that arrived at a particular AS (from the [Extrapolator](#extrapolator-submodule) and whether or not that announcement would have been blocked by standard ROV. This usually takes 10-20 minutes.
7. We also download all data from bgpstream.com with the [BGPStream Website Parser](#bgpstream-website-submodule). Using this data we can know whether an announcement is actually hijacked or not. This takes about 20 minutes the first time, and then about 1-5 minutes every time after on our machine. This takes a while because querying the website takes a while.
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
* [Todo and Possible Future Improvements](#todopossible-future-improvements)

NOTE: This submodule is not yet complete, and should not be used


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

## Base Parser
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#base-parser-short-description)
   * [Long Description](#base-parser-long-description)
   * [Usage](#base-parser-usage)
   * [Design Choices](#base-parser-design-choices)

status = development

### Base Parser Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Base Parser](#base-parser)

The purpose of this parser is to template all the other parsers, for faster code writing, and so that others can use the library easier. 

### Base Parser Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [Base Parser](#base-parser)

The purpose of this parser is to template all the other parsers, for faster code writing, and so that others can use the library easier. 

To start with we have \_\_slots\_\_. This is a python way of confining the classes attributes to just those mentioned here, which allows for faster access and imo more readability. 

This class also uses a metaclass called DecoMeta, which decorates all functions within the class and all subclasses to have the error_catcher decorator. This decorator will encapsulate any programming errors and log them properly. 

You'll also notice in the init section we must set the section variable. This is the section from the config file that your code will run in. This controls the database, and other config settings. Basically it is so that multiple people can work on the same machine, and not conflict with one another.

You'll notice that the path and csv directories that are created depend on the name of your class. That is  because we don't want multiple classes conflicting with one another if they are running side by side. In other words, with different names, they will be parsed into different path and csv directories.

Then there is the run function. All parsers should have a _run function, which this function calls. It simply records the time the parser takes to complete, and captures errors nicely. The reason this is enforced is so that the base parser can delete the path and csv directory, no matter what errors occur during the subclass._run method.

The argparse call method isn't something you need to worry about. If you really want to know, that is the method argparse will call when you pass in the name of this class as a command line argument. It is done here so that all parsers have that functionality. By default the run method will be called for the class.

If you were privy to previous versions you may notice that the decorated features were removed. Previously we would use metaclasses to decorate all functions to log errors in a specific way. I decided this was unnecessary since the only time we will ever need this is when we call the run method, for which we already have logging, and overriding the default traceback seems unnecessary. So to avoid complications with logging this was removed. 

Also you do not need to worry about it, but we override the \_\_init\_subclass\_\_ in the Parser class. This is a new method in python 3.6, from which we can control inheritance. With this method we can add all subclasses that inherit the Parser class to a list called parsers, and store it as a class attribute. Later, we use this list in \_\_main\_\_.py to store all the parsers as command line arguments. In this way, anyone that simply inherits the Parser class will automatically have their parser added to the command line arguments.

### Base Parser Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Base Parser](#base-parser)

#### In a Script
To create other parsers, simply inherit this class, and make sure the parser has a _run method (essentially, the main method of the parser).

```python
# Assuming you are in lib_bgp_data.lib_bgp_data.my_new_parser:

from ..base_classes import Parser
class My_New_Parser(Parser):
    # Note that you do not need **kwargs, but you always need self and args
    def _run(self, *args, **kwargs):
        pass  # My function stuff here
```

##### Parser Initialization:
To initialize any parser that inherits this class:

**Please note that for all of these examples - your python env MUST still be activated.**

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
| section | ```"bgp"  ```                      | database section to use                                                                                      |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

**Note that for all examples below, we use the MRT_Parser, but you could do this the same way with any class that inherits the base parser**

NOTE: Later this should be changed in the html, so that whenever someone redirects from another url, that parser will be the default.

To initialize MRT_Parser with default values:
```python
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser()
```

To initialize MRT_Parser with custom path, CSV directory, and logging level, and database section:
```python
from logging import DEBUG
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser(path="/my_custom_path",
                        csv_dir="/my_custom_csv_dir",
                        stream_level=DEBUG,
                        section="mydbsection")
```

To run the MRT Parser with defaults:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run()
```
#### From the Command Line

**Please note that for all of these examples - your python env MUST still be activated.**

There are two ways you can run this parser. It will run with all the defaults. Later in the future it is possible more parameters will be added, but for now this is unnecessary. This will call the run method.

**Note that for all examples below, we use the MRT_Parser, but you could do this the same way with any class that inherits the base parser. Simply change the name of the parser, to be the lowercase version of the class name of your parser.**

Best way:
```bash
lib_bgp_data --mrt_parser
```
For debugging:
```bash
lib_bgp_data --mrt_parser --debug
```


This example must be run over the package, so cd into one directory above that package
```bash
python3 -m lib_bgp_data --mrt_parser
```

### Base Parser Design Choices 
* [lib\_bgp\_data](#lib_bgp_data)
* [Base Parser](#base-parser)

Design choices are explained in the [Long Description](#base-parser-long-description). The template of this class was for easy extendability of this python package. Before without this, it was much harder to create parser classes in a template like fashion.

## MRT Announcements Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#mrt-announcements-short-description)
   * [Long Description](#mrt-announcements-long-description)
   * [Usage](#mrt-announcements-usage)
   * [Table Schema](#mrt-announcements-table-schema)
   * [Design Choices](#mrt-announcements-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)
 
Status: Production

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
2. Get the urls from [https://isolar.io/Isolario_MRT_data/](https://isolar.io/Isolario_MRT_data/)
    * Handled in _get_mrt_urls function
    * By using the custom naming scheme we can get all the MRT files for the relevant time period
3. Then all the mrt files are downloaded in parallel
    * Handled in MRT_Parser class
    * This instantiates the MRT_File class with each url
        * utils.download_file handles downloading each particular file
    * Four times the CPUs is used for thread count since it is I/O bound
        * Mutlithreading with GIL lock is better than multiprocessing since this is just intensive I/O in this case
    * Downloaded first so that we parse the largest files first
    * In this way, more files are parsed in parallel (since the largest files are not left until the end)
4. Then all mrt_files are parsed in parallel
    * Handled in the MRT_Parser class
    * The mrt_files class handles the actual parsing of the files
    * CPUs - 1 is used for thread count since this is a CPU bound process
    * Largest files are parsed first for faster overall parsing
    * bgpscanner is the fastest BGP dump scanner so it is used for tests
    * Note that for our process, bgpscanner is modified to include malformed announcements. We include these because they are present in the actual MRT files so they must be present on the internet
    * bgpdump is kept for unit testing, and is an optional parameter for this step
    * sed is used because it is cross compatible and fast
        * Must use regex parser that can find/replace for array format
        * AS Sets are not parsed because they are unreliable, these are less than .5% of all announcements
6. Parsed information is stored in csv files, and old files are deleted
    * This is handled by the MRT_File class
    * This is done because there is thirty to one hundred gigabytes
        * Fast insertion is needed, and bulk insertion is the fastest
    * CSVs are chosen over binaries even though they are slightly slower
        * CSVs are more portable and don't rely on postgres versions
        * Binary file insertion relies on specific postgres instance
    * Old files are deleted to free up space
7. CSV files are inserted into postgres using COPY, and then deleted
    * This is handled by MRT_File class
    * COPY is used for speedy bulk insertions
    * Files are deleted to save space
    * Duplicates are not deleted because this is an intensive process
        * There are not a lot of duplicates, so it's not worth the time
        * The overall project takes longer if duplicates are deleted
        * A duplicate has the same AS path and prefix
8. VACUUM ANALYZE is then called to analyze the table for statistics
### MRT Announcements Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)

#### In a Script
Initializing the MRT Parser:

**Please note that for all of these examples - your python env MUST still be activated.**


The Defaults for the MRT Parser are the same as the [base parser's](base-parser-usage) it inherits:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
| section | ```"bgp"  ```                      | database section to use                                                                                      |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize MRT_Parser with default values:
```python
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser()
```

To initialize MRT_Parser with custom path, CSV directory, section, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import MRT_Parser
mrt_parser = MRT_Parser(path="/my_custom_path",
                        csv_dir="/my_custom_csv_dir",
                        stream_level=DEBUG,
                        section="mydbsection")
```

Running the MRT Parser:

Note that only the first MRT file is collected between the start and end times

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| start         | ```utils.get_default_start()```     | This is an epoch timestamp specifying the start time for which to collect MRT Files|
| end         | ```utils.get_default_end()```     |This is the end time for which to stop collecting MRT files                                                            |
| api_param_mods      | ```{}``` | Optional parameters to pass to Caida API, should be used when trying to limit input. See [https://bgpstream.caida.org/docs/api/broker#Data-API](https://bgpstream.caida.org/docs/api/broker#Data-API) for all possible parameters, and further usage examples below.                                                                               |
| download_threads | ```None```                        | Number of threads to download files. Later gets changed to cpu_count * 4 since this is mostly an I/O bound process                                                                                       |
| parse_threads | ```None```                        | Number of threads to parse files. Later gets changed to cpu_count. This is because for each thread, a bgpscanner thread, sed thread, csv writing thread are all spawned. Probably should optimize this.                                                                                        |
| IPV4 | ```True```                        | Keep IPV4 prefixes                                                                                        |
| IPV6 | ```False```                        | Keep IPV6 prefixes. False by default since the extrapolator cannot handle them, and discards them anyways.                                                                                        |
| bgpscanner | ```True```                        | Use bgpscanner for parsing. If false uses bgpdump, which is slower and is only used for unit testing                                            |
| Sources | ```MRT_Sources.__members__.values()``` | A list of possible sources for MRT Files to be parsed from. Currently listed at the time of writing are MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS, and MRT_Sources.ISOLARIO. See example usage below if you'd like to exclude some.

> Note that any one of the above attributes can be changed or all of them can be changed in any combination

API params that cannot be changed:

```python
{'human': True,  # This value cannot be changed
'intervals': ["{},{}".format(start, end)],  # This value cannot be changed
'types': ['ribs']
}
```

To run the MRT Parser with defaults:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run()
```
To run the MRT Parser with specific time intervals:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run(start=1558974033, end=1558974033)
```
To run the MRT Parser with custom api parameters:

See: [https://bgpstream.caida.org/docs/api/broker](https://bgpstream.caida.org/docs/api/broker) for full listof API Parameters. Note that these params are only added to a dictionary of:
 {'human': True,  'intervals': ["{},{}".format(start, end)]}
In this example we get all RIB files from a specific collector, route-views2. Note that we will still get all the MRT files from isolario, since we did not exclude them in the sources.
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run(api_param_mods={"collectors[]": ["route-views2", "rrc03"]})
```

To run the MRT Parser with custom api parameters, and exclude Isolario collectors:

See: [https://bgpstream.caida.org/docs/api/broker](https://bgpstream.caida.org/docs/api/broker) for full listof API Parameters. Note that these params are only added to a dictionary of:
 {'human': True,  'intervals': ["{},{}".format(start, end)]}
In this example we get all RIB files from a specific collector, route-views2. We also only include RIPE and ROUTE_VIEWS (Discluding ISOLARIO)

```python
from lib_bgp_data import MRT_Parser, MRT_Sources
MRT_Parser().run(api_param_mods={"collectors[]": ["route-views2", "rrc03"]},
                 sources=[MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS])
```

To run the MRT Parser with specific time intervals and bgpdump (this will be much slower):
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run(start=1558974033,
                 end=1558974033,
                 bgpscanner=False)
```

To run the MRT Parser with specific time intervals and IPV4 and IPV6 data:
```python
from lib_bgp_data import MRT_Parser
MRT_Parser().run(start=1558974033,
                 end=1558974033,
                 IPV4=True,
                 IPV6=True)
```
To run the MRT Parser with specific time intervals and different number of threads:
```python
from multiprocessing import cpu_count
from lib_bgp_data import MRT_Parser
MRT_Parser().run(start=1558974033,
                 end=1558974033,
                 download_threads=cpu_count(),
                 parse_threads=cpu_count()//4)
```
#### From the Command Line

**Please note that for all of these examples - your python env MUST still be activated.**

There are two ways you can run this parser. It will run with all the defaults. Later in the future it is possible more parameters will be added, but for now this is unnecessary.

Best way:
```bash
lib_bgp_data --mrt_parser
```
For debugging:
```bash
lib_bgp_data --mrt_parser --debug
```
This example must be run over the package, so cd into one directory above that package
```bash
python3 -m lib_bgp_data --mrt_parser
```


### MRT Announcements Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [MRT Announcements Submodule](#mrt-announcements-submodule)
    * This table contains information on the MRT    Announcements retrieved from the https://bgpstream.caida.org/broker/data and https://isolar.io/Isolario_MRT_data/
    * Unlogged tables are used for speed
    * prefix: The prefix of an AS *(CIDR)*
    * as\_path: An array of all the AS numbers in the   AS Path (*bigint ARRAY)*
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
    * Instead, for longer intervals use one BGP dump and updates (not yet implimented)
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
* AS Sets are not parsed because they are unreliable, and are only .5% of all announcements

## Relationships Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#relationships-short-description)
   * [Long Description](#relationships-long-description)
   * [Usage](#relationships-usage)
   * [Table Schema](#relationships-table-schema)
   * [Design Choices](#relationships-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

Status: Production

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
    * Handled in _get_urls function
    * This will return the URL of the file that we need to download
    * In that URL we have the date of the file, which is also parsed out
    * The serial 2 data set is used because it has multilateral peering
    * which appears to be the more complete data set
2. Then the Relationships_File class is then instantiated
3. The relationship file is then downloaded
    * This is handled in the utils.download_file function
4. Then the file is unzipped
    * handled by utils _unzip_bz2
5. The relationship file is then split into two
    * Handled in the Relationships_File class
    * This is done because the file contains both peers and customer_provider data.
    * The file itself is a formatted CSV with "|" delimiters
    * Using grep and cut the relationships file is split and formatted
    * This is done instead of regex because it is faster and simpler
6. Then each CSV is inserted into the database
    * The old table gets destroyed first
    * This is handleded in the utils.csv_to_db function
    * This is done because the file comes in CSV format
    * Optionally data can be inserted into ROVPP tables for the ROVPP simulation

### Relationships Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)

#### In a Script

Initializing the Relationships Parser:
The Defaults for the Relationships Parser are:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
| section | ```"bgp"  ```                      | database section to use                                                                                      |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination


To initialize Relationships_Parser with default values:
```python
from lib_bgp_data import Relationships_Parser
relationships_parser = Relationships_Parser()
```                 
To initialize Relationships_Parser with custom path, CSV directory, and logging level and database section:
```python
from logging import DEBUG
from lib_bgp_data import Relationships_Parser
relationships_parser = Relationships_Parser(path="/my_custom_path",
                                            csv_dir="/my_custom_csv_dir",
                                            stream_level=DEBUG.
                                            section="mydatabasesection")
```
Running the Relationships_Parser:

To run the Relationships Parser with defaults:
```python
from lib_bgp_data import Relationships_Parser
Relationships_Parser().run()
```
To run the Relationships Parser for with a specific URL:
```python
from lib_bgp_data import Relationships_Parser
Relationships_Parser().run(url="my_specific_url")
```
#### From the Command Line

**Please note that for all of these examples - your python env MUST still be activated.**

There are two ways you can run this parser. It will run with all the defaults. Later in the future it is possible more parameters will be added, but for now this is unnecessary.

Best way:
```bash
lib_bgp_data --relationships_parser
```
For debugging:
```bash
lib_bgp_data --relationships_parser --debug
```
This example must be run over the package, so cd into one directory above that package
```bash
python3 -m lib_bgp_data --relationships_parser
```

### Relationships Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [Relationships Submodule](#relationships-submodule)
* [providers customer_Table Schema](#provider_customers-table-schema)
* [peers Table Schema](#peers-table-schema)
* [ases Table Schema](#ases-table-schema)
* [as_connectivity Table Schema](#as_connectivity-table-schema)

* These tables contains information on the relationship data retrieved from http://data.caida.org/datasets/as-relationships/serial-2/
* Unlogged tables are used for speed
#### provider_customers Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for customer provider pairs
* provider_as: Provider ASN *(bigint)*
* customer_as: Customer ASN (*bigint)*
* Create Table SQL:
    ```
    CREATE UNLOGGED TABLE IF NOT EXISTS
        provider_customers (
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
#### ASes Table Schema:
* [Relationships Table Schema](#relationships-table-schema)

* Contains data for peer pairs
* asn: An ASN *(bigint)*
* as_type: An AS type to indicate policy it adopts, such as ROV, ROV++, etc. Used for ROV++. Numbers are from an enum called Policies. Numbers are used for faster SQL joins *(bigint)*
* Create Table SQL:
    ```
        CREATE UNLOGGED TABLE IF NOT EXISTS ases AS (
                 SELECT customer_as AS asn, 'bgp' AS as_type,
                    FALSE AS impliment FROM (
                     SELECT DISTINCT customer_as FROM provider_customers
                     UNION SELECT DISTINCT provider_as FROM provider_customers
                     UNION SELECT DISTINCT peer_as_1 FROM peers
                     UNION SELECT DISTINCT peer_as_2 FROM peers) union_temp
                 );
    ```
##### as_connectivity Table Schema:
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

## Roas Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#roas-short-description)
   * [Long Description](#roas-long-description)
   * [Usage](#roas-usage)
   * [Table Schema](#roas-table-schema)
   * [Design Choices](#roas-design-choices)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)

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
Initializing the ROAs_Parser:


| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
| section | ```"bgp"  ```                      | database section to use                                                                                      |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize ROAs_Parser with default values:
```python
from lib_bgp_data import ROAs_Parser
roas_parser = ROAs_Parser()
```                 
To initialize ROAs_Parser with custom path, CSV directory, and logging level and section:
```python
from logging import DEBUG
from lib_bgp_data import ROAs_Parser
roas_parser = ROAs_Parser(path="/my_custom_path",
                          csv_dir="/my_custom_csv_dir",
                          stream_level=DEBUG,
                          section="mydatabasesection")
```
To run the ROAs_Parser with defaults (there are no optional parameters):
```python
from lib_bgp_data import ROAs_Parser
ROAs_Parser().parse_roas()
```

#### From the Command Line
Depending on the permissions of your system, and whether or not you pip installed the package with sudo, you might be able to run the ROAs Parser with:

```lib_bgp_data --roas_parser```

For debugging:
```bash
lib_bgp_data --roas_parser --debug
```
or a variety of other possible commands, I've tried to make it fairly idiot proof with the capitalization and such.

The other way you can run it is with:
```python3 -m lib_bgp_data --roas_parser```

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

## Extrapolator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Extrapolator Short Description](#extrapolator-short-description)
   * [Long Description](#extrapolator-long-description)
   * [Usage](#extrapolator-usage)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)

Status: Development

### Extrapolator Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)

The Extrapolator takes as input mrt announcement data from the a table that is similar to the tables generated by the [MRT Parser](#mrt-announcements-submodule) and peer and customer-provider data from the [Relationships Parser](#relationships-submodule). The Extrapolator then propagates announcements to all appropriate AS's which would receive them, and outputs this data. This submodule is a simple wrapper to make it easier for a python script to run the extrapolator. Details other than how to run the wrapper are not included because up to date information should be found on the actual github page.

For more in depth documentation please refer to: [https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)

### Extrapolator Long Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)

The extrapolator takes in public announcement data and relationships data for the internet topology and using algorithms that rely on BGP we can guess the announcements at every AS across the internet.

When this parser is run, we first do input validation. The input table (default filtered_mrt_announcements), and the relationships tables are checked to make sure they exist and are filled. If the relationship tables are not filled, the Relationships_Parser is run. In addition, it is checked if the extrapolator is installed. If it is not, it is installed.

Then the BGP-Extrapolator is run with bash arguments, and results are stored in the class attributes for results table and depref table of the extrapolator parser.

### Extrapolator Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Extrapolator Submodule](#extrapolator-submodule)

#### In a Script

Initializing the Extrapolator_Parser

**Please note that for all of these examples - your python env MUST still be activated.**


The Defaults for the Extrapolator_Parser are the same as the [base parser's](base-parser-usage) it inherits:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | not used                                                                            |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |

> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize Extrapolator_Parser with default values:
```python
from lib_bgp_data import Extrapolator_Parser
extrapolator_parser = Extrapolator_Parser()
```

To initialize Extrapolator_Parser with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import Extrapolator_Parser
extrapolator_parser = Extrapolator_Parser(path="/my_custom_path",
                                          csv_dir="/my_custom_csv_dir",
                                          stream_level=DEBUG)
```

To run the Extrapolator_Parser:
> The params for the forecast extrapolator function are:

| Parameter   | Default | Description                                                                                                        |
|-------------|---------|--------------------------------------------------------------------------------------------------------------------|
| input_table | None    | Announcements table the extrapolator will pull data from, if it is none the default is the filtered_mrt_announcements table |

To initialize Extrapolator_Parser and run:
```python
from lib_bgp_data import Extrapolator_Parser
Extrapolator_Parser().run(input_table="mrt_announcements")
```                                                            

#### From command line

**Please note that for all of these examples - your python env MUST still be activated.**

There are two ways you can run this parser. It will run with all the defaults. Later in the future it is possible more parameters will be added, but for now this is unnecessary.

Best way:
```bash
lib_bgp_data --extrapolator_parser
```
For debugging:
```bash
lib_bgp_data --extrapolator_parser --debug
```
This example must be run over the package, so cd into one directory above that package
```bash
python3 -m lib_bgp_data --extrapolator_parser
```

## BGPStream Website Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#bgpstream-website-short-description)
   * [Long Description](#bgpstream-website-long-description)
   * [Usage](#bgpstream-website-usage)
   * [Table Schema](#bgpstream-website-table-schema)
   * [Design Choices](#bgpstream-website-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

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

Initializing the BGPStream_Website_Parser:

**Please note that for all of these examples - your python env MUST still be activated.**


The Defaults for the BGPStream_Website_Parser are the same as the [base parser's](base-parser-usage) it inherits:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |
| section | ```"bgp"  ```                      | database section to use                                                                                      |
> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize BGPStream_Website_Parser with default values:
```python
from lib_bgp_data import BGPStream_Website_Parser
bgpstream_website_parser = BGPStream_Website_Parser()
```

To initialize BGPStream_Website_Parser with custom path, CSV directory, database section, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import BGPStream_Website_Parser
bgpstream_website_parser = BGPStream_Website_Parser(path="/my_custom_path",
                                                    csv_dir="/my_custom_csv_dir",
                                                    stream_level=DEBUG,
                                                    section="mydatabasesection")
```

Running the BGPStream_Website_Parser:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| row_limit         | ```None```     |  Defaults to all rows - 10 to get rid of corrupt rows. Really just for quick  tests|
| IPV4         | ```True```     | Include IPV4 prefixes                                    |
| IPV6      | ```False``` | Include IPV6 prefixes                                         |
| data_types | ```Event_Types.list_values()```  | Event types to download, hijack, leak, or outage        |
| refresh | ```False```                        | If you've already seen the event, download it again anyways. Really just for quick testing                                                                                |

> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To run the BGPStream_Website_Parser with defaults:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().run()
```
To run the BGPStream_Website_Parser with just hijacks:
```python
from lib_bgp_data import BGPStream_Website_Parser, BGPStream_Types
BGPStream_Website_Parser().run(data_types=[BGPStream_Types.HIJACK.value])

To run the BGPStream_Website_Parser with all IPV4 and IPV6 prefixes:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().run(IPV4=True, IPV6=True)
```

#### Useful examples for test usage:
To run the BGPStream_Website_Parser with just the first 50 rows for a quick test:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().run(row_limit=50)
```
To run the BGPStream_Website_Parser and reparse all events you've seen already:
```python
from lib_bgp_data import BGPStream_Website_Parser
BGPStream_Website_Parser().run(refresh=True)
```

#### From the Command Line
Best way:
```bash
lib_bgp_data --bgpstream_website_parser
```
For debugging:
```bash
lib_bgp_data --bgpstream_website_parser --debug
```
Must be called on the library:
```bash
python3 -m lib_bgp_data --bgpstream_website_parser
```
### BGPStream Website Table Schema
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Submodule](#bgpstream-website-submodule)

* These tables contains information on the relationship data retrieved from bgpstream.com
* Unlogged tables are used for speed
* Note that explanations are not provided because these fields are chosen by bgpstream.com

#### hijacks Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for hijack events
* id: *(serial PRIMARY KEY)*
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
              id serial PRIMARY KEY,
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

#### leaks Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for leak events
* id: *(serial PRIMARY KEY)*
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
        id serial PRIMARY KEY,
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
#### outages Table Schema:
* [lib\_bgp\_data](#lib_bgp_data)
* [BGPStream Website Table Schema](#bgpstream-website-table-schema)
* Contains data for outage events
* id: *(serial PRIMARY KEY)*
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
        id serial PRIMARY KEY,
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
* Multithreading isn't used because the website blocks the requests and rate limits                              
* Parsing is done from the end of the page to the top                                            
    * The start of the page is not always the same                                               

## RPKI Validator Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rpki-validator-short-description)
   * [Long Description](#rpki-validator-long-description)
   * [Usage](#rpki-validator-usage)
   * [Table Schema](#rpki-validator-table-schema)
   * [Design Choices](#rpki-validator-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

Status: Production

### RPKI Validator Short description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)

This submodule contains both a wrapper around the RPKI Validator and a Parser that parsers data from it. The purpose of this module is to get any necessary data from the RPKI Validator and insert it into the database, or to simply run the rpki validator.

### RPKI Validator Long description
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)

The purpose of this class is to obtain the validity data for all of the prefix origin pairs in our announcements data, and insert it into a database. This is done using the RPKI Validator. 

To start with, the module is installed by default if it is not already. The installation defaults must be changed because we have reconfigured the RPKI Validator. Instead of pulling from an online file of all distinct prefix origin pairs, we instead use our own file with our own announcements data. To install correctly, we (in the RPKI_Validator_Wrapper's Installation Function Section):

1. Install the Validator, and move it to /var/lib/rpki-validator-3. We do this also so that no matter the version the naming scheme will be the same (unless they move to RPKI validator -4, in which case we would want it to break
2. Then we download Arins Tal. This is not included by default due to legal issues.
3. Then we change the location of the hosted file the RPKI validator pulls from to pull from our own file that is locally hosted
4. We change the server address from localhost to 0.0.0.0 for proxy reasons on our server
5. Then we configure absolute paths in order to be able to run the validator from any directory

After we have installed the validator, but before we can run it, we first need to create our own locally hosted file. To do this, we use the RPKI_File class. We give it a table as input. This table will be copied into a csv, and it will spawn another thread that will host the file until the RPKI_Validator_Wrapper dies. This file will take a table similar to the format of the mrt_announcements table (must have a column called prefix, and another called origin), and it must be gzipped to satisfy the RPKI Validator. It must also have distinct prefix origin pairs. The placeholder value in this table doesn't matter, I don't even remember what it is anymore other than that the RPKI Validator only sees values over 5, so we have a placeholder of 100. Note that the file class can be used as a context manager

Then there is the RPKI_Validator_Wrapper itself. This wrapper class is also a context manager to ensure proper opening and closing of different processes. (in the RPKI_Validator_Wrapper's Context Manager Function Section)

1. First this wrapper checks if the RPKI Validator is installed, and if not it installs it
2. Then it kills all processes running on port 8080. This is because sometimes the RPKI Validator doesn't die properly, or other processes block it from running.
3. Then it removed the database directories in the validator. This is because the validator's database directories get corrupted if it dies, and will never turn back on again.
4. Then it chowns the installed files, since they have weird permissions
5. Then the RPKI_File process is spawned, as described above.
6. Then the start validator function is started in another process. This just runs the file in the RPKI Validator that starts the validator.
7. The context manager returns the RPKI_Validator_Wrapper object.

The RPKI_Validator_Wrapper has many useful wrapper functions, including waiting until trust anchors are loaded, making queries the the API, and also getting the validity data. All will be shown in the examples usage section.

The RPKI_Validator_Parser simply runs the RPKI_Validator_Wrapper and calls it's methods.
(in the RPKI_Validator_Wrapper's Wrapper Function Section)
1. First we load the trust anchors. There is a function that the RPKI Validator API has that will return a JSON of the trust anchors loading status. We call this endlessly until all trust anchors loading status is True. NOTE that this will usually take around 20 minutes at least even for a small data set.
2. Once these are loaded, you can then query the results with get_validity_data. This will return a JSON of the validity data of all the prefix origin pairs. This can be decoded using the RPKI_Validitator_Wrapper.get_validity_dict. 
3. This information is then formatted in the RPKI_Validator_Parser._format_asn and the information is copied to a CSV and then inserted into the ROV_Validity table.

### RPKI Validator Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
* [RPKI Validator Parser Usage](#rpki-validator-parser-usage)
* [RPKI Validator Wrapper Usage](#rpki-validator-wrapper-usage)

Note that if you want to access the validator on our machine ahlocal, here is how you would ssh tunnel into the gateway (this can be extremely useful for debugging):
```bash
ssh -L localhost:8080:localhost:8080 jmf@csi-lab-ssh.engr.uconn.edu
ssh -L localhost:8080:localhost:8080 ahlocal
```
Then simply swap out your username with jmf, and you can view the RPKI Validator UI in your browser by typing localhost:8080

### RPKI Validator Parser Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
* [RPKI Validator Usage](#rpki-validator-usage)

#### In a Script
Initializing the RPKI Validator Parser:

**Please note that for all of these examples - your python env MUST still be activated.**

Also NOTE: Other parsers are multi section safe. Meaning they can use different databases and such. This validator does NOT have that. It can only have one running at any given time. This is because during the installation, port numbers and file paths are hardcoded in. So we cannot have two running at once.

The Defaults for the RPKI Validator Parser are the same as the [base parser's](base-parser-usage) it inherits:

| Parameter    | Default                             | Description                                                                                                       |
|--------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| name         | ```self.__class__.__name__```     | The purpose of this is to make sure when we clean up paths at the end it doesn't delete files from other parsers. |
| path         | ```"/tmp/bgp_{}".format(name)```     | Not used                                                                                         |
| csv_dir      | ```"/dev/shm/bgp_{}".format(name)``` | Path for CSV files, located in RAM                                                                                |
| stream_level | ```logging.INFO```                        | Logging level for printing                                                                                        |

> Note that any one of the above attributes can be changed or all of them can be changed in any combination

To initialize RPKI_Validator_Parser with default values:
```python
from lib_bgp_data import RPKI_Validator_Parser
rpki_validator_parser = RPKI_Validator_Parser()
```

To initialize RPKI_Validator_Parser with custom path, CSV directory, and logging level:
```python
from logging import DEBUG
from lib_bgp_data import RPKI_Validator_Parser
rpki_validator_parser = RPKI_Validator_Parser(path="/my_custom_path",
                                              csv_dir="/my_custom_csv_dir",
                                              stream_level=DEBUG)
```
To run the RPKI_Validator_Parser with defaults (there are no optional parameters):
```python
from lib_bgp_data import RPKI_Validator_Parser
RPKI_Validator_Parser().run()
```

Now on top of the RPKI Validator Parser, there is also the RPKI_Validator_Wrapper. This contains functionality to basically install and run the RPKI_Validator in a nice controlled way, and provides an easy access point to be able to make API queries to it.


#### From the Command Line

**Please note that for all of these examples - your python env MUST still be activated.**

There are two ways you can run this parser. It will run with all the defaults. Later in the future it is possible more parameters will be added, but for now this is unnecessary.

Best way:
```bash
lib_bgp_data --rpki_validator_parser
```
For debugging:
```bash
lib_bgp_data --rpki_validator_parser --debug
```
This example must be run over the package, so cd into one directory above that package
```bash
python3 -m lib_bgp_data --rpki_validator_parser
```

### RPKI Validator Wrapper Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [RPKI Validator Submodule](#rpki-validator-submodule)
* [RPKI Validator Usage](#rpki-validator-usage)

The wrapper can be used on it's own to provide an easy pythonic way to run the RPKI Validator over your own file of announcements. Read the [Long Description](#rpki-validator-long-description) to see how the RPKI Validator Wrapper works.

To create the RPKI File and run the RPKI Validator Wrapper, you need to use the class as a context manager. This will manage installation (if not already), opening, and closing connections all behind the scene. You must also wait for the trust anchors to be uploaded before you can perform most API queries, which is why it is the default example:

```python
from lib_bgp_data import RPKI_Validator_Wrapper
# This will create the file for upload, and upload it to the validator
# Ifyou do not specify table input, it defaults to mrt_rpki
with RPKI_Validator_Wrapper(table_input="table_name_of_prefix_origins") as _rpki_validator:
    # Always run this before anything else. This loads the trust anchors with the ROA info
    _rpki_validator.load_trust_anchors()
# Stuff outside the validator goes here. The validator will now be closed.
```

If you want to get the validity data:
```python
from lib_bgp_data import RPKI_Validator_Wrapper
# This will create the file for upload, and upload it to the validator
# Ifyou do not specify table input, it defaults to mrt_rpki
with RPKI_Validator_Wrapper(table_input="table_name_of_prefix_origins") as _rpki_validator:
    # Always run this before anything else. This loads the trust anchors with the ROA info
    _rpki_validator.load_trust_anchors()
    _rpki_validator.get_validity_data()
# Stuff outside the validator goes here. The validator will now be closed.
```

If you want to make any query to the API, see below.
```python
from lib_bgp_data import RPKI_Validator_Wrapper
# This will create the file for upload, and upload it to the validator
# Ifyou do not specify table input, it defaults to mrt_rpki
with RPKI_Validator_Wrapper(table_input="table_name_of_prefix_origins") as _rpki_validator:
    # Always run this before anything else. This loads the trust anchors with the ROA info
    _rpki_validator.load_trust_anchors()
    # NOTE: This function does not take the full URL, only the API endpoint
    # The beginning of the URL is prepended behind the scenes and is: http://[::1]:8080/api/
    # Also, this is just an example query. They have more available, check out their website
    # I won't link their website here since their links often move/break
    _rpki_validator.make_query("bgp/?pageSize=10000000")
# Stuff outside the validator goes here. The validator will now be closed.
```

NOTE that the make_query function will by default return the data of the JSON is recieves. If you want the full JSON, pass the keyword data=False:
```python
from lib_bgp_data import RPKI_Validator_Wrapper
# This will create the file for upload, and upload it to the validator
# Ifyou do not specify table input, it defaults to mrt_rpki
with RPKI_Validator_Wrapper(table_input="table_name_of_prefix_origins") as _rpki_validator:
    # Always run this before anything else. This loads the trust anchors with the ROA info
    _rpki_validator.load_trust_anchors()
    # NOTE: This function does not take the full URL, only the API endpoint
    # The beginning of the URL is prepended behind the scenes and is: http://[::1]:8080/api/
    # Also, this is just an example query. They have more available, check out their website
    # I won't link their website here since their links often move/break
    _rpki_validator.make_query("bgp/?pageSize=10000000", data=False)
# Stuff outside the validator goes here. The validator will now be closed.
```

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
                 FROM input_table ORDER BY prefix ASC;
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
    * Everything is kept as a contextmanager so that everything closes properly
    * The massive pile of class attributes is saved so that the install and everywhere relies on a single string
    * The RPKI file, wrapper, and parser are kept separate to make it easier to modify and use them in other applications
    * This parser is not multi section safe. The reason being that install needs hardcoded paths and since we are not installing a new validator every time, there can only ever be one validator being run at any given time.
    * Data is bulk inserted into postgres
        * Bulk insertion using COPY is the fastest way to insert data into postgres and is neccessary due to massive data size
    * Parsed information is stored in CSV files
        * Binary files require changes based on each postgres version
        * Not as compatable as CSV files
     * Instructions on multi sectional capabilities are not included only one should be run at a time. However, if you are just running one on a different database, you can use a different section.

## What if Analysis Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#what-if-analysis-short-description)
   * [Long Description](#what-if-analysis-long-description)
   * [Usage](#what-if-analysis-usage)
   * [Table Schema](#what-if-analysis-table-schema)
   * [Design Choices](#what-if-analysis-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

NOTE: This is not yet complete and should not be used.

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

## API Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#api-short-description)
   * [Usage](#api-usage)
   * [Design Choices](#api-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

NOTE: This is not yet complete and should not be used

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

## ROVPP Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Short Description](#rovpp-short-description)
   * [Long Description](#rovpp-long-description)
   * [Usage](#rovppusage)
   * [Table Schema](#rovpp-table-schema)
   * [Design Choices](#rovpp-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

NOTE: Do not use, due to deadlines became hardcoded mess. Avoid lmaooo

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

## Utils
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#utils-description)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

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
* Delete files: A decorator that can delete files before and after a function call
* low overhead log: prints without logging overhead, useful for multiprocessing.
* Progress bar: Makes a custom progress bar, better than tqdm for mrt_parser
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
* get_lines_in_file: Returns number of lines in any given file
* run_cmds: Runs bash commands with proper logging
* replace_lines: Replaces lines in file, mostly for installs

## Database Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#database-description)
   * [Usage](#database-usage)
   * [Design Choices](#database-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

Status: Development

### Database Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)

This module contains all the functionality to interact with a database. First we have the config class in the config.py. This class keeps track of all the different database sections and their login information. By default pytest always uses the test database class, and if section is not set then bgp is used. Note that this class will install the database for any section that is passed in and does not exist.

Then there is the Postgres class in postgres.py. This class contains some useful features for controlling postgres. It contains the functionality to install postgres and perform modifications for a nice fast database (Note that these modifications make the database corruptable upon crashing, but don't care about that since we can reproduce the data easily). We can also "unhinge" the database, which basically means turning off all safety features and writing to disk for some really fast queries. This also contains the functionality to restart the postgres database. Note that a lot of these system modifications will affect all running instances of postgres databases.

Then there is the database class. This class deals specifically with connecting to the database and performing some minor functions. You can use it as a context manager to be able to access the database and execute commands. By default the realDictCursor is used so that all results returned are lists of dictionaries.

Lastly there is the generic table class. This class is super convenient to write functions with. It inherits the database class. Is it mainly to be used through inheritance. When a class inherits this class, it gains access to a large swath of functionality. It can connect to the database, and whenever it does create tables if they do not exist. It can clear tables upon connection. It has built in clear_table and other functions such as get_count, etc. Check out some great examples of how this is used in the ROAs Parser Submodule in tables.py, and in the usage examples below.

### Database Enhancements
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)

Rather than repeat documentation, please view the Postgres class for the modify database function. In addition, see the unhinge_db function, for when the database is unhinged. These are extensive lists of sql queries and the reasons why we use them in order to improve database performance.

Note that we NEVER alter the config file for the database. We only ever use the ALTER SYSTEM command so that we can always have the default config to be able to go back to.

### Database  Usage
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)


#### Postgres Functions
Erasing all installed databases:
```python
from lib_bgp_data import Postgres
Postgres().erase_all()
```
Unhinging database:
```python
from lib_bgp_data import Postgres
Postgres().unhinge_db()
# Do stuff here
Postgres().rehinge_db()
```
Restarting postgres:
```python
from lib_bgp_data import Postgres
Postgres().restart_postgres()
```
#### Database Functions
Connecting to the database
```python
from lib_bgp_data import Database
with Database() as db:
    db.execute("my sql query")
# Database is closed here
```
Executing multiple sql queries at once:
```python
from lib_bgp_data import Database
sql_queries = ["sql quer 1", "sql query 2"]
with Database() as db:
    db.multiprocess_execute(sql_queries)
# Database is closed here
```
#### Generic Table Functions
Lets say you have a table called roas (example in roas [arser.

```python
from lib_bgp_data import Generic_Table
class ROAs_Table(Generic_Table):
    """Announcements table class"""

    __slots__ = []

    name = "roas"

    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS roas (
              asn bigint,
              prefix cidr,
              max_length integer
              ) ;"""
        self.execute(sql)

```
Lets get all rows from the Roas_Table:
```python
# Note that when it is initialized, create tables is called!
with ROAs_Table() as db:
    # Returns a list of dictionaries
    rows = db.get_all()
# connection is closed here
```
Lets clear the table upon initializing, in case it has things in it
```python
# This will drop the table (if exists) and recreate it
with ROAs_Table(clear=True) as db:
    # Do stuff here
# Connection closed here
```
Other convenience funcs:
* get_count: returns total count
* get_all: Returns all rows as a list of dicts
* clear_table: Drops table if exists
* copy_table: Takes as input a path string and copies table to that path
* filter_by_IPV_family: Filter table by IPV6 or IPV4
* columns: Returns the columns of that table

Again please note: upon connection, it creates the tables. If clear is passed, it will clear them. After the context manager is over it will close the database.

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

### Database Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)
    * RealDictCursor is used as the default cursor factory because it is more OO and using a dictionary is very intuitive.
    * Unlogged tables are used for speed
    * Most safety measures for corruption and logging are disabled to get a speedup since our database is so heavily used with such massive amounts of data
    * Lots of convenience functions so that code would not be duplicated across submodules

### Database Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Database Submodule](#database-submodule)

See: [Installation Instructions](#installation-instructions)

## Logging Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Description](#logging-description)
   * [Design Choices](#logging-design-choices)
   * [Todo and Possible Future Improvements](#todopossible-future-improvements)

Status: Development

### Logging Description
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)

In utils there is a file called logger.py. In this file there is a config_logging function with inputs as to the section in the config to run from, and the level of the logging. This will configure the logging to the standard out and to a file in /var/log/lib_bgp_data/.

The default logging.INFO and the default section is bgp.

You can run debug logs with --debug in the command line arguments

logging in certain files is disabled because logging adds heavy overhead to the point of deadlocking for highly parallelizable programs.

For an explanation on how logging works:
logging has different levels. If you are below the set logging level,
nothing gets recorded. The levels are, in order top to bottom:

        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        logging.NOTSET

### Logging Design Choices
* [lib\_bgp\_data](#lib_bgp_data)
* [Logger Submodule](#logger-submodule)
    * A catch all error catcher is no longer used, instead if a parser errors the exception is logged
    * logging will deadlock in parallel processes and must be disabled
    * config_logging is designed so that logging can never be configured twice

## Installation
   * [lib\_bgp\_data](#lib_bgp_data)
   * [Installation Instructions](#installation-instructions)
   * [Postgres Installation](#postgres-instructions)
   * [System Requirements](#system-requirements)

Status: Production

### Installation instructions
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)


First you need some dependencies. Run
```bash
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
```
Then install postgres 12 (see [Postgres Installation](#postgres-installation))

If you are on a machine that has SELinux, you are going to need to run this in a python environment. On Ubuntu, the steps are as follows
NOTE: We now use python3.8. Make sure that you are using python 3.8.
```bash
sudo apt-get install python3-pip
sudo python3.8 -m pip3 install virtualenv 
```

On Redhat the steps can be found here:
[https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/](https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/)
NOTE: If you are installing it on an OS other than ubuntu, I do not think the install script will work. Good luck doing it all manually.

Note: if you are using our machine ahlocal, there are some very weird permission errors. Due to SE Linux and the gateway, etc, sudo cannot access your home directory. I have tried using ```export HOME=/root``` and other solutions to no avail. No one seems to be able to figure it out. No one seems to care either, and I have told the higher ups and coding is the priority. To run this I would install it in a top level directory like /ext and install it by using ```sudo su``` and continuing from there. I'm sure this is not completely secure so hopefully this will get fixed in the future but no one seems to know how to do that lol.

Once you have virtualenv installed, run 
```bash
python3.8 -m venv env
source ./env/bin/activate
```
You now have a python virtual environment. You should still be a super user.
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

There are lots of other dependencies, but they will be installed automatically the first time they are needed. If not, manual install links are below:

>bgpscanner manual install link:
>[https://gitlab.com/Isolario/bgpscanner](https://gitlab.com/Isolario/bgpscanner)
>bgpdump manual install link:
>[https://bitbucket.org/ripencc/bgpdump/wiki/Home](https://bitbucket.org/ripencc/bgpdump/wiki/Home)
>extrapolator manual install link:
>[https://github.com/c-morris/BGPExtrapolator](https://github.com/c-morris/BGPExtrapolator)
>RPKI Validator manual install link:
>[https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources](https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources)

Note that now that you have installed every part of lib_bgp_data, you can test it if you'd like. You can run:

```pip3 install lib_bgp_data --upgrade --force --install-option test```

to test the install. 

To test the development package, cd into the root directory and run pytest.

### Postgres Installation
* [lib\_bgp\_data](#lib_bgp_data)
* [Installation Instructions](#installation-instructions)
* [Installation Submodule](#installation-submodule)


For this, you are going to need postgres 12. You need this because it allows for parallel query execution, which significantly speeds up processing time. For installing postgres on your machine, see:
Ubuntu Install:
[https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/](https://computingforgeeks.com/install-postgresql-11-on-ubuntu-18-04-ubuntu-16-04/)

or redhat install:

[https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/](https://computingforgeeks.com/how-to-install-postgresql-11-on-centos-7/)

After the database is installed, we are going to need to make a couple of changes. First, we need to start the database. To do this run:
```bash
sudo systemctl start postgresql@12-main.service
# or maybe
sudo systemctl start postgresql
```
To check to see if it is running:
```bash
sudo systemctl status postgresql@12-main.service
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

In addition, the machine needs postgres 12 and python3.8 or above


## Testing
   * [lib\_bgp\_data](#lib_bgp_data)

NOTE: Along with everything else in this package, you must be a super user and have your python environment activated before running any of these commands.

Run tests on install by doing:
```sudo pip3 install lib_bgp_data --force --install-option test```
This will install the package, force the command line arguments to be installed, and run the tests

You can test the package if in development by moving/cd into the directory where setup.py is located and running:
```sudo python3 setup.py test```

To test a specific submodule, run pytest --help. Then you can run pytest -m <submodule_name> and onl tests from that submodule will be run.

Also note that slow tests are marked as slow. So you can not run slow tests by doing pytest -m "not slow".

All the skipped tests are for the interns to fill in. I have completed these tests manually and am confident they will succeed, and I have been told by my bosses to move on to other tasks.

## Adding a Submodule
   * [lib\_bgp\_data](#lib_bgp_data)
   * [How to Add a Submodule](#how-to-add-a-submodule)
### How to Add a Submodule
NOTE: If you are a collaborator, make sure to branch! Never, ever push to master.

Where to begin. To start, first I would install the package and run the roas parser. That way you can kind of get a feel for how to run something from this package. Once that is done, you will need to get up to speed on a few python things. If you know some of these things, feel free to skip them:

list comprehensions:
[https://www.youtube.com/watch?v=3dt4OGnU5sM](https://www.youtube.com/watch?v=3dt4OGnU5sM)
decorators:
[https://www.youtube.com/watch?v=FsAPt_9Bf3U](https://www.youtube.com/watch?v=FsAPt_9Bf3U)
context managers:
[https://www.youtube.com/watch?v=-aKFBoZpiqA](https://www.youtube.com/watch?v=-aKFBoZpiqA)
Python packages (NOTE: There's no good youtube vids, but here is something quick):
[https://www.youtube.com/watch?v=uVJf5wuPpyw](https://www.youtube.com/watch?v=uVJf5wuPpyw)
SQL/PostgreSQL: google your own stuff for this
pytest: 
[https://www.udemy.com/course/elegant-automation-frameworks-with-python-and-pytest/](https://www.udemy.com/course/elegant-automation-frameworks-with-python-and-pytest/)

To explain this easier we will look at the roas collector submodule. Do not use this submodule. Instead, copy it and all of it's contents into another directory. If you have access to a bash terminal you can accomplish this by copying doing:
```bash
cp -R roas_collector my_submodule
```
Then you can manipulate this submodule to do what you want. If you want to look at a very simple submodule for another example, the relationships_parser is also fairly straightforward.

Let's first look at the \_\_init\_\_.py file inside this new submodule. For formatting of all python files, I looked it up and the proper way to do it is to have a shebang at the top defining that it is python and that the coding is in utf8, as you can see. Then there is usually a docstring containing all the information you would need about the file. For a normal file someone should be able to read it and obtain a thorough understanding of what's in the file. For the \_\_init\_\_.py file a user should be able to read it and obtain a thorough understanding of the whole submodule. I like to split these docstrings into a series of parts. The first line, as is specified by pep8, is a short description. Then a new line, and then a slightly longer description. Then I like to list out the steps that my file will perform. After that there is a design choices section, which should summarize design choices from above. This section is important because you can clearly detail why certain decisions where made for future users. There is also a future extensions section, which should contain all possible future work for the current file, or, in the case of the \_\_init\_\_.py file, all the future work for the current submodule. Then we are going to include some python headers with some metadata. This data should be kept up to date, and make sure to give credit where credit is due. Another thing, for the love of god please make your files pep8 compliant. There are numerous tools to do this automatically that exist for many different text editors. If you are using vim you can use flake8. If doing it on a remote server is to difficult, feel free to download it onto your own laptop and do it there.

If you are not familiar with the \_\_init\_\_.py file, this is a file in python that the package manager will look at to determine what is inside of a folder. That is a very short explanation, a much better explanation can be found at:
google.com
just kidding lol.  I thought I had a good tutorial but I couldn't find it. However, some of this python code is not basic stuff, if you are ever confused I suggest searching the problem with "Corey Shafer" on youtube, his tutorials are usually pretty good.
All classes, functions, etc. that will be used outside of your submodule should be imported in \_\_init\_\_.py . Similar import statements should again occur at the top level \_\_init\_\_.py file. Only the programs that are in the top level \_\_init\_\_.py file can be easily accessed in a script. Also notice how my submodule name, my file in the submodule that contains the most important class required to run that will be imported above, and the class that will be imported to upper level folders are almost all the same name. This will let a user know what the main files are in a program.

Before you continue, you should try to get your new submodule to run. Make sure that you have imported it correctly in both the \_\_init\_\_.py file that is located within your submodules folder, and also the \_\_init\_\_.py file located in the folder above. Then try to import it from lib_bgp_data in a script and run it. Note that to get the traceback from errors, you should pass in as an argument to the initialization of your class stream_level=logging.DEBUG}. Good luck! Let me know if you have any problems!

Now lets take a look at the roas_parser. Aside from the stuff at the top which is similar to the \_\_init\_\_.py file, the imports are very different. You'll notice that normal packages import normally, such as the re function. To import classes from files outside of your current folder (in the folder above) you need to do 
```python
from ..<above folder> import <stuff you want to import>
```
You can see this as an example in the line:
```python
from ..utils import utils
```
This imports the utils file from the utils folder, which is outside of our current folder. To import classes and other things from the current folder, do the same as above but with one less period. Example below.
```python
from .tables import ROAs_Table
```
After that we have the class. Notice all the docstrings and comments throughout the code. If the information is included in the docstring at the top of the file, just say for a more in depth explanation refer to the top of the file. Also notice the use of \_\_slots\_\_. This is not required, but turns the class almost like into a named tuple. Attributes that are not included in the \_\_slots\_\_ cannot be added. It decreases the reference time for a value significantly, I think by about a third. You probably won't need this, and it can cause lots of errors if you don't understand it, so probably just delete it.

Note that the ROAs_Parser inherits from the Parser class. You should use this class. All subclasses of parser are automatically added to the command line arguments (as the lowercase name of your class). They must also have a _run function, which will act as the main function that runs your code. This function will also catch all errors and log them. 

Inside this function we have a Database context manager. This will open a connection to the database with the table specified and also create that table by automatically calling the _create_tables function. 

After this function we have a helper functions sign. This is usually if you have a long list of functions, and want to group them somehow. Helper functions just means that they are private. Notice these functions, and all other variables that should be private have an underscore underneath them. 

Lets take a look at the file tables.py. This file typically contains all the database interactions side of things. All the tables that get generated. The names of these classes are important and are used in the program. They inherit from a Generic_Table class. When this class is initialized it connects to the database, and calls the _create_tables function. This function should create whatever table you are trying to create. Another function, clear_table, should be included in whatever class you created. This is the function that is called whenever db_connection is initiated, to drop whatever previous data was there before. The \_\_slots\_\_ is empty here because it inherits from the database class. The real dict cursor is used to make all return values into a list of dictionaries, to make it easier to use. Note that this is not the most effective memory wise, and other cursor factories should be used if memory consumption is a problem. See the [Database](#database-submodule) for more details on how to ineract with a database.

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
   * 0.3.0 - Got many submodules up to date and with lots of unit tests. Backwards compatibility destroyed
   * 0.2.3 - Fixed bugs found in the RPKI Validator, MRT Parser. Various other bug fixes. Added pytest for roas_collector.
   * 0.2.2 - Automated full run

## Credits
   * [lib\_bgp\_data](#lib_bgp_data)

This is a massive python package, and it obviously would not have been possible without lots of help.

Thanks goes out first to Matt Jaccino. He added the isolario announcements and also the capabilities for a multi section config, among many other contributions. Truly amazing work.

Thanks to Cameron for helping with the RPKI Validator, pulling various all nighters with me to push for deadlines, various other contributions, and pointing out many bugs along the development process.

Thanks to James for looking into the mrt_w_roas join duplication bug and the numerous bugs that were discovered in Caida's API, and communicating with them and debugging some SQL queries

Thanks to Comcast for funding such amazing research. It had really been a pleasure working with you guys and this research is yielding some pretty incredible results.

Thanks to Dr. Amir Herzberg and Dr. Bing Wang with all the help for leading the development team and for all of their knowledge on this subject, and for employing me to work on this.

Thanks to Luke Malinowski for help in debugging some SQL queries.

Thanks to Reynaldo Morris for his help for showing me how to configure the API to use flasgger docs and writing the first YAML file. Thanks also for writing the first draft of the traceback function used in the ROVPP submodule.

Thanks to Cameron, Reynaldo, and James for connecting the API to the website

And of course thanks to the new python hires, Abhinna, Tony, and Nicholas, I look forward to working with you.

Thanks for all the other help that I have since neglected to write down, it's been a pleasure working with you all.

There is also all  of the tools that we use:
Thanks to the bgpscanner team. The tool is amazing, it is much faster than bgpdump. They also helped me out to modify their script, and were very responsive to emails.
[https://gitlab.com/Isolario/bgpscanner](https://gitlab.com/Isolario/bgpscanner)

Thanks to the people behind the RPKI Validator. It is an extremely useful tool.
[https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources](https://www.ripe.net/manage-ips-and-asns/resource-management/certification/tools-and-resources)

Thanks to the people behind bgpdump. This tool was what we originally used and has had consistent updates. 
[https://bitbucket.org/ripencc/bgpdump/wiki/Home](https://bitbucket.org/ripencc/bgpdump/wiki/Home)

Thanks to Caida for their MRT and Relationship data, which is extremely useful:
[http://www.caida.org/home/](http://www.caida.org/home/)

Thanks to ISOlario for their MRT data:
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
* [https://stackoverflow.com/a/43057166/8903959](https://stackoverflow.com/a/43057166/8903959)
* https://www.geeksforgeeks.org/python-difference-between-two-dates-in-minutes-using-datetime-timedelta-method/
* [https://stackoverflow.com/a/427533/8903959](https://stackoverflow.com/a/427533/8903959)  
* [https://stackoverflow.com/a/3468410](https://stackoverflow.com/a/3468410)  
* [https://stackoverflow.com/a/54919285](https://stackoverflow.com/a/54919285)  
* [https://stackoverflow.com/a/18431364](https://stackoverflow.com/a/18431364)  
* [https://www.tutorialdocs.com/article/python-class-dynamically.html](https://www.tutorialdocs.com/article/python-class-dynamically.html)  
* [https://stackoverflow.com/a/40409974](https://stackoverflow.com/a/40409974)  
* [https://stackoverflow.com/a/55961848/8903959](https://stackoverflow.com/a/55961848/8903959)  
* [https://stackoverflow.com/a/9079062/8903959](https://stackoverflow.com/a/9079062/8903959)  
* [https://stackoverflow.com/a/9079080/8903959](https://stackoverflow.com/a/9079080/8903959)  
* [https://stackoverflow.com/a/1883251/8903959](https://stackoverflow.com/a/1883251/8903959)  
* [https://stackoverflow.com/a/7065242](https://stackoverflow.com/a/7065242)  
* [https://stackoverflow.com/q/12400256/8903959](https://stackoverflow.com/q/12400256/8903959)  
* [https://stackoverflow.com/a/43064544/8903959](https://stackoverflow.com/a/43064544/8903959)  
* [https://github.com/tqdm/tqdm/issues/484](https://github.com/tqdm/tqdm/issues/484)  
* [https://stackoverflow.com/a/3160819/8903959](https://stackoverflow.com/a/3160819/8903959)  
* [https://stackoverflow.com/a/39281387](https://stackoverflow.com/a/39281387)
* [https://stackoverflow.com/a/1482316](https://stackoverflow.com/a/1482316)https://stackoverflow.com/a/1482316
* https://stackoverflow.com/a/19640319
* 

## License
   * [lib\_bgp\_data](#lib_bgp_data)

BSD License

## New Hires
   * [lib\_bgp\_data](#lib_bgp_data)

I added this section just so I would have to deal with less overhead with all the new hires that we were getting. To start with you will need to do some things to get started.

1. Email Amir and Jeanette (if you don't know her email just email Amir) and get set up with payroll on ess.uconn.edu. When you submit your hours, you will also need to submit an excel spreadsheet of the times that you worked, and what you did during those hours. You can keep the descriptions short, for example: Aug 8 9am-5pm Worked on Roas parser. Whenever you work please update your hours so that you do not forget. Please remind me and I will get you access to this doc. Also note that all training is billable hours. We expect at least 10 hours a week, but if you have heavy or light weeks due to school everything is very flexible, certainly don't let this get in the way of your grades. Please just let me know in advance if you will be working less and have high priority tasks, and I'll redelegate them elsewhere.
2. Email Professor Laurent with your public ssh key and password, cc Amir and myself, and make sure to ask for access and sudo power on ahlocal and ahdev. To log on to these servers, do:
```ssh -A jmf@csi-lab-ssh.engr.uconn.edu```
```ssh -A ahlocal```
```sudo -E su```
Once you have cloned this repo (NOTE: DO NOT USE GLOBAL CONFIG!!):
```git config user.email <youremail>```
```git config user.name <"Your Name">```
Also note that you should code and run your programs on these servers. You should not do it on your local machine. Our servers are much faster than your laptop with much more memory, by a margin of more than 10X. Time is money. In addition, when there is a problem it will help me to debug if I can access your code and run it. We've also had problems in the past of code breaking when run on our environments that didn't break on laptops, and it had to be scrapped. I recommend using tmux in conjunction with vim.
3. We will need to get you access to slack. Email me a reminder to do that, and to give you access to Jira. Any questions you may have, slack is the way to reach me.
4. Once you have access to the Jira board, this is where we will keep track of what we need to do. Every week we have a "stand up" meeting, a short 15 minute meeting where we go over the progress we've made on the tickets we are working on, and any roadblocks we may have. Make sure to have pushed your code to your own branch before this meeting.
5. Read the Goa Rexford paper (ask for access) and I'd read this README for clarity on some things. Message me when this is done so that we can have a one on one discussion of our research and what you will be working on. Don't worry if this stuff is confusing, I did not get anything when I first started, it won't be a problem at all.
6. That's about it! We are working on some exciting stuff and exciting papers. We usually publish a couple every year, so you are definitely working on some awesome stuff that will change the internet as we know it!

## TODO/Possible Future Improvements
   * [lib\_bgp\_data](#lib_bgp_data)


See Jira Board: [https://wkkbgp.atlassian.net/jira/software/projects/FORECAST/boards/1](https://wkkbgp.atlassian.net/jira/software/projects/FORECAST/boards/1)

## FAQ
   * [lib\_bgp\_data](#lib_bgp_data)

Q: More links to some research

A: Read these:
* [https://www.cs.bu.edu/~goldbe/papers/survey.pdf](https://www.cs.bu.edu/~goldbe/papers/survey.pdf)
* [https://www.nsf.gov/awardsearch/showAward?AWD_ID=1840041&HistoricalAwards=false](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1840041&HistoricalAwards=false)
    * Feel free to email Dr. Amir Herzberg for this paper
* [https://www.cs.princeton.edu/~jrex/papers/sigmetrics00.pdf](https://www.cs.princeton.edu/~jrex/papers/sigmetrics00.pdf)
* [https://www.ideals.illinois.edu/bitstream/handle/2142/103896/Deployable%20Internet%20Routing%20Security%20-%20Trusted%20CI%20Webinar.pdf?sequence=2&isAllowed=y](https://www.ideals.illinois.edu/bitstream/handle/2142/103896/Deployable%20Internet%20Routing%20Security%20-%20Trusted%20CI%20Webinar.pdf?sequence=2&isAllowed=y)
* RPKI/ROV Forecast web proposal - email Dr. Amir Herzberg for this paper
* ROVPP Hotnets paper: email Dr. Amir Herzberg for this paper

Q: What is the fastest way to dump these tables?

A: ```pgdump bgp | pigz -p <numthreads> > jdump.sql.gz``` I have tested all of the different possibilities, and this is the fastest for dumping and reuploading for our tables. Note that indexes do not get dumped and must be recreated.

Q: What is inter domain routing, gao rexford, hijacks, and ROV from a laymens perspective?

A: I'm glad you asked! The internet is comprised of these giant networks called ASes (Autonomous Systems). You can almost think of it as a bunch of servers that communicate with each other, and they communicate using the Border Gateway Protocol, or BGP. In this protocol, they send back and forth their AS number (also called the origin) and their prefixes (a list of ip address, or in other words urls). So basically, one AS will send out a prefix (1.2.0.0/16) and it's origin (1) to the entire internet. Then, any url/ip address that falls within 1.2.0.0/16 will be go to that address. Now, what happens if two ASes announce the same prefix?! This is called a hijacking. One of them is surely lying! But how do the ASes that recieve both announcements decide which one to trust? With the Gao Rexford protocol (mostly)! In this protocol, the AS selects the announcements that they think will make them the most money. Not the shortest path, but the cheapest one. In this case, if the prefix is the same, they will choose the announcement that has a shorter path to it's destination. If the prefix was different, it would choose the more specific prefix (i.e. 1.2.3/24 instaed of 1.2/16). In this way, any AS can lie, and get all the traffic! How do we stop this do you ask? With ROV (Route Origin Validation). You can think of it almost as a database of information for announcements (in reality it is a public key infrastructure, but don't worry about that). This database contains information on the prefix and the origins. So if an announcement occurs that is in conflict with an entry (a ROA) in this database, it will be blocked! However, ROAs are not always accurate. If they were, everyone would use ROV, but they do not. Sometimes ROAs are outdate and wrong. Other times they are made with errors. When this happens, good traffic and good announcements can get blocked, even though it is not a hijack. Network operators want to know - what will happen to MY traffic if I use this security policy?? That is what this package is trying to solve. Please see the package description for further information on that.
