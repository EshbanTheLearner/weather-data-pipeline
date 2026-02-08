---
description: master-orchestrator
---
```mermaid
flowchart TD
    start_node_default([Start])
    end_node_default([End])
    agent_1770200345506[requirements_analyzer]
    question_1770200452878{AskUserQuestion:<br/>The analysis recommends setting up the database first. Do you want to proceed with database setup?}
    agent_1770200534074[execute_db_agent]
    agent_1770200577640[validate_db_output]
    prompt_1770201456002[I need to build a weather d...]
    agent_1770201718569[agent_order_planner]
    ifelse_1770202089040{If/Else:<br/>Conditional Branch}
    agent_1770202298823[error_handler_db]
    agent_1770202421044[execute_spark_agent]
    agent_1770202533141[validate_spark_output]
    ifelse_1770202793865{If/Else:<br/>Conditional Branch}
    agent_1770202862210[error_handler_spark]
    agent_1770202986750[execute_webapp_agent]
    agent_1770203128693[validate_webapp_output]
    ifelse_1770203224918{If/Else:<br/>Conditional Branch}
    agent_1770203290457[final_validation]
    agent_1770203370217[report_generator]
    prompt_1770203500570[Database setup skipped. Pro...]
    agent_1770203820754[error_handler_webapp]

    start_node_default --> prompt_1770201456002
    prompt_1770201456002 --> agent_1770200345506
    agent_1770200345506 --> agent_1770201718569
    agent_1770201718569 --> question_1770200452878
    question_1770200452878 -->|Yes, set up TimescaleDB first| agent_1770200534074
    agent_1770200534074 --> agent_1770200577640
    agent_1770200577640 --> ifelse_1770202089040
    ifelse_1770202089040 -->|Invalid| agent_1770202298823
    ifelse_1770202089040 -->|Valid| agent_1770202421044
    agent_1770202421044 --> agent_1770202533141
    agent_1770202533141 --> ifelse_1770202793865
    ifelse_1770202793865 -->|False| agent_1770202862210
    ifelse_1770202793865 -->|True| agent_1770202986750
    agent_1770202986750 --> agent_1770203128693
    agent_1770203128693 --> ifelse_1770203224918
    ifelse_1770203224918 -->|True| agent_1770203290457
    agent_1770203290457 --> agent_1770203370217
    question_1770200452878 -->|No, I already have the database configured| prompt_1770203500570
    prompt_1770203500570 --> agent_1770202421044
    agent_1770203370217 --> end_node_default
    ifelse_1770203224918 -->|False| agent_1770203820754
```

## Workflow Execution Guide

Follow the Mermaid flowchart above to execute the workflow. Each node type has specific execution methods as described below.

### Execution Methods by Node Type

- **Rectangle nodes**: Execute Sub-Agents using the Task tool
- **Diamond nodes (AskUserQuestion:...)**: Use the AskUserQuestion tool to prompt the user and branch based on their response
- **Diamond nodes (Branch/Switch:...)**: Automatically branch based on the results of previous processing (see details section)
- **Rectangle nodes (Prompt nodes)**: Execute the prompts described in the details section below

### Prompt Node Details

#### prompt_1770201456002(I need to build a weather d...)

```
I need to build a weather data system with the following requirements:

{{user_requirements}}

Please analyze what components are needed and create:
- Database schema (if needed)
- Data processing pipeline (if needed)
- Web dashboard (if needed)

Context:
- Technology Stack: {{tech_stack}}
- Timeline: {{timeline}}
- Team Size: {{team_size}}
```

#### prompt_1770203500570(Database setup skipped. Pro...)

```
Database setup skipped. Proceeding with Spark and WebApp agents only.

Note: Ensure your database is already configured at:
- Host: {{db_host}}
- Database: {{db_name}}
- Schema: {{db_schema}}"

Variables: db_host, db_name, db_schema
```

### AskUserQuestion Node Details

Ask the user and proceed based on their choice.

#### question_1770200452878(The analysis recommends setting up the database first. Do you want to proceed with database setup?)

**Selection mode:** Single Select (branches based on the selected option)

**Options:**
- **Yes, set up TimescaleDB first**: yes_db_setup
- **No, I already have the database configured**: no_db_skip

### If/Else Node Details

#### ifelse_1770202089040(Binary Branch (True/False))

**Evaluation Target**: proceed_to_next_agent == true

**Branch conditions:**
- **Valid**: When condition is true
- **Invalid**: When condition is false

**Execution method**: Evaluate the results of the previous processing and automatically select the appropriate branch based on the conditions above.

#### ifelse_1770202793865(Binary Branch (True/False))

**Evaluation Target**: proceed_to_next_agent == true

**Branch conditions:**
- **True**: When condition is true
- **False**: When condition is false

**Execution method**: Evaluate the results of the previous processing and automatically select the appropriate branch based on the conditions above.

#### ifelse_1770203224918(Binary Branch (True/False))

**Evaluation Target**: proceed_to_next_agent == true

**Branch conditions:**
- **True**: When condition is true
- **False**: When condition is false

**Execution method**: Evaluate the results of the previous processing and automatically select the appropriate branch based on the conditions above.
