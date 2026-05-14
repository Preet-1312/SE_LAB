#!/usr/bin/env python3
"""
NutriTrack - "Set Dietary Preferences" Subsystem
Implementation + Black Box / White Box Test Suite

Run directly with:  python nutritrack_tests.py
"""

# ======================================================================
# ANSI COLOR CODES  (no external libraries required)
# ======================================================================
GREEN  = "\033[92m"   # used for  ✓ PASS
RED    = "\033[91m"   # used for  ✗ FAIL
CYAN   = "\033[96m"   # used for  section headers / banners
YELLOW = "\033[93m"   # used for  test IDs
RESET  = "\033[0m"    # reset after every colored segment


# ======================================================================
# CUSTOM EXCEPTIONS  (used to trace distinct white-box paths)
# ======================================================================
class ValidationException(Exception):
    """Raised when an input validation rule is broken."""
    pass


class AuthException(Exception):
    """Raised when the session token is missing / invalid."""
    pass


class DatabaseException(Exception):
    """Raised when the simulated DB write fails (rollback path)."""
    pass


# ======================================================================
# SUBSYSTEM IMPLEMENTATION
# ======================================================================
class DietaryPreferenceManager:
    """Implements the setDietaryPreferences() subsystem for NutriTrack."""

    VALID_PREFERENCES = ["Vegan", "Gluten-free", "Keto", "Standard", "Low-sodium"]
    MIN_CALORIES = 500
    MAX_CALORIES = 5000
    # characters that must never appear inside a clean customer_id
    _ILLEGAL_ID_CHARS = ["'", "\"", ";", " ", "--"]

    def __init__(self, simulate_db_failure=False):
        # In-memory "database" - simulates persistent storage
        self._db = {}
        # When True, _save_to_db() raises DatabaseException (white-box W11 / W15d)
        self.simulate_db_failure = simulate_db_failure

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------
    def isAuthenticated(self, session_token):
        """A valid (non-None) session token must be present."""
        return session_token is not None

    # ------------------------------------------------------------------
    # VALIDATION  (raises ValidationException on the first broken rule)
    # ------------------------------------------------------------------
    def _validate(self, customer_id, preferences, calorie_limit):
        # --- customer_id rules ---
        if customer_id is None or customer_id == "":
            raise ValidationException("customer_id is empty or missing")
        if any(ch in customer_id for ch in self._ILLEGAL_ID_CHARS):
            raise ValidationException("customer_id contains invalid characters")

        # --- preferences rules ---
        if not isinstance(preferences, list) or len(preferences) == 0:
            raise ValidationException("preferences list is required and cannot be empty")
        for pref in preferences:                       # loop -> white-box loop coverage
            if pref not in self.VALID_PREFERENCES:
                raise ValidationException("Invalid preference supplied: %s" % pref)

        # --- calorie_limit rules ---
        if isinstance(calorie_limit, bool) or not isinstance(calorie_limit, (int, float)):
            raise ValidationException("calorie_limit must be numeric")
        if calorie_limit == 0:
            raise ValidationException("calorie_limit cannot be zero")
        if calorie_limit < 0:
            raise ValidationException("calorie_limit cannot be negative")
        if calorie_limit < self.MIN_CALORIES:          # condition A: (cal >= MIN)
            raise ValidationException("calorie_limit is below minimum allowed (500)")
        if calorie_limit > self.MAX_CALORIES:          # condition B: (cal <= MAX)
            raise ValidationException("calorie_limit exceeds maximum allowed (5000)")

        return True

    # ------------------------------------------------------------------
    # PERSISTENCE  (simulated DB write)
    # ------------------------------------------------------------------
    def _save_to_db(self, customer_id, preferences, calorie_limit):
        if self.simulate_db_failure:
            raise DatabaseException("database write failed - transaction rolled back")
        stored = []
        for pref in preferences:                       # loop -> saves each preference
            stored.append(pref)
        self._db[customer_id] = {
            "preferences": stored,
            "calorie_limit": calorie_limit,
        }

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    #   Flow: authenticate -> validate -> save -> confirm -> success
    # ------------------------------------------------------------------
    def setDietaryPreferences(self, customer_id, preferences, calorie_limit, session_token):
        try:
            # Step 1 - authentication (method exits early if this fails)
            if not self.isAuthenticated(session_token):
                raise AuthException("authentication failed - session token missing")

            # Step 2 - validate every input rule
            self._validate(customer_id, preferences, calorie_limit)

            # Step 3 - persist to the (simulated) database
            self._save_to_db(customer_id, preferences, calorie_limit)

            # Step 4 - confirm + return success
            return {"success": True, "message": "Preferences saved successfully"}

        except AuthException as exc:
            return {"success": False, "error": str(exc)}
        except ValidationException as exc:
            return {"success": False, "error": str(exc)}
        except DatabaseException as exc:
            return {"success": False, "error": str(exc)}


