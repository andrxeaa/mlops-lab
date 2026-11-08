from datetime import datetime
import pandas as pd

TARGET = "price"
NUMERIC_BOUNDS = {
    "price": (10_000, 10_000_000),
    "sqft": (300, 20_000),
    "bedrooms": (1, 10),
    "bathrooms": (0.5, 10),
    "year_built": (1800, datetime.now().year),
}
INTEGER_COLUMNS = ["bedrooms", "year_built"]
CATEGORIES = {
    "location": {"Rural", "Suburb", "Urban", "Downtown", "Waterfront", "Mountain"},
    "condition": {"Poor", "Fair", "Good", "Excellent"},
}
EXPECTED_COLUMNS = ["price", "sqft", "bedrooms", "bathrooms", "location", "year_built", "condition"]

def check_contract(df: pd.DataFrame, require_target: bool = True) -> list[dict]:
    expected = EXPECTED_COLUMNS if require_target else [c for c in EXPECTED_COLUMNS if c != TARGET]
    violations = []

    missing = [c for c in expected if c not in df.columns]
    if missing:
        return [{"check": "schema", "column": ", ".join(missing), "rows": len(df), "detail": "faltan columnas obligatorias"}]

    def add(check, column, mask, detail):
        n = int(mask.sum())
        if n:
            violations.append({"check": check, "column": column, "rows": n, "detail": detail})

    for col in expected:
        add("nulls", col, df[col].isnull(), "valores nulos")

    for col, (lo, hi) in NUMERIC_BOUNDS.items():
        if col not in expected:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        add("type", col, values.isnull() & df[col].notnull(), "no es numérico")
        add("range", col, (values < lo) | (values > hi), f"fuera de [{lo}, {hi}]")

    for col in INTEGER_COLUMNS:
        values = pd.to_numeric(df[col], errors="coerce")
        add("type", col, values.notnull() & (values % 1 != 0), "debería ser entero")

    for col, allowed in CATEGORIES.items():
        add("category", col, df[col].notnull() & ~df[col].isin(allowed), f"fuera de {sorted(allowed)}")

    add("duplicates", "*", df.duplicated(), "filas duplicadas")
    return violations