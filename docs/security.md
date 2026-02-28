# Enterprise Security & Privacy Architecture

The Private Business Intelligence Agent is engineered from the ground up for strict organizational, on-premise, and air-gapped deployments. It provides sophisticated AI data analysis with **zero data exfiltration risk**.

## Core Security Pillars

### 1. 100% Local Execution

- **No Cloud APIs:** Unlike wrappers around ChatGPT, Claude, or Gemini, this application does not make any external HTTP requests to cloud providers.
- **Local Inferencing:** The Large Language Model (`llama3.2:3b`) runs entirely on your local machine or local network server via the open-source Ollama daemon.
- **Air-Gapped Capable:** Once the application runtime and model weights are downloaded, the server running this application can be completely physically disconnected from the internet and it will continue to function flawlessly.

### 2. Zero Data Exfiltration

- **Data Locality:** Your sensitive proprietary data (e.g., the CSV files) are loaded directly from the local disk into local RAM by the Python `pandas` library.
- **Bounded Context:** When the LLM generates narrative insights (Pass 2 of the architecture), it only sees highly compressed, anonymous statistical summaries generated locally, not raw PII or row-level transaction data.
- **No Telemetry:** There are no tracking scripts, analytics, or ping-backs embedded in the application code.

### 3. Predictable Mathematical Sandboxing

- **Elimination of "Code Execution" Risks:** Many AI agents attempt to write and execute arbitrary Python or SQL code on the fly to answer questions. This creates a massive attack surface for prompt injection (e.g., tricking the AI into writing a `DROP TABLE` command or reading shadow files).
- **Hardcoded Tooling:** This agent _cannot_ execute arbitrary code. The LLM is strictly used as a router pointing to 1 of 13 pre-compiled, mathematically verified Python functions. Even if a user maliciously prompts the AI, the worst possible outcome is triggering the wrong, safe, read-only charting function.

### 4. Enterprise Compliance Suitability

Because all data processing, storage, and AI inference happens strictly within your own network perimeter, this application inherently bypasses major compliance headaches:

- **GDPR & CCPA:** No third-party data processors are involved.
- **HIPAA:** If analyzing healthcare data, no BAA (Business Associate Agreement) is required with an AI vendor because there is no vendor.
- **SOC2:** Simplifies internal auditing as external data transmission vectors are eliminated.

## Summary

The application treats your hardware as the ultimate trust boundary. It brings the AI to your data, rather than sending your data to the AI.
