#https://stackoverflow.com/a/17262097
--RAW DATA:
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
        av.list_index, av.policy_val, av.percent_iter, av.attack_type,
        all_ases.t_name AS table_name,
        all_ases.as_types[av.list_index + 1] AS adopting_or_not,
        all_ases.as_types[av.list_index + 1]::int * policy_val AS adopted_policy  --add one to list index, postgres arrays start at 1 UGH
    from tr
INNER JOIN attacker_victims av
    ON av.attacker_prefix = tr.prefix OR av.victim_prefix = tr.prefix
INNER JOIN (
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
    ) all_ases ON all_ases.asn = tr.asn
where received_from_asn = 64512
    OR received_from_asn = 64513
    OR received_from_asn = 64514
ORDER BY path_length;




--TRIAL DATA:
with recursive tr(asn, received_from_asn) as (
      select t.asn, t.received_from_asn, t.prefix, t.origin, 1 as path_length
      from rovpp_extrapolator_rib_out t UNION ALL
      select b.asn, tr.received_from_asn, tr.prefix, tr.origin, tr.path_length + 1
      from rovpp_extrapolator_rib_out b INNER join
           tr
           on b.received_from_asn = tr.asn
        WHERE tr.path_length <= 64
     )
select av.attack_type,
       all_ases.t_name,
       av.attacker_origin,
       av.attacker_prefix,
       av.victim_origin,
       av.victim_prefix,
       av.policy_val,
       av.list_val,
       av.percent_iter,
       --collateral info


       --total blackholed collateral
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.adopting = 0
                    then 1 else 0 end) AS total_blackholed_collateral
       --blackholed to blackholed collateral
       SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = 34512
                AND tr.adopting = 0
                    then 1 else 0 end) AS blackholed_to_blackholed_collateral
        --preventive to blackholed collateral
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS preventive_to_blackholed_collateral
        --hijacked to blackholed collateral
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 0
                    then 1 else 0 end) AS hijacked_to_blackholed_collateral
        --normal prefix to blackholed collateral
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS victim_to_blackholed_collateral



       --total hijacked collateral
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.adopting = 0
                    then 1 else 0 end) AS total_hijacked_collateral
       --blackholed to hijacked collateral
       SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = 34512
                AND tr.adopting = 0
                    then 1 else 0 end) AS blackholed_to_hijacked_collateral
        --preventive to hijacked collateral
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS preventive_to_hijacked_collateral
        --hijacked to hijacked collateral
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 0
                    then 1 else 0 end) AS hijacked_to_hijacked_collateral
        --normal prefix to hijacked collateral
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS victim_to_hijacked_collateral        


       --total succesful connection collateral
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.adopting = 0
                    then 1 else 0 end) AS total_successful_connection_collateral
       --blackholed to successful connection collateral
       SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = 34512
                AND tr.adopting = 0
                    then 1 else 0 end) AS blackholed_to_successful_connection_collateral
        --preventive to successful connection collateral
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS preventive_to_successful_connection_collateral
        --hijacked to successful_connection collateral
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 0
                    then 1 else 0 end) AS hijacked_to_successful_connection_collateral
        --normal prefix to successful_connection collateral
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 0
                    then 1 else 0 end) AS victim_to_successful_connection_collateral




        ----------------
        --adopting info


       --total blackholed adopting
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.adopting = 1
                    then 1 else 0 end) AS total_blackholed_adopting
       --blackholed to blackholed adopting
       SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = 34512
                AND tr.adopting = 1
                    then 1 else 0 end) AS blackholed_to_blackholed_adopting
        --preventive to blackholed adopting
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS preventive_to_blackholed_adopting
        --hijacked to blackholed adopting
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 1
                    then 1 else 0 end) AS hijacked_to_blackholed_adopting
        --normal prefix to blackholed adopting
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS victim_to_blackholed_adopting



       --total hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.adopting = 1
                    then 1 else 0 end) AS total_hijacked_adopting
       --blackholed to hijacked adopting
       SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = 34512
                AND tr.adopting = 1
                    then 1 else 0 end) AS blackholed_to_hijacked_adopting
        --preventive to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS preventive_to_hijacked_adopting
        --hijacked to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 1
                    then 1 else 0 end) AS hijacked_to_hijacked_adopting
        --normal prefix to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS victim_to_hijacked_adopting



       --total succesful connection adopting
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.adopting = 1
                    then 1 else 0 end) AS total_successful_connection_adopting
       --blackholed to successful connection adopting
       SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = 34512
                AND tr.adopting = 1
                    then 1 else 0 end) AS blackholed_to_successful_connection_adopting
        --preventive to successful connection adopting
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS preventive_to_successful_connection_adopting
        --hijacked to successful_connection adopting
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                AND tr.adopting = 1
                    then 1 else 0 end) AS hijacked_to_successful_connection_adopting
        --normal prefix to successful_connection adopting
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                AND tr.adopting = 1
                    then 1 else 0 end) AS victim_to_successful_connection_adopting


        ----------------
        --combined info


       --total blackholed
        SUM(case
            WHEN tr.received_from_asn = 34512
                    then 1 else 0 end) AS total_blackholed
       --blackholed to blackholed
       SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = 34512
                    then 1 else 0 end) AS blackholed_to_blackholed
        --preventive to blackholed 
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                    then 1 else 0 end) AS preventive_to_blackholed
        --hijacked to blackholed 
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                    then 1 else 0 end) AS hijacked_to_blackholed
        --normal prefix to blackholed
        SUM(case
            WHEN tr.received_from_asn = 34512
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                    then 1 else 0 end) AS victim_to_blackholed



       --total hijacked
        SUM(case
            WHEN tr.received_from_asn = 34513
                    then 1 else 0 end) AS total_hijacked
       --blackholed to hijacked adopting
       SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = 34512
                    then 1 else 0 end) AS blackholed_to_hijacked
        --preventive to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                    then 1 else 0 end) AS preventive_to_hijacked
        --hijacked to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                    then 1 else 0 end) AS hijacked_to_hijacked
        --normal prefix to hijacked adopting
        SUM(case
            WHEN tr.received_from_asn = 34513
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                    then 1 else 0 end) AS victim_to_hijacked


       --total succesful connection
        SUM(case
            WHEN tr.received_from_asn = 34514
                    then 1 else 0 end) AS total_successful_connection
       --blackholed to successful connection
       SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = 34512
                    then 1 else 0 end) AS blackholed_to_successful_connection
        --preventive to successful connection
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.attacker_prefix
                    then 1 else 0 end) AS preventive_to_successful_connection
        --hijacked to successful_connection 
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.prefix = av.attacker_prefix
                AND tr.origin = av.attacker_origin
                    then 1 else 0 end) AS hijacked_to_successful_connection
        --normal prefix to successful_connection adopting
        SUM(case
            WHEN tr.received_from_asn = 34514
                AND tr.origin = av.victim_origin
                AND tr.prefix = av.victim_prefix
                    then 1 else 0 end) AS victim_to_successful_connection



        --------------NOTE: need to break this out into a completely separate join!!
        -------------NOTE: NEEDS COMMAS AFTER ALL THE AS STATEMENTS!!!

        --NO RIB INFO
        --norib collateral
        SUM(case WHEN norib.adopting = 0
            then 1 else 0 end) AS no_rib_collateral

        --norib adopting
        SUM(case WHEN norib.adopting = 1
            then 1 else 0 end) AS no_rib_adopting

        --norib total
        SUM(case WHEN norib.adopting = 1
            then 1 else 0 end) AS no_rib_adopting

    from tr
INNER JOIN attacker_victims av
    ON av.attacker_prefix = tr.prefix OR av.victim_prefix = tr.prefix
INNER JOIN (
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
    ) all_ases ON all_ases.asn = tr.asn
where received_from_asn = 64512
    OR received_from_asn = 64513
    OR received_from_asn = 64514
ORDER BY path_length;
