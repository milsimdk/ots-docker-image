#!/usr/bin/env python3
import requests, sys;

URL = "http://localhost:8081/api/health"

try:
    response = requests.head(URL)
except Exception as e:
    sys.exit(1)
else:
    if response.status_code == 200:
        sys.exit(0)
    else:
        sys.exit(1)
