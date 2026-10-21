 # ConfigProof

ConfigProof — Automated Firmware Configuration Verification for Apache NuttX RTOS.

## Problem

Firmware developers and QA engineers working with Apache NuttX RTOS must manage thousands of configuration options across drivers, boards, power management, and security. Manually checking these settings takes time and can lead to missed dependencies or risky configuration changes. For example, accidentally disabling a watchdog setting may reduce a device's ability to recover from certain software failures. ConfigProof extracts configuration options into structured JSON, validates the extracted data, generates release checklists, and flags potentially risky changes before firmware release.

## Who it is for

- Firmware QA engineers at drone-electronics companies who verify flight-controller configurations before release.
- Embedded software developers building battery-powered devices using Apache NuttX RTOS who need to check configuration dependencies and power-management settings.

## Signature feature

ConfigProof combines structured Kconfig extraction with device-specific release checklists and a pull-request review agent that identifies potentially risky firmware configuration changes and links findings to their source files.

## Hardest problem (my interview story)

The hardest problem is accurately extracting configuration information from a large collection of Kconfig files while preserving each option's name, type, default value, dependencies, help text, and source location. Incorrectly extracted information could produce unreliable checklists or misleading warnings. I will validate the extracted data against 100 manually checked configuration options and aim for at least 95% field-level extraction accuracy.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| Apache NuttX RTOS source repository | https://github.com/apache/nuttx | To be measured after cloning and scanning the repository | Not applicable; source code repository | Apache-2.0 for files covered by that licence; verify individual file headers and third-party components |

The dataset includes Kconfig files, board configurations, drivers, and relevant examples from the Apache NuttX repository. The actual number of files processed will be recorded after scanning the repository.

## 10 real questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md).

The questions will cover watchdog configuration, configuration defaults, dependencies, low-power sleep examples, board-specific settings, memory and stack configuration, and potentially risky changes.

## Run it

```bash
git clone https://github.com/apache/nuttx.git
```

Clone the ConfigProof project repository separately, then run the following commands from its root directory.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows Command Prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Create the environment file:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Note: These commands assume the project contains the specified files and endpoint. Adjust them to match the implementation if necessary.

## Live link

To be added in Week 2 after deployment.

