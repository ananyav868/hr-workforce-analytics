# DAX Measures: Turnover Analysis

Power BI DAX measure definitions for the Turnover Analysis dashboard page. These measures reference the star schema tables: `fact_employee_metrics`, `dim_department`, and `dim_date`.

> **Validates: Requirements 6.1, 6.2, 6.4**

---

## 1. Overall Attrition Rate

**Measure Name:** `Overall Attrition Rate`

**Description:** Calculates the overall attrition rate as a percentage for the selected time period. Defined as the number of employees who departed divided by the average headcount, multiplied by 100.

**Intended Visual:** KPI card on the Turnover Analysis page; also used as a reference line on trend charts.

```dax
Overall Attrition Rate =
VAR _Departures =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        fact_employee_metrics[attrition_flag] = TRUE()
    )
VAR _AvgHeadcount =
    AVERAGE( fact_employee_metrics[headcount] )
RETURN
    IF(
        _AvgHeadcount = 0,
        BLANK(),
        DIVIDE( _Departures, _AvgHeadcount ) * 100
    )
```

---

## 2. Department Attrition Rate

**Measure Name:** `Department Attrition Rate`

**Description:** Calculates the attrition rate per department for the selected time period. Uses the same formula as the overall rate but is evaluated within the filter context of each department. When used in a visual grouped by `dim_department[department_name]`, it automatically computes the rate for each department.

**Intended Visual:** Bar chart showing attrition rate by department; also used in the department comparison table.

```dax
Department Attrition Rate =
VAR _Departures =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        fact_employee_metrics[attrition_flag] = TRUE()
    )
VAR _AvgHeadcount =
    AVERAGE( fact_employee_metrics[headcount] )
RETURN
    IF(
        _AvgHeadcount = 0,
        BLANK(),
        DIVIDE( _Departures, _AvgHeadcount ) * 100
    )
```

> **Usage Note:** Place `dim_department[department_name]` on the axis of a bar chart and this measure as the value. The DAX engine evaluates the measure within each department's filter context automatically.

---

## 3. Monthly Attrition Trend

**Measure Name:** `Monthly Attrition Trend`

**Description:** Calculates the attrition rate for each month, enabling time-series visualization of turnover trends. Evaluated per month when `dim_date[year]` and `dim_date[month]` (or `dim_date[full_date]`) are placed on the chart axis.

**Intended Visual:** Line chart showing monthly attrition trend over the available date range (time-series).

```dax
Monthly Attrition Trend =
VAR _MonthlyDepartures =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        fact_employee_metrics[attrition_flag] = TRUE()
    )
VAR _MonthlyHeadcount =
    SUM( fact_employee_metrics[headcount] )
RETURN
    IF(
        _MonthlyHeadcount = 0,
        BLANK(),
        DIVIDE( _MonthlyDepartures, _MonthlyHeadcount ) * 100
    )
```

> **Usage Note:** Place a date hierarchy (e.g., `dim_date[year]`, `dim_date[month_name]`) or `dim_date[full_date]` on the X-axis of a line chart with this measure as the Y-axis value. Use slicers on `dim_date` to control the visible date range.

---

## Usage Instructions

1. Open Power BI Desktop and connect to the star schema database.
2. Navigate to the **Modeling** tab → **New Measure**.
3. Paste each DAX formula above into the formula bar.
4. Assign measures to the appropriate visuals as described.

### Slicer Compatibility

All three measures respond to the following slicers (cross-filter):
- **Date Range** — filters `dim_date` to constrain the time period
- **Department** — filters `dim_department[department_name]`
- **Job Role** — filters `dim_job_role[job_title]`
- **Location** — filters `dim_location[city]` or `dim_location[region]`

### Relationships Required

Ensure the Power BI data model has active relationships:
- `fact_employee_metrics[department_key]` → `dim_department[department_key]`
- `fact_employee_metrics[date_key]` → `dim_date[date_key]`
- `fact_employee_metrics[job_role_key]` → `dim_job_role[job_role_key]`
- `fact_employee_metrics[location_key]` → `dim_location[location_key]`
