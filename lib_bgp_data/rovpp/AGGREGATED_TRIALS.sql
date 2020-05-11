CREATE UNLOGGED TABLE IF NOT EXISTS aggregated_trials AS (

SELECT
    a.list_index,
    a.policy_val,
    a.percent_iter,
    a.attack_type,
    a.table_name,
    a.adopting_or_not,
    a.adopted_policy,
    SUM (CASE
      WHEN a.start_bhole = TRUE
        AND a.end_state = 64512
      THEN a.total
    ELSE 0
      END) AS start_bhole_end_bhole,
    SUM (CASE
      WHEN a.start_bhole = TRUE
        AND a.end_state = 64513
      THEN a.total
    ELSE 0
      END) AS start_bhole_end_hijacked,
    SUM (CASE
      WHEN a.start_bhole = TRUE
        AND a.end_state = 64514
      THEN a.total
    ELSE 0
      END) AS start_bhole_end_victim,
    SUM (CASE
      WHEN a.start_preventive = TRUE
        AND a.end_state = 64512
      THEN a.total
    ELSE 0
      END) AS start_preventive_end_bhole,
    SUM (CASE
      WHEN a.start_preventive = TRUE
        AND a.end_state = 64513
      THEN a.total
    ELSE 0
      END) AS start_preventive_end_hijacked,
    SUM (CASE
      WHEN a.start_preventive = TRUE
        AND a.end_state = 64514
      THEN a.total
    ELSE 0
      END) AS start_preventive_end_victim,
    SUM (CASE
      WHEN a.start_hijacked = TRUE
        AND a.end_state = 64512
      THEN a.total
    ELSE 0
      END) AS start_hijacked_end_bhole,
    SUM (CASE
      WHEN a.start_hijacked = TRUE
        AND a.end_state = 64513
      THEN a.total
    ELSE 0
      END) AS start_hijacked_end_hijacked,
    SUM (CASE
      WHEN a.start_hijacked = TRUE
        AND a.end_state = 64514
      THEN a.total
    ELSE 0
      END) AS start_hijacked_end_victim,
    SUM (CASE
      WHEN a.start_successful = TRUE
        AND a.end_state = 64512
      THEN a.total
    ELSE 0
      END) AS start_success_end_bhole,
    SUM (CASE
      WHEN a.start_successful = TRUE
        AND a.end_state = 64513
      THEN a.total
    ELSE 0
      END) AS start_success_end_hijacked,
    SUM (CASE
      WHEN a.start_successful = TRUE
        AND a.end_state = 64514
      THEN a.total
    ELSE 0
      END) AS start_success_end_victim,
    SUM (CASE
      WHEN a.start_bhole = TRUE
          THEN a.total
    ELSE 0
      END) AS start_bhole,
    SUM (CASE
      WHEN a.start_preventive = TRUE
          THEN a.total
    ELSE 0
      END) AS start_preventive,
    SUM (CASE
      WHEN a.start_hijacked = TRUE
          THEN a.total
    ELSE 0
      END) AS start_hijacked,
    SUM (CASE
      WHEN a.start_successful = TRUE
          THEN a.total
    ELSE 0
      END) AS start_success,
    SUM (CASE
      WHEN a.end_state = 64512
          THEN a.total
    ELSE 0
      END) AS end_bhole,
    SUM (CASE
      WHEN a.end_state = 64513
          THEN a.total
    ELSE 0
      END) AS end_hijacked,
    SUM (CASE
      WHEN a.end_state = 64514
          THEN a.total
    ELSE 0
      END) AS end_victim,
    SUM (CASE
      WHEN a.end_state IS NULL
          THEN a.total
    ELSE 0
      END) AS no_rib,
    SUM(a.total) AS total_ases
FROM aggregated_raw a
    GROUP BY 
        a.list_index,
        a.policy_val,
        a.percent_iter,
        a.attack_type,
        a.table_name,
        a.adopting_or_not,
        a.adopted_policy,
        a.table_name

);
