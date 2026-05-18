-- Dimension Table: dim_employee
-- Stores employee demographic and employment attributes for analytics

CREATE TABLE dim_employee (
    employee_key    INT IDENTITY(1,1) NOT NULL,
    employee_id     VARCHAR(50)       NOT NULL,
    full_name       VARCHAR(200)      NOT NULL,
    gender          VARCHAR(20)       NOT NULL,
    ethnicity       VARCHAR(50)       NOT NULL,
    age_group       VARCHAR(20)       NOT NULL,
    hire_date       DATE              NOT NULL,
    termination_date DATE             NULL,
    salary_band     VARCHAR(30)       NOT NULL,
    promotion_recent BIT              NOT NULL DEFAULT 0,

    CONSTRAINT PK_dim_employee PRIMARY KEY (employee_key),
    CONSTRAINT UQ_dim_employee_employee_id UNIQUE (employee_id)
);
