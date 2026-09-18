import logging

from humanoid_bot.logging_setup import RedactionFilter


def make_record(msg: str) -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, __file__, 1, msg, (), None)


def test_redacts_api_key() -> None:
    f = RedactionFilter()
    rec = make_record("calling with api_key=sk-abcdefabcdefabcdef123456 done")
    assert f.filter(rec)
    assert "sk-abcdefabcdefabcdef123456" not in str(rec.msg)
    assert "[REDACTED]" in str(rec.msg)


def test_redacts_bearer() -> None:
    f = RedactionFilter()
    rec = make_record("Authorization: Bearer abc.def.ghi")
    f.filter(rec)
    assert "abc.def.ghi" not in str(rec.msg)


def test_normal_message_untouched() -> None:
    f = RedactionFilter()
    rec = make_record("opened notepad successfully")
    f.filter(rec)
    assert rec.msg == "opened notepad successfully"
