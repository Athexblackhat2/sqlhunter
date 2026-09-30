<div align="center">

<img src="assets/logo.png" alt="SQLHunter Pro Logo" width="280">

# 🛡️ SQLHunter Pro

### Advanced SQL Injection Scanner

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Version](https://img.shields.io/badge/Version-2.1-blue?style=for-the-badge)](https://github.com/Athexblackhat2/sqlhunter/releases)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey?style=for-the-badge)]()
[![Security](https://img.shields.io/badge/Focus-Web%20Security-red?style=for-the-badge)](https://owasp.org/www-community/attacks/SQL_Injection)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/Athexblackhat2/sqlhunter?style=for-the-badge&color=yellow)](https://github.com/Athexblackhat2/sqlhunter/stargazers)

**A modern, multi-threaded SQL Injection scanner supporting GET & POST parameters,  
5 database engines, and 4 detection techniques — built for authorized penetration testers.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Examples](#-examples) • [Roadmap](#-roadmap) • [Disclaimer](#%EF%B8%8F-disclaimer)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Supported Databases](#-supported-databases)
- [Detection Techniques](#-detection-techniques)
- [Installation](#-installation)
- [Usage](#-usage)
- [Examples](#-examples)
- [Command-Line Arguments](#-command-line-arguments)
- [Output Example](#-output-example)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Performance Tips](#-performance-tips)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Disclaimer](#%EF%B8%8F-disclaimer)
- [License](#-license)
- [Author](#-author)

---

## 🔍 Overview

**SQLHunter Pro** is a lightweight yet powerful **SQL Injection scanner** built in pure Python.  
It automates the detection of SQL Injection vulnerabilities in web applications — for both  
**GET query parameters** and **POST form data** — using four industry-standard detection techniques.

Designed for:
- 🎯 Penetration testers
- 🐛 Bug bounty hunters
- 🔐 Security researchers
- 📚 Students learning web security

Unlike bloated scanners, SQLHunter Pro stays **fast, readable, and scriptable** — with no external dependencies beyond `requests`.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔎 **Error-Based Detection** | Injects payloads that trigger DB error messages in the response |
| ⚖️ **Boolean-Based Detection** | Compares response length between `OR 1=1` and `OR 1=2` |
| ⏱️ **Time-Based (Blind) Detection** | Uses `SLEEP`, `pg_sleep`, `WAITFOR` with **double verification** (5s + 8s) |
| 🎯 **UNION-Based Detection** | Injects **visible markers** to confirm UNION injection (false-positive resistant) |
| 🌐 **GET & POST Support** | Scan URL query strings **and** HTML form bodies |
| 🗄️ **5 Database Engines** | MySQL, PostgreSQL, MSSQL, Oracle, SQLite |
| ⚡ **Multi-Threaded** | Scan multiple targets in parallel with thread-safe session pooling |
| 🧠 **Baseline-Aware Timing** | Measures network latency first, then compares — no false positives |
| 🕵️ **Proxy & Tor Support** | Route through Burp Suite, ZAP, or Tor (`socks5://`) |
| 🍪 **Custom Cookies & Headers** | Session-based scanning for authenticated areas |
| 📊 **JSON / TXT Reports** | Structured output for automation pipelines |
| 🎨 **Colored Terminal UI** | Spinner animations, live progress, clear vulnerability highlights |
| 🔢 **Request Counter** | Tracks total HTTP requests sent during the scan |

---

## 🗄️ Supported Databases

| Database | Error-Based | Boolean | Time-Based | UNION |
|---|:---:|:---:|:---:|:---:|
| **MySQL / MariaDB** | ✅ | ✅ | ✅ | ✅ |
| **PostgreSQL** | ✅ | ✅ | ✅ | ✅ |
| **Microsoft SQL Server** | ✅ | ✅ | ✅ | ✅ |
| **Oracle** | ✅ | ✅ | ✅ | ✅ |
| **SQLite** | ✅ | ✅ | ✅ | ✅ |

---

## 🧪 Detection Techniques

<details>
<summary><b>1. Error-Based SQL Injection</b></summary>

Injects payloads designed to force the database to leak information inside error messages.

**Example payload (MySQL):**
```sql
' AND updatexml(1,concat(0x7e,(SELECT @@version),0x7e),1)-- -
```

**Detection:** Scans the HTTP response for database-specific keywords (`xpath`, `SQL syntax`, `ORA-`, etc.) and increases confidence when HTTP status is `500`.

</details>

<details>
<summary><b>2. Boolean-Based SQL Injection</b></summary>

Sends two logically opposite payloads and compares the response.

```sql
' OR 1=1-- -    → should return MORE data
' OR 1=2-- -    → should return LESS data
```

**Detection:** Response length difference > 50 bytes with identical HTTP status = indication.

</details>

<details>
<summary><b>3. Time-Based (Blind) SQL Injection</b></summary>

Forces the database to sleep, revealing the vulnerability even when no output is shown.

```sql
' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)-- -
```

**Detection:**
- Measures **baseline latency** of a normal request first
- Requires **two delays** (5s and 8s) to confirm — eliminates network jitter false positives

</details>

<details>
<summary><b>4. UNION-Based SQL Injection</b></summary>

Injects a **unique visible marker** via `UNION SELECT` and checks if it appears in the response.

```sql
' UNION SELECT 'SQLHX4821',NULL,NULL-- -
```

**Detection:** Marker string observed in the response body → confirmed.  
**Zero false positives** — response length diffing alone is unreliable.

</details>

---

## ⚙️ Installation

### Requirements
- Python **3.8+**
- pip

### Steps

```
# 1. Clone the repository
git clone https://github.com/Athexblackhat2/sqlhunter.git
cd sqlhunter

# 2. (Recommended) Create a virtual environment
virtualenv athex
source athex/bin/activate      

# 3. Install dependencies
pip install -r requirements.txt
```

> 🍏 **macOS / Windows users:** For colored terminal output, use **Windows Terminal** or **iTerm2**.  
> Legacy `cmd.exe` may not render ANSI escape codes.

---

## 🚀 Usage

```
   ███████╗ ██████╗ ██╗           ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗
   ██╔════╝██╔═══██╗██║           ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
   ███████╗██║   ██║██║           ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
   ╚════██║██║▄▄ ██║██║           ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
   ███████║╚██████╔╝██║           ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
   ╚══════╝ ╚═════╝ ███████║      ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
                             DEVELOPER - ATHEX BLACK HAT

usage: python3 sqlhunter.py [options]

options:
  -h, --help            show this help message and exit
  -u, --url URL         Target URL (example: http://site.com/page.php?id=1)
  -l, --list FILE       Scan multiple targets from file
  -t, --threads N       Threads (default: 5)
  -o, --output FORMAT   Save report (json | txt)
  --method {GET,POST}   HTTP method (default: GET)
  --data DATA           POST data (example: 'user=admin&pass=1')
  --cookie COOKIE       Cookie header
  --proxy PROXY         HTTP proxy (example: http://127.0.0.1:8080)
  --tor                 Route through Tor (socks5://127.0.0.1:9050)
  --delay SEC           Delay between payload requests
  -v, --version         Show program version
```

---

## 💡 Examples

### 🔹 GET — Single URL

```
python3 sqlhunter.py -u "http://testphp.vulnweb.com/artists.php?artist=1"
```

### 🔹 GET — Multiple targets

`targets.txt`:
```
http://site1.com/item.php?id=1
http://site2.com/view.php?id=5
http://site3.com/page.php?cat=2
```

```
python3 sqlhunter.py -l targets.txt -t 10
```

### 🔹 POST — Login form

```
python3 sqlhunter.py \
    -u "http://target.com/login" \
    --method POST \
    --data "username=admin&password=test"
```

### 🔹 POST + Cookie + JSON Report

```
python3 sqlhunter.py \
    -u "http://target.com/api/login" \
    --method POST \
    --data "user=admin&pass=1&csrf=abc123" \
    --cookie "PHPSESSID=xyz987" \
    -o json
```

### 🔹 GET + Burp Proxy

```
python3 sqlhunter.py \
    -u "http://target.com/page.php?id=1" \
    --proxy http://127.0.0.1:8080
```

### 🔹 Through Tor

```
python3 sqlhunter.py \
    -u "http://target.com/page.php?id=1" \
    --tor --delay 2
```

### 🔹 Stealth Mode (WAF evasion)

```
python3 sqlhunter.py \
    -u "http://target.com/page.php?id=1" \
    --delay 3 -t 1
```

---


**Detection Flow:**
1. Parse URL or POST body into parameter dictionary
2. For each parameter:
   - Inject error payloads → scan for DB error keywords
   - Inject `OR 1=1` vs `OR 1=2` → compare response lengths
   - Inject `SLEEP(5)` and `SLEEP(8)` → verify timing anomaly
   - Inject `UNION SELECT 'marker'` → check response for marker
3. Aggregate findings + save report

---

## ⚡ Performance Tips

| Scenario | Recommendation |
|---|---|
| **Fast scan (no WAF)** | `-t 10` (10 threads), no delay |
| **Behind Cloudflare / WAF** | `--delay 2 -t 1` (single thread, throttled) |
| **Time-based only** | Disable boolean via payload file (future feature) |
| **Huge target list** | Split into chunks of 50, run in parallel terminals |
| **Over Tor** | `--delay 3 -t 1` (Tor is slow, throttling avoids circuit issues) |

---

### Guidelines
- Follow **PEP 8** style
- Add **docstrings** to new functions
- Test against **DVWA / bWAPP / Juice Shop** before submitting
- Never test against systems you don't own

---

## ⚠️ Disclaimer

> **This tool is provided for educational and authorized security testing purposes only.**

By using SQLHunter Pro, you agree that:

- You will **only** use it against systems you **own** or have **explicit written permission** to test
- You understand that **unauthorized access to computer systems is illegal** under laws including:
  - 🇵🇰 **PECA 2016** (Pakistan)
  - 🇮🇳 **IT Act 2000** (India)
  - 🇺🇸 **CFAA** (United States)
  - 🇬🇧 **Computer Misuse Act 1990** (UK)
  - 🌍 **GDPR** and equivalent regulations worldwide
- The **author is not responsible** for any misuse, damage, or legal consequences

**Practice legally on:**
- [DVWA](https://github.com/digininja/DVWA)
- [bWAPP](http://www.itsecgames.com/)
- [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [HackTheBox](https://www.hackthebox.com/) / [TryHackMe](https://tryhackme.com/)

---

## 👤 Author

<div align="center">

**ATHEX BLACK HAT**

[![GitHub](https://img.shields.io/badge/GitHub-Athexblackhat2-181717?style=for-the-badge&logo=github)](https://github.com/Athexblackhat2)

*"Break it to fix it — ethically."*

</div>

---
<div align="center">

### ⭐ If SQLHunter Pro helped you, star the repo!

**Made with 🖤 by ATHEX BLACK HAT**

</div>
