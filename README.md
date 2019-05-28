# lib\_bgp\_data
This package contains multiple submodules that are used to gather and manipulate real data in order to simulate snapshots of the internet. The purpose of this is to test different security policies to determine their accuracy, and hopefully find ones that will create a safer, more secure, internet as we know it.

* [lib\_bgp\_data](#lib_bgp_data)
* [Description](#package-description)
* [Main Submodule](#main-submodule)
    * [Short Description](#main-short-description)
    * [Long Description](#main-long-description)
    * [Usage](#main-usage)
    * [Table Schema](#main-table-schema)
    * [Design Choices](#main-design-choices)
    * [Possible Future Improvements](#main-possible-future-improvements)
* [MRT Announcements Submodule](#mrt-announcements-submodule)
    * [Short Description](#mrt-announcements-short-description)
    * [Long Description](#mrt-announcements-long-description)
    * [Usage](#mrt-announcements-usage)
    * [Table Schema](#mrt-announcements-table-schema)
    * [Design Choices](#mrt-announcements-design-choices)
    * [Possible Future Improvements](#mrt-announcements-possible-future-improvements)
* [Relationships Submodule](#relationships-submodule)
    * [Short Description](#relationships-short-description)
    * [Long Description](#relationships-long-description)
    * [Usage](#relationships-usage)
    * [Table Schema](#relationships-table-schema)
    * [Design Choices](#relationships-design-choices)
    * [Possible Future Improvements](#relationships-possible-future-improvements)
* [Roas Submodule](#roas-submodule)
    * [Short Description](#roas-short-description)
    * [Long Description](#roas-long-description)
    * [Usage](#roas-usage)
    * [Table Schema](#roas-table-schema)
    * [Design Choices](#roas-design-choices)
    * [Possible Future Improvements](#roas-possible-future-improvements)
* [Extrapolator Submodule](#extrapolator-submodule)
    * [Short Description](#extrapolator-short-description)
    * [Long Description](#extrapolator-long-description)
    * [Usage](#extrapolator-usage)
    * [Table Schema](#extrapolator-table-schema)
    * [Design Choices](#extrapolator-design-choices)
    * [Possible Future Improvements](#extrapolator-possible-future-improvements)
* [BGPStream Website Submodule](#bgpstream-website-submodule)
    * [Short Description](#bgpstream-website-short-description)
    * [Long Description](#bgpstream-website-long-description)
    * [Usage](#bgpstream-website-usage)
    * [Table Schema](#bgpstream-website-table-schema)
    * [Design Choices](#bgpstream-website-design-choices)
    * [Possible Future Improvements](#bgpstream-website-possible-future-improvements)
* [RPKI Validator Submodule](#rpki-validator-submodule)
    * [Short Description](#rpki-validator-short-description)
    * [Long Description](#rpki-validator-long-description)
    * [Usage](#rpki-validator-usage)
    * [Table Schema](#rpki-validator-table-schema)
    * [Design Choices](#rpki-validator-design-choices)
    * [Possible Future Improvements](#rpki-validator-possible-future-improvements)
* [What if Analysis Submodule](#what-if-analysis-submodule)
    * [Short Description](#what-if-analysis-short-description)
    * [Long Description](#what-if-analysis-long-description)
    * [Usage](#what-if-analysis-usage)
    * [Table Schema](#what-if-analysis-table-schema)
    * [Design Choices](#what-if-analysis-design-choices)
    * [Possible Future Improvements](#what-if-analysis-possible-future-improvements)
* [Utils](#utils)
    * [Description](#utils-description)
    * [Design Choices](#utils-design-choices)
    * [Possible Future Improvements](#utils-possible-future-improvements)
* [Database](#database-submodule)
    * [Description](#database-description)
    * [Usage](#database-usage)
    * [Design Choices](#database-design-choices)
    * [Possible Future Improvements](#database-possible-future-improvements)
* [Logging](#logging-submodule)
    * [Description](#logging-description)
    * [Design Choices](#logging-design-choices)
    * [Possible Future Improvements](#logging-possible-future-improvements)
* [Installation](#installation)
    * [Installation Instructions](#installation-instructions)
    * [Database Installation](#database-instructions)
    * [bgpscanner installation](#bgpscanner-installation)
    * [System Requirements](#system-requirements)
* [Development/Contributing](#developmentcontributing)
* [History](#history)
* [Credits](#credits)
* [Licence](#licence)
* [Todo and Possible Future Improvements](#todopossible-future-improvements)
* [FAQ](#faq)
## Package Description
This README is split up into several subsections for each of the submodules included in this package. Each subsection has it's own descriptions, usage instructions, etc. The main (LINK HERE) subsection details how all of the submodules combine to completely simulate the internet. For an overall view of how the project will work, see below:

<diagram here!!!>

The project first starts by using the mrt parser (LINK HERE) to collect all announcements sent over the internet for a specific time interval. 
<diagram here!!!>
The roas parser (LINK HERE) also downloads all the roas for that time interval.
<diagram here!!!>
A new table is formed with all mrt announcements that have roas. 
<diagram here!!!>
The relationships data (LINK HERE) is also gathered in order to be able to simulate the connections between different AS's on the internet. 
<diagram here!!!>
Each of these data sets gets fed into the extrapolator (LINK HERE) which then creates a graph of the internet and propagates announcements through it. After this stage is complete, there is a graph of the internet, with each AS having all of it's announcements that was propagated to it (with the best announcement for each prefix saved based on gao rexford). 
<diagram here!!>
At this point we also run the rpki validator, (LINK HERE), to get the validity of these announcements. With this data we can know whether an announcement that arrived at a particular AS (from the extrapolator data (LINK HERE) and whether or not that annoucement would have been blocked by standard ROV. 
<diagram here!!!>
We also download all data from bgpstream.com (LINK HERE). Using this data we can know whether an announcement is actually hijacked or not.
<diagram here!!>
 Using the bgpstream.com data (LINK HERE) and the rpki validator data (LINK HERE) we can tell is an announcement would have been blocked or not, and whether or not that announcement would have been blocked correctly. This calculation is done in the last submodule, the what if analysis (LINK HERE). 
 <diagram here!!>
The output of this data is for each as, a table of how many announcements have been blocked correctly, blocked incorrectly, not blocked correctly, and not blocked incorrectly.
<diagram here!!> This data is then available to query form a web interface through the api (LINK HERE), the last last submodule. All of these steps are done in the submodule called main (LINK HERE), which does all of these steps in the fastest most efficient way possible. These results are then displayed on our website at (LINK HERE)
<pic of website here!!>

## Main Submodule
### Main Short description
### Main Long description
### Main Usage
#### In a Script
#### From the Command Line
### Main Table Schema
### Main Design Choices
### Main Possible Future Improvements
## MRT Announcements Submodule
### MRT Announcements Short description
### MRT Announcements Long description
### MRT Announcements Usage
#### In a Script
#### From the Command Line
### MRT Announcements Table Schema
### MRT Announcements Design Choices 
### MRT Announcements Possible Future Improvements
## Relationships Submodule
### Relationships Short description
### Relationships Long description
### Relationships Usage
#### In a Script
#### From the Command Line
### Relationships Table Schema
### Relationships Design Choices
### Relationships Possible Future Improvements
## Roas Submodule
### Roas Short description
### Roas Long description
### Roas Usage
#### In a Script
#### From the Command Line
### Roas Table Schema
### Roas Design Choices
### Roas Possible Future Improvements
## Extrapolator Submodule
### Extrapolator Short description
### Extrapolator Long description
### Extrapolator Usage
#### In a Script
#### From the Command Line
### Extrapolator Table Schema
### Extrapolator Design Choices
### Extrapolator Possible Future Improvements
## BGPStream Website Submodule
### BGPStream Website Short description
### BGPStream Website Long description
### BGPStream Website Usage
#### In a Script
#### From the Command Line
### BGPStream Website Table Schema
### BGPStream Website Design Choices
### BGPStream Website Possible Future Improvements
## RPKI Validator Submodule
### RPKI Validator Short description
### RPKI Validator Long description
### RPKI Validator Usage
#### In a Script
#### From the Command Line
### RPKI Validator Table Schema
### RPKI Validator Design Choices
### RPKI Validator Possible Future Improvements
## What if Analysis Submodule
### What if Analysis  Short description
### What if Analysis  Long description
### What if Analysis  Usage
#### In a Script
#### From the Command Line
### What if Analysis  Table Schema
### What if Analysis  Design Choices
### What if Analysis  Possible Future Improvements
## Utils
### Utils Description
### Utils Design Choices
### Utils Possible Future Improvements
## Database Submodule
### Database Description
### Database Enhancements
### Database  Usage
#### In a Script
#### From the Command Line
### Database Design Choices
### Database Possible Future Improvements
## Logging Submodule
### Logging Description
### Logging Design Choices
### Logging Possible Future Improvements
## Installation
### Installation instructions
### Database Installation
### BGPScanner Installation
### System Requirements
## Development/Contributing
## History
## Credits
## License
## TODO/Possible Future Improvements
command line args
## FAQ
