from solution import User, parse_users


def _invalid(row) -> bool:
    users, errors = parse_users([row])
    return users == [] and len(errors) == 1


def test_valid_row_becomes_user_with_default_tags():
    users, errors = parse_users([{"name": "Ada", "age": 36, "email": "ada@example.com"}])
    assert errors == [], f"expected no errors, got {errors!r}"
    assert len(users) == 1 and isinstance(users[0], User), f"expected one User, got {users!r}"
    assert users[0].tags == [], f"tags should default to [], got {users[0].tags!r}"


def test_converts_numeric_strings():
    users, errors = parse_users([{"name": "Bo", "age": "41", "email": "bo@x.io"}])
    assert errors == [] and users[0].age == 41, f"age '41' should become 41, got users={users!r} errors={errors!r}"


def test_rejects_out_of_range_age():
    assert _invalid({"name": "A", "age": -1, "email": "a@b.co"}), "age -1 should be rejected"
    assert _invalid({"name": "A", "age": 151, "email": "a@b.co"}), "age 151 should be rejected"


def test_rejects_empty_name_and_bad_email():
    assert _invalid({"name": "", "age": 30, "email": "a@b.co"}), "empty name should be rejected"
    assert _invalid({"name": "A", "age": 30, "email": "not-an-email"}), "'not-an-email' should be rejected"


def test_reports_one_based_row_numbers_and_keeps_going():
    rows = [
        {"name": "Ok", "age": 1, "email": "ok@x.io"},
        {"name": "Bad", "age": "old", "email": "bad@x.io"},
        {"name": "Also ok", "age": 2, "email": "also@x.io", "tags": ["vip"]},
        {"age": 5},
    ]
    users, errors = parse_users(rows)
    assert [u.name for u in users] == ["Ok", "Also ok"], f"expected the 2 valid users, got {users!r}"
    assert len(errors) == 2, f"expected 2 errors, got {errors!r}"
    assert errors[0].startswith("row 2:") and errors[1].startswith("row 4:"), \
        f"errors should start with 'row 2:' and 'row 4:', got {errors!r}"
