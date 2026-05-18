-- Dimension Table: dim_department
-- Stores department organizational attributes

CREATE TABLE dim_department (
    department_key  INT IDENTITY(1,1) NOT NULL,
    department_name VARCHAR(100)      NOT NULL,
    department_head VARCHAR(200)      NOT NULL,
    cost_center     VARCHAR(50)       NOT NULL,

    CONSTRAINT PK_dim_department PRIMARY KEY (department_key),
    CONSTRAINT UQ_dim_department_name UNIQUE (department_name)
);
