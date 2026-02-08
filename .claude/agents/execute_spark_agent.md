---
name: execute_spark_agent
description: execute spark agent sub-agent
tools: Read,Write,Bash
model: opus
---
Execute the Spark Agent workflow.

Your task:
1. Run: claude run-command spark-agent-workflow
2. Pass DB schema information from previous DB agent
3. Monitor execution
4. Capture outputs

Provide context:
- Database schema from: src/database/schema.sql
- Connection config from: config/database.py

Output status JSON:
{
  "status": "success" | "error",
  "files_created": ["src/spark/process_weather.py", ...],
  "errors": [],
  "execution_time": "...",
  "next_agent": "validate_spark_output"
}