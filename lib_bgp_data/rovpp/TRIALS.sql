--#https://stackoverflow.com/a/17262097
--RAW DATA:

CREATE UNLOGGED TABLE aggregated_raw AS (
    WITH RECURSIVE tr(
        og_asn, end_state, received_from_asn,
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
    SELECT av.list_index,
           av.policy_val,
           av.percent_iter,
           av.attack_type,
           av.attacker_prefix,
           av.attacker_origin,
           av.victim_prefix,
           av.victim_origin,
           --all ases stuff
           av.table_name,
            --must add 1 cause postgres arrays start at 1
           av.adopting_or_not,
           av.adopted_policy,
           av.attacker_prefix = tr.prefix AND tr.origin = 64512 AS start_bhole, --bhole
           av.attacker_prefix = tr.prefix AND av.victim_origin = tr.origin AS start_preventive,
           av.attacker_prefix = tr.prefix AND av.attacker_origin = tr.origin AS start_hijacked,
           av.victim_prefix = tr.prefix AND av.victim_origin = tr.origin AS start_successful,
           tr.end_state,
    --       av.attacker_prefix = tr.prefix AND av.attacker_origin = 64512, --bhole
           COUNT(av.asn) AS total
        FROM tr
    FULL OUTER JOIN (--full outer join to get the no rib data
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
                END) AS adopted_policy,
                tempav.attacker_prefix,
                tempav.attacker_origin,
                tempav.victim_prefix,
                tempav.victim_origin,
                tempav.attack_type,
                tempav.percent_iter
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
         INNER JOIN attacker_victims tempav
            ON tempav.list_index = (q.list_index_one_added - 1)
                AND tempav.policy_val = vals_table.policy_val
       ) av
     ON av.asn = tr.og_asn
        AND av.list_index = tr.list_index
        AND av.policy_val = tr.policy_val
    WHERE
        tr.received_from_asn IS NULL
    GROUP BY
        av.list_index,
        av.policy_val,
        av.percent_iter,
        av.attack_type,
        av.attacker_prefix,
        av.attacker_origin,
        av.victim_prefix,
        av.victim_origin,
        av.table_name,
        av.adopting_or_not,
        av.adopted_policy,
        av.attacker_prefix = tr.prefix AND tr.origin = 64512, --bholestart
        av.attacker_prefix = tr.prefix AND av.victim_origin = tr.origin, --preventive start
        av.attacker_prefix = tr.prefix AND av.attacker_origin = tr.origin,  --hijacked start
        av.victim_prefix = tr.prefix AND av.victim_origin = tr.origin,  --prefix start
        tr.end_state
);
