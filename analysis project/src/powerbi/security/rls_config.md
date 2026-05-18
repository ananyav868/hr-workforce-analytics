# Row-Level Security (RLS) Configuration

## Overview

This document defines the Row-Level Security configuration for the HR Workforce Analytics Power BI dashboards. RLS restricts data access so that department managers see only their own department's data, while HR executives have unrestricted access across all departments.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

---

## Role Definitions

### 1. Department_Manager Role

**Purpose:** Restricts all dashboard data to the manager's assigned department only.

**Table:** `dim_department`

**DAX Filter Expression:**

```dax
[department_head] = USERPRINCIPALNAME()
```

**Behavior:**
- When a user assigned to the `Department_Manager` role opens the dashboard, the filter expression evaluates against the `dim_department` table.
- The `USERPRINCIPALNAME()` function returns the user's email address (e.g., `jane.smith@company.com`) from the Power BI service authentication context.
- Only rows in `dim_department` where `department_head` matches the authenticated user's UPN are visible.
- Because `dim_department` participates in relationships with `fact_employee_metrics`, the filter propagates to all related tables — effectively restricting all visuals to the manager's department.

**Alternative (on-premises):**

If using an on-premises gateway where UPN is not available, use `USERNAME()` instead:

```dax
[department_head] = USERNAME()
```

> `USERNAME()` returns `DOMAIN\username` format. Ensure the `department_head` column stores values in the matching format.

---

### 2. HR_Executive Role

**Purpose:** Provides unrestricted access to all departments and all data.

**Table:** `dim_department`

**DAX Filter Expression:**

```dax
1 = 1
```

**Behavior:**
- The expression `1 = 1` always evaluates to `TRUE`, meaning no rows are filtered out.
- Users assigned to the `HR_Executive` role see data across all departments without restriction.
- This role is intended for senior HR leadership and system administrators who require a complete view of workforce analytics.

---

### 3. Access-Denied Behavior (No Role Assigned)

**Behavior:**
- If a user has **no assigned role** in the Power BI service, RLS returns an empty dataset for all tables.
- All visuals display blank/empty states since no data passes through the security filter.
- To provide a user-friendly experience, configure a **conditional visibility message** on each dashboard page:

**Recommended Implementation:**

1. Create a DAX measure to detect empty data:

```dax
Has Access = 
IF(
    COUNTROWS(dim_department) > 0,
    1,
    0
)
```

2. Create a text card visual with the message:

```
⚠️ Access Denied: You do not have permission to view this data.
Please contact your HR administrator to request access.
```

3. Set the text card's visibility to show only when `[Has Access] = 0` using conditional formatting or bookmarks.
4. Set all other visuals to be visible only when `[Has Access] = 1`.

---

## User-to-Department Mapping Table (Optional)

If a single manager oversees multiple departments, or if the `department_head` field does not directly store the user's UPN, create a mapping table:

### Table: `rls_user_department_map`

| Column | Data Type | Description |
|--------|-----------|-------------|
| user_email | VARCHAR(200) | User's UPN / email address |
| department_key | INT | FK to dim_department.department_key |
| role_name | VARCHAR(50) | Role assignment (Department_Manager, HR_Executive) |

### DDL (if needed):

```sql
CREATE TABLE rls_user_department_map (
    map_id          INT IDENTITY(1,1) NOT NULL,
    user_email      VARCHAR(200)      NOT NULL,
    department_key  INT               NOT NULL,
    role_name       VARCHAR(50)       NOT NULL,

    CONSTRAINT PK_rls_user_department_map PRIMARY KEY (map_id),
    CONSTRAINT FK_rls_map_department FOREIGN KEY (department_key)
        REFERENCES dim_department(department_key)
);
```

### Modified DAX Filter (using mapping table):

```dax
[department_key] IN 
CALCULATETABLE(
    VALUES(rls_user_department_map[department_key]),
    rls_user_department_map[user_email] = USERPRINCIPALNAME()
)
```

> Use this approach when the direct `department_head` match is insufficient.

---

## Configuration Instructions (Power BI Desktop)

### Step 1: Open the Data Model

1. Open the `.pbix` file in Power BI Desktop.
2. Navigate to **Modeling** tab in the ribbon.

### Step 2: Create Roles

1. Click **Manage Roles** in the Modeling tab.
2. Click **Create** to add a new role.

### Step 3: Define Department_Manager Role

1. Name the role: `Department_Manager`
2. Select the `dim_department` table in the table list.
3. In the **Table filter DAX expression** field, enter:

```dax
[department_head] = USERPRINCIPALNAME()
```

4. Click the checkmark to validate the expression.
5. Click **Save**.

### Step 4: Define HR_Executive Role

1. Click **Create** to add another role.
2. Name the role: `HR_Executive`
3. Select the `dim_department` table.
4. In the **Table filter DAX expression** field, enter:

```dax
1 = 1
```

5. Click the checkmark to validate.
6. Click **Save**.

### Step 5: Publish to Power BI Service

1. Publish the report to a Power BI workspace.
2. In the Power BI service, navigate to the dataset settings.
3. Under **Security**, assign users to the appropriate roles:
   - Add department managers to `Department_Manager`
   - Add HR executives to `HR_Executive`

---

## Testing Instructions

### Test in Power BI Desktop (View as Role)

1. In Power BI Desktop, go to **Modeling** → **View as**.
2. Check the `Department_Manager` role.
3. Optionally enter a specific UPN in the **Other user** field (e.g., `john.doe@company.com`).
4. Click **OK**.
5. **Verify:** Only data for the department where `department_head = john.doe@company.com` is visible.
6. Repeat for `HR_Executive` role — all data should be visible.

### Test with No Role

1. In **View as**, uncheck all roles.
2. **Verify:** All data is visible (this is the report author view).
3. To simulate no-role behavior, publish to the service and access with a user who has no role assignment — they should see no data.

### Test in Power BI Service

1. Navigate to the published dataset in the Power BI service.
2. Click the **ellipsis (...)** next to the dataset → **Security**.
3. Select the `Department_Manager` role.
4. Enter a test user's email in the **Test as** field.
5. Click **Test**.
6. **Verify:** The report opens showing only the test user's department data.
7. Repeat for `HR_Executive` — all departments should be visible.
8. Test with a user who has no role — verify empty visuals and access-denied message.

### Validation Checklist

| Test Case | Expected Result | Status |
|-----------|----------------|--------|
| Department_Manager sees own department only | Only matching department data visible | ☐ |
| Department_Manager cannot see other departments | Other department data is hidden | ☐ |
| HR_Executive sees all departments | All department data visible | ☐ |
| Unassigned user sees no data | Empty visuals, access-denied message shown | ☐ |
| Filter propagates to fact table | Metrics, charts, and KPIs all respect RLS | ☐ |
| Drill-through respects RLS | Detail pages show only permitted data | ☐ |

---

## Summary

| Role | DAX Filter | Scope |
|------|-----------|-------|
| Department_Manager | `[department_head] = USERPRINCIPALNAME()` | Own department only |
| HR_Executive | `1 = 1` | All departments |
| No role assigned | N/A (no data returned) | Access denied |
