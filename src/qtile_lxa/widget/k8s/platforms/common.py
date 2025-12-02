def validate_size_mb(size: str):
    s = size.lower().strip()
    if s.endswith(("gb", "g")):
        size_mb = int(s[:-2]) * 1024
    elif s.endswith(("mb", "m")):
        size_mb = int(s[:-2])
    elif s.endswith(("tb", "t")):
        size_mb = int(s[:-2]) * 1024 * 1024
    else:
        raise ValueError(
            "Disk size must be like '10GB', '10G', '500MB','500M', '1TB', '1T'."
        )
    return size_mb
