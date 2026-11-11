from solution import ConfigError, load_settings

GOOD = {"ANTHROPIC_API_KEY": "sk-ant-secret-123", "DATABASE_URL": "postgresql://db/app"}


def test_reads_values_from_env():
    s = load_settings({**GOOD, "MODEL": "claude-opus-5-5", "MAX_TOKENS": "2048", "ENVIRONMENT": "prod"})
    assert s.model == "claude-opus-5-5", f"expected model from MODEL, got {s.model!r}"
    assert s.max_tokens == 2048, f"MAX_TOKENS='2048' should become the int 2048, got {s.max_tokens!r}"
    assert s.environment == "prod", f"expected 'prod', got {s.environment!r}"
    assert s.database_url == "postgresql://db/app", f"got {s.database_url!r}"
    assert s.anthropic_api_key.get_secret_value() == "sk-ant-secret-123", "the key should be stored as a SecretStr"


def test_defaults_apply_when_optional_vars_are_missing():
    s = load_settings(GOOD)
    got = (s.model, s.max_tokens, s.environment)
    want = ("claude-haiku-5-5", 1024, "dev")
    assert got == want, f"expected defaults {want!r}, got {got!r}"


def test_missing_required_vars_raise_config_error_naming_them():
    try:
        load_settings({"MODEL": "claude-opus-5-5"})
    except ConfigError as e:
        msg = str(e)
        assert "ANTHROPIC_API_KEY" in msg and "DATABASE_URL" in msg, f"message should name both missing vars, got {msg!r}"
        return
    except Exception as e:
        raise AssertionError(f"expected ConfigError, got {type(e).__name__}: {e}")
    raise AssertionError("missing required vars should raise ConfigError")


def test_bad_values_fail_fast():
    for extra, var in [({"MAX_TOKENS": "lots"}, "MAX_TOKENS"), ({"MAX_TOKENS": "0"}, "MAX_TOKENS"),
                       ({"ENVIRONMENT": "staging"}, "ENVIRONMENT"), ({"ANTHROPIC_API_KEY": ""}, "ANTHROPIC_API_KEY")]:
        try:
            load_settings({**GOOD, **extra})
        except ConfigError as e:
            assert var in str(e), f"error for {extra!r} should name {var}, got {str(e)!r}"
            continue
        except Exception as e:
            raise AssertionError(f"{extra!r}: expected ConfigError, got {type(e).__name__}")
        raise AssertionError(f"{extra!r} should be rejected")


def test_api_key_is_hidden_when_printed():
    s = load_settings(GOOD)
    for shown in (repr(s), str(s)):
        assert "sk-ant-secret-123" not in shown, f"the API key leaked into: {shown}"


def test_unrelated_env_vars_are_ignored():
    s = load_settings({**GOOD, "PATH": "/usr/bin", "HOME": "/root"})
    assert s.model == "claude-haiku-5-5", "unrelated variables like PATH should be ignored"
