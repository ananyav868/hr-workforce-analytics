# Power BI Dashboard Layout Specification

This document provides a comprehensive page-by-page specification for the HR Workforce Analytics Power BI report. A Power BI developer should use this document to build the `.pbix` file, including visual placement, data bindings, slicer configurations, drill-through navigation, cross-filter behavior, and sparkline settings.

> **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 7.2, 7.3, 7.4, 8.2, 8.4, 8.5**

---

## Report Structure

| Page # | Page Name | Purpose |
|--------|-----------|---------|
| 1 | Turnover Analysis | Attrition trends by department, role, tenure; drill-through to employee detail |
| 2 | Diversity Metrics | Workforce composition across demographic dimensions with department comparison |
| 3 | Department Insights | Scorecard KPIs with sparklines; drill-through to employee risk profiles |
| 4 | Employee Attrition Detail | Drill-through target: individual employee attrition records |
| 5 | Employee Risk Profile | Drill-through target: individual predicted risk and contributing factors |

---

## Data Model Relationships

All pages rely on the following active relationships in the Power BI data model:

```
fact_employee_metrics[employee_key]   → dim_employee[employee_key]
fact_employee_metrics[department_key] → dim_department[department_key]
fact_employee_metrics[job_role_key]   → dim_job_role[job_role_key]
fact_employee_metrics[location_key]   → dim_location[location_key]
fact_employee_metrics[date_key]       → dim_date[date_key]
```

---

## Global Slicer Configuration

The following slicers appear on Pages 1–3 (summary pages) in a consistent slicer panel at the top of each page. They cross-filter all visuals on the page.

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Date Range | `dim_date[full_date]` | Between (date range picker) | Last 12 months |
| Department | `dim_department[department_name]` | Dropdown multi-select | All |
| Job Role | `dim_job_role[job_title]` | Dropdown multi-select | All |
| Location | `dim_location[region]` | Dropdown multi-select | All |

### Slicer Panel Layout

