CREATE UNLOGGED TABLE IF NOT EXISTS aggregated_trials_avg AS (

SELECT
    a.list_index,
    a.policy_val,
    a.percent_iter,
    a.attack_type,
    a.table_name,
    a.adopting_or_not,
    a.adopted_policy,
    a.start_bhole_end_bhole::decimal / a.total_ases::decimal AS percent_start_bhole_end_bhole,
    a.start_bhole_end_hijacked::decimal / a.total_ases::decimal AS percent_start_bhole_end_hijacked,
    a.start_bhole_end_victim::decimal / a.total_ases::decimal AS percent_start_bhole_end_victim,
    a.start_preventive_end_bhole::decimal / a.total_ases::decimal AS percent_start_preventive_end_bhole,
    a.start_preventive_end_hijacked::decimal / a.total_ases::decimal AS percent_start_preventive_end_hijacked,
    a.start_preventive_end_victim::decimal / a.total_ases::decimal AS percent_start_preventive_end_victim,
    a.start_hijacked_end_bhole::decimal / a.total_ases::decimal AS percent_start_hijacked_end_bhole,
    a.start_hijacked_end_hijacked::decimal / a.total_ases::decimal AS percent_start_hijacked_end_hijacked,
    a.start_hijacked_end_victim::decimal / a.total_ases::decimal AS percent_start_hijacked_end_victim,
    a.start_success_end_bhole::decimal / a.total_ases::decimal AS percent_start_success_end_bhole,
    a.start_success_end_hijacked::decimal / a.total_ases::decimal AS percent_start_success_end_hijacked,
    a.start_success_end_victim::decimal / a.total_ases::decimal AS percent_start_success_end_victim,
    a.start_bhole::decimal / a.total_ases::decimal AS percent_start_bhole,
    a.start_preventive::decimal / a.total_ases::decimal AS percent_start_preventive,
    a.start_hijacked::decimal / a.total_ases::decimal AS percent_start_hijacked,
    a.start_success::decimal / a.total_ases::decimal AS percent_start_success,
    a.end_bhole::decimal / a.total_ases::decimal AS percent_end_bhole,
    a.end_hijacked::decimal / a.total_ases::decimal AS percent_end_hijacked,
    a.end_victim::decimal / a.total_ases::decimal AS percent_end_victim,
    a.no_rib::decimal / a.total_ases::decimal AS percent_no_rib,
    a.disconnected::decimal / a.total_ases::decimal AS percent_disconnected,
    a.total_ases
FROM aggregated_trials a
);
