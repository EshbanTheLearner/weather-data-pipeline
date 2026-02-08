---
description: spark-agent-workflow
---
```mermaid
flowchart TD
    start_node_default([Start])
    end_node_default([End])
    prompt_1770194724903[Create Apache Spark process...]
    agent_1770194795266[spark_configurator]
    agent_1770194872648[spark_processor]
    agent_1770194964009[spark_aggregator]

    start_node_default --> prompt_1770194724903
    prompt_1770194724903 --> agent_1770194795266
    agent_1770194795266 --> agent_1770194872648
    agent_1770194872648 --> agent_1770194964009
    agent_1770194964009 --> end_node_default
```

## Workflow Execution Guide

Follow the Mermaid flowchart above to execute the workflow. Each node type has specific execution methods as described below.

### Execution Methods by Node Type

- **Rectangle nodes**: Execute Sub-Agents using the Task tool
- **Diamond nodes (AskUserQuestion:...)**: Use the AskUserQuestion tool to prompt the user and branch based on their response
- **Diamond nodes (Branch/Switch:...)**: Automatically branch based on the results of previous processing (see details section)
- **Rectangle nodes (Prompt nodes)**: Execute the prompts described in the details section below

### Prompt Node Details

#### prompt_1770194724903(Create Apache Spark process...)

```
Create Apache Spark processing pipeline with:

{{requirements}}

Process data from TimescaleDB:
- Schema: {{db_schema}}

Generate:
- Spark configuration
- PySpark data processing script
- Hourly/daily aggregation jobs
```
