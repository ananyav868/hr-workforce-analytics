-- Dimension Table: dim_location
-- Stores geographic location attributes

CREATE TABLE dim_location (
    location_key INT IDENTITY(1,1) NOT NULL,
    city         VARCHAR(100)      NOT NULL,
    state        VARCHAR(100)      NOT NULL,
    country      VARCHAR(100)      NOT NULL,
    region       VARCHAR(50)       NOT NULL,

    CONSTRAINT PK_dim_location PRIMARY KEY (location_key),
    CONSTRAINT UQ_dim_location_city_state_country UNIQUE (city, state, country)
);
