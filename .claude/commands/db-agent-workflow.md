---
description: db-agent-workflow
---
```mermaid
flowchart TD
    start_node_default([Start])
    end_node_default([End])
    agent_1770193963026[db_schema_creator]
    prompt_1770194169427[Create TimescaleDB database...]
    agent_1770194253580[db_connection_config]
    agent_1770194347947[data_ingestion_script]
    agent_1770194424428[db_validation]

    prompt_1770194169427 --> agent_1770193963026
    agent_1770193963026 --> agent_1770194253580
    agent_1770194253580 --> agent_1770194347947
    start_node_default --> prompt_1770194169427
    agent_1770194347947 --> agent_1770194424428
    agent_1770194424428 --> end_node_default
```

## Workflow Execution Guide

Follow the Mermaid flowchart above to execute the workflow. Each node type has specific execution methods as described below.

### Execution Methods by Node Type

- **Rectangle nodes**: Execute Sub-Agents using the Task tool
- **Diamond nodes (AskUserQuestion:...)**: Use the AskUserQuestion tool to prompt the user and branch based on their response
- **Diamond nodes (Branch/Switch:...)**: Automatically branch based on the results of previous processing (see details section)
- **Rectangle nodes (Prompt nodes)**: Execute the prompts described in the details section below

### Prompt Node Details

#### prompt_1770194169427(Create TimescaleDB database...)

```
Create TimescaleDB database for weather data with the following requirements:

{{requirements}}

Include:
- Schema design for time-series weather data
- Hypertable configuration
- Indexes for efficient queries
- Python ingestion script using psycopg2
```
