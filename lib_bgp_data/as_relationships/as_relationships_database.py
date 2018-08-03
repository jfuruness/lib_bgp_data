class AS_Relationship_DB:
    def __init__(self):
        pass
    def add_as_relationship(self, row):
        try:
            sql = """SELECT * FROM as_relationships 
                     WHERE cone_as = %s AND
                     customer_as = %s AND
                     provider_as = %s AND
                     peer_as_1 = %s AND
                     peer_as_2 = %s AND
                     source = %s"""
            customers = row.get("customer_as")
            if customers is not None and not isinstance(customers, list):
                customers = [int(customers)]
            elif customers is not None:
                customers = [int(x) for x in customers]
            data = [row.get("cone_as"),
                    customers,
                    row.get("provider_as"),
                    row.get("peer_as_1"),
                    row.get("peer_as_2"),
                    row.get("source")
                   ]
            self.cursor.execute(sql, self.sanitize_data(data))
            results = self.cursor.fetchall()
            if len(results) == 0:
                sql = """INSERT INTO as_relationships
                         (cone_as, customer_as, provider_as, peer_as_1, 
                         peer_as_2, source) 
                         VALUES (%s, %s, %s, %s, %s, %s)"""
                self.cursor.execute(sql, self.sanitize_data(data))
                action = "inserted"
            else:
                action = "updated"
            if self.verbose:
                print("{} as_relationships".format(action))
        except Exception as e:
            self.print_error(locals())
            raise e