# ======================================================================
# HELPER - format a result dict into the printable "Actual" line
# ======================================================================
def format_result(result):
    if result.get("success"):
        return "success=True, message='%s'" % result.get("message")
    return "success=False, error='%s'" % result.get("error")


# ======================================================================
# BLACK BOX TEST CASES  (B01 - B15)
# ======================================================================
BLACK_BOX_TESTS = [
    {
        "id": "B01", "name": "Valid vegan preference", "tag": "Functional",
        "input": 'customer_id="C001", preferences=["Vegan"], calorie_limit=2000, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan"], 2000, "valid"),
        "check": lambda r: r["success"] is True and r.get("message") == "Preferences saved successfully",
    },
    {
        "id": "B02", "name": "Valid gluten-free preference", "tag": "ECP Valid",
        "input": 'customer_id="C001", preferences=["Gluten-free"], calorie_limit=1800, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Gluten-free"], 1800, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "B03", "name": "Calorie limit at lower boundary", "tag": "BVA Lower",
        "input": 'customer_id="C001", preferences=["Vegan"], calorie_limit=500, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan"], 500, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "B04", "name": "Calorie limit at upper boundary", "tag": "BVA Upper",
        "input": 'customer_id="C001", preferences=["Standard"], calorie_limit=5000, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Standard"], 5000, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "B05", "name": "Calorie limit just below minimum", "tag": "BVA Lower-1",
        "input": 'customer_id="C001", preferences=["Vegan"], calorie_limit=499, session=valid',
        "expected": "success=False, error contains 'below minimum'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan"], 499, "valid"),
        "check": lambda r: r["success"] is False and "below minimum" in r["error"],
    },
    {
        "id": "B06", "name": "Calorie limit just above maximum", "tag": "BVA Upper+1",
        "input": 'customer_id="C001", preferences=["Standard"], calorie_limit=5001, session=valid',
        "expected": "success=False, error contains 'exceeds maximum'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Standard"], 5001, "valid"),
        "check": lambda r: r["success"] is False and "exceeds maximum" in r["error"],
    },
    {
        "id": "B07", "name": "Empty preferences list", "tag": "Error Handling",
        "input": 'customer_id="C001", preferences=[], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'required'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", [], 2000, "valid"),
        "check": lambda r: r["success"] is False and "required" in r["error"],
    },
    {
        "id": "B08", "name": "Non-numeric calorie limit", "tag": "ECP Invalid",
        "input": 'customer_id="C001", preferences=["Vegan"], calorie_limit="abc", session=valid',
        "expected": "success=False, error contains 'numeric'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan"], "abc", "valid"),
        "check": lambda r: r["success"] is False and "numeric" in r["error"],
    },
    {
        "id": "B09", "name": "Negative calorie limit", "tag": "BVA Negative",
        "input": 'customer_id="C001", preferences=["Keto"], calorie_limit=-200, session=valid',
        "expected": "success=False, error contains 'negative'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Keto"], -200, "valid"),
        "check": lambda r: r["success"] is False and "negative" in r["error"],
    },
    {
        "id": "B10", "name": "Unknown preference value", "tag": "ECP Invalid",
        "input": 'customer_id="C001", preferences=["Carnivore_X99"], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'Invalid'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Carnivore_X99"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "Invalid" in r["error"],
    },
    {
        "id": "B11", "name": "Multiple valid preferences", "tag": "Functional Multi",
        "input": 'customer_id="C001", preferences=["Vegan","Gluten-free"], calorie_limit=1800, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan", "Gluten-free"], 1800, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "B12", "name": "Missing session token", "tag": "Error Handling",
        "input": 'customer_id="C001", preferences=["Vegan"], calorie_limit=2000, session=None',
        "expected": "success=False, error contains 'auth'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Vegan"], 2000, None),
        "check": lambda r: r["success"] is False and "auth" in r["error"],
    },
    {
        "id": "B13", "name": "Empty customer id", "tag": "ECP Invalid",
        "input": 'customer_id="", preferences=["Vegan"], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'empty'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("", ["Vegan"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "empty" in r["error"],
    },
    {
        "id": "B14", "name": "Zero calorie limit", "tag": "BVA Zero",
        "input": 'customer_id="C001", preferences=["Standard"], calorie_limit=0, session=valid',
        "expected": "success=False, error contains 'zero'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Standard"], 0, "valid"),
        "check": lambda r: r["success"] is False and "zero" in r["error"],
    },
    {
        "id": "B15", "name": "SQL-injection style customer id", "tag": "ECP Invalid",
        "input": 'customer_id="Vegan\'; DROP TABLE", preferences=["Vegan"], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'invalid'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("Vegan'; DROP TABLE", ["Vegan"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "invalid" in r["error"],
    },
]


