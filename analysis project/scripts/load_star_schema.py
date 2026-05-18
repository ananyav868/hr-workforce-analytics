"""Load staging data into MySQL star schema (dimensions + fact table)."""

import pymysql

conn = pymysql.connect(host='localhost', user='root', password='sharma2003', database='hr_analytics')
cursor = conn.cursor()

# Create dimension and fact tables
print("Creating star schema tables...")

# Drop existing tables in correct order (fact first due to FK constraints)
cursor.execute("DROP TABLE IF EXISTS fact_employee_metrics")
cursor.execute("DROP TABLE IF EXISTS dim_employee")
cursor.execute("DROP TABLE IF EXISTS dim_department")
cursor.execute("DROP TABLE IF EXISTS dim_job_role")
cursor.execute("DROP TABLE IF EXISTS dim_location")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_department (
    department_key INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_job_role (
    job_role_key INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(150) NOT NULL UNIQUE
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_location (
    location_key INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(200) NOT NULL UNIQUE
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_employee (
    employee_key INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    gender VARCHAR(20),
    ethnicity VARCHAR(50),
    age INT,
    age_group VARCHAR(20),
    hire_date DATE,
    salary_band VARCHAR(30)
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fact_employee_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_key INT NOT NULL,
    department_key INT NOT NULL,
    job_role_key INT NOT NULL,
    location_key INT NOT NULL,
    attrition_flag TINYINT NOT NULL,
    headcount INT NOT NULL DEFAULT 1,
    tenure_months DECIMAL(6,1),
    satisfaction_score DECIMAL(3,1),
    salary DECIMAL(12,2),
    overtime_hours INT,
    overtime_flag TINYINT,
    FOREIGN KEY (employee_key) REFERENCES dim_employee(employee_key),
    FOREIGN KEY (department_key) REFERENCES dim_department(department_key),
    FOREIGN KEY (job_role_key) REFERENCES dim_job_role(job_role_key),
    FOREIGN KEY (location_key) REFERENCES dim_location(location_key)
)""")

conn.commit()
print("Tables created!")

# Load dimensions from staging
print("\nLoading dimensions...")

cursor.execute("INSERT IGNORE INTO dim_department (department_name) SELECT DISTINCT department FROM stg_employee_data")
print(f"  dim_department: {cursor.rowcount} rows")

cursor.execute("INSERT IGNORE INTO dim_job_role (job_title) SELECT DISTINCT job_role FROM stg_employee_data")
print(f"  dim_job_role: {cursor.rowcount} rows")

cursor.execute("INSERT IGNORE INTO dim_location (location_name) SELECT DISTINCT location FROM stg_employee_data")
print(f"  dim_location: {cursor.rowcount} rows")

cursor.execute("""
    INSERT IGNORE INTO dim_employee (employee_id, name, gender, ethnicity, age, age_group, hire_date, salary_band)
    SELECT employee_id, name, gender, ethnicity, age, age_group, hire_date, salary_band
    FROM stg_employee_data
""")
print(f"  dim_employee: {cursor.rowcount} rows")

conn.commit()

# Load fact table
print("\nLoading fact table...")
cursor.execute("DELETE FROM fact_employee_metrics")  # Clear for idempotency

cursor.execute("""
    INSERT INTO fact_employee_metrics
        (employee_key, department_key, job_role_key, location_key,
         attrition_flag, headcount, tenure_months, satisfaction_score,
         salary, overtime_hours, overtime_flag)
    SELECT
        e.employee_key, d.department_key, j.job_role_key, l.location_key,
        s.attrition, 1, s.tenure_months, s.satisfaction_score,
        s.salary, s.overtime_hours, s.overtime_flag
    FROM stg_employee_data s
    JOIN dim_employee e ON e.employee_id = s.employee_id
    JOIN dim_department d ON d.department_name = s.department
    JOIN dim_job_role j ON j.job_title = s.job_role
    JOIN dim_location l ON l.location_name = s.location
""")
print(f"  fact_employee_metrics: {cursor.rowcount} rows")
conn.commit()

# Create views
print("\nCreating views...")

cursor.execute("""
    CREATE OR REPLACE VIEW vw_turnover_summary AS
    SELECT
        d.department_name,
        COUNT(*) AS headcount,
        SUM(f.attrition_flag) AS departures,
        ROUND(SUM(f.attrition_flag) / COUNT(*) * 100, 1) AS turnover_rate_pct
    FROM fact_employee_metrics f
    JOIN dim_department d ON f.department_key = d.department_key
    GROUP BY d.department_name
    ORDER BY turnover_rate_pct DESC
""")

cursor.execute("""
    CREATE OR REPLACE VIEW vw_diversity_metrics AS
    SELECT
        d.department_name, e.gender, e.ethnicity, e.age_group,
        COUNT(*) AS headcount
    FROM fact_employee_metrics f
    JOIN dim_employee e ON f.employee_key = e.employee_key
    JOIN dim_department d ON f.department_key = d.department_key
    GROUP BY d.department_name, e.gender, e.ethnicity, e.age_group
""")
conn.commit()
print("  Views created!")

# Print summary
print("\n" + "="*50)
print("TURNOVER SUMMARY BY DEPARTMENT")
print("="*50)
cursor.execute("SELECT * FROM vw_turnover_summary")
print(f"{'Department':<15} {'Headcount':<10} {'Departures':<12} {'Turnover %':<10}")
print("-"*47)
for row in cursor.fetchall():
    print(f"{row[0]:<15} {row[1]:<10} {row[2]:<12} {row[3]:<10}")

print("\n" + "="*50)
print("TABLE ROW COUNTS")
print("="*50)
for table in ['dim_department', 'dim_job_role', 'dim_location', 'dim_employee', 'fact_employee_metrics']:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table:<30} {count} rows")

conn.close()
print("\nDone! Star schema fully loaded in MySQL.")
