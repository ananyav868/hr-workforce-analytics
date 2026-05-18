-- View: vw_diversity_metrics
-- Joins fact_employee_metrics with dim_employee and dim_department
-- Aggregates headcount by gender, ethnicity, age_group per department
-- Validates: Requirements 4.6

CREATE VIEW vw_diversity_metrics
AS
SELECT
    dep.department_name,
    e.gender,
    e.ethnicity,
    e.age_group,
    COUNT(*)               AS headcount,
    CASE
        WHEN dept_total.total_headcount = 0 THEN 0
        ELSE (CAST(COUNT(*) AS DECIMAL(10,4))
              / CAST(dept_total.total_headcount AS DECIMAL(10,4))) * 100
    END                    AS percentage
FROM fact_employee_metrics f
INNER JOIN dim_employee e
    ON f.employee_key = e.employee_key
INNER JOIN dim_department dep
    ON f.department_key = dep.department_key
INNER JOIN (
    SELECT
        f2.department_key,
        COUNT(*) AS total_headcount
    FROM fact_employee_metrics f2
    GROUP BY f2.department_key
) dept_total
    ON f.department_key = dept_total.department_key
GROUP BY
    dep.department_name,
    e.gender,
    e.ethnicity,
    e.age_group,
    dept_total.total_headcount;
