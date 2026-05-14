# NutriTrack — Set Dietary Preferences Test Suite

Implementation and a full Black Box / White Box test suite for the
`setDietaryPreferences()` subsystem of the **NutriTrack** nutrition tracking
platform. Written as a single, dependency-free Python file for a Software
Engineering lab deliverable.

## Overview

NutriTrack is a nutrition tracking platform with three actors — Customer,
Restaurant Admin, and Health Organization. This project covers one subsystem:
**Set Dietary Preferences**, which lets a customer save dietary tags and a daily
calorie limit against their account.

The deliverable contains two parts in one file:

1. **`DietaryPreferenceManager`** — the subsystem implementation, including
   authentication, input validation, and a simulated (in-memory) database save.
2. **`TestRunner`** — executes 15 Black Box and 15 White Box test cases and
   prints color-coded results plus a final summary.

## Requirements

- Python 3.x
- No external libraries (colors use raw ANSI escape codes)
- A terminal that supports ANSI colors (most modern terminals do)

## How to Run

```bash
python nutritrack_tests.py
```

The script prints a header banner, the Black Box section, the White Box
section, and a summary — then exits.

## The Subsystem

`setDietaryPreferences(customer_id, preferences, calorie_limit, session_token)`

Flow: **authenticate → validate → save → confirm → success**

- On success it returns `{"success": True, "message": "Preferences saved successfully"}`
- On failure it returns `{"success": False, "error": "<specific message>"}`

### Validation Rules

| Field | Rule |
|-------|------|
| `customer_id` | Must not be `None` or empty; must not contain illegal characters (quotes, semicolons, spaces) |
| `preferences` | Must be a non-empty list |
| each preference | Must be one of: `Vegan`, `Gluten-free`, `Keto`, `Standard`, `Low-sodium` |
| `calorie_limit` | Must be numeric, not zero, not negative, and within `[500, 5000]` inclusive |
| `session_token` | Must not be `None` (authentication check) |

### Exceptions

Three custom exceptions are used internally to keep the white-box paths
distinct. They are caught inside `setDietaryPreferences()` and converted into
the failure dict.

- `ValidationException` — a validation rule was broken
- `AuthException` — the session token was missing
- `DatabaseException` — the simulated DB write failed (rollback path)

The constructor accepts `simulate_db_failure=True` to deliberately trigger the
`DatabaseException` path (used by tests W11 and W15d).

## Test Coverage

### Black Box (B01–B15)

Equivalence Class Partitioning, Boundary Value Analysis, and functional checks
— covering valid inputs, boundary calorie values (499 / 500 / 5000 / 5001),
zero and negative calories, non-numeric input, empty and invalid preferences,
missing session token, empty customer ID, and an injection-style customer ID.

### White Box (W01–W15)

Statement, branch, decision, condition, path, loop, MC/DC, and cyclomatic
coverage of the implementation. Three of the entries are groups with sub-tests:

- **W13a–c** — each valid enum value hits its correct branch
- **W14a–d** — MC/DC on `(cal >= 500)` AND `(cal <= 5000)`
- **W15a–d** — the four independent cyclomatic paths

A group passes only if every sub-test inside it passes.

> Note: the MC/DC `(F,F)` case (W14d) is logically infeasible for a single
> scalar — no number is both below 500 and above 5000 — so it is represented by
> a degenerate non-numeric value that still drives the decision to an error.

## Output Format

Each test prints an ID, a colored PASS/FAIL status, a short name, a category
tag, and indented Input / Expected / Actual lines:

```
B01 ✓ PASS  Valid vegan preference  [Functional]
    Input   : customer_id="C001", preferences=["Vegan"], calorie_limit=2000, session=valid
    Expected: success=True, message='Preferences saved successfully'
    Actual  : success=True, message='Preferences saved successfully'
```

Colors: green for PASS, red for FAIL, cyan for section headers, yellow for test
IDs.

### Summary

The run ends with a summary banner:

```
================================================
TEST SUMMARY
================================================
Black Box : 15/15 PASSED
White Box  : 15/15 PASSED
Total      : 30/30 PASSED
Overall    : PASS
================================================
```

`Overall` reads `PASS` only when all 30 tests pass, otherwise `FAIL`.

## File Structure

```
nutritrack_tests.py
├── ANSI color constants
├── Custom exceptions (Validation / Auth / Database)
├── DietaryPreferenceManager      # the subsystem under test
├── format_result()               # formats a result dict for display
├── BLACK_BOX_TESTS               # B01–B15 definitions
├── WHITE_BOX_TESTS               # W01–W15 definitions (incl. groups)
├── TestRunner                    # runs cases, prints results, prints summary
├── print_header() / print_section()
└── main()
```

## Course Info

Software Engineering | Q2 Implementation
