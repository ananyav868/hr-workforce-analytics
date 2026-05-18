-- Fact Table: fact_employee_metrics
-- Central fact table storing attrition events, headcount, and workforce metrics
-- References all dimension tables via foreign key constraints

CREATE TABLE fact_employee_metrics (
    metric_id             INT IDENTITY(1,1) NOT NULL,
    employee_key          INT               NOT NULL,
    department_key        INT               NOT NULL,
    job_role_key          INT               NOT NULL,
    location_key          INT               NOT NULL,
    date_key              INT               NOT NULL,
    attrition_flag        BIT               NOT NULL,
    headcount             INT               NOT NULL,
    tenure_months         DECIMAL(6,2)      NOT NULL,
    satisfaction_score    DECIMAL(4,2)      NOT NULL,
    attrition_probability DECIMAL(5,4)      NOT NULL,
    salary                DECIMAL(12,2)     NOT NULL,
    overtime_hours        INT               NOT NULL,

    CONSTRAINT PK_fact_employee_metrics PRIMARY KEY (metric_id),

    CONSTRAINT FK_fact_employee_metrics_employee
        FOREIGN KEY (employee_key) REFERENCES dim_employee (employee_key),

    CONSTRAINT FK_fact_employee_metrics_department
        FOREIGN KEY (department_key) REFERENCES dim_department (department_key),

    CONSTRAINT FK_fact_employee_metrics_job_role
        FOREIGN KEY (job_role_key) REFERENCES dim_job_role (job_role_key),

    CONSTRAINT FK_fact_employee_metrics_location
        FOREIGN KEY (location_key) REFERENCES dim_location (location_key),

    CONSTRAINT FK_fact_employee_metrics_date
        FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);
