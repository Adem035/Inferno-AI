# Inferno AI

**Inferno AI** is an open‑source, multi‑agent autonomous penetration‑testing framework derived from the MAPTA research system. It orchestrates large language models (LLMs) with lightweight sandbox tools to discover and validate web‑application vulnerabilities without human intervention.

---

## Architecture Overview

```
Coordinator Agent  ←  Strategic planning & orchestration
│
├─ sandbox_agent(s)  ←  Executes tactical commands (curl, python, etc.)
│   • run_command
│   • run_python
│   • (future) browser automation
│
└─ validator_agent  ←  Verifies PoC exploits end‑to‑end
    • Confirms vulnerability impact
    • Returns clear pass/fail verdict
```

- **Pure execution model** – only `sandbox_run_command` and `sandbox_run_python` are exposed to the agents, keeping the attack surface minimal.
- **Stateless coordination** – the Coordinator maintains high‑level state, while sandbox agents share a single per‑job Docker container for file‑system persistence.
- **Budget‑aware loops** – the system stops automatically when a flag/PoC is found or when configurable limits (tool calls, time, cost) are reached.

---

## Supported LLMs

Inferno AI can work with any provider that implements the standard OpenAI‑compatible chat completion API. Out‑of‑the‑box support includes:

- **OpenAI GPT‑5** (default, high‑reasoning mode)
- **Claude 4.5 Sonnet** 
- **DeepSeek‑Chat** (cost‑effective alternative)
- **Ollama**
The LLM is selected via the `LLM_PROVIDER` and `LLM_MODEL` environment variables. Reasoning effort can be tuned (`LLM_REASONING_EFFORT=low|medium|high`).

---

## Core Components

| Component | Responsibility |
|-----------|------------------|
| `main.py` | Entry point, parses arguments, launches the Coordinator, tracks usage metrics |
| `agent_prompts.py` | System prompts for Coordinator, Sandbox, and Validator agents. Includes CTF‑mode and Bug‑Bounty‑mode variants |
| `function_tool.py` | Decorators that expose `sandbox_run_command` and `sandbox_run_python` to the agents |
| `llm_provider.py` | Wrapper around the chosen LLM API, handles streaming, token limits, and reasoning effort |
| `docker_sandbox.py` | Minimal Docker image (Ubuntu) that runs the sandbox agents safely |
| `requirements.txt` | Python dependencies (e.g., `httpx`, `pydantic`, `openai`, `anthropic`) |

---

## Usage

Set up the environment variables in the .env file.

# Run the scanner
./inferno.sh
```

The script launches the Docker sandbox, streams LLM thoughts to the console, and prints a concise report when a vulnerability or flag is discovered.

---

## Extensibility

- **Add new tools** – implement a Python function and expose it via `@function_tool`.
- **Custom prompts** – edit `agent_prompts.py` to add domain‑specific strategies (e.g., API‑first, GraphQL, IoT).
- **Plug‑in validators** – replace the PoC verification step with external services (e.g., Burp Suite, ZAP) if desired.

---

## License

Inferno AI is released under the **MIT License**. Contributions are welcome via pull‑requests.

---

*Inferno AI – autonomous, lightweight, and ready for real‑world bug‑bounty testing.*
