from app.production_hardening import SlidingWindowRateLimiter,safe_rate_limit_key

def test_blocks_after_limit():
    r=SlidingWindowRateLimiter(2,60)
    assert r.allow("user:1"); assert r.allow("user:1"); assert not r.allow("user:1")

def test_keys_are_scoped():
    assert safe_rate_limit_key(7,"x")=="user:7"
    assert safe_rate_limit_key(None,"x")=="anon:x"

def test_users_have_separate_buckets():
    r=SlidingWindowRateLimiter(1,60)
    assert r.allow("user:1"); assert r.allow("user:2"); assert not r.allow("user:1")
