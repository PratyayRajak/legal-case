"""Declarative Logic Evaluator for Language-Neutral Legal Rules.

Evaluates structured logic blocks without running code or models on raw text.
All inputs are canonical fields (enums, ISO dates, normalized concepts).

Supports:
- Atomic operators: equals, not_equals, in, not_in, exists, is_null
- Comparison operators: greater_than, less_than, between (dates & numbers)
- List quantifiers: any_match, all_match
- Boolean combinators: and, or, not
- Implication: if: <cond>, require: <cond>
"""
from __future__ import annotations

from typing import Any


def _get_field_value(fields: dict[str, Any], field_path: str) -> Any:
    """Retrieve field value from canonical fields dict.

    Handles both wrapped ExtractedField dicts ({"value": ...}) and bare values.
    """
    parts = field_path.split(".")
    curr: Any = fields

    for p in parts:
        if curr is None:
            return None
        if isinstance(curr, dict):
            curr = curr.get(p)
            # Unwrap ExtractedField if present
            if isinstance(curr, dict) and "value" in curr and len(curr) <= 7:
                # If further path parts exist, dig into value
                pass
        else:
            return None

    if isinstance(curr, dict) and "value" in curr and "found" in curr:
        if not curr.get("found", True):
            return None
        return curr.get("value")

    return curr


def evaluate_condition(cond: dict[str, Any], fields: dict[str, Any]) -> bool:
    """Evaluate a single logic condition against canonical fields."""
    if not cond:
        return True

    # 1. Combinators: and, or, not
    if "and" in cond:
        sub_conds = cond["and"]
        return all(evaluate_condition(sc, fields) for sc in sub_conds)

    if "or" in cond:
        sub_conds = cond["or"]
        return any(evaluate_condition(sc, fields) for sc in sub_conds)

    if "not" in cond:
        return not evaluate_condition(cond["not"], fields)

    # 2. Implication: if -> require
    if "if" in cond:
        if_matched = evaluate_condition(cond["if"], fields)
        if not if_matched:
            return True  # Condition didn't trigger -> requirement not enforced
        req_cond = cond.get("require", {})
        return evaluate_condition(req_cond, fields)

    # 3. Field-level operators
    field_name = cond.get("field")
    if not field_name:
        return True

    val = _get_field_value(fields, field_name)

    if "exists" in cond:
        should_exist = bool(cond["exists"])
        return (val is not None) if should_exist else (val is None)

    if "is_null" in cond:
        should_be_null = bool(cond["is_null"])
        return (val is None) if should_be_null else (val is not None)

    if "equals" in cond:
        expected = cond["equals"]
        # Handle enum/str conversion
        return str(val).lower() == str(expected).lower() if val is not None else False

    if "not_equals" in cond:
        expected = cond["not_equals"]
        return str(val).lower() != str(expected).lower() if val is not None else True

    if "in" in cond:
        allowed = [str(x).lower() for x in cond["in"]]
        return str(val).lower() in allowed if val is not None else False

    if "not_in" in cond:
        forbidden = [str(x).lower() for x in cond["not_in"]]
        return str(val).lower() not in forbidden if val is not None else True

    if "greater_than" in cond:
        target = cond["greater_than"]
        return val > target if val is not None else False

    if "less_than" in cond:
        target = cond["less_than"]
        return val < target if val is not None else False

    if "between" in cond:
        low, high = cond["between"]
        return (low <= val <= high) if val is not None else False

    # 4. List matching operators
    if "any_match" in cond:
        sub_rule = cond["any_match"]
        if not isinstance(val, list):
            return False
        return any(evaluate_condition(sub_rule, item if isinstance(item, dict) else {"item": item}) for item in val)

    if "all_match" in cond:
        sub_rule = cond["all_match"]
        if not isinstance(val, list):
            return False
        return all(evaluate_condition(sub_rule, item if isinstance(item, dict) else {"item": item}) for item in val)

    return True
