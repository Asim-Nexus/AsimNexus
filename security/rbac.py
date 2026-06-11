from core.security.rbac import RBACManager, get_rbac_manager, RateLimiter, get_rate_limiter

def get_rbac():
    return get_rbac_manager()
