-- Dimension Table: dim_job_role
-- Stores job classification attributes

CREATE TABLE dim_job_role (
    job_role_key INT IDENTITY(1,1) NOT NULL,
    job_title    VARCHAR(150)      NOT NULL,
    job_level    VARCHAR(50)       NOT NULL,
    job_family   VARCHAR(100)      NOT NULL,

    CONSTRAINT PK_dim_job_role PRIMARY KEY (job_role_key),
    CONSTRAINT UQ_dim_job_role_title_level UNIQUE (job_title, job_level)
);
