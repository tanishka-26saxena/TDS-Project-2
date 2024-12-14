#eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDMyMDhAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.J_AL0psyCUJA-oeR-6xN1BQGfKH8pF951OzO3tzPPKE

import os

token = os.environ.get("AIPROXY_TOKEN")
if not token:
    raise ValueError("AIPROXY_TOKEN is not set in the environment!")
