# Justin-Furuness

A program that parses data from bgpstream.com

## Installation

git clone https://github.com/jfuruness/lib_bgpstream_parser.git 

## Usage

Once you have installed it with pip3 install lib_bgpstream_parser:
On the command line you can type parse_bgpstream.com to print all data from bgpstream.com

Or you can use it in a script by:

import lib_bgpstream_parser
parser = lib_bgpstream_parser.bgpstream_website_announcements.BGPStream_Website_Parser()
parser.parallel_parse()

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

* 0.1.0 - Initial setup

## Credits

N/A

## License

MIT