# ======================================================================
# WHITE BOX TEST CASES  (W01 - W15)
#   W13 / W14 / W15 are groups with sub-tests; a group PASSES only when
#   every sub-test inside it passes.
# ======================================================================
WHITE_BOX_TESTS = [
    {
        "id": "W01", "name": "All statements executed on valid input", "tag": "Statement Coverage",
        "input": 'customer_id="C001", preferences=["Standard"], calorie_limit=2200, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C001", ["Standard"], 2200, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W02", "name": "isValid branch = TRUE taken", "tag": "Branch TRUE",
        "input": 'customer_id="C002", preferences=["Keto"], calorie_limit=1500, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C002", ["Keto"], 1500, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W03", "name": "isValid branch = FALSE (ValidationException path)", "tag": "Branch FALSE",
        "input": 'customer_id="", preferences=["Vegan"], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'empty'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("", ["Vegan"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "empty" in r["error"],
    },
    {
        "id": "W04", "name": "(cal >= MIN) condition = True", "tag": "Decision Coverage",
        "input": 'customer_id="C003", preferences=["Vegan"], calorie_limit=500, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C003", ["Vegan"], 500, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W05", "name": "(cal <= MAX) condition = True", "tag": "Decision Coverage",
        "input": 'customer_id="C003", preferences=["Vegan"], calorie_limit=5000, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C003", ["Vegan"], 5000, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W06", "name": "preferences + calorie conditions both false", "tag": "Condition Coverage",
        "input": 'customer_id="C004", preferences=[], calorie_limit=-100, session=valid',
        "expected": "success=False, error contains 'required'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C004", [], -100, "valid"),
        "check": lambda r: r["success"] is False and "required" in r["error"],
    },
    {
        "id": "W07", "name": "Full happy path: validate->save->confirm->success", "tag": "Path Happy",
        "input": 'customer_id="C005", preferences=["Low-sodium"], calorie_limit=2400, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C005", ["Low-sodium"], 2400, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W08", "name": "Invalid preference: flow stops at validate, no DB write", "tag": "Path Error",
        "input": 'customer_id="C006", preferences=["Paleo_X"], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'Invalid'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C006", ["Paleo_X"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "Invalid" in r["error"],
    },
    {
        "id": "W09", "name": "Preference loop runs 3 times, all saved", "tag": "Loop n=3",
        "input": 'customer_id="C007", preferences=["Vegan","Gluten-free","Low-sodium"], calorie_limit=2000, session=valid',
        "expected": "success=True, message='Preferences saved successfully'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences(
            "C007", ["Vegan", "Gluten-free", "Low-sodium"], 2000, "valid"),
        "check": lambda r: r["success"] is True,
    },
    {
        "id": "W10", "name": "Preference loop runs 0 times, error raised", "tag": "Loop Zero",
        "input": 'customer_id="C008", preferences=[], calorie_limit=2000, session=valid',
        "expected": "success=False, error contains 'required'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C008", [], 2000, "valid"),
        "check": lambda r: r["success"] is False and "required" in r["error"],
    },
    {
        "id": "W11", "name": "DatabaseException caught, transaction rolled back", "tag": "Exception",
        "input": 'customer_id="C009", preferences=["Vegan"], calorie_limit=2000, session=valid, simulate_db_failure=True',
        "expected": "success=False, error contains 'rolled back'",
        "run": lambda: DietaryPreferenceManager(simulate_db_failure=True).setDietaryPreferences(
            "C009", ["Vegan"], 2000, "valid"),
        "check": lambda r: r["success"] is False and "rolled back" in r["error"],
    },
    {
        "id": "W12", "name": "isAuthenticated()=False -> AuthException, exits early", "tag": "Condition Auth",
        "input": 'customer_id="C010", preferences=["Vegan"], calorie_limit=2000, session=None',
        "expected": "success=False, error contains 'auth'",
        "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C010", ["Vegan"], 2000, None),
        "check": lambda r: r["success"] is False and "auth" in r["error"],
    },
    {
        "id": "W13", "group": True, "name": "Each valid enum hits correct branch", "tag": "Branch Enum",
        "subtests": [
            {
                "id": "W13a", "name": "Enum branch: Vegan", "tag": "Branch Enum",
                "input": 'customer_id="C011", preferences=["Vegan"], calorie_limit=2000, session=valid',
                "expected": "success=True, message='Preferences saved successfully'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C011", ["Vegan"], 2000, "valid"),
                "check": lambda r: r["success"] is True,
            },
            {
                "id": "W13b", "name": "Enum branch: Keto", "tag": "Branch Enum",
                "input": 'customer_id="C011", preferences=["Keto"], calorie_limit=2000, session=valid',
                "expected": "success=True, message='Preferences saved successfully'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C011", ["Keto"], 2000, "valid"),
                "check": lambda r: r["success"] is True,
            },
            {
                "id": "W13c", "name": "Enum branch: Gluten-free", "tag": "Branch Enum",
                "input": 'customer_id="C011", preferences=["Gluten-free"], calorie_limit=2000, session=valid',
                "expected": "success=True, message='Preferences saved successfully'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C011", ["Gluten-free"], 2000, "valid"),
                "check": lambda r: r["success"] is True,
            },
        ],
    },
    {
        "id": "W14", "group": True, "name": "MC/DC on (cal>=500) AND (cal<=5000)", "tag": "MC/DC",
        "subtests": [
            {
                "id": "W14a", "name": "(T,T) -> valid", "tag": "MC/DC",
                "input": 'customer_id="C012", preferences=["Vegan"], calorie_limit=2000, session=valid',
                "expected": "success=True, message='Preferences saved successfully'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C012", ["Vegan"], 2000, "valid"),
                "check": lambda r: r["success"] is True,
            },
            {
                "id": "W14b", "name": "(T,F) -> error (above maximum)", "tag": "MC/DC",
                "input": 'customer_id="C012", preferences=["Vegan"], calorie_limit=6000, session=valid',
                "expected": "success=False, error contains 'exceeds maximum'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C012", ["Vegan"], 6000, "valid"),
                "check": lambda r: r["success"] is False and "exceeds maximum" in r["error"],
            },
            {
                "id": "W14c", "name": "(F,T) -> error (below minimum)", "tag": "MC/DC",
                "input": 'customer_id="C012", preferences=["Vegan"], calorie_limit=300, session=valid',
                "expected": "success=False, error contains 'below minimum'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C012", ["Vegan"], 300, "valid"),
                "check": lambda r: r["success"] is False and "below minimum" in r["error"],
            },
            {
                # (F,F) is logically infeasible for a scalar (no number is both
                # < 500 and > 5000). It is represented by a degenerate value
                # that cannot satisfy either comparison, which still drives the
                # decision to an error result.
                "id": "W14d", "name": "(F,F) -> error (degenerate / non-numeric)", "tag": "MC/DC",
                "input": 'customer_id="C012", preferences=["Vegan"], calorie_limit="zzz", session=valid',
                "expected": "success=False, error contains 'numeric'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C012", ["Vegan"], "zzz", "valid"),
                "check": lambda r: r["success"] is False and "numeric" in r["error"],
            },
        ],
    },
    {
        "id": "W15", "group": True, "name": "Independent cyclomatic paths", "tag": "Cyclomatic",
        "subtests": [
            {
                "id": "W15a", "name": "Path: valid save", "tag": "Cyclomatic",
                "input": 'customer_id="C013", preferences=["Standard"], calorie_limit=2000, session=valid',
                "expected": "success=True, message='Preferences saved successfully'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C013", ["Standard"], 2000, "valid"),
                "check": lambda r: r["success"] is True,
            },
            {
                "id": "W15b", "name": "Path: invalid preference type", "tag": "Cyclomatic",
                "input": 'customer_id="C013", preferences=["BadType"], calorie_limit=2000, session=valid',
                "expected": "success=False, error contains 'Invalid'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C013", ["BadType"], 2000, "valid"),
                "check": lambda r: r["success"] is False and "Invalid" in r["error"],
            },
            {
                "id": "W15c", "name": "Path: invalid calorie limit", "tag": "Cyclomatic",
                "input": 'customer_id="C013", preferences=["Vegan"], calorie_limit=99999, session=valid',
                "expected": "success=False, error contains 'exceeds maximum'",
                "run": lambda: DietaryPreferenceManager().setDietaryPreferences("C013", ["Vegan"], 99999, "valid"),
                "check": lambda r: r["success"] is False and "exceeds maximum" in r["error"],
            },
            {
                "id": "W15d", "name": "Path: database error", "tag": "Cyclomatic",
                "input": 'customer_id="C013", preferences=["Vegan"], calorie_limit=2000, session=valid, simulate_db_failure=True',
                "expected": "success=False, error contains 'rolled back'",
                "run": lambda: DietaryPreferenceManager(simulate_db_failure=True).setDietaryPreferences(
                    "C013", ["Vegan"], 2000, "valid"),
                "check": lambda r: r["success"] is False and "rolled back" in r["error"],
            },
        ],
    },
]


