from ..roas_parser.tables import ROAs_Table

def get_metadata(prefix):

    ret = dict()

    with ROAs_Table() as db:
        # size of block
        sql = f"""
                SELECT MAX(max_length)
                FROM roas
                WHERE prefix <<= '{prefix}'
                """

        max_len = db.execute(sql)[0]['max']

        # no valid ROA
        if not max_len:
            return None

        ret['num_ip_addr'] = 2 ** (32 - max_len)

        # number of roas that cover prefix
        sql = f"""
                SELECT DISTINCT ON (prefix) * 
                FROM roas 
                WHERE 
                    prefix << '{prefix}'
                    AND
                    masklen(prefix) = (
                        SELECT MAX(masklen(prefix))
                        FROM roas
                        WHERE prefix << '{prefix}')
                ORDER BY
                    prefix,
                    created_at DESC;
                """

        roas = db.execute(sql)
        ret['num_roas'] = len(roas)

        ret['most_recent'] = roas[0]['created_at']
       
        return ret
 
if __name__ == '__main__':
    print(get_metadata('120.28.0.0/16'))
