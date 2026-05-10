
import subprocess, time, os, json

RML = "/Volumes/External/Code/aot"
DAEMON = f"{RML}/Bin/SynanDaemon"
URL = "http://localhost:8089?dummy=1&action=syntax&langua=Ukrainian"

def restart_daemon():
    os.system("pkill -f SynanDaemon 2>/dev/null")
    time.sleep(1)
    os.system(f"RML={RML} {DAEMON} --host 127.0.0.1 --port 8089 > /tmp/synan_punct.log 2>&1 &")
    time.sleep(4)

def test(text, label):
    with open("/tmp/punct_input.txt", "w") as f:
        f.write(text)
    try:
        r = subprocess.run(
            ["curl", "-s", "-w", "\\n%{http_code}", "-X", "POST", URL, "-d", "@/tmp/punct_input.txt"],
            capture_output=True, text=True, timeout=10
        )
        lines = r.stdout.strip().split("\n")
        code = lines[-1] if lines else "?"
        body = "\n".join(lines[:-1])
        if code == "200":
            try:
                data = json.loads(body)
                nw = sum(len(c.get('words',[])) for s in data for c in (s if isinstance(s,list) else [s]) if isinstance(c,dict))
                return "OK", f"{nw}w"
            except:
                return "OK", f"json={len(body)}"
        elif code == "000":
            return "CRASH", ""
        elif code == "400":
            return "EMPTY", "400"
        else:
            return f"HTTP:{code}", ""
    except subprocess.TimeoutExpired:
        return "HANG", ""
    except Exception as e:
        return "ERR", str(e)

def alive():
    try:
        r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}","http://localhost:8089?dummy=1"], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() in ("200","400")
    except:
        return False

tests = []

def t(char_seq, label):
    tests.append((char_seq, label))

