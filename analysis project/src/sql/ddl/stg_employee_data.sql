-- Staging Table: stg_employee_data
-- Landing zone for ETL pipeline output (transformed and scored employee data)
-- No foreign keys enforced; data is validated before loading into star schema

CREATE TABLE stg_employee_data (
    staging_id              INT IDENTITY(1,1) NOT NULL,
    employee_id             VARCHAR(50)       NOT NULL,
    name                    VARCHAR(200)      NOT NULL,
    department              VARCHAR(100)      NOT NULL,
    job_role                VARCHAR(150)      NOT NULL,
    hire_date               DATE              NOT NULL,
    age                     INT               NOT NULL,
    gender                  VARCHAR(20)       NOT NULL,
    ethnicity               VARCHAR(50)       NOT NULL,
    salary                  DECIMAL(12,2)     NOT NULL,
    satisfaction_score      DECIMAL(4,2)      NOT NULL,
    overtime_hours          INT               NOT NULL,
    promotion_date          DATE              NULL,
    location                VARCHAR(100)      NOT NULL,
    attrition               BIT               NOT NULL,
    tenure_months           DECIMAL(6,2)      NOT NULL,
    age_group               VARCHAR(20)       NOT NULL,
    salary_band             VARCHAR(30)       NOT NULL,
    overtime_flag           BIT               NOT NULL,
    promotion_recency       DECIMAL(6,1)      NULL,
    attrition_probability   DECIMAL(5,4)      NOT NULL,
    load_timestamp          DATETIME          NOT NULL DEFAULT GETDATE(),

    CONSTRAINT PK_stg_employee_data PRIMARY KEY (staging_id)
);
