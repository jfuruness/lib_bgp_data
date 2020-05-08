with recursive tr(asn, received_from_asn) as (
      select t.asn, t.received_from_asn, t.prefix, t.origin, 1 as path_length
      from rovpp_extrapolator_rib_out t UNION ALL
      select b.asn, tr.received_from_asn, tr.prefix, tr.origin, tr.path_length + 1
      from rovpp_extrapolator_rib_out b INNER join
           tr
           on b.received_from_asn = tr.asn
        WHERE tr.path_length <= 64
     )
select tr.asn, tr.received_from_asn, tr.prefix, tr.origin, tr.path_length,
        av.attacker_prefix, av.attacker_origin,
        av.victim_prefix, av.victim_origin,
        av.list_index, av.policy_val, av.percent_iter,
        COALESCE(edge_ases_w_name.table_name,
                 etc_ases_w_name.table_name,
                 top_100_ases_w_name.table_name) AS table_name,
        COALESCE(edge_ases_w_name.as_types,
                 etc_ases_w_name.as_types,
                 top_100_ases_w_name.as_types) AS as_types,
        as_types[av.list_index + 1] AS adopting_or_not,
        as_types[av.list_index + 1] * policy_val AS adopted_policy  --add one to list index, postgres arrays start at 1 UGH
    from tr
INNER JOIN attacker_victims av
    ON av.attacker_prefix = tr.prefix OR av.victim_prefix = tr.prefix
INNER JOIN (
        SELECT 'edge_ases' AS t_name, edge_ases.asn, edge_ases.as_types
            FROM edge_ases) edge_ases_w_name
    ON edge_ases_w_name.asn = tr.asn
INNER JOIN (
        SELECT 'etc_ases' AS t_name, etc_ases.asn, etc_ases.as_types
            FROM etc_ases) etc_ases_w_name
    ON etc_ases_w_name.asn = tr.asn
INNER JOIN (
        SELECT 'top_100_ases' AS t_name, top_100_ases.asn, top_100_ases.as_types
            FROM top_100_ases) top_100_ases_w_name
    ON top_100_ases_w_name.asn = tr.asn
where received_from_asn = 64512
    OR received_from_asn = 64513
    OR received_from_asn = 64514
ORDER BY path_length;
