--#https://stackoverflow.com/a/17262097
--RAW DATA:

WITH unnested_ases AS (
--full outer join to get the no rib data
    --Why is this like this?
    --because first we want each asn per test
    --to get that we must unnest the asns, but we want to preserve the list index
    --so we use with ordinality
    --https://stackoverflow.com/questions/8760419/postgresql-unnest-with-element-number
    --but it gets worse. Because we add each policy for each list index,
    --we must unnest again. Insane in the membrane

    SELECT all_ases.asn,
           all_ases.t_name AS table_name,
           q.as_type AS adopting_or_not,
           q.list_index_one_added - 1 AS list_index,  --minus 1 because postgres starts at 1
           vals_table.policy_val,
           (CASE
                WHEN q.as_type = TRUE
            THEN vals_table.policy_val
                ELSE 0
            END) AS adopted_policy
    FROM (
        SELECT * FROM (
            SELECT 0 AS t_name, edge_ases.asn, edge_ases.as_types
                FROM edge_ases) edge_ases_w_name
        UNION ALL
        SELECT * FROM (
            SELECT 1 AS t_name, etc_ases.asn, etc_ases.as_types
                FROM etc_ases) etc_ases_w_name
        UNION ALL
        SELECT * FROM (
            SELECT 2 AS t_name, top_100_ases.asn, top_100_ases.as_types
                FROM top_100_ases) top_100_ases_w_name
        ) all_ases
        ---NOTE: this can be written with implicit cross join lateral
        ---but this if more verbose
    LEFT JOIN LATERAL UNNEST(all_ases.as_types)
         WITH ORDINALITY AS q(as_type, list_index_one_added)
            ON TRUE

     CROSS JOIN (
        SELECT DISTINCT policy_val
            FROM attacker_victims
        ) vals_table
   )


WITH traceback_base AS (
    SELECT ro.asn,
           ro.prefix,
           ro.origin,
           av.attacker_origin,
           av.attacker_prefix,
           av.victim_origin,
           av.victim_prefix,
           av.attack_type,
           av.percent_iter,
           unnested_ases.list_index,
           unnested_ases.policy_val,
           unnested_ases.adopting_or_not
        FROM rovpp_extrapolator_rib_out ro
    INNER JOIN attacker_victims av
        ON av.attacker_prefix = ro.prefix OR av.victim_prefix = ro.prefix
    INNER JOIN unnested_ases
        ON unnested_ases.asn = ro.asn
            AND unnested_ases.list_index = av.list_index,
            AND unnested_ases.policy_val = av.policy_val)
--------This gets the aggregate from the raw data
WITH RECURSIVE tr(
    og_asn,
    end_state,
    received_from_asn,
    prefix,
    origin,
    as_path,
    list_index,
    policy_val,
    prev_prefix,
    prev_origin,
    attacker_prefix,
    attacker_origin,
    victim_prefix,
    victim_origin,
    percent_iter,
    attack_type,
    adopting_or_not,
    bhole_to_bhole,
    bhole_to_hijack,
    bhole_to_preventive,
    bhole_to_prefix,
    hijack_to_bhole,
    hijack_to_hijack,
    hijack_to_preventive,
    hijack_to_prefix,
    preventive_to_bhole,
    preventive_to_hijack,
    preventive_to_preventive,
    preventive_to_prefix,
    prefix_to_bhole,
    prefix_to_hijack,
    prefix_to_preventive,
    prefix_to_prefix)
