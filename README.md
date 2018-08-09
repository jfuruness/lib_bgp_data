# lib\_bgp\_data
This package parses bgp data and inserts the raw data into a database. The data is parsed from bgpstream.com, http://data.caida.org/datasets/as-relationships/, and from the BGP Stream using https://bgpstream.caida.org/docs/api/pybgpstream/_pybgpstream.html. The entirety of this data can be inserted into the database upon processing.

* [lib\_bgp\_data](#lib_bgp_data)
* [Description](#description)
    * [Parser Description](#parser)
    * [Database Description](#database)
        * [Database Schema](#database-schema)
            * [as\_relationships Schema](#as_relationships-schema)
            * [hijack Schema](#hijack-schema)
            * [leak Schema](#leak-schema)
            * [outage Schema](#outage-schema)
            * [records Schema](#records-schema)
            * [elements Schema](#elements-schema)
            * [communities Schema](#communities-schema)
    * [Logging Description](#logging-description)
* [Installation](#installation)
    * [Database Installation](#database-installation)
    * [pybgpstream Installation](#pybgpstream-installation)
    * [lib\_bgp\_data Installation](#lib_bgp_data-installation)
    * [Testing your installation](#testing-your-installation)
* [Usage](#usage)
    * [In a Script](#in-a-script)
        * [Initializing the Database and Parser](#initializing-the-database-and-parser)
        * [How to Run BGPStream\_Website\_Parser](#how-to-run-bgpstream_website_parser)
        * [How to Run Caida\_AS\_Relationships\_Parser](#how-to-run-caida_as_relationships_parser)
        * [How to Run BGP\_Records to get BGPStream data](#how-to-run-bgp_records-to-get-bgpstream-data)
    * [From the Command Line](#from-the-command-line)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [Todo](#todo)


## Description
There are two main classes in the package, Parser and Database. The parser parses information while the database is used to insert/update/select information.
### Parser
* Logging:
    * The parser has logging functionality, See logging description for an explanation of logging
    * The default logging is as follow:
        * Log to /var/log/bgp/parser.log
        * Log level of the file is set to logging.ERROR
        * Log level for printing is set to logging.INFO
* Different parsers:
    * The parser class can run three different processors, detailed below:
    * bgpstream.com data:
        * The class for this parser is BGPStream\_Website\_Parser
        * This class pulls html from bgpstream.com and parses it based on three kinds of events:
            * Possible Hijack (stored in database table hijack)
            * BGP Leak (stored in database table leak)
            * Outage (stored in database table outage)
        * If the entry does not already exist in the database, the information is inserted
        * If the entry does exist, then that entry is updated
        * See database schema for the specific information that is processed
    * Caida as relationship data:
        * The class for this parser is Caida\_AS\_Relationships_Parser
        * First the parser downloads files from http://data.caida.org/datasets/as-relationships/ into a default directory of /tmp/bgp
        * Then the parser unzips all the files
        * Then the parser parses the information based on the file format
            * There are three kinds of file formats:
                * The 'serial-1' as-rel files contain p2p and p2c relationships. 
                    * The format is:
                        * \<provider-as\>|\<customer-as\>|-1
                        * \<peer-as\>|\<peer-as\>|0
                * The 'serial-2' as-rel files add the source of the inference
                    * The Format is:
                        * \<provider-as\>|\<customer-as\>|-1|\<source\>
                        * \<peer-as\>|\<peer-as\>|0|\<source\>
                * The 'serial-1' ppdc-ases files contain the provider-peer customer cones
inferred for each AS.  
                    * Each line specifies an AS and all ASes we infer
to be reachable following a customer link.  
                    * The format is:
                        * \<cone-as\> \<customer-1-as\> \<customer-2-as\> .. \<customer-N-as\>
        * Then the parser adds the information to the database if it doesn't exist
        * Then the parser deletes all the files (unless otherwise specified)
    * BGP Stream data:
        * This gets BGP Stream data using the api described here: https://bgpstream.caida.org/docs/api/pybgpstream
        * The class for this parser is BGP\_Records
        * This data is formatted in a DB\_Info class then stored in the database
        * The api first gets all records
           * If the record is valid, it gets all elements
            * If the record is invalid, stop searching
        * For the specific information stored in the database, refer to the database schema
### Database
* The database is run using postgresql
    * Once the database is set up and you have logged into where it was set up, you can send it commands by doing:
        ```sh
        $ sudo -i -u postgres
        $ psql -d bgp
        ```
    * To be able to create the database tables with postgresql on ubuntu, run these commands:
        ```sh
        $ sudo apt-get update
        $ sudo apt-get install postgresql postgresql-contrib
        ```
* Since the parser takes a database as an argument when initialized, a different database other than the one described here can be used
* The database supports logging
*   The default logging is as follows:
    * Log to /var/log/bgp/parser.log
    * Log level of the file is set to logging.ERROR
    * Log level for printing is set to logging.INFO
* The Database class inherits functions from many other database classes. I know this isn't really how inheritance should work, but I wanted to split up the file into multiple files for readability
* The Database class can add information to the database, and also select information for usability in other scripts
#### Database Schema
All tables are stored in database bgp, with test tables in bgp\_test
##### as\_relationships Schema
* Note that because there are multiple different formats, some fields may be empty
    * The 'serial-1' as-rel files contain p2p and p2c relationships. 
        * The format is:
            * \<provider-as\>|\<customer-as\>|-1
            * \<peer-as\>|\<peer-as\>|0
    * The 'serial-2' as-rel files add the source of the inference
        * The Format is:
            * \<provider-as\>|\<customer-as\>|-1|\<source\>
            * \<peer-as\>|\<peer-as\>|0|\<source\>
    * The 'serial-1' ppdc-ases files contain the provider-peer customer cones
inferred for each AS.  
        * Each line specifies an AS and all ASes we infer
to be reachable following a customer link.  
        * The format is:
            * \<cone-as\> \<customer-1-as\> \<customer-2-as\> .. \<customer-N-as\>
* relationships\_id: id of relationship object in table *(primary key)*
* cone\_as: AS number *(integer)*
* customer\_as: List of AS numbers *(integer[])*
* provider\_as: AS number *(integer)*
* peer\_as\_1: AS number *(integer)*
* peer\_as\_2: AS number *(integer)*
* Source: *(character varying(25))*
* Create Table SQL commands:
    ```sql
    CREATE TABLE as_relationships (
        relationships_id serial PRIMARY KEY,
        cone_as integer,
        customer_as integer ARRAY,
        provider_as integer,
        peer_as_1 integer,
        peer_as_2 integer,
        source varchar (25)
    );
    ```
##### hijack Schema
* This data comes from bgpstream.com possible hijack events
* hijack\_id: id of hijack object in table *(primary key)*
* country: string of country, usually two letters *(character varying(50))*
* detected\_as\_path: string of ASNs *(character varying(250))*
    * Example: '38719 8932 39216 205906 205906 202055'
* detected\_by\_bgpmon\_peers: number of BGPMon peers detected by *(integer)*
* detected\_origin\_name: origin AS name *(character varying(100))*
* detected\_origin\_number: origin ASN *(integer)*
* start\_time: start time in utc *(timestamp without time zone)*
* end\_time: end time in utc *(timestamp without time zone)*
* event\_number: number assigned to each event by bgpstream.com *(integer)* 
* event\_type: 'Possible Hijack' *(character varying(50))*
* expected\_origin\_name: expected origin AS name *(character varying(100))*
* expected\_origin\_number: expected origin ASN *(integer)*
* expected\_prefix: prefix that was expected *(character varying(100))*
    * Example: '103.243.5.0/24'
* more\_specific\_prefix: prefix that was used *(character varying(100))*
    * Example: '103.243.5.0/24'
* url: link to in depth details on event *(character varying(250))*
    * Example: '/event/143947'
* Create Table SQL commands:
    ```sql
    CREATE TABLE hijack (
        hijack_id serial PRIMARY KEY,
        country varchar (50),
        detected_as_path varchar (250),
        detected_by_bgpmon_peers integer,
        detected_origin_name varchar (100),
        detected_origin_number integer,
        start_time timestamp,
        end_time timestamp,
        event_number integer,
        event_type varchar (50),
        expected_origin_name varchar (100),
        expected_origin_number integer,
        expected_prefix varchar (100),
        more_specific_prefix varchar (100),
        url varchar (250)
    );
    ```
##### leak Schema
* This data comes from bgpstream.com BGP Leak events
* leak\_id: id of leak object in table *(primary key)*
* country: string of country, usually two letters *(character varying(50))*
* detected\_by\_bgpmon\_peers: number of BGPMon peers detected by *(integer)*
* start\_time: start time in utc *(timestamp without time zone)*
* end\_time: end time in utc *(timestamp without time zone)*
* event\_number: number assigned to each event by bgpstream.com *(integer)* 
* event\_type: 'BGP Leak' *(character varying(50))*
* example\_as\_path: AS path *(character varying(250))*
    * Example: '135646 64515 65534 20473 3356 6453 10089 9587 15932 4788 1299 7473 132167 136975 133524 133384'
* leaked\_prefix: prefix that was leaked *(character varying(250))*
    * Example: '103.243.5.0/24'
* leaked\_to\_name: list of AS names *(character varying(200)[])*
* leaked\_to\_number: list of AS numbers *(integer[])*
* leaker\_as\_name: Leaker AS name *(character varying(100))*
* leaker\_as\_number: Leaker ASN *(integer)*
* origin\_as\_name: Origin AS name *(character varying(100))*
* origin\_as\_number: Origin ASN *(integer)*
* url: link to in depth details on event *(character varying(250))*
    * Example: '/event/143947'
* Create Table SQL commands:
    ```sql
    CREATE TABLE leak (
        leak_id serial PRIMARY KEY,
        country varchar (50),
        detected_by_bgpmon_peers integer,
        start_time timestamp,
        end_time timestamp,
        event_number integer,
        event_type varchar (50),
        example_as_path varchar (250),
        leaked_prefix varchar (250),
        leaked_to_name varchar (200) ARRAY,
        leaked_to_number integer ARRAY,
        leaker_as_name varchar (100),
        leaker_as_number integer,
        origin_as_name varchar (100),
        origin_as_number integer,
        url varchar (250)
    );
    ```
##### outage Schema
* This data comes from bgpstream.com BGP Outage events
* outage\_id: id of outage object in table *(primary key)*
* as\_name: AS name *(character varying(150))*
* as\_number: ASN *(integer)*
* country: string of country, usually two letters *(character varying(50))*
* start\_time: start time in utc *(timestamp without time zone)*
* end\_time: end time in utc *(timestamp without time zone)*
* event\_number: number assigned to each event by bgpstream.com *(integer)* 
* event\_type: 'Outage' *(character varying(50))*
* number\_prefixes\_affected: Number of the prefixes that where affected *(integer)*
*percent\_prefixes\_affected: percentage (out of 100) of prefixes that where affected *(smallint)*
* url: link to in depth details on event *(character varying(150))*
    * Example: '/event/143947'
    * Create Table SQL commands:
    ```sql
    CREATE TABLE outage (
        outage_id serial PRIMARY KEY,
        as_name varchar (150),
        as_number integer,
        country varchar (25),
        start_time timestamp,
        end_time timestamp,
        event_number integer,
        event_type varchar (25),
        number_prefixes_affected integer,
        percent_prefixes_affected smallint,
        url varchar(150)
    );
    ```
##### records Schema
* This data comes from the BGP Stream retrieved with pybgpstream
* This table is for the record information only
* record\_id: id of record object in table *(primary key)*
* record\_status: ‘valid’, ‘filtered-source’, ‘empty-source’, ‘corrupted-source’, or ‘unknown’ *(varchar(25))*
* record\_type: 'update', 'rib', or 'unknown' *(varchar(25))*
* record\_collector: name of the collector that created the record*(varchar(50))*
* record\_project: name of the project that created the collector *(varchar(50))*
* record\_time: time that the record was generated by the collector *(integer)*
* Create Table SQL commands:
    ```sql
    CREATE TABLE records (
        record_id serial PRIMARY KEY,
        record_status varchar (25),
        record_type varchar (25),
        record_collector varchar (50),
        record_project varchar (50),
        record_time integer
    );
    ```
##### elements Schema
* This data comes from the BGP Stream retrieved with pybgpstream
* This table is for the element information only
* For each record there are multiple elements
* element\_id: id of element object in table *(primary key)*
* element\_type: 'R' (rib), 'A' (announcement), 'W' (withdrawal), 'S' (peerstate), ''(unknown) *(varchar(50))*
* element\_peer\_asn: ASN if the peer this element was recieved from *(integer)*
* element\_peer\_address: The IP address of the peer that this element was recieved from *(varchar(25))*
* as\_path: list of ASNs in AS path *(integer[])*
* prefix: prefix *(varchar(25))*
* next\_hop: The next hop IP address *(varchar(25))*
* record\_id: Corresponding record's id *(integer)*
* Create Table SQL commands:
    ```sql
    CREATE TABLE elements (
        element_id serial PRIMARY KEY,
        element_type varchar(50),
        element_peer_asn integer,
        element_peer_address varchar (25),
        as_path integer ARRAY,
        prefix varchar (25),
        next_hop varchar (25),
        record_id integer   
    );
    ```
##### communities Schema
* This data comes from the BGP Stream retrieved with pybgpstream
* This table is for the community information only
* For each record there are multiple elements
* Each element contains a community, a list of ASNs and Values
* community\_id: id of community object in table *(primary key)*
* asn: ASN *(integer)*
* value: value of ASN *(integer)*
* element_id: corresponding element id *(integer)*
* Create Table SQL commands:
    ```sql
    CREATE TABLE communities (
        community_id serial PRIMARY KEY,
        asn integer,
        value integer,
        element_id integer
    );
    ```
### Logging Description
* Quick Explanation of logging below:
    * There are five logging levels:
        * (highest) logging.CRITICAL *Serious error, program cannot continue to run*
        * logging.ERROR *Serious problem, software cannot complete a task*
        * logging.WARNING *Something unexpected has happened, but software is still working*
        * logging.INFO *Confirms that things are working as expected*
        * (lowest) logging.DEBUG *Detailed info, only of interest when diagnosing problems*
    * When a logging level is set, it will log everything at that log level and higher
        * For example, if logging is set to logging.ERROR, it will only log logging.ERROR and logging.CRITICAL

## Installation
##### Database installation
* For the database to be able to run, you must have set up the postgresql database with the credentials located in /etc/bgp/bgp.conf and the test postgresql database credentials located in /etc/bgp/bgp.conf
* For more information on how to setup postgresql databases, refer to: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04
##### pybgpstream installation:
* This program requires pybgpstream to be able to parse bgpstream data
* This will have the latest information on how to install pybgpstream and its dependencies: https://bgpstream.caida.org/docs/install/pybgpstream
* This was correct as of 8/9/17:
```sh
$ sudo apt-get install zlib1g-dev libbz2-dev libcurl4-openssl-dev
$ mkdir ~/src
$ cd ~/src/
$ curl -O https://research.wand.net.nz/software/wandio/wandio-1.0.4.tar.gz
$ tar zxf wandio-1.0.4.tar.gz
$ cd wandio-1.0.4/
$ ./configure
$ make
$ sudo make install
$ sudo ldconfig
$ cd ~/src/
$ curl -O http://bgpstream.caida.org/bundles/caidabgpstreamwebhomepage/dists/bgpstream-1.2.1.tar.gz
$ tar zxf bgpstream-1.2.1.tar.gz
$ cd bgpstream-1.2.1/
$ ./configure
$ make
$ make check
$ sudo make install
$ sudo ldconfig
```
##### lib\_bgp\_data installation:
Once postgresql database is set up, and pybgpstream is set up:
```sh
pip3 install lib_bgp_data
```
##### testing your installation:
Coming Soon

## Usage
### In a Script
##### Initializing the Database and Parser

> The default params for the database and parser are:   
> log\_name = "database.log"  # For Database   
> log\_name = "parser.log"  # For Parser   
> log\_file\_level = logging.ERROR  # Logging level for file   
> log\_stream\_level = logging.INFO  # Logging level for printing   
> This will cause any errors to be appended to the log file   
> This will also cause any information (and higher) to be printed.   
> See [logging description](#logging-description) for more details   

Initialize with default logging:
```python
from lib_bgp_data import Database, Parser
database = Database()
parser = Parser(database)
```
Initialize for errors only (print nothing):
```python
from lib_bgp_data import Database, Parser
import logging
database = Database(log_stream_level=logging.ERROR)
parser = Parser(database, log_stream_level=logging.ERROR)
```
Initialize for debugging:
> This will print all debug statements and above   
> This will also log all info statements and above   
```python
from lib_bgp_data import Database, Parser
import logging
database = Database(log_file_level=logging.INFO,
                    log_stream_level=logging.DEBUG
                    )
parser = Parser(database,
                log_file_level=logging.INFO,
                log_stream_level=logging.DEBUG
                )
```

#### How to Run BGPStream\_Website\_Parser
This will get data from bgpstream.com and insert it into the database
Default arguments for the bgpstream parser:
> parellel = None   
> This doesn't run in parallel even though it can, because   
> bgpstream.com cuts off the program after about 100 rows.   
> If you are doing a very small amount of rows, then you can parse in parallel for speed.   
   
> row\_limit = None   
> The row\_limit is how many rows of data from bgpstream.com to parse   
> This was mainly added for testing purposes   
   
Default argument for running the bgpstream parser:   
> max\_processes=multiprocessing.cpu\_count()   
> Note that this argument will only be used if parallel argument is not None   
> Defines the number of processes to run at any given time   
To parse data from bgpstream.com with defaults (recommended):
```python
from lib_bgp_data import Database, Parser
database = Database()
parser = Parser(database)
parser.run_bgpstream_parser()
```
To parse data from bgpstream.com in parallel for testing:
```python
from lib_bgp_data import Database, Parser
database = Database()
# Will make the bgpstream_parser run in parallel for 10 rows
bgp_stream_args = {"parallel": True, "row_limit": 10}
parser = Parser(database, bgp_stream_args=bgp_stream_args)
# Runs in parallel with 5 processes at most at any given time
parser.run_bgpstream_parser(max_processes=5)
```
#### How to Run Caida\_AS\_Relationships\_Parser
This will get data from http://data.caida.org/datasets/as-relationships/ and insert it into the database
Default arguments for the as\_relationships parser:
> path = "/tmp/bgp"   
> This is the default path for the files to be downloaded to   

Default argument for running the as\_relationships parser:
> clean\_up=True   
> If clean\_up == True, downloaded files will be deleted after parsing   
> downloaded=False   
> If downloaded == False, the directory will be deleted and the files will be downloaded again   
To parse as\_relationships data with defaults (recommended):
```python
from lib_bgp_data import Database, Parser
database = Database()
parser = Parser(database)
parser.run_as_relationship_parser()
```
To parse as\_relationships data in non default location, without deleting files, after they have already been downloaded:
```python
from lib_bgp_data import Database, Parser
database = Database()
# Will make the bgpstream_parser run in parallel for 10 rows
as_relationships_args = {"path": "/tmp/not_default/"}
parser = Parser(database,  as_relationships_args=as_relationships_args)
parser.run_as_relationship_parser(downloaded=True, clean_up=False)
```
#### How to Run BGP\_Records to get BGPStream data
This will get data from BGPStream and insert it into the database   
Start and end must be entered as a datatime object   
To parse bgpstream data with start and end:
```python
from datetime import datetime
from lib_bgp_data import Database, Parser
database = Database()
parser = Parser(database)
start = datetime(2015, 8, 1, 8, 20, 11)
end = start
parser.run_as_announcements_parser(start, end)
```

### From the Command Line
Coming Soon

## Development/Contributing
This will install lib\_bgp\_data and any dependencies
```sh
git clone https://github.com/jfuruness/lib_bgp_data.git
cd lib_bgp_data
pip install -e .
```
1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request and email (I don't check github often)

## History

* 0.1.0 - Initial setup

## Credits

https://bgpstream.caida.org/docs/tutorials/pybgpstream

## License

MIT

## TODO

