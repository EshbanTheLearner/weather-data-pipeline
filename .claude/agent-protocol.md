# Agent Communication Protocol

## Inter-Agent Communication

### 1. Output Format
All agents produce structured output in this format:

```json
{
  "agent": "agent_name",
  "status": "success|error|partial",
  "outputs": {
    "files_created": ["path/to/file1", "path/to/file2"],
    "summary": "Brief description of what was done",
    "next_agent": "agent_to_run_next (optional)",
    "metadata": {
      "duration": "5s",
      "confidence": "high|medium|low"
    }
  },
  "errors": [],
  "warnings": []
}
```

### 2. Dependency Chain

```
DB Agent Output → Spark Agent Input
  - Database schema files
  - Connection configuration
  - Table structures

Spark Agent Output → WebApp Agent Input
  - Processed data format
  - API data specifications
  - Aggregation schemas

All Outputs → Orchestrator
  - Progress tracking
  - Error handling
  - Final validation
```

### 3. Error Handling

**Agent Failure Protocol:**
1. Agent reports error with details
2. Orchestrator logs error
3. Orchestrator retries (max 2 attempts)
4. If still failing, orchestrator skips dependent agents
5. Orchestrator generates error report for user

### 4. Validation Checkpoints

**DB Agent Validation:**
- [ ] Schema files exist and are valid SQL
- [ ] Connection config is properly formatted
- [ ] Ingestion script runs without errors

**Spark Agent Validation:**
- [ ] PySpark scripts have valid syntax
- [ ] Spark config matches DB schema
- [ ] Test job runs successfully

**WebApp Agent Validation:**
- [ ] Flask app starts without errors
- [ ] React build completes successfully
- [ ] API endpoints are accessible