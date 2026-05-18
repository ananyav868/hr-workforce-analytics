"""
Generate a realistic sample employee dataset for the HR Workforce Analytics pipeline.
Produces ~500 rows with correlated features for attrition modeling.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Reproducibility
np.random.seed(42)

NUM_EMPLOYEES = 500

# --- Name pools ---
first_names_male = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph",
    "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Steven",
    "Andrew", "Joshua", "Kevin", "Brian", "Ryan", "Nathan", "Eric", "Tyler",
    "Brandon", "Aaron", "Justin", "Samuel", "Benjamin", "Patrick", "Carlos",
    "Luis", "Jorge", "Miguel", "Raj", "Amit", "Wei", "Hiroshi", "Omar",
    "Hassan", "Derek", "Marcus", "Terrence", "Jamal", "Andre", "Darius",
]

first_names_female = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan",
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Emily", "Donna", "Michelle", "Dorothy", "Amanda", "Melissa",
    "Stephanie", "Rebecca", "Laura", "Maria", "Priya", "Aisha", "Yuki",
    "Mei", "Fatima", "Jasmine", "Keisha", "Latoya", "Monique", "Aaliyah",
    "Gabriela", "Sofia", "Valentina", "Carmen", "Rosa", "Angela", "Tanya",
]

first_names_nonbinary = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn",
    "Avery", "Skyler", "Dakota", "Reese", "Finley", "Rowan", "Sage",
    "Phoenix", "River", "Emery", "Hayden", "Kendall", "Blair",
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Patel", "Chen", "Kim", "Park", "Singh",
    "Tanaka", "Ahmed", "Ali", "Khan", "Okafor", "Mensah", "Diaz",
]

# --- Department and role mappings ---
department_roles = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "DevOps Engineer", "QA Engineer", "Engineering Manager"],
    "Sales": ["Sales Rep", "Senior Sales Rep", "Account Executive", "Sales Manager"],
    "Marketing": ["Marketing Analyst", "Content Strategist", "Marketing Manager", "SEO Specialist"],
    "HR": ["HR Specialist", "HR Manager", "Recruiter", "Compensation Analyst"],
    "Finance": ["Accountant", "Senior Accountant", "Financial Analyst", "Finance Manager"],
    "Operations": ["Operations Analyst", "Operations Manager", "Supply Chain Coordinator", "Logistics Specialist"],
    "Support": ["Support Agent", "Senior Support Agent", "Support Team Lead", "Technical Support Engineer"],
}

# Salary ranges by role seniority keywords
salary_ranges = {
    "Manager": (90000, 150000),
    "Senior": (75000, 120000),
    "Lead": (80000, 130000),
    "Executive": (85000, 140000),
    "Director": (100000, 150000),
    "default": (35000, 80000),
}

departments = list(department_roles.keys())
department_weights = [0.25, 0.18, 0.12, 0.08, 0.12, 0.13, 0.12]  # Engineering-heavy

locations = [
    "New York, NY, USA",
    "San Francisco, CA, USA",
    "Chicago, IL, USA",
    "Austin, TX, USA",
    "Seattle, WA, USA",
]

genders = ["Male", "Female", "Non-Binary"]
gender_weights = [0.48, 0.47, 0.05]

ethnicities = ["White", "Black", "Hispanic", "Asian", "Other"]
ethnicity_weights = [0.45, 0.18, 0.20, 0.12, 0.05]


def get_salary_range(role: str) -> tuple:
    """Determine salary range based on role title keywords."""
    for keyword, (low, high) in salary_ranges.items():
        if keyword in role:
            return (low, high)
    return salary_ranges["default"]


def generate_name(gender: str) -> str:
    """Generate a realistic name based on gender."""
    if gender == "Male":
        first = np.random.choice(first_names_male)
    elif gender == "Female":
        first = np.random.choice(first_names_female)
    else:
        first = np.random.choice(first_names_nonbinary)
    last = np.random.choice(last_names)
    return f"{first} {last}"


def generate_dataset(n: int = NUM_EMPLOYEES) -> pd.DataFrame:
    """Generate the full employee dataset."""
    records = []

    for emp_id in range(1, n + 1):
        # Demographics
        gender = np.random.choice(genders, p=gender_weights)
        ethnicity = np.random.choice(ethnicities, p=ethnicity_weights)
        name = generate_name(gender)
        age = np.random.randint(22, 63)

        # Department and role
        dept = np.random.choice(departments, p=department_weights)
        role = np.random.choice(department_roles[dept])

        # Hire date: between 2015-01-01 and 2024-06-01
        start_date = pd.Timestamp("2015-01-01")
        end_date = pd.Timestamp("2024-06-01")
        days_range = (end_date - start_date).days
        hire_date = start_date + pd.Timedelta(days=np.random.randint(0, days_range))

        # Salary correlated with role
        sal_low, sal_high = get_salary_range(role)
        # Add age/tenure bonus
        tenure_years = (pd.Timestamp("2024-06-01") - hire_date).days / 365.25
        base_salary = np.random.uniform(sal_low, sal_high)
        tenure_bonus = tenure_years * np.random.uniform(500, 2000)
        salary = int(min(base_salary + tenure_bonus, 150000))

        # Satisfaction score: 1.0 - 5.0
        satisfaction_score = round(np.random.uniform(1.0, 5.0), 1)

        # Overtime hours: 0-30, slightly skewed low
        overtime_hours = int(np.random.exponential(scale=8))
        overtime_hours = min(overtime_hours, 30)

        # Promotion date: ~40% have been promoted, must be after hire_date
        promotion_date = None
        if np.random.random() < 0.4:
            days_since_hire = (pd.Timestamp("2024-06-01") - hire_date).days
            if days_since_hire > 365:  # At least 1 year tenure for promotion
                promo_offset = np.random.randint(365, max(366, days_since_hire))
                promotion_date = hire_date + pd.Timedelta(days=promo_offset)

        # Location
        location = np.random.choice(locations)

        # Attrition: ~20% overall, correlated with low satisfaction and high overtime
        attrition_prob = 0.10  # base probability
        if satisfaction_score <= 2.0:
            attrition_prob += 0.25
        elif satisfaction_score <= 3.0:
            attrition_prob += 0.10
        if overtime_hours >= 20:
            attrition_prob += 0.15
        elif overtime_hours >= 15:
            attrition_prob += 0.08
        # Cap probability
        attrition_prob = min(attrition_prob, 0.70)
        attrition = 1 if np.random.random() < attrition_prob else 0

        records.append({
            "employee_id": emp_id,
            "name": name,
            "department": dept,
            "job_role": role,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "age": age,
            "gender": gender,
            "ethnicity": ethnicity,
            "salary": salary,
            "satisfaction_score": satisfaction_score,
            "overtime_hours": overtime_hours,
            "promotion_date": promotion_date.strftime("%Y-%m-%d") if promotion_date else None,
            "location": location,
            "attrition": attrition,
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    # Ensure output directory exists
    output_dir = Path(__file__).resolve().parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "employee_data.csv"

    df = generate_dataset()
    df.to_csv(output_path, index=False)

    # Print summary stats
    print(f"Generated {len(df)} employee records -> {output_path}")
    print(f"\nAttrition rate: {df['attrition'].mean():.1%}")
    print(f"\nDepartment distribution:")
    print(df["department"].value_counts().to_string())
    print(f"\nSalary stats:")
    print(df["salary"].describe().to_string())
    print(f"\nSatisfaction score stats:")
    print(df["satisfaction_score"].describe().to_string())
    print(f"\nPromotion rate: {df['promotion_date'].notna().mean():.1%}")
