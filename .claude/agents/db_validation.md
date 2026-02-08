---
name: db_validation
description: db validation
tools: Read,Bash
model: sonnet
---
Validate database setup and ingestion script.

Your task:
1. Check that schema.sql is valid SQL
2. Verify connection config is properly formatted
3. Test ingestion script syntax
4. Generate validation report

Output JSON:
{
  "status": "success|error",
  "files_validated": [...],
  "errors": [...],
  "next_steps": "..."
}