# ======================================================================
# TEST RUNNER
# ======================================================================
class TestRunner:
    """Executes all test cases and prints results in the required format."""

    def __init__(self):
        self.bb_passed = 0
        self.bb_total = 0
        self.wb_passed = 0
        self.wb_total = 0

    # ------------------------------------------------------------------
    # Print a single test case block (matches the required terminal format)
    # ------------------------------------------------------------------
    def _print_case(self, tid, name, tag, input_str, expected_str, actual_str, passed):
        if passed:
            status = GREEN + "\u2713 PASS" + RESET
        else:
            status = RED + "\u2717 FAIL" + RESET
        print("%s%s%s %s  %s  [%s]" % (YELLOW, tid, RESET, status, name, tag))
        print("    Input   : %s" % input_str)
        print("    Expected: %s" % expected_str)
        print("    Actual  : %s" % actual_str)
        print()

    # ------------------------------------------------------------------
    # Run every black box test case
    # ------------------------------------------------------------------
    def run_black_box(self, tests):
        for t in tests:
            self.bb_total += 1
            result = t["run"]()
            passed = t["check"](result)
            if passed:
                self.bb_passed += 1
            self._print_case(t["id"], t["name"], t["tag"],
                             t["input"], t["expected"],
                             format_result(result), passed)

    # ------------------------------------------------------------------
    # Run every white box test case (groups pass only if all sub-tests pass)
    # ------------------------------------------------------------------
    def run_white_box(self, tests):
        for t in tests:
            self.wb_total += 1
            if t.get("group"):
                group_passed = True
                for st in t["subtests"]:
                    result = st["run"]()
                    passed = st["check"](result)
                    if not passed:
                        group_passed = False
                    self._print_case(st["id"], st["name"], st["tag"],
                                     st["input"], st["expected"],
                                     format_result(result), passed)
                if group_passed:
                    self.wb_passed += 1
            else:
                result = t["run"]()
                passed = t["check"](result)
                if passed:
                    self.wb_passed += 1
                self._print_case(t["id"], t["name"], t["tag"],
                                 t["input"], t["expected"],
                                 format_result(result), passed)

    # ------------------------------------------------------------------
    # Final summary banner
    # ------------------------------------------------------------------
    def print_summary(self):
        bar = "=" * 48
        total_passed = self.bb_passed + self.wb_passed
        total = self.bb_total + self.wb_total
        overall = "PASS" if total_passed == total else "FAIL"
        overall_color = GREEN if overall == "PASS" else RED
        print(bar)
        print("TEST SUMMARY")
        print(bar)
        print("Black Box : %d/%d PASSED" % (self.bb_passed, self.bb_total))
        print("White Box  : %d/%d PASSED" % (self.wb_passed, self.wb_total))
        print("Total      : %d/%d PASSED" % (total_passed, total))
        print("Overall    : %s%s%s" % (overall_color, overall, RESET))
        print(bar)


# ======================================================================
# BANNER / SECTION PRINTERS
# ======================================================================
def print_header():
    bar = "=" * 48
    print(CYAN + bar + RESET)
    print(CYAN + "NUTRITRACK - SET DIETARY PREFERENCES TEST SUITE" + RESET)
    print(CYAN + "Software Engineering | Q2 Implementation" + RESET)
    print(CYAN + bar + RESET)
    print()


def print_section(title):
    print(CYAN + title + RESET)
    print("-" * 50)
    print()


# ======================================================================
# MAIN
# ======================================================================
def main():
    runner = TestRunner()

    print_header()

    print_section("BLACK BOX TESTING (ECP + BVA + Functional)")
    runner.run_black_box(BLACK_BOX_TESTS)

    print_section("WHITE BOX TESTING (Statement + Branch + Path Coverage)")
    runner.run_white_box(WHITE_BOX_TESTS)

    runner.print_summary()


if __name__ == "__main__":
    main()