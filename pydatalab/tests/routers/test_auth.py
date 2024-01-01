from pydatalab.routes.v0_1.auth import _check_email_domain


def test_allow_emails():
    # Test that a valid email is allowed
    assert _check_email_domain("test@example.org", ["example.org"])
    assert _check_email_domain("test@example.org", ["example.org", "example2.org"])
    assert _check_email_domain("test@subdomain.example.org", ["example.org", "example2.org"])
    assert _check_email_domain("test@subdomain.example.org", ["subdomain.example.org"])
    assert _check_email_domain("test@example2.org", [])
    assert not _check_email_domain("test@example2.org", None)
    assert not _check_email_domain("test@example.org", ["subdomain.example.org"])
    assert not _check_email_domain("test@example2.org", ["example.org"])
