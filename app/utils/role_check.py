def is_admin_or_superuser(user):
    return str(getattr(user, "role", "")).lower() in ["admin", "superuser"]
