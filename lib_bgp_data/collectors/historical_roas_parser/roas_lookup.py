#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
These lookups take a long time because there are so many roas.
"""
__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .tables import Historical_ROAS_Table


def roas_lookup(prefix):
    """Return information about the most recent and most specific ROA that covers prefix"""
    with Historical_ROAS_Table() as db:

        # get the latest expiring roa
        sql = f"""SELECT * FROM {db.name} WHERE prefix <= '{prefix}'
                  ORDER BY prefix DESC, notafter DESC
                  LIMIT 1"""
        data = db.execute(sql)[0]

        # the number of ip addresses allocated by this roa
        minlen = data['prefix'].split('/')[1]
        data['num_addresses'] = (data['maxlen'] - minlen) ** 2
        
        sql = f"SELECT COUNT(*) FROM {db.name} WHERE prefix <= '{prefix'}"
        data['num_roas'] = self.get_count(sql)

        return data


if __name__ == '__main__':
    prefix = '41.191.212.212'
    print(roas_lookup(prefix))


