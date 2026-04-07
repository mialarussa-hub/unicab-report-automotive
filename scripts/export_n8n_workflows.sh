#!/bin/bash
# Export n8n workflows to JSON files for version control
# Usage: bash scripts/export_n8n_workflows.sh

set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_USER="${N8N_BASIC_AUTH_USER:-admin}"
N8N_PASS="${N8N_BASIC_AUTH_PASSWORD:-changeme}"
OUTPUT_DIR="n8n/workflows"

echo "Exporting n8n workflows from ${N8N_URL}..."

# Get all workflows
workflows=$(curl -s -u "${N8N_USER}:${N8N_PASS}" "${N8N_URL}/api/v1/workflows" | python -c "
import sys, json
data = json.load(sys.stdin)
for wf in data.get('data', []):
    print(f\"{wf['id']}|{wf['name']}\")
")

while IFS='|' read -r id name; do
    # Sanitize filename
    filename=$(echo "$name" | tr ' ' '_' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]//g')
    echo "  Exporting: ${name} -> ${OUTPUT_DIR}/${filename}.json"
    curl -s -u "${N8N_USER}:${N8N_PASS}" "${N8N_URL}/api/v1/workflows/${id}" | python -m json.tool > "${OUTPUT_DIR}/${filename}.json"
done <<< "$workflows"

echo "Done. Workflows exported to ${OUTPUT_DIR}/"