- Position: Top of page, full width
- Height: 60px
- Arrangement: Horizontal, evenly spaced (4 slicers in a row)
- Background: Light gray (#F5F5F5) with subtle border

### Slicer Sync

All four slicers are synced across Pages 1–3 using Power BI's "Sync Slicers" feature. Changing a slicer on one page persists the selection when navigating to another page.

---

## Page 1: Turnover Analysis

**Purpose:** Provide HR leaders with an interactive view of attrition patterns across departments, roles, and time periods. Supports drill-through to individual employee attrition details.

### Page Layout (1280×720 canvas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Date Range]   [Department]   [Job Role]   [Location]              │  ← Slicer Panel (60px)
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  KPI Card:   │  │  KPI Card:   │  │  KPI Card:   │              │  ← KPI Row (100px)
│  │  Overall     │  │  Total       │  │  Avg Monthly │              │
│  │  Attrition % │  │  Departures  │  │  Trend       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Line Chart: Monthly Attrition Trend                           │ │  ← Trend Chart (200px)
│  │  X: dim_date[month_name] + dim_date[year]                     │ │
│  │  Y: [Monthly Attrition Trend] measure                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────┬──────────────────────────────────┤
│  ┌──────────────────────────────┐│  ┌──────────────────────────────┐│
│  │  Bar Chart: Attrition by     ││  │  Bar Chart: Attrition by     ││  ← Detail Charts (260px)
│  │  Department                  ││  │  Job Role                    ││
│  │  X: dim_department           ││  │  X: dim_job_role[job_title]  ││
│  │     [department_name]        ││  │  Y: [Department Attrition    ││
│  │  Y: [Department Attrition    ││  │       Rate] measure          ││
│  │       Rate] measure          ││  │                              ││
│  └──────────────────────────────┘│  └──────────────────────────────┘│
├──────────────────────────────────┴──────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Clustered Bar: Attrition by Tenure Band                       │ │  ← Tenure Chart (100px)
│  │  X: dim_employee[salary_band] (used as tenure band proxy)      │ │
│  │  Y: [Department Attrition Rate] measure                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Visual Specifications

#### V1.1 — KPI Card: Overall Attrition Rate
| Property | Value |
|----------|-------|
| Visual Type | Card |
| Measure | `[Overall Attrition Rate]` |
| Format | Percentage, 1 decimal place |
| Conditional Format | Green < 10%, Yellow 10–20%, Red > 20% |
| Size | 200×100 px |

#### V1.2 — KPI Card: Total Departures
| Property | Value |
|----------|-------|
| Visual Type | Card |
| Measure | `CALCULATE(COUNTROWS(fact_employee_metrics), fact_employee_metrics[attrition_flag] = TRUE())` |
| Format | Whole number |
| Size | 200×100 px |

#### V1.3 — KPI Card: Average Monthly Attrition
| Property | Value |
|----------|-------|
| Visual Type | Card |
| Measure | `AVERAGEX(VALUES(dim_date[month]), [Monthly Attrition Trend])` |
| Format | Percentage, 1 decimal place |
| Size | 200×100 px |

#### V1.4 — Line Chart: Monthly Attrition Trend
| Property | Value |
|----------|-------|
| Visual Type | Line Chart |
| X-Axis | `dim_date[full_date]` (continuous, month granularity) |
| Y-Axis | `[Monthly Attrition Trend]` measure |
| Reference Line | `[Overall Attrition Rate]` as constant line (dashed) |
| Data Labels | Off |
| Markers | On (small circles) |
| Size | Full width × 200px |

#### V1.5 — Bar Chart: Attrition by Department
| Property | Value |
|----------|-------|
| Visual Type | Clustered Bar Chart |
| Y-Axis (Category) | `dim_department[department_name]` |
| X-Axis (Value) | `[Department Attrition Rate]` measure |
| Sort | Descending by value |
| Data Labels | On (end of bar) |
| Size | 50% width × 260px |

#### V1.6 — Bar Chart: Attrition by Job Role
| Property | Value |
|----------|-------|
| Visual Type | Clustered Bar Chart |
| Y-Axis (Category) | `dim_job_role[job_title]` |
| X-Axis (Value) | `[Department Attrition Rate]` measure |
| Sort | Descending by value |
| Data Labels | On (end of bar) |
| Size | 50% width × 260px |

#### V1.7 — Clustered Bar: Attrition by Tenure Band
| Property | Value |
|----------|-------|
| Visual Type | Clustered Bar Chart |
| X-Axis (Category) | Tenure band grouping (0–12mo, 13–36mo, 37–60mo, 60+mo) |
| Y-Axis (Value) | `[Department Attrition Rate]` measure |
| Sort | Logical order (shortest to longest tenure) |
| Size | Full width × 100px |

### Cross-Filter Behavior

| Source Visual | Target Visuals | Interaction |
|---------------|----------------|-------------|
| Bar: Attrition by Department | All other visuals on page | Cross-filter (highlight) |
| Bar: Attrition by Job Role | All other visuals on page | Cross-filter (highlight) |
| Line: Monthly Trend | Bar charts | Cross-filter when point selected |
| Bar: Tenure Band | All other visuals on page | Cross-filter (highlight) |

**Interaction Rules:**
- All visuals cross-filter each other by default (Power BI default behavior)
- The Monthly Attrition Trend line chart does NOT filter the KPI cards (edit interaction → None)
- Clicking a department bar filters the Job Role and Tenure charts to show only that department's data

### Drill-Through: Employee Attrition Detail

**Trigger:** Right-click on any department bar or data point → "Drill through" → "Employee Attrition Detail"

**Drill-through field:** `dim_department[department_name]`

When triggered, navigates to Page 4 (Employee Attrition Detail) filtered to the selected department.

---

## Page 2: Diversity Metrics

**Purpose:** Monitor workforce composition across demographic dimensions (gender, ethnicity, age group) and compare diversity metrics across departments. Supports dynamic dimension switching.

### Page Layout (1280×720 canvas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Date Range]   [Department]   [Job Role]   [Location]              │  ← Slicer Panel (60px)
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Demographic Dimension Selector: [Gender] [Ethnicity] [Age]  │   │  ← Selector (40px)
│  └──────────────────────────────────────────────────────────────┘   │
├──────────────────────────────────┬──────────────────────────────────┤
│  ┌──────────────────────────────┐│  ┌──────────────────────────────┐│
│  │  Stacked Bar Chart:          ││  │  Donut Chart:                ││  ← Primary Visuals (280px)
│  │  Distribution by Department  ││  │  Overall Distribution        ││
│  │                              ││  │                              ││
│  │  X: dim_department           ││  │  Legend: demographic field   ││
│  │     [department_name]        ││  │  Value: distribution %       ││
│  │  Y: [distribution %] measure││  │                              ││
│  │  Legend: demographic field   ││  │                              ││
│  └──────────────────────────────┘│  └──────────────────────────────┘│
├──────────────────────────────────┴──────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Matrix / Table: Department Comparison                         │ │  ← Comparison (200px)
│  │  Rows: dim_department[department_name]                         │ │
│  │  Columns: demographic categories (dynamic)                     │ │
│  │  Values: distribution % measure                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Bar Chart: Year-over-Year Diversity Change                    │ │  ← YoY Chart (140px)
│  │  X: demographic categories                                     │ │
│  │  Y: [YoY Diversity Change %] measure                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Demographic Dimension Selector

**Implementation:** Use a disconnected slicer table (also called a "what-if parameter" or field parameter) to allow users to switch the active demographic dimension.

#### Disconnected Table: `DemographicSelector`

```
| DimensionName | DimensionOrder |
|---------------|----------------|
| Gender        | 1              |
| Ethnicity     | 2              |
| Age Group     | 3              |
```

#### Dynamic Measure: `Selected Distribution %`

```dax
Selected Distribution % =
SWITCH(
    SELECTEDVALUE( DemographicSelector[DimensionName] ),
    "Gender", [Gender Ratio %],
    "Ethnicity", [Ethnicity Distribution %],
    "Age Group", [Age Group Distribution %],
    [Gender Ratio %]  -- default
)
```

#### Dynamic Category Field (Field Parameter)

Create a Field Parameter named `DemographicCategory` containing:
- `dim_employee[gender]`
- `dim_employee[ethnicity]`
- `dim_employee[age_group]`

The dimension selector slicer controls which field is active on the axis/legend of all visuals.

### Visual Specifications

#### V2.1 — Demographic Dimension Selector
| Property | Value |
|----------|-------|
| Visual Type | Slicer (Tile/Button style) |
| Field | `DemographicSelector[DimensionName]` |
| Selection | Single select |
| Default | Gender |
| Style | Horizontal button tiles |
| Size | Full width × 40px |

#### V2.2 — Stacked Bar Chart: Distribution by Department
| Property | Value |
|----------|-------|
| Visual Type | 100% Stacked Bar Chart |
| X-Axis (Category) | `dim_department[department_name]` |
| Y-Axis (Value) | `[Selected Distribution %]` measure |
| Legend | `DemographicCategory` field parameter (dynamic) |
| Color | Consistent palette per demographic category (see Color Coding below) |
| Data Labels | On (percentage inside segments) |
| Size | 50% width × 280px |

#### V2.3 — Donut Chart: Overall Distribution
| Property | Value |
|----------|-------|
| Visual Type | Donut Chart |
| Legend | `DemographicCategory` field parameter (dynamic) |
| Values | `[Selected Distribution %]` measure |
| Detail Labels | Category name + percentage |
| Inner Radius | 60% |
| Color | Same consistent palette as stacked bar |
| Size | 50% width × 280px |

#### V2.4 — Matrix: Department Comparison
| Property | Value |
|----------|-------|
| Visual Type | Matrix |
| Rows | `dim_department[department_name]` |
| Columns | `DemographicCategory` field parameter (dynamic) |
| Values | `[Selected Distribution %]` measure |
| Conditional Formatting | Background color scale (light to dark) based on percentage |
| Row Subtotals | On (shows overall distribution) |
| Size | Full width × 200px |

#### V2.5 — Bar Chart: Year-over-Year Diversity Change
| Property | Value |
|----------|-------|
| Visual Type | Clustered Bar Chart |
| X-Axis (Category) | `DemographicCategory` field parameter (dynamic) |
| Y-Axis (Value) | `[YoY Diversity Change %]` measure |
| Conditional Format | Green bars for positive change, Red bars for negative change |
| Reference Line | Zero line (baseline) |
| Data Labels | On (value at end of bar with +/- sign) |
| Size | Full width × 140px |

### Color Coding (Consistent Across All Visuals)

| Dimension | Category | Color |
|-----------|----------|-------|
| Gender | Male | #4472C4 (Blue) |
| Gender | Female | #ED7D31 (Orange) |
| Gender | Non-Binary | #70AD47 (Green) |
| Ethnicity | White | #4472C4 |
| Ethnicity | Black/African American | #ED7D31 |
| Ethnicity | Hispanic/Latino | #70AD47 |
| Ethnicity | Asian | #FFC000 (Gold) |
| Ethnicity | Other | #5B9BD5 (Light Blue) |
| Age Group | 18–25 | #4472C4 |
| Age Group | 26–35 | #ED7D31 |
| Age Group | 36–45 | #70AD47 |
| Age Group | 46–55 | #FFC000 |
| Age Group | 56+ | #5B9BD5 |

### Cross-Filter Behavior

| Source Visual | Target Visuals | Interaction |
|---------------|----------------|-------------|
| Dimension Selector | All visuals on page | Updates field parameter (switches dimension) |
| Stacked Bar (click segment) | Donut, Matrix, YoY chart | Cross-filter (highlight matching category) |
| Donut (click slice) | Stacked Bar, Matrix, YoY chart | Cross-filter (highlight matching category) |
| Matrix (click cell) | Stacked Bar, Donut | Cross-filter (highlight department + category) |

**Interaction Rules:**
- Selecting a demographic dimension via the selector updates ALL visuals to reflect that dimension
- Clicking a department segment in the stacked bar highlights that department across all visuals
- The YoY chart does NOT filter other visuals (edit interaction → None for outgoing)

---

## Page 3: Department Insights

**Purpose:** Provide department managers with an at-a-glance scorecard of workforce health KPIs, each with 12-month trend sparklines. Supports drill-through to individual employee risk profiles.

### Page Layout (1280×720 canvas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Date Range]   [Department]                                        │  ← Slicer Panel (60px)
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Page Title: "Department Insights — [Department Name]"      │    │  ← Title (40px)
│  └─────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Headcount │ │Attrition │ │Avg Tenure│ │Avg Satis.│ │  Open    │ │  ← Scorecard Row 1
│  │  [value] │ │  [value] │ │  [value] │ │  [value] │ │Positions │ │    (120px)
│  │ ~~spark~~│ │ ~~spark~~│ │ ~~spark~~│ │ ~~spark~~│ │ ~~spark~~│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Predicted Attrition Risk — Gauge Visual                     │   │  ← Risk Gauge (120px)
│  │  Value: [Predicted Attrition Risk] measure                   │   │
│  │  Target: 15% (organizational goal)                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Table: Employee Risk Summary                                  │ │  ← Risk Table (280px)
│  │  Columns: Employee Name | Job Title | Tenure | Satisfaction |  │ │
│  │           Attrition Probability | Risk Level                   │ │
│  │  Sort: Attrition Probability descending                        │ │
│  │  Drill-through enabled on each row                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Row-Level Security Default Behavior

When a user with the `Department_Manager` role opens this page:
- The Department slicer is automatically filtered to the manager's assigned department
- All KPIs and the employee table show only that department's data
- The slicer is visible but restricted (cannot select other departments)

When a user with the `HR_Executive` role opens this page:
- The Department slicer defaults to "All" showing aggregated metrics
- The executive can select individual departments to drill into

### Visual Specifications

#### V3.1–V3.5 — Scorecard KPI Cards with Sparklines

Each KPI card follows the same template:

| Property | Value |
|----------|-------|
| Visual Type | Multi-row Card or KPI Visual |
| Layout | 5 cards in a horizontal row, equal width |
| Card Size | ~230×120 px each |

**Individual KPI Bindings:**

| Card | Measure | Format | Sparkline Measure |
|------|---------|--------|-------------------|
| V3.1 Headcount | `[Department Headcount]` | Whole number | Monthly headcount trend |
| V3.2 Attrition Rate | `[Dept Attrition Rate %]` | Percentage, 1 decimal | Monthly attrition trend |
| V3.3 Avg Tenure | `[Avg Tenure (Months)]` | Number, 1 decimal + "mo" | Monthly avg tenure trend |
| V3.4 Avg Satisfaction | `[Avg Satisfaction Score]` | Number, 2 decimals | Monthly satisfaction trend |
| V3.5 Open Positions | `[Open Positions]` | Whole number | Monthly open positions trend |

### Sparkline Configuration

Each KPI card includes an inline sparkline showing the last 12 months of trend data.

#### Sparkline Implementation

**Option A — Native Sparkline (Power BI 2023+):**

Use the built-in sparkline feature in the new Card visual:
1. Add the KPI measure as the primary value
2. In the card's "Sparkline" section, configure:
   - X-axis: `dim_date[full_date]` (last 12 months)
   - Y-axis: Same measure as the KPI
   - Line color: Match KPI conditional formatting color
   - Show min/max markers: Yes

**Option B — Calculated Sparkline (Legacy):**

If native sparklines are unavailable, use a small line chart visual overlaid on each card:

```dax
Headcount Sparkline =
CALCULATE(
    [Department Headcount],
    DATESINPERIOD(
        dim_date[full_date],
        MAX( dim_date[full_date] ),
        -12,
        MONTH
    )
)
```

| Sparkline Property | Value |
|--------------------|-------|
| Visual Type | Line Chart (small, no axis labels) |
| X-Axis | `dim_date[full_date]` (last 12 months) |
| Y-Axis | Respective KPI measure |
| Show X-Axis | Off |
| Show Y-Axis | Off |
| Show Legend | Off |
| Show Data Labels | Off |
| Line Width | 2px |
| Line Color | Matches KPI conditional color |
| Show Min/Max Points | Highlighted dots at min and max values |
| Size | ~200×40 px (embedded within card) |

#### Sparkline Date Filter

All sparklines use a fixed 12-month rolling window regardless of the date range slicer:

```dax
Sparkline Date Filter =
DATESINPERIOD(
    dim_date[full_date],
    MAX( dim_date[full_date] ),
    -12,
    MONTH
)
```

#### V3.6 — Gauge: Predicted Attrition Risk
| Property | Value |
|----------|-------|
| Visual Type | Gauge |
| Value | `[Predicted Attrition Risk]` measure |
| Min | 0% |
| Max | 50% |
| Target | 15% (organizational threshold) |
| Color Bands | Green: 0–15%, Yellow: 15–30%, Red: 30–50% |
| Size | Full width × 120px |

#### V3.7 — Table: Employee Risk Summary
| Property | Value |
|----------|-------|
| Visual Type | Table |
| Columns (in order) | See below |
| Sort | `attrition_probability` descending |
| Conditional Formatting | Row background: gradient by risk level |
| Pagination | 15 rows per page |
| Size | Full width × 280px |

**Table Columns:**

| Column | Source | Format |
|--------|--------|--------|
| Employee Name | `dim_employee[full_name]` | Text |
| Job Title | `dim_job_role[job_title]` | Text |
| Tenure (Months) | `fact_employee_metrics[tenure_months]` | Number, 0 decimals |
| Satisfaction | `fact_employee_metrics[satisfaction_score]` | Number, 2 decimals |
| Attrition Probability | `fact_employee_metrics[attrition_probability]` | Percentage, 1 decimal |
| Risk Level | Calculated column (see below) | Text with icon |

**Risk Level Calculated Column:**

```dax
Risk Level =
SWITCH(
    TRUE(),
    fact_employee_metrics[attrition_probability] >= 0.30, "High",
    fact_employee_metrics[attrition_probability] >= 0.15, "Medium",
    "Low"
)
```

**Conditional Formatting for Risk Level:**
- High: Red background (#FFC7CE), Red text (#9C0006)
- Medium: Yellow background (#FFEB9C), Dark yellow text (#9C6500)
- Low: Green background (#C6EFCE), Green text (#006100)

### Cross-Filter Behavior

| Source Visual | Target Visuals | Interaction |
|---------------|----------------|-------------|
| KPI Cards | No outgoing filter | None |
| Gauge | No outgoing filter | None |
| Employee Table (row click) | Enables drill-through | Drill-through to Page 5 |

**Interaction Rules:**
- KPI cards and gauge are display-only (no outgoing cross-filter)
- The Employee Risk Summary table supports row-level drill-through
- Department slicer filters all visuals on the page

### Drill-Through: Employee Risk Profile

**Trigger:** Right-click on any row in the Employee Risk Summary table → "Drill through" → "Employee Risk Profile"

**Drill-through field:** `dim_employee[employee_key]`

When triggered, navigates to Page 5 (Employee Risk Profile) filtered to the selected employee.

---

## Page 4: Employee Attrition Detail (Drill-Through Target)

**Purpose:** Show individual employee attrition records for a selected department. This page is accessed via drill-through from the Turnover Analysis page.

### Drill-Through Configuration

| Property | Value |
|----------|-------|
| Drill-through field | `dim_department[department_name]` |
| Keep all filters | Yes |
| Back button | Top-left corner, always visible |
| Page visibility | Hidden (only accessible via drill-through) |

### Page Layout (1280×720 canvas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [← Back]   Department: [Selected Department Name]                  │  ← Header (50px)
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Total    │  │ Dept     │  │ Avg      │  │ Most     │           │  ← Summary KPIs (80px)
│  │Departures│  │Attrition%│  │ Tenure at│  │ Common   │           │
│  │          │  │          │  │ Departure│  │ Role     │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Table: Employee Attrition Records                             │ │  ← Detail Table (500px)
│  │  Columns: Name | Role | Hire Date | Termination Date |         │ │
│  │           Tenure | Satisfaction | Overtime | Salary Band        │ │
│  │  Filter: attrition_flag = TRUE                                 │ │
│  │  Sort: Termination Date descending                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Visual Specifications

#### V4.1 — Summary KPI Cards
| Card | Measure/Field | Format |
|------|---------------|--------|
| Total Departures | `CALCULATE(COUNTROWS(fact_employee_metrics), fact_employee_metrics[attrition_flag] = TRUE())` | Whole number |
| Dept Attrition % | `[Dept Attrition Rate %]` | Percentage, 1 decimal |
| Avg Tenure at Departure | `CALCULATE(AVERAGE(fact_employee_metrics[tenure_months]), fact_employee_metrics[attrition_flag] = TRUE())` | Number, 1 decimal + "mo" |
| Most Common Role | `TOPN(1, VALUES(dim_job_role[job_title]), COUNTROWS(fact_employee_metrics), DESC)` | Text |

#### V4.2 — Detail Table: Employee Attrition Records
| Column | Source | Format |
|--------|--------|--------|
| Employee Name | `dim_employee[full_name]` | Text |
| Job Title | `dim_job_role[job_title]` | Text |
| Hire Date | `dim_employee[hire_date]` | Date (MMM YYYY) |
| Termination Date | `dim_employee[termination_date]` | Date (MMM YYYY) |
| Tenure (Months) | `fact_employee_metrics[tenure_months]` | Number, 0 decimals |
| Satisfaction Score | `fact_employee_metrics[satisfaction_score]` | Number, 2 decimals |
| Overtime Hours | `fact_employee_metrics[overtime_hours]` | Number, 0 decimals |
| Salary Band | `dim_employee[salary_band]` | Text |

**Table Filter:** `fact_employee_metrics[attrition_flag] = TRUE()`
**Sort:** Termination Date descending (most recent departures first)
**Pagination:** 20 rows per page

---

## Page 5: Employee Risk Profile (Drill-Through Target)

**Purpose:** Show detailed risk information for a single employee, including predicted attrition probability, contributing factors, and historical risk trend. Accessed via drill-through from the Department Insights page.

### Drill-Through Configuration

| Property | Value |
|----------|-------|
| Drill-through field | `dim_employee[employee_key]` |
| Keep all filters | Yes |
| Back button | Top-left corner, always visible |
| Page visibility | Hidden (only accessible via drill-through) |

### Page Layout (1280×720 canvas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [← Back]   Employee: [Employee Name]                               │  ← Header (50px)
├──────────────────────────────────┬──────────────────────────────────┤
│  ┌──────────────────────────────┐│  ┌──────────────────────────────┐│
│  │  Employee Info Card          ││  │  Risk Gauge                  ││  ← Profile Row (150px)
│  │  Name: [full_name]           ││  │  Value: attrition_probability││
│  │  Department: [dept_name]     ││  │  Bands: Green/Yellow/Red     ││
│  │  Role: [job_title]           ││  │                              ││
│  │  Tenure: [tenure_months] mo  ││  │                              ││
│  │  Location: [city, region]    ││  │                              ││
│  └──────────────────────────────┘│  └──────────────────────────────┘│
├──────────────────────────────────┴──────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Bar Chart: Top Contributing Factors                           │ │  ← Factors (220px)
│  │  Y-Axis: Feature names (from feature importance)               │ │
│  │  X-Axis: Contribution weight                                   │ │
│  │  Top 8 factors shown                                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Line Chart: Historical Risk Score Trend                       │ │  ← Trend (200px)
│  │  X-Axis: dim_date[full_date] (monthly)                        │ │
│  │  Y-Axis: fact_employee_metrics[attrition_probability]          │ │
│  │  Reference Line: 15% threshold (dashed red)                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  KPI Row: Key Metrics                                          │ │  ← Metrics (100px)
│  │  [Satisfaction] [Overtime Hrs] [Salary Band] [Promotion Recent]│ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Visual Specifications

#### V5.1 — Employee Info Card
| Property | Value |
|----------|-------|
| Visual Type | Multi-row Card |
| Fields | `dim_employee[full_name]`, `dim_department[department_name]`, `dim_job_role[job_title]`, `fact_employee_metrics[tenure_months]`, `dim_location[city]`, `dim_location[region]` |
| Size | 50% width × 150px |

#### V5.2 — Risk Gauge
| Property | Value |
|----------|-------|
| Visual Type | Gauge |
| Value | `fact_employee_metrics[attrition_probability]` |
| Min | 0% |
| Max | 100% |
| Target | 15% |
| Color Bands | Green: 0–15%, Yellow: 15–30%, Red: 30–100% |
| Size | 50% width × 150px |

#### V5.3 — Bar Chart: Top Contributing Factors
| Property | Value |
|----------|-------|
| Visual Type | Clustered Bar Chart |
| Y-Axis (Category) | Feature name (from model feature importance data) |
| X-Axis (Value) | Feature importance weight |
| Top N | Show top 8 factors only |
| Sort | Descending by importance weight |
| Data Labels | On (end of bar) |
| Color | Single color (#4472C4) |
| Size | Full width × 220px |

> **Note:** Feature importance data comes from the ML model's `get_feature_importance()` output, stored in a supplementary table or embedded in the fact table. If stored separately, create a relationship on `employee_key`.

#### V5.4 — Line Chart: Historical Risk Score Trend
| Property | Value |
|----------|-------|
| Visual Type | Line Chart |
| X-Axis | `dim_date[full_date]` (monthly granularity) |
| Y-Axis | `fact_employee_metrics[attrition_probability]` |
| Reference Line | Constant at 0.15 (15% threshold), dashed red |
| Markers | On |
| Data Labels | Off |
| Size | Full width × 200px |

#### V5.5 — KPI Metric Cards
| Card | Field | Format |
|------|-------|--------|
| Satisfaction | `fact_employee_metrics[satisfaction_score]` | Number, 2 decimals |
| Overtime Hours | `fact_employee_metrics[overtime_hours]` | Whole number + "hrs/mo" |
| Salary Band | `dim_employee[salary_band]` | Text |
| Promotion Recent | `dim_employee[promotion_recent]` | Yes/No icon |

---

## Cross-Page Navigation Summary

```
┌─────────────────────┐     Drill-through      ┌──────────────────────────┐
│  Page 1: Turnover   │ ──────────────────────► │  Page 4: Employee        │
│  Analysis           │  (by department_name)   │  Attrition Detail        │
└─────────────────────┘                         └──────────────────────────┘

┌─────────────────────┐     Drill-through      ┌──────────────────────────┐
│  Page 3: Department │ ──────────────────────► │  Page 5: Employee        │
│  Insights           │  (by employee_key)      │  Risk Profile            │
└─────────────────────┘                         └──────────────────────────┘
```

### Navigation Buttons

Each summary page (1–3) includes a navigation bar at the bottom:

| Button | Target | Style |
|--------|--------|-------|
| "Turnover Analysis" | Page 1 | Active/highlighted when on page |
| "Diversity Metrics" | Page 2 | Active/highlighted when on page |
| "Department Insights" | Page 3 | Active/highlighted when on page |

Implementation: Use Power BI Buttons with "Page navigation" action type.

---

## Appendix: Implementation Checklist

| # | Task | Page |
|---|------|------|
| 1 | Create data model with all relationships | All |
| 2 | Create DemographicSelector disconnected table | Page 2 |
| 3 | Create Field Parameter for demographic categories | Page 2 |
| 4 | Import all DAX measures from `src/powerbi/dax_measures/` | All |
| 5 | Build slicer panel and configure sync | Pages 1–3 |
| 6 | Build Turnover Analysis visuals | Page 1 |
| 7 | Configure drill-through on department_name | Page 1 → 4 |
| 8 | Build Diversity Metrics visuals with dimension selector | Page 2 |
| 9 | Build Department Insights scorecard with sparklines | Page 3 |
| 10 | Configure drill-through on employee_key | Page 3 → 5 |
| 11 | Build Employee Attrition Detail page | Page 4 |
| 12 | Build Employee Risk Profile page | Page 5 |
| 13 | Configure cross-filter interactions per spec | All |
| 14 | Add navigation buttons | Pages 1–3 |
| 15 | Apply consistent color theme | All |
| 16 | Configure Row-Level Security roles | All |
| 17 | Test drill-through navigation end-to-end | Pages 1,3,4,5 |
