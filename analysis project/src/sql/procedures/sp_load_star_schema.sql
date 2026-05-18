-- Stored Procedure: sp_load_star_schema
-- Loads data from stg_employee_data into the star schema (dimensions + fact table)
-- Implements SCD Type 1 (overwrite), idempotent loads, transaction safety, and logging
--
-- Requirements: 4.4, 4.7, 5.2, 5.3, 5.4, 5.5

CREATE PROCEDURE dbo.sp_load_star_schema
AS
BEGIN
    SET NOCOUNT ON;

    -- =========================================================================
    -- Variable declarations
    -- =========================================================================
    DECLARE @staging_count       INT = 0;
    DECLARE @emp_inserted        INT = 0;
    DECLARE @emp_updated         INT = 0;
    DECLARE @dept_inserted       INT = 0;
    DECLARE @dept_updated        INT = 0;
    DECLARE @job_inserted        INT = 0;
    DECLARE @job_updated         INT = 0;
    DECLARE @loc_inserted        INT = 0;
    DECLARE @loc_updated         INT = 0;
    DECLARE @date_inserted       INT = 0;
    DECLARE @fact_inserted       INT = 0;
    DECLARE @fact_updated        INT = 0;
    DECLARE @rejected            INT = 0;
    DECLARE @error_message       NVARCHAR(4000);
    DECLARE @error_severity      INT;
    DECLARE @error_state         INT;
    DECLARE @load_start          DATETIME = GETDATE();

    -- Table variables for capturing MERGE OUTPUT actions
    DECLARE @DeptActions TABLE (ActionType NVARCHAR(10));
    DECLARE @JobActions  TABLE (ActionType NVARCHAR(10));
    DECLARE @LocActions  TABLE (ActionType NVARCHAR(10));
    DECLARE @EmpActions  TABLE (ActionType NVARCHAR(10));
    DECLARE @FactActions TABLE (ActionType NVARCHAR(10));

    BEGIN TRY
        BEGIN TRANSACTION;

        -- =====================================================================
        -- Step 1: Validate row counts in staging table
        -- Requirement 5.2: validate row counts between staging and source
        -- =====================================================================
        SELECT @staging_count = COUNT(*) FROM stg_employee_data;

        IF @staging_count = 0
        BEGIN
            RAISERROR('No rows found in staging table stg_employee_data. Aborting load.', 16, 1);
        END;

        -- =====================================================================
        -- Step 2: Load dim_department (SCD Type 1)
        -- Natural key: department_name
        -- Requirement 4.4: insert or update dimensions before fact
        -- =====================================================================
        MERGE dim_department AS tgt
        USING (
            SELECT DISTINCT
                department AS department_name,
                'TBD' AS department_head,
                'TBD' AS cost_center
            FROM stg_employee_data
        ) AS src
        ON tgt.department_name = src.department_name
        WHEN MATCHED AND (
            tgt.department_head <> src.department_head
            OR tgt.cost_center <> src.cost_center
        )
        THEN UPDATE SET
            tgt.department_head = src.department_head,
            tgt.cost_center = src.cost_center
        WHEN NOT MATCHED BY TARGET
        THEN INSERT (department_name, department_head, cost_center)
             VALUES (src.department_name, src.department_head, src.cost_center)
        OUTPUT $action INTO @DeptActions;

        SELECT @dept_inserted = COUNT(*) FROM @DeptActions WHERE ActionType = 'INSERT';
        SELECT @dept_updated  = COUNT(*) FROM @DeptActions WHERE ActionType = 'UPDATE';

        -- =====================================================================
        -- Step 3: Load dim_job_role (SCD Type 1)
        -- Natural key: job_title + job_level
        -- Staging field job_role maps to job_title; job_level defaults to 'Standard'
        -- =====================================================================
        MERGE dim_job_role AS tgt
        USING (
            SELECT DISTINCT
                job_role AS job_title,
                'Standard' AS job_level,
                'General' AS job_family
            FROM stg_employee_data
        ) AS src
        ON tgt.job_title = src.job_title AND tgt.job_level = src.job_level
        WHEN MATCHED AND (
            tgt.job_family <> src.job_family
        )
        THEN UPDATE SET
            tgt.job_family = src.job_family
        WHEN NOT MATCHED BY TARGET
        THEN INSERT (job_title, job_level, job_family)
             VALUES (src.job_title, src.job_level, src.job_family)
        OUTPUT $action INTO @JobActions;

        SELECT @job_inserted = COUNT(*) FROM @JobActions WHERE ActionType = 'INSERT';
        SELECT @job_updated  = COUNT(*) FROM @JobActions WHERE ActionType = 'UPDATE';

        -- =====================================================================
        -- Step 4: Load dim_location (SCD Type 1)
        -- Natural key: city + state + country
        -- Staging field location is parsed as 'City, State, Country'
        -- If format doesn't match, use full value as city with 'Unknown' state/country
        -- =====================================================================
        MERGE dim_location AS tgt
        USING (
            SELECT DISTINCT
                CASE
                    WHEN CHARINDEX(',', location) > 0
                    THEN LTRIM(RTRIM(LEFT(location, CHARINDEX(',', location) - 1)))
                    ELSE LTRIM(RTRIM(location))
                END AS city,
                CASE
                    WHEN LEN(location) - LEN(REPLACE(location, ',', '')) >= 2
                    THEN LTRIM(RTRIM(SUBSTRING(
                        location,
                        CHARINDEX(',', location) + 1,
                        CHARINDEX(',', location, CHARINDEX(',', location) + 1) - CHARINDEX(',', location) - 1
                    )))
                    WHEN CHARINDEX(',', location) > 0
                    THEN LTRIM(RTRIM(SUBSTRING(location, CHARINDEX(',', location) + 1, LEN(location))))
                    ELSE 'Unknown'
                END AS state,
                CASE
                    WHEN LEN(location) - LEN(REPLACE(location, ',', '')) >= 2
                    THEN LTRIM(RTRIM(SUBSTRING(
                        location,
                        CHARINDEX(',', location, CHARINDEX(',', location) + 1) + 1,
                        LEN(location)
                    )))
                    ELSE 'Unknown'
                END AS country,
                'Unknown' AS region
            FROM stg_employee_data
        ) AS src
        ON tgt.city = src.city AND tgt.state = src.state AND tgt.country = src.country
        WHEN MATCHED AND (
            tgt.region <> src.region
        )
        THEN UPDATE SET
            tgt.region = src.region
        WHEN NOT MATCHED BY TARGET
        THEN INSERT (city, state, country, region)
             VALUES (src.city, src.state, src.country, src.region)
        OUTPUT $action INTO @LocActions;

        SELECT @loc_inserted = COUNT(*) FROM @LocActions WHERE ActionType = 'INSERT';
        SELECT @loc_updated  = COUNT(*) FROM @LocActions WHERE ActionType = 'UPDATE';

        -- =====================================================================
        -- Step 5: Load dim_employee (SCD Type 1)
        -- Natural key: employee_id
        -- =====================================================================
        MERGE dim_employee AS tgt
        USING (
            SELECT DISTINCT
                employee_id,
                name AS full_name,
                gender,
                ethnicity,
                age_group,
                hire_date,
                CASE WHEN attrition = 1 THEN CAST(GETDATE() AS DATE) ELSE NULL END AS termination_date,
                salary_band,
                CASE WHEN promotion_date IS NOT NULL THEN 1 ELSE 0 END AS promotion_recent
            FROM stg_employee_data
        ) AS src
        ON tgt.employee_id = src.employee_id
        WHEN MATCHED THEN UPDATE SET
            tgt.full_name         = src.full_name,
            tgt.gender            = src.gender,
            tgt.ethnicity         = src.ethnicity,
            tgt.age_group         = src.age_group,
            tgt.hire_date         = src.hire_date,
            tgt.termination_date  = src.termination_date,
            tgt.salary_band       = src.salary_band,
            tgt.promotion_recent  = src.promotion_recent
        WHEN NOT MATCHED BY TARGET
        THEN INSERT (employee_id, full_name, gender, ethnicity, age_group, hire_date, termination_date, salary_band, promotion_recent)
             VALUES (src.employee_id, src.full_name, src.gender, src.ethnicity, src.age_group, src.hire_date, src.termination_date, src.salary_band, src.promotion_recent)
        OUTPUT $action INTO @EmpActions;

        SELECT @emp_inserted = COUNT(*) FROM @EmpActions WHERE ActionType = 'INSERT';
        SELECT @emp_updated  = COUNT(*) FROM @EmpActions WHERE ActionType = 'UPDATE';

        -- =====================================================================
        -- Step 6: Load dim_date
        -- Ensure date records exist for all hire_dates in staging
        -- date_key format: YYYYMMDD as integer
        -- =====================================================================
        INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name, day_of_week, is_month_end)
        SELECT DISTINCT
            CAST(CONVERT(VARCHAR(8), s.hire_date, 112) AS INT) AS date_key,
            s.hire_date AS full_date,
            YEAR(s.hire_date) AS year,
            DATEPART(QUARTER, s.hire_date) AS quarter,
            MONTH(s.hire_date) AS month,
            DATENAME(MONTH, s.hire_date) AS month_name,
            DATEPART(WEEKDAY, s.hire_date) AS day_of_week,
            CASE WHEN s.hire_date = EOMONTH(s.hire_date) THEN 1 ELSE 0 END AS is_month_end
        FROM stg_employee_data s
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_date d
            WHERE d.date_key = CAST(CONVERT(VARCHAR(8), s.hire_date, 112) AS INT)
        );

        SET @date_inserted = @@ROWCOUNT;

        -- =====================================================================
        -- Step 7: Load fact_employee_metrics (idempotent)
        -- Requirement 5.4: no duplicates on re-run
        -- Match on employee_key + date_key; update if exists, insert if not
        -- =====================================================================
        MERGE fact_employee_metrics AS tgt
        USING (
            SELECT
                de.employee_key,
                dd.department_key,
                dj.job_role_key,
                dl.location_key,
                dt.date_key,
                s.attrition AS attrition_flag,
                1 AS headcount,
                s.tenure_months,
                s.satisfaction_score,
                s.attrition_probability,
                s.salary,
                s.overtime_hours
            FROM stg_employee_data s
            INNER JOIN dim_employee de
                ON de.employee_id = s.employee_id
            INNER JOIN dim_department dd
                ON dd.department_name = s.department
            INNER JOIN dim_job_role dj
                ON dj.job_title = s.job_role AND dj.job_level = 'Standard'
            INNER JOIN dim_location dl
                ON dl.city = CASE
                        WHEN CHARINDEX(',', s.location) > 0
                        THEN LTRIM(RTRIM(LEFT(s.location, CHARINDEX(',', s.location) - 1)))
                        ELSE LTRIM(RTRIM(s.location))
                    END
                AND dl.state = CASE
                        WHEN LEN(s.location) - LEN(REPLACE(s.location, ',', '')) >= 2
                        THEN LTRIM(RTRIM(SUBSTRING(
                            s.location,
                            CHARINDEX(',', s.location) + 1,
                            CHARINDEX(',', s.location, CHARINDEX(',', s.location) + 1) - CHARINDEX(',', s.location) - 1
                        )))
                        WHEN CHARINDEX(',', s.location) > 0
                        THEN LTRIM(RTRIM(SUBSTRING(s.location, CHARINDEX(',', s.location) + 1, LEN(s.location))))
                        ELSE 'Unknown'
                    END
                AND dl.country = CASE
                        WHEN LEN(s.location) - LEN(REPLACE(s.location, ',', '')) >= 2
                        THEN LTRIM(RTRIM(SUBSTRING(
                            s.location,
                            CHARINDEX(',', s.location, CHARINDEX(',', s.location) + 1) + 1,
                            LEN(s.location)
                        )))
                        ELSE 'Unknown'
                    END
            INNER JOIN dim_date dt
                ON dt.date_key = CAST(CONVERT(VARCHAR(8), s.hire_date, 112) AS INT)
        ) AS src
        ON tgt.employee_key = src.employee_key AND tgt.date_key = src.date_key
        WHEN MATCHED THEN UPDATE SET
            tgt.department_key        = src.department_key,
            tgt.job_role_key          = src.job_role_key,
            tgt.location_key          = src.location_key,
            tgt.attrition_flag        = src.attrition_flag,
            tgt.headcount             = src.headcount,
            tgt.tenure_months         = src.tenure_months,
            tgt.satisfaction_score    = src.satisfaction_score,
            tgt.attrition_probability = src.attrition_probability,
            tgt.salary                = src.salary,
            tgt.overtime_hours        = src.overtime_hours
        WHEN NOT MATCHED BY TARGET
        THEN INSERT (employee_key, department_key, job_role_key, location_key, date_key,
                     attrition_flag, headcount, tenure_months, satisfaction_score,
                     attrition_probability, salary, overtime_hours)
             VALUES (src.employee_key, src.department_key, src.job_role_key, src.location_key, src.date_key,
                     src.attrition_flag, src.headcount, src.tenure_months, src.satisfaction_score,
                     src.attrition_probability, src.salary, src.overtime_hours)
        OUTPUT $action INTO @FactActions;

        SELECT @fact_inserted = COUNT(*) FROM @FactActions WHERE ActionType = 'INSERT';
        SELECT @fact_updated  = COUNT(*) FROM @FactActions WHERE ActionType = 'UPDATE';

        -- Calculate rejected rows (staging rows that couldn't join to all dimensions)
        SET @rejected = @staging_count - (@fact_inserted + @fact_updated);

        -- =====================================================================
        -- Step 8: Final row count validation
        -- Requirement 5.2: validate row counts between staging and star schema
        -- =====================================================================
        DECLARE @fact_total INT = @fact_inserted + @fact_updated;

        IF @fact_total = 0 AND @staging_count > 0
        BEGIN
            RAISERROR('Row count validation failed: staging has %d rows but no fact records were loaded.', 16, 1, @staging_count);
        END;

        -- =====================================================================
        -- Step 9: Commit and log success
        -- Requirement 5.5: log rows inserted, updated, and rejected
        -- =====================================================================
        COMMIT TRANSACTION;

        -- Log success summary
        PRINT '=== Star Schema Load Completed Successfully ===';
        PRINT 'Load Start Time: ' + CONVERT(VARCHAR(30), @load_start, 121);
        PRINT 'Load End Time:   ' + CONVERT(VARCHAR(30), GETDATE(), 121);
        PRINT '';
        PRINT '--- Dimension Load Summary ---';
        PRINT 'dim_department: ' + CAST(@dept_inserted AS VARCHAR) + ' inserted, ' + CAST(@dept_updated AS VARCHAR) + ' updated';
        PRINT 'dim_job_role:   ' + CAST(@job_inserted AS VARCHAR) + ' inserted, ' + CAST(@job_updated AS VARCHAR) + ' updated';
        PRINT 'dim_location:   ' + CAST(@loc_inserted AS VARCHAR) + ' inserted, ' + CAST(@loc_updated AS VARCHAR) + ' updated';
        PRINT 'dim_employee:   ' + CAST(@emp_inserted AS VARCHAR) + ' inserted, ' + CAST(@emp_updated AS VARCHAR) + ' updated';
        PRINT 'dim_date:       ' + CAST(@date_inserted AS VARCHAR) + ' inserted';
        PRINT '';
        PRINT '--- Fact Load Summary ---';
        PRINT 'fact_employee_metrics: ' + CAST(@fact_inserted AS VARCHAR) + ' inserted, ' + CAST(@fact_updated AS VARCHAR) + ' updated';
        PRINT 'Staging rows:          ' + CAST(@staging_count AS VARCHAR);
        PRINT 'Rejected rows:         ' + CAST(@rejected AS VARCHAR);
        PRINT '================================================';

        -- Return summary result set for programmatic consumption
        SELECT
            @staging_count   AS staging_row_count,
            @dept_inserted   AS dept_inserted,
            @dept_updated    AS dept_updated,
            @job_inserted    AS job_inserted,
            @job_updated     AS job_updated,
            @loc_inserted    AS loc_inserted,
            @loc_updated     AS loc_updated,
            @emp_inserted    AS emp_inserted,
            @emp_updated     AS emp_updated,
            @date_inserted   AS date_inserted,
            @fact_inserted   AS fact_inserted,
            @fact_updated    AS fact_updated,
            @rejected        AS rejected_rows,
            @load_start      AS load_start_time,
            GETDATE()        AS load_end_time,
            'SUCCESS'        AS load_status;

    END TRY
    BEGIN CATCH
        -- =================================================================
        -- Error handling: rollback and log
        -- Requirement 5.3: rollback all changes and log failure reason
        -- =================================================================
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @error_message  = ERROR_MESSAGE();
        SET @error_severity = ERROR_SEVERITY();
        SET @error_state    = ERROR_STATE();

        -- Log error details
        PRINT '=== Star Schema Load FAILED ===';
        PRINT 'Load Start Time: ' + CONVERT(VARCHAR(30), @load_start, 121);
        PRINT 'Failure Time:    ' + CONVERT(VARCHAR(30), GETDATE(), 121);
        PRINT 'Error Message:   ' + @error_message;
        PRINT 'Error Severity:  ' + CAST(@error_severity AS VARCHAR);
        PRINT 'Error State:     ' + CAST(@error_state AS VARCHAR);
        PRINT '================================';

        -- Return error result set for programmatic consumption
        SELECT
            @staging_count   AS staging_row_count,
            0                AS dept_inserted,
            0                AS dept_updated,
            0                AS job_inserted,
            0                AS job_updated,
            0                AS loc_inserted,
            0                AS loc_updated,
            0                AS emp_inserted,
            0                AS emp_updated,
            0                AS date_inserted,
            0                AS fact_inserted,
            0                AS fact_updated,
            0                AS rejected_rows,
            @load_start      AS load_start_time,
            GETDATE()        AS load_end_time,
            'FAILED'         AS load_status,
            @error_message   AS error_message;

        -- Re-raise the error for the calling application
        RAISERROR(@error_message, @error_severity, @error_state);
    END CATCH;
END;
GO