# Build all test cases
t("Привіт-світ", "hyphen-minus 002D")
t("Привіт‑світ", "non-breaking hyphen 2011")
t("Привіт–світ", "en dash 2013")
t("Привіт—світ", "em dash 2014")
t("Привіт―світ", "horizontal bar 2015")
t("Привіт‒світ", "figure dash 2012")
t("Привіт⸺світ", "two-em dash 2E3A")
t("Привіт⸻світ", "three-em dash 2E3B")
t("(тест)", "parens 0028/0029")
t("[тест]", "brackets 005B/005D")
t("{тест}", "braces 007B/007D")
t("«тест»", "guillemets 00AB/00BB")
t("‹тест›", "single angles 2039/203A")
t("„тест“", "low-9 + left double 201E/201C")
t("‚тест‘", "low-9 + left single 201A/2018")
t("「тест」", "CJK corner brackets 300C")
t("【тест】", "CJK lenticular 3010")
t("〈тест〉", "CJK angle 3008")
t("《тест》", "CJK double angle 300A")
t(")тест", "close paren only 0029")
t("]тест", "close bracket only 005D")
t("}тест", "close brace only 007D")
t(".", "period 002E")
t("!", "exclamation 0021")
t("?", "question 003F")
t(",", "comma 002C")
t(";", "semicolon 003B")
t(":", "colon 003A")
t("·", "middle dot 00B7")
t("…", "ellipsis 2026")
t("…тест", "ellipsis before word")
t("тест…", "ellipsis after word")
t("¡", "inverted exclamation 00A1")
t("¿", "inverted question 00BF")
t("#", "number sign 0023")
t("%", "percent 0025")
t("@", "commercial at 0040")
t("&", "ampersand 0026")
t("*", "asterisk 002A")
t("\\", "backslash 005C")
t("'", "apostrophe 0027")
t('"', "dquote 0022")
t("^", "circumflex 005E")
t("`", "grave accent 0060")
t("|", "vertical line 007C")
t("~", "tilde 007E")
t("©", "copyright 00A9")
t("®", "registered 00AE")
t("™", "trademark 2122")
t("°", "degree 00B0")
t("±", "plus-minus 00B1")
t("¶", "pilcrow 00B6")
t("¸", "cedilla 00B8")
t("†", "dagger 2020")
t("‡", "double dagger 2021")
t("•", "bullet 2022")
t("‣", "triangular bullet 2023")
t("․", "one dot leader 2024")
t("‥", "two dot leader 2025")
t("‰", "per mille 2030")
t("′", "prime 2032")
t("″", "double prime 2033")
t("‴", "triple prime 2034")
t("※", "reference mark 203B")
t("‼", "double exclamation 203C")
t("⁇", "double question 2047")
t("⁈", "question-exclamation 2048")
t("⁉", "exclamation-question 2049")
t("§", "section sign 00A7")
t("№", "numero sign 2116")
t("_", "low line 005F")
t("‿", "undertie 203F")
t("⁀", "character tie 2040")
t("те́ст", "combining acute 0301")
t("тёст", "combining diaeresis 0308")
t("тѐст", "combining grave 0300")
t("те̂ст", "combining circumflex 0302")
t("те̌ст", "combining caron 030C")
t("­тест", "soft hyphen 00AD")
t("тест світ", "nbsp 00A0")
t("тест​світ", "zero-width space 200B")
t("тест‌світ", "ZWNJ 200C")
t("тест‍світ", "ZWJ 200D")
t("тест﻿світ", "BOM FEFF")
t("тест⁠світ", "word joiner 2060")
t("Привіт, світ!", "comma + exclamation")
t("Хто? Я.", "question + period")
t("Так — ні.", "em dash + period")
t("«Привіт».", "guillemets + period")
t("(так).", "parens + period")
t("тест: а, б; в.", "colon comma semicolon period")
t("а / б \\\\ в | г", "slashes and pipe")
t("!!!", "triple exclamation")
t("???", "triple question")
t("...", "triple dot ascii")
t(",,,", "triple comma")
t(":::", "triple colon")
t(";;;", "triple semicolon")
t("‎тест‏", "LTR/RTL marks")
t("тест світ", "line separator 2028")
t("тест світ", "paragraph separator 2029")
t("«тест", "left guillemet only")
t("тест»", "right guillemet only")
t("“тест”", "curly double quotes")
t("‘тест’", "curly single quotes")
t("д'Артаньян", "ascii apostrophe in word")
t("д’Артаньян", "right single quote in word")
t("дʼАртаньян", "modifier letter apostrophe 2BC")
t("д`Артаньян", "grave as apostrophe")
t("/", "single slash")
t("\\", "single backslash")
t("|", "single pipe")
t("$", "dollar")
t("€", "euro 20AC")
t("₴", "hryvnia 20B4")
t("£", "pound 00A3")
t("¥", "yen 00A5")
t("¢", "cent 00A2")

restart_daemon()

crashes = []
hangs = []
passed = 0
other = 0

for text, label in tests:
    status, detail = test(text, label)
    disp = repr(text[:30])
    if status == "CRASH":
        crashes.append((label, disp))
        print(f"  ✗ CRASH  {label:<50}")
        restart_daemon()
    elif status == "HANG":
        hangs.append((label, disp))
        print(f"  ⏳ HANG   {label:<50}")
        restart_daemon()
    elif status == "OK":
        passed += 1
        print(f"  ✓ OK     {label:<50} {detail:>5}  {disp}")
    else:
        other += 1
        print(f"  ○ {status:<7}{label:<50} {detail:>5}  {disp}")
        if not alive():
            restart_daemon()

print(f"\n{'='*70}")
print(f"Total: {len(tests)} | OK: {passed} | Crash: {len(crashes)} | Hang: {len(hangs)} | Other: {other}")
if crashes:
    print(f"\nCRASHES:")
    for label, txt in crashes:
        print(f"  ✗ {label}: {txt}")
if hangs:
    print(f"\nHANGS:")
    for label, txt in hangs:
        print(f"  ⏳ {label}: {txt}")
