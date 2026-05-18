# DAX Measures: Diversity Metrics

Power BI DAX measure definitions for the Diversity Metrics dashboard page. These measures reference the star schema tables: `fact_employee_metrics`, `dim_employee`, `dim_department`, and `dim_date`.

> **Validates: Requirements 7.1, 7.5**

---

## 1. Gender Ratio

**Measure Name:** `Gender Ratio %`

**Description:** Calculates the percentage of each gender within the workforce for the current filter context. When used in a visual grouped by `dim_employee[gender]` and optionally by `dim_department[department_name]`, it shows the gender distribution per department.

**Intended Visual:** Stacked bar chart showing gender breakdown by department; donut chart for overall gender split.

```dax
Gender Ratio % =
VAR _GenderCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALLEXCEPT( dim_employee, dim_employee[gender] )
    )
VAR _TotalCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALL( dim_employee[gender] )
    )
RETURN
    IF(
        _TotalCount = 0,
        BLANK(),
        DIVIDE( _GenderCount, _TotalCount ) * 100
    )
```

> **Usage Note:** Place `dim_employee[gender]` on the legend/axis and `dim_department[department_name]` on the axis of a stacked bar chart. This measure evaluates within each gender's filter context to produce the percentage. For a donut chart, use `dim_employee[gender]` as the legend and this measure as the value.

---

## 2. Ethnicity Distribution Percentage

**Measure Name:** `Ethnicity Distribution %`

**Description:** Calculates the percentage of each ethnicity group within the workforce for the current filter context. Evaluates per ethnicity when `dim_employee[ethnicity]` is placed on the visual axis or legend.

**Intended Visual:** Stacked bar chart showing ethnicity breakdown by department; donut chart for overall ethnicity distribution.

```dax
Ethnicity Distribution % =
VAR _EthnicityCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALLEXCEPT( dim_employee, dim_employee[ethnicity] )
    )
VAR _TotalCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALL( dim_employee[ethnicity] )
    )
RETURN
    IF(
        _TotalCount = 0,
        BLANK(),
        DIVIDE( _EthnicityCount, _TotalCount ) * 100
    )
```

> **Usage Note:** Place `dim_employee[ethnicity]` on the axis/legend and `dim_department[department_name]` on the axis for a department-level breakdown. Use consistent color coding per ethnicity group across all visuals for readability.

---

## 3. Age Group Distribution

**Measure Name:** `Age Group Distribution %`

**Description:** Calculates the percentage of each age group within the workforce for the current filter context. Age groups are defined in `dim_employee[age_group]` (e.g., "18-25", "26-35", "36-45", "46-55", "56+").

**Intended Visual:** Stacked bar chart showing age group breakdown by department; donut chart for overall age distribution.

```dax
Age Group Distribution % =
VAR _AgeGroupCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALLEXCEPT( dim_employee, dim_employee[age_group] )
    )
VAR _TotalCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALL( dim_employee[age_group] )
    )
RETURN
    IF(
        _TotalCount = 0,
        BLANK(),
        DIVIDE( _AgeGroupCount, _TotalCount ) * 100
    )
```

> **Usage Note:** Place `dim_employee[age_group]` on the axis/legend. Sort the age group axis in logical order (youngest to oldest) using the column sort feature in Power BI.

---

## 4. Year-over-Year Diversity Change

**Measure Name:** `YoY Diversity Change %`

**Description:** Calculates the change in diversity composition (percentage point difference) compared to the same period in the previous year. This measure works within the current demographic filter context (gender, ethnicity, or age group) and computes how the representation percentage has shifted year over year.

**Intended Visual:** Bar chart with conditional formatting (green for positive change, red for negative) showing YoY shifts; KPI card for headline diversity change.

```dax
YoY Diversity Change % =
VAR _CurrentYearCount =
    COUNTROWS( fact_employee_metrics )
VAR _CurrentYearTotal =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALL( dim_employee[gender], dim_employee[ethnicity], dim_employee[age_group] )
    )
VAR _CurrentPct =
    IF(
        _CurrentYearTotal = 0,
        BLANK(),
        DIVIDE( _CurrentYearCount, _CurrentYearTotal ) * 100
    )
VAR _PreviousYearCount =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        DATEADD( dim_date[full_date], -1, YEAR )
    )
VAR _PreviousYearTotal =
    CALCULATE(
        COUNTROWS( fact_employee_metrics ),
        ALL( dim_employee[gender], dim_employee[ethnicity], dim_employee[age_group] ),
        DATEADD( dim_date[full_date], -1, YEAR )
    )
VAR _PreviousPct =
    IF(
        _PreviousYearTotal = 0,
        BLANK(),
        DIVIDE( _PreviousYearCount, _PreviousYearTotal ) * 100
    )
RETURN
    IF(
        ISBLANK( _PreviousPct ),
        BLANK(),
        _CurrentPct - _PreviousPct
    )
```

> **Usage Note:** This measure returns the percentage point change (e.g., +2.5 means the group's representation increased by 2.5 percentage points). Use conditional formatting to highlight positive vs. negative shifts. Requires an active relationship between `fact_employee_metrics[date_key]` and `dim_date[date_key]` with a date column marked as a date table.

---

## Usage Instructions

1. Open Power BI Desktop and connect to the star schema database.
2. Navigate to the **Modeling** tab → **New Measure**.
3. Paste each DAX formula above into the formula bar.
4. Assign measures to the appropriate visuals as described.

### Slicer Compatibility

All measures respond to the following slicers (cross-filter):
- **Date Range** — filters `dim_date` to constrain the time period
- **Department** — filters `dim_department[department_name]`
- **Demographic Dimension** — selecting gender, ethnicity, or age group updates all visuals (Requirement 7.3)

### Relationships Required

Ensure the Power BI data model has active relationships:
- `fact_employee_metrics[employee_key]` → `dim_employee[employee_key]`
- `fact_employee_metrics[department_key]` → `dim_department[department_key]`
- `fact_employee_metrics[date_key]` → `dim_date[date_key]`

### Color Coding

Use consistent color assignments for demographic categories across all visuals:
- Assign fixed colors per gender value (e.g., consistent palette for Male, Female, Non-Binary)
- Assign fixed colors per ethnicity group
- Assign fixed colors per age group bucket

This ensures visual consistency when switching between chart types and pages (Requirement 7.2).
