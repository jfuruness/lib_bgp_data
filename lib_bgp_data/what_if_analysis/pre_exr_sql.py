#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains sql to be run before the extrapolator"""

from .sql_utils import Policies, Validity
from .sql_utils import create_gist, create_index, create_btree
from .sql_utils import create_table_w_gist
from .sql_utils import create_table_w_btree
from .sql_utils import create_table_w_btree_asn

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

def get_pre_exr_sql(valid_before_time):

    # MUST BE IN EPOCH!!!!!!
    all_sql = []
    create_index_sql = []
    for table in ["mrt_announcements",
                  "rov_validity",
                  "unique_prefix_origins",
                  "hijack_temp"]:
        create_index_sql.append(create_gist(table))
    create_index_sql.append(create_index("mrt_announcements", "mrt_index"))
    create_index_sql.append(create_index("rov_validity", "validity"))

    all_sql.extend(create_index_sql)

    all_sql += "VACUUM ANALYZE;"

    all_policies = {Policies.ASN.value: {Validity.invalid.value: "= -2",
                                         Validity.valid.value: "!= -2"},
                    Policies.LENGTH.value: {Validity.invalid.value: "= -1",
                                           Validity.valid.value: "!= -1"},
                    Policies.ROV.value: {Validity.invalid.value: "< 0",
                                         Validity.valid.value: ">= 0"}}

    # We want:
    # invalid asn:
    # invalid and hijacked prefix origins
    prefix_origin_sql = []
    for policy, v_dict in all_policies.items():
        # Gets invalid and hijacked prefix origins
        prefix_origin_sql.extend(
            create_table_w_gist(
                "invalid_{}_hijacked_prefix_origins".format(policy),
                """SELECT DISTINCT u.prefix, u.origin, h.url FROM unique_prefix_origins u
                    INNER JOIN rov_validity r ON r.prefix = u.prefix AND r.origin = u.origin
                    INNER JOIN hijack_temp h ON h.prefix = r.prefix AND h.origin = r.origin
                WHERE r.validity {}""".format(v_dict[Validity.invalid.value])))

        prefix_origin_sql.extend(
            create_table_w_gist(
                "invalid_{}_not_hijacked_prefix_origins".format(policy),
               """SELECT DISTINCT u.prefix, u.origin FROM unique_prefix_origins u
                    INNER JOIN rov_validity r ON r.prefix = u.prefix AND r.origin = u.origin
                    LEFT JOIN hijack_temp h ON h.prefix = r.prefix AND h.origin = r.origin
                    WHERE r.validity {} AND h.prefix IS NULL
                """.format(v_dict[Validity.invalid.value])))

        prefix_origin_sql.extend(
            create_table_w_gist(
                "invalid_{}_extra_prefix_origins".format(policy),
                """SELECT DISTINCT r.prefix,
                                   r.origin,
                                   u.prefix AS extra_prefix,
                                   u.origin AS extra_origin
                        FROM unique_prefix_origins u
                    INNER JOIN rov_validity r
                        ON r.prefix << u.prefix
                            OR (r.prefix = u.prefix AND r.origin != u.origin)
                    LEFT JOIN (
                            SELECT prefix, origin
                               FROM rov_validity
                            WHERE validity {0}) r2
                        ON r2.prefix = u.prefix AND r2.origin = u.origin
                    WHERE r2.prefix IS NULL AND r.validity {0}
                """.format(v_dict[Validity.invalid.value]),
                extra=True))

        prefix_origin_sql.extend(
            create_table_w_gist(
                "valid_{}_hijacked_prefix_origins".format(policy),
                """SELECT DISTINCT u.prefix, u.origin FROM unique_prefix_origins u
                    INNER JOIN rov_validity r ON r.prefix = u.prefix AND r.origin = u.origin
                    INNER JOIN hijack_temp h ON h.prefix = r.prefix AND h.origin = r.origin
                WHERE r.validity {}
                """.format(v_dict[Validity.invalid.value])))


    all_sql.extend(prefix_origin_sql)

    interesting_sql = []
    interesting_sql.extend(
        create_table_w_gist(
            "interesting_prefix_origins",
            """SELECT prefix, origin FROM invalid_rov_hijacked_prefix_origins
            UNION
            SELECT prefix, origin FROM invalid_rov_not_hijacked_prefix_origins
            UNION
            SELECT extra_prefix, extra_origin FROM invalid_rov_extra_prefix_origins
            UNION
            SELECT prefix, origin FROM valid_rov_prefix_origins"""))

    interesting_sql.extend("VACUUM ANALYZE;")

    interesting_sql.extend(
        create_table_w_gist(
            "interesting_ann",
            """SELECT DISTINCT ON (m.prefix, m.origin, m.time)
                      m.prefix,
                      m.as_path,
                      m.origin,
                      m.time
                FROM mrt_announcements m
            INNER JOIN interesting_prefix_origins i
                ON i.prefix = m.prefix AND i.origin = m.origin"""))

    interesting_sql.extend("ALTER TABLE interesting_ann ADD COLUMN mrt_index SERIAL PRIMARY KEY;")

    for col in ["time", "mrt_index"]:
        interesting_sql.append(create_index("interesting_ann", col))

    interesting_sql.extend("VACUUM ANALYZE;")
    all_sql.extend(interesting_sql)

    ann_indexes_sql = [
       create_table_w_btree(
            "invalid_{}_hijacked_ann_indexes",
            """SELECT m.mrt_index FROM interesting_ann m
                    INNER JOIN invalid_{}_hijacked_prefix_origins i
                        ON i.prefix = m.prefix AND i.origin = m.origin"""),
        create_table_w_btree(
            "invalid_{}_not_hijacked_ann_indexes",
            """SELECT m.mrt_index FROM interesting_ann m
                INNER JOIN invalid_{}_not_hijacked_prefix_origins i
                    ON i.prefix = m.prefix AND i.origin = m.origin""")
        create_table_w_btree(
            "invalid_{}_extra_ann_indexes",
            """SELECT m.mrt_index, m2.mrt_index AS extra_mrt_index
                    FROM interesting_ann m
                INNER JOIN invalid_{}_extra_prefix_origins i
                    ON i.prefix = m.prefix AND i.origin = m.origin
                INNER JOIN interesting_ann m2
                    ON i.extra_prefix = m2.prefix AND i.extra_origin = m2.origin""",
            extra=True)
        create_table_w_btree(
            "valid_{}_hijacked_ann_indexes",
            """SELECT m.mrt_index FROM interesting_announcements m
                    INNER JOIN valid_{}_hijacked_prefix_origins i
                        ON i.prefix = m.prefix AND i.origin = m.origin""")]

    for policy in [x.value for x in Policies.__members__.values()]:
        for table_sql in ann_indexes_sql:
            for sql in table_sql:
                all_sql.append(sql.format(policy))

    ann_indexes_w_time_sql = [
        create_table_w_btree(
            "invalid_{}_time_extra_ann_indexes",
            """SELECT m.mrt_index, m2.mrt_index AS extra_mrt_index FROM interesting_ann m
                INNER JOIN invalid_asn_extra_prefix_origins i
                    ON i.prefix = m.prefix AND i.origin = m.origin
                INNER JOIN interesting_ann m2
                    ON i.extra_prefix = m2.prefix AND i.extra_origin = m2.origin
            WHERE m.time > {1} AND m2.time < {1}""",
            extra=True),
        create_table_w_btree(
            "invalid_{}_time_hijacked_ann_indexes",
            """SELECT m.mrt_index FROM interesting_ann m
                INNER JOIN invalid_{}_hijacked_ann_indexes i
                    ON i.mrt_index = m.mrt_index
                WHERE m.time > {}"""),
        create_table_w_btree(
            "invalid_{}_time_not_hijacked_ann_indexes",
            """SELECT m.mrt_index FROM interesting_ann m
                INNER JOIN invalid_asn_not_hijacked_ann_indexes i
                    ON i.mrt_index = m.mrt_index
                WHERE m.time > {}"""),
        create_table_w_btree(
            "invalid_{}_time_ann_indexes",
            """SELECT mrt_index
                    FROM invalid_{0}_time_not_hijacked_ann_indexes
                UNION
               SELECT mrt_index
                    FROM invalid_{0}_time_hijacked_ann_indexes"""),
        create_table_w_btree(
            "invalid_{}_time_extra_ann_indexes",
            """SELECT DISTINCT m.mrt_index, m2.mrt_index AS extra_mrt_index
                    FROM interesting_ann m
               INNER JOIN invalid_{}_time_ann_indexes i
                    ON i.mrt_index = m.mrt_index
               INNER JOIN interest_ann m2
                    ON i.mrt_index != m2.mrt_index AND
                        (m.prefix << m2.prefix
                        OR (m.prefix = m2.prefix AND m.origin != m2.origin))""",
            extra=True)]

    for policy in [x.value for x in Policies.__members__.values()]:
        for table_sql in ann_indexes_w_time_sql:
            for sql in table_sql:
                all_sql.append(sql.format(policy,valid_before_time))

    return all_sql
