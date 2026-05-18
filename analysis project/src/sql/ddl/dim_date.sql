-- Dimension Table: dim_date
-- Stores calendar date attributes for time-based analysis

CREATE TABLE dim_date (
    date_key     INT          NOT NULL,
    full_date    DATE         NOT NULL,
    year         INT          NOT NULL,
    quarter      INT          NOT NULL,
    month        INT          NOT NULL,
    month_name   VARCHAR(20)  NOT NULL,
    day_of_week  INT          NOT NULL,
    is_month_end BIT          NOT NULL DEFAULT 0,

    CONSTRAINT PK_dim_date PRIMARY KEY (date_key),
    CONSTRAINT UQ_dim_date_full_date UNIQUE (full_date),
    CONSTRAINT CK_dim_date_quarter CHECK (quarter BETWEEN 1 AND 4),
    CONSTRAINT CK_dim_date_month CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT CK_dim_date_day_of_week CHECK (day_of_week BETWEEN 1 AND 7)
);