AS (
  SELECT asn AS og_asn,
         asn,
         received_from_asn,
         prefix,
         origin,
         ARRAY[asn]::bigint[] as as_path,
         list_index,
         policy_val,
         prefix AS prev_prefix,
         origin AS prev_origin,
         attacker_prefix,
         attacker_origin,
         victim_prefix,
         victim_origin,
         percent_iter,
         attack_type,
         adopting_or_not,
         0 AS bhole_to_bhole_adopting,
         0 AS bhole_to_hijack_adopting,
         0 AS bhole_to_preventive_adopting,
         0 AS bhole_to_prefix_adopting,
         0 AS hijack_to_bhole_adopting,
         0 AS hijack_to_hijack_adopting,
         0 AS hijack_to_preventive_adopting,
         0 AS hijack_to_prefix_adopting,
         0 AS preventive_to_bhole_adopting,
         0 AS preventive_to_hijack_adopting,
         0 AS preventive_to_preventive_adopting,
         0 AS preventive_to_prefix_adopting,
         0 AS prefix_to_bhole_adopting,
         0 AS prefix_to_hijack_adopting,
         0 AS prefix_to_preventive_adopting,
         0 AS prefix_to_prefix_adopting,
         0 AS bhole_to_bhole_non_adopting,
         0 AS bhole_to_hijack_non_adopting,
         0 AS bhole_to_preventive_non_adopting,
         0 AS bhole_to_prefix_non_adopting,
         0 AS hijack_to_bhole_non_adopting,
         0 AS hijack_to_hijack_non_adopting,
         0 AS hijack_to_preventive_non_adopting,
         0 AS hijack_to_prefix_non_adopting,
         0 AS preventive_to_bhole_non_adopting,
         0 AS preventive_to_hijack_non_adopting,
         0 AS preventive_to_preventive_non_adopting,
         0 AS preventive_to_prefix_non_adopting,
         0 AS prefix_to_bhole_non_adopting,
         0 AS prefix_to_hijack_non_adopting,
         0 AS prefix_to_preventive_non_adopting,
         0 AS prefix_to_prefix_non_adopting,

    FROM traceback_base
  UNION
  SELECT tr.og_asn, tr.received_from_asn,
         (CASE 
            WHEN COALESCE(ARRAY_LENGTH(tr.as_path, 1)) <=64
          THEN t.received_from_asn
            ELSE
               NULL
           END),
         tr.prefix,
         tr.origin,
         (CASE
            WHEN t.asn IS NOT NULL
          THEN ARRAY_APPEND(tr.as_path, t.asn)
            ELSE tr.as_path
          END),
         tr.list_index,
         tr.policy_val
         t.prefix AS prev_prefix,
         t.origin AS prev_origin,
         tr.attacker_prefix,
         tr.attacker_origin,
         tr.victim_prefix,
         tr.victim_origin,
         tr.percent_iter,
         tr.attack_type,
         tr.adopting_or_not,
--------------NOTE: because of all these case statements
--you cannot group by adopting or not
-- because in the middle of the path some adopt and some do not!
         tr.bhole_to_bhole_adopting + (CASE
                                        WHEN tr.prev_origin=64512
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = TRUE
                                      THEN 1
                                        ELSE 0
                                      END) AS bhole_to_bhole_adopting,
         tr.bhole_to_hijack_adopting + (CASE
                                        WHEN tr.prev_origin=64512
                                            AND t.origin = tr.attacker_origin
                                            AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = TRUE
                                        THEN 1
                                          ELSE 0
                                        END) AS bhole_to_hijack_adopting,
         tr.bhole_to_preventive_adopting + (CASE
                                            WHEN tr.prev_origin=64512
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS bhole_to_preventive_adopting,
         tr.bhole_to_prefix_adopting + (CASE
                                         WHEN tr.prev_origin=64512
                                             AND t.origin = tr.victim_origin
                                             AND t.prefix = tr.victim_prefix
                                            AND t.adopting_or_not = TRUE
                                         THEN 1
                                           ELSE 0
                                         END) AS bhole_to_prefix_adopting,
         tr.hijack_to_bhole_adopting + (CASE
                                        WHEN tr.prev_origin = tr.attacker_origin
                                            AND tr.prev_prefix = tr.attacker_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = TRUE
                                        THEN 1
                                          ELSE 0
                                        END) AS hijack_to_bhole_adopting,
         tr.hijack_to_hijack_adopting + (CASE
                                         WHEN tr.prev_origin = tr.attacker_origin
                                             AND tr.prev_prefix = tr.attacker_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = TRUE
                                         THEN 1
                                           ELSE 0
                                         END) AS hijack_to_bhole_adopting,
         tr.hijack_to_preventive_adopting + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.attacker_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS hijack_to_preventive_adopting,
         tr.hijack_to_prefix_adopting + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.attacker_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.victim_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS hijack_to_prefix_adopting,
         tr.preventive_to_bhole_adopting + (CASE
                                        WHEN tr.prev_origin = tr.attacker_origin
                                            AND tr.prev_prefix = tr.victim_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = TRUE
                                        THEN 1
                                          ELSE 0
                                        END) AS preventive_to_bhole_adopting,
         tr.preventive_to_hijack_adopting + (CASE
                                         WHEN tr.prev_origin = tr.attacker_origin
                                             AND tr.prev_prefix = tr.victim_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = TRUE
                                         THEN 1
                                           ELSE 0
                                         END) AS preventive_to_bhole_adopting,
         tr.preventive_to_preventive_adopting + (CASE
                                                WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS preventive_to_preventive_adopting,
         tr.preventive_to_prefix_adopting + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.victim_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS preventive_to_prefix_adopting,
         tr.prefix_to_bhole_adopting + (CASE
                                        WHEN tr.prev_origin = tr.victim_origin
                                            AND tr.prev_prefix = tr.victim_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = TRUE
                                        THEN 1
                                          ELSE 0
                                        END) AS prefix_to_bhole_adopting,
         tr.prefix_to_hijack_adopting + (CASE
                                         WHEN tr.prev_origin = tr.victim_origin
                                             AND tr.prev_prefix = tr.victim_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = TRUE
                                         THEN 1
                                           ELSE 0
                                         END) AS prefix_to_bhole_adopting,
         tr.prefix_to_preventive_adopting + (CASE
                                            WHEN tr.prev_origin = tr.victim_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = TRUE
                                            THEN 1
                                              ELSE 0
                                            END) AS prefix_to_preventive_adopting,
         tr.prefix_to_prefix_adopting + (CASE
                                    WHEN tr.prev_origin = tr.victim_origin
                                        AND tr.prev_prefix = tr.victim_prefix
                                        AND t.origin = tr.victim_origin
                                        AND t.prefix = tr.victim_prefix
                                        AND t.adopting_or_not = TRUE
                                    THEN 1
                                      ELSE 0
                                    END) AS prefix_to_prefix_adopting,

         tr.bhole_to_bhole_collateral + (CASE
                                        WHEN tr.prev_origin=64512
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = FALSE
                                      THEN 1
                                        ELSE 0
                                      END) AS bhole_to_bhole_collateral,
         tr.bhole_to_hijack_collateral + (CASE
                                        WHEN tr.prev_origin=64512
                                            AND t.origin = tr.attacker_origin
                                            AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = FALSE
                                        THEN 1
                                          ELSE 0
                                        END) AS bhole_to_hijack_collateral,
         tr.bhole_to_preventive_collateral + (CASE
                                            WHEN tr.prev_origin=64512
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS bhole_to_preventive_collateral,
         tr.bhole_to_prefix_collateral + (CASE
                                         WHEN tr.prev_origin=64512
                                             AND t.origin = tr.victim_origin
                                             AND t.prefix = tr.victim_prefix
                                            AND t.adopting_or_not = FALSE
                                         THEN 1
                                           ELSE 0
                                         END) AS bhole_to_prefix_collateral,
         tr.hijack_to_bhole_collateral + (CASE
                                        WHEN tr.prev_origin = tr.attacker_origin
                                            AND tr.prev_prefix = tr.attacker_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = FALSE
                                        THEN 1
                                          ELSE 0
                                        END) AS hijack_to_bhole_collateral,
         tr.hijack_to_hijack_collateral + (CASE
                                         WHEN tr.prev_origin = tr.attacker_origin
                                             AND tr.prev_prefix = tr.attacker_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = FALSE
                                         THEN 1
                                           ELSE 0
                                         END) AS hijack_to_bhole_collateral,
         tr.hijack_to_preventive_collateral + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.attacker_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS hijack_to_preventive_collateral,
         tr.hijack_to_prefix_collateral + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.attacker_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.victim_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS hijack_to_prefix_collateral,
         tr.preventive_to_bhole_collateral + (CASE
                                        WHEN tr.prev_origin = tr.attacker_origin
                                            AND tr.prev_prefix = tr.victim_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = FALSE
                                        THEN 1
                                          ELSE 0
                                        END) AS preventive_to_bhole_collateral,
         tr.preventive_to_hijack_collateral + (CASE
                                         WHEN tr.prev_origin = tr.attacker_origin
                                             AND tr.prev_prefix = tr.victim_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = FALSE
                                         THEN 1
                                           ELSE 0
                                         END) AS preventive_to_bhole_collateral,
         tr.preventive_to_preventive_collateral + (CASE
                                                WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS preventive_to_preventive_collateral,
         tr.preventive_to_prefix_collateral + (CASE
                                            WHEN tr.prev_origin = tr.attacker_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.victim_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS preventive_to_prefix_collateral,
         tr.prefix_to_bhole_collateral + (CASE
                                        WHEN tr.prev_origin = tr.victim_origin
                                            AND tr.prev_prefix = tr.victim_prefix
                                            AND t.origin = 64512
                                            AND t.adopting_or_not = FALSE
                                        THEN 1
                                          ELSE 0
                                        END) AS prefix_to_bhole_collateral,
         tr.prefix_to_hijack_collateral + (CASE
                                         WHEN tr.prev_origin = tr.victim_origin
                                             AND tr.prev_prefix = tr.victim_prefix
                                             AND t.origin = tr.attacker_origin
                                             AND t.prefix = tr.attacker_prefix
                                            AND t.adopting_or_not = FALSE
                                         THEN 1
                                           ELSE 0
                                         END) AS prefix_to_bhole_collateral,
         tr.prefix_to_preventive_collateral + (CASE
                                            WHEN tr.prev_origin = tr.victim_origin
                                                AND tr.prev_prefix = tr.victim_prefix
                                                AND t.origin = tr.victim_origin
                                                AND t.prefix = tr.attacker_prefix
                                                AND t.adopting_or_not = FALSE
                                            THEN 1
                                              ELSE 0
                                            END) AS prefix_to_preventive_collateral,
         tr.prefix_to_prefix_collateral + (CASE
                                    WHEN tr.prev_origin = tr.victim_origin
                                        AND tr.prev_prefix = tr.victim_prefix
                                        AND t.origin = tr.victim_origin
                                        AND t.prefix = tr.victim_prefix
                                        AND t.adopting_or_not = FALSE
                                    THEN 1
                                      ELSE 0
                                    END) AS prefix_to_prefix_collateral,

    FROM tr
        LEFT OUTER JOIN traceback_base t
            ON (t.asn = tr.received_from_asn
                AND tr.list_index = t.list_index
                AND tr.policy_val = t.policy_val)
          WHERE tr.received_from_asn IS NOT NULL
)
SELECT unnested_ases.list_index,
       unnested_ases.policy_val,
       tr.percent_iter,
       tr.attack_type,
       tr.attacker_prefix,
       tr.attacker_origin,
       tr.victim_prefix,
       tr.victim_origin,
       --all ases stuff
       unnested_ases.table_name,
        --------------sum the cols here!
        SUM(

    FROM tr
FULL OUTER JOIN unnested_ases
 ON unnested_ases.asn = tr.og_asn
    AND unnested_ases.list_index = tr.list_index
    AND unnested_ases.policy_val = tr.policy_val
WHERE
    tr.received_from_asn IS NULL
GROUP BY
    unnested_ases.list_index,
    unnested_ases.policy_val,
    av.percent_iter,
    av.attack_type,
    av.attacker_prefix,
    av.attacker_origin,
    av.victim_prefix,
    av.victim_origin,
    unnested_ases.table_name;
