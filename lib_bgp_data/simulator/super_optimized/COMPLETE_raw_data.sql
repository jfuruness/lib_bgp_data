--#https://stackoverflow.com/a/17262097
--RAW DATA:

WITH RECURSIVE tr(
    og_asn, asn, received_from_asn,
    prefix, origin, as_path, list_index, policy_val)
AS (
  SELECT asn AS og_asn, asn, received_from_asn, prefix,
         origin, ARRAY[asn]::bigint[] as as_path,
         list_index, policy_val
    FROM rovpp_extrapolator_rib_out
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
    FROM tr
        LEFT OUTER JOIN rovpp_extrapolator_rib_out t
            ON (t.asn = tr.received_from_asn
                AND tr.list_index = t.list_index
                AND tr.policy_val = t.policy_val)
          WHERE tr.received_from_asn IS NOT NULL
)
SELECT tr.og_asn, tr.asn AS end_state,
       tr.prefix, tr.origin,
       tr.as_path,
       --attacker victim stuff
       av.attacker_prefix, av.attacker_origin,
       av.victim_prefix, av.victim_origin,
       av.list_index, av.policy_val, av.percent_iter, av.attack_type,
       --all ases stuff
       unnested_ases.t_name AS table_name,
        --must add 1 cause postgres arrays start at 1
       unnested_ases.as_type AS adopting_or_not,
       (CASE
            WHEN unnested_ases.as_type = TRUE
        THEN 1
            ELSE 0
        END) * unnested_ases.policy_val AS adopted_policy
    FROM tr
INNER JOIN attacker_victims av
    ON av.list_index = tr.list_index AND av.policy_val = tr.policy_val
FULL OUTER JOIN (--full outer join to get the no rib data
    --Why is this like this?
    --because first we want each asn per test
    --to get that we must unnest the asns, but we want to preserve the list index
    --so we use with ordinality
    --https://stackoverflow.com/questions/8760419/postgresql-unnest-with-element-number
    --but it gets worse. Because we add each policy for each list index,
    --we must unnest again. Insane in the membrane

    SELECT partial_unnest.asn,
           partial_unnest.t_name,
           partial_unnest.as_type,
           partial_unnest.list_index,
           UNNEST(partial_unnest.possible_vals) as policy_val
    FROM (
        SELECT all_ases.asn,
               all_ases.t_name,
               q.as_type,
               q.list_index_one_added - 1 AS list_index,  --minus 1 because postgres starts at 1
               vals_table.possible_vals
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
            SELECT ARRAY_AGG(policy_val::smallint) AS possible_vals
                FROM
                    (SELECT DISTINCT policy_val
                        FROM attacker_victims) distinct_pol_vals
            ) vals_table
        ) partial_unnest
   ) unnested_ases
 ON unnested_ases.asn = tr.og_asn
    AND unnested_ases.list_index = tr.list_index
    AND unnested_ases.policy_val = tr.policy_val
WHERE tr.received_from_asn IS NULL;
