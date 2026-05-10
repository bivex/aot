import subprocess, time, os, signal, json

RML = "/Volumes/External/Code/aot"
DAEMON = f"{RML}/Bin/SynanDaemon"
URL = "http://localhost:8089?dummy=1&action=syntax&langua=Ukrainian"

def restart_daemon():
    # Kill existing
    os.system("pkill -f SynanDaemon 2>/dev/null")
    time.sleep(1)
    os.system(f"RML={RML} {DAEMON} --host 127.0.0.1 --port 8089 > /tmp/synan_char_test.log 2>&1 &")
    time.sleep(4)

def test(text, label):
    # Write to temp file
    with open("/tmp/char_test_input.txt", "w") as f:
        f.write(text)
    try:
        r = subprocess.run(
            ["curl", "-s", "-w", "\\n%{http_code}", "-X", "POST", URL, "-d", "@/tmp/char_test_input.txt"],
            capture_output=True, text=True, timeout=10
        )
        lines = r.stdout.strip().split("\n")
        http_code = lines[-1] if lines else "?"
        body = "\n".join(lines[:-1])
        
        if http_code == "200":
            try:
                data = json.loads(body)
                n_words = sum(len(c.get('words',[])) for s in data for c in (s if isinstance(s,list) else [s]) if isinstance(c,dict))
                return "OK", f"{n_words}w"
            except:
                return "OK", f"json={len(body)}b"
        elif http_code == "000":
            return "CRASH", ""
        else:
            return f"HTTP:{http_code}", ""
    except subprocess.TimeoutExpired:
        return "HANG", ""
    except Exception as e:
        return "ERR", str(e)

# Test cases: (text, label)
tests = [
    # Basic
    ("Привіт", "basic latin+uk"),
    # Numbers
    ("1234567890", "digits"),
    ("3.14", "decimal"),
    ("-42", "negative"),
    ("+380", "plus sign"),
    # Punctuation
    ("„Привіт“", "uk quotes"),
    ("«Привіт»", "guillemets"),
    ("\"Привіт\"", "ascii quotes"),
    ("'Привіт'", "single quotes"),
    ("Привіт—світ", "em dash"),
    ("Привіт–світ", "en dash"),
    ("Привіт - світ", "hyphen spaces"),
    ("Привіт…світ", "ellipsis"),
    ("Привіт!!!", "multi exclaim"),
    ("???!!", "mixed punct"),
    # Currency
    ("100 грн", "currency word"),
    ("100$", "dollar sign"),
    ("100€", "euro sign"),
    ("₴500", "hryvnia sign"),
    ("£100", "pound sign"),
    ("¥1000", "yen sign"),
    # Math/logic
    ("2 + 2 = 4", "math"),
    ("2 × 3", "multiply"),
    ("10 ÷ 2", "divide"),
    ("5 ≥ 3", "gte"),
    ("3 ≤ 5", "lte"),
    ("a ≠ b", "neq"),
    ("∞", "infinity"),
    ("±5", "plus-minus"),
    ("≈100", "approx"),
    # Parentheses & brackets
    ("(тест)", "parens"),
    ("[тест]", "brackets"),
    ("{тест}", "braces"),
    ("<тест>", "angle brackets"),
    ("«тест»", "guillemets2"),
    # Slashes
    ("і/або", "forward slash"),
    ("15.03.2012", "date dots"),
    ("15/03/2012", "date slash"),
    ("2012-03-15", "date dash"),
    ("Ф-12345/2026", "id slash"),
    # At/Hash/Percent
    ("test@example.com", "at sign"),
    ("#tag", "hash"),
    ("100%", "percent"),
    ("0%", "zero percent"),
    ("№ 123", "numero sign"),
    ("§ 5", "section sign"),
    ("© 2026", "copyright"),
    ("®", "registered"),
    ("™", "trademark"),
    # Apostrophe (Ukrainian)
    ("д'Артаньян", "ascii apostrophe"),
    ("д’Артаньян", "right single quote"),
    ("дʼАртаньян", "modifier letter prime"),
    # Unicode special
    (" ", "nbsp"),
    ("привіт світ", "nbsp between"),
    ("\t\t", "tabs"),
    ("   ", "spaces only"),
    ("​", "zero-width space"),
    ("‍", "zero-width joiner"),
    ("﻿", "bom"),
    # Emoji
    ("😀", "emoji face"),
    ("Привіт 🇺🇦", "emoji flag"),
    ("★☆", "stars"),
    ("→←↑↓", "arrows"),
    ("✔✘", "check cross"),
    # Mixed scripts
    ("test тест тест", "latin+uk"),
    ("123 abc", "digits+latin"),
    ("грн.USD", "uk+eng mixed"),
    # Long number
    ("2845601234", "long number"),
    ("2 500 000", "spaced number"),
    # Pipe and backslash
    ("а | б", "pipe"),
    ("а \\ б", "backslash"),
    # Tilde
    ("~100", "tilde"),
    ("≈100", "almost equal"),
    # Ampersand
    ("а та б & в", "ampersand"),
    # Caret
    ("а^б", "caret"),
    # Grave
    ("а`б", "backtick"),
    # Control chars
    ("привіт\r\nсвіт", "CRLF"),
    ("привіт\0світ", "null byte"),
    # Empty
    ("", "empty string"),
    # Single chars
    (".", "single dot"),
    (",", "single comma"),
    ("!", "single bang"),
    ("?", "single question"),
    (":", "single colon"),
    (";", "single semicolon"),
]

restart_daemon()

crashes = []
hangs = []
passed = 0

for text, label in tests:
    status, detail = test(text, label)
    marker = "✓"
    if status == "CRASH":
        marker = "✗ CRASH"
        crashes.append((label, text[:50]))
        restart_daemon()
    elif status == "HANG":
        marker = "⏳ HANG"
        hangs.append((label, text[:50]))
        restart_daemon()
    elif "ERR" in status:
        marker = "?"
    
    display = text[:30].replace('\n','\\n').replace('\r','\\r').replace('\0','\\0').replace('\t','\\t')
    print(f"  {marker} [{status:>8}] {label:<25} '{display}'  {detail}")
    
    if status == "OK":
        passed += 1
    elif status != "CRASH" and status != "HANG":
        # Daemon might be dead after non-200
        try:
            r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}","http://localhost:8089?dummy=1"], capture_output=True, text=True, timeout=3)
            if r.stdout.strip() not in ("400","200"):
                restart_daemon()
        except:
            restart_daemon()

print(f"\n{'='*60}")
print(f"Passed: {passed}/{len(tests)}")
print(f"Crashes: {len(crashes)}")
for label, txt in crashes:
    print(f"  ✗ {label}: '{txt}'")
print(f"Hangs: {len(hangs)}")
for label, txt in hangs:
    print(f"  ⏳ {label}: '{txt}'")
