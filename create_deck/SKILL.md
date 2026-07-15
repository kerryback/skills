---
name: create_deck
description: >
  Creates a PowerPoint deck (revenue_by_country.pptx) with a bar chart of revenue by
  country from Northwind Excel files in the current directory. Use this skill whenever
  the user asks to create the revenue deck, generate the PowerPoint, run the revenue
  chart script, or produce a bar chart of Northwind sales by country.
---

# create_deck

Produce `revenue_by_country.pptx` — a PowerPoint slide with a bar chart of revenue by
country — by running the bundled script against the Northwind Excel files in the current
working directory.

## Required files (must exist in the current directory)

- `northwind_orders.xlsx`
- `northwind_orderdetails.xlsx`
- `northwind_customers.xlsx`

## Steps

1. Check that the three Excel files above exist. If any are missing, tell the user which
   ones are needed and stop.

2. Check whether `python-pptx` is installed:
   ```
   python3 -c "import pptx"
   ```
   If it fails, install it:
   ```
   pip install python-pptx --break-system-packages -q
   ```

3. Copy the bundled script to the current directory (overwrite silently — the bundled
   version is authoritative):
   ```
   cp ~/.claude/skills/create_deck/scripts/revenue_by_country.py revenue_by_country.py
   ```

4. Run the script:
   ```
   python3 revenue_by_country.py
   ```

5. Confirm `revenue_by_country.pptx` was created and report success to the user.
