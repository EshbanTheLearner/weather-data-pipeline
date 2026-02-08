---
description: webapp-agent-workflow
---
```mermaid
flowchart TD
    start_node_default([Start])
    end_node_default([End])
    prompt_1770195147978[Create Flask REST API and R...]
    agent_1770195153357[flask_api_creator]
    agent_1770195232677[react_dashboard_creator]
    agent_1770195703316[visualization_configurator]
    agent_1770195773936[webapp_testing_setup]

    start_node_default --> prompt_1770195147978
    prompt_1770195147978 --> agent_1770195153357
    agent_1770195153357 --> agent_1770195232677
    agent_1770195232677 --> agent_1770195703316
    agent_1770195703316 --> agent_1770195773936
    agent_1770195773936 --> end_node_default
```

## Workflow Execution Guide

Follow the Mermaid flowchart above to execute the workflow. Each node type has specific execution methods as described below.

### Execution Methods by Node Type

- **Rectangle nodes**: Execute Sub-Agents using the Task tool
- **Diamond nodes (AskUserQuestion:...)**: Use the AskUserQuestion tool to prompt the user and branch based on their response
- **Diamond nodes (Branch/Switch:...)**: Automatically branch based on the results of previous processing (see details section)
- **Rectangle nodes (Prompt nodes)**: Execute the prompts described in the details section below

### Prompt Node Details

#### prompt_1770195147978(Create Flask REST API and R...)

```
Create Flask REST API and React dashboard with the following requirements:

{{requirements}}

Use data from:
- Database schema: {{db_schema}}
- Processed data format: {{spark_output_format}}

Generate:
- Flask REST API with endpoints
- React dashboard components
- Data visualizations
- Testing setup"

Variables:
- requirements
- db_schema (optional)
- spark_output_format (optional)
```
