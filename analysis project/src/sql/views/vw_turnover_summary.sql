-- View: vw_turnover_summary
-- Joins fact_employee_metrics with dim_department and dim_date
-- Aggregates monthly turnover rate per department
-- Validates: Requirements 4.5

CREATE VIEW vw_turnover_summary
AS
SELECT
    d.year,
    d.month,
    dep.department_name,
    SUM(f.headcount)       AS headcount,
    SUM(CAST(f.attrition_flag AS INT)) AS departures,
    CASE
        WHEN SUM(f.headcount) = 0 THEN 0
        ELSE (CAST(SUM(CAST(f.attrition_flag AS INT)) AS DECIMAL(10,4))
              / CAST(SUM(f.headcount) AS DECIMAL(10,4))) * 100
    END                    AS turnover_rate
FROM fact_employee_metrics f
INNER JOIN dim_department dep
    ON f.department_key = dep.department_key
INNER JOIN dim_date d
    ON f.date_key = d.date_key
GROUP BY
    d.year,
    d.month,
    dep.department_name;
