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
Also note: for a list of queriable endpoints: https://rpki-validator.ripe.net/swagger-ui.html#/Input32validation
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
