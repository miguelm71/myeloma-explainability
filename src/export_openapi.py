# src/export_openapi.py
import json
import yaml
import sys
sys.path.append('.')
from api import app

# Export OpenAPI spec
openapi_spec = app.openapi()

# Save as JSON
with open('docs/openapi.json', 'w') as f:
    json.dump(openapi_spec, f, indent=2)

# Save as YAML
with open('docs/openapi.yaml', 'w') as f:
    yaml.dump(openapi_spec, f, default_flow_style=False, allow_unicode=True)

print("OpenAPI spec exported to docs/openapi.json and docs/openapi.yaml")