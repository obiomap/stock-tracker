import urllib.request, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
html = urllib.request.urlopen("https://jpstocktracker.pro", context=ctx, timeout=15).read().decode()

# Build sym -> price map from wl-row data
syms   = re.findall(r'data-sym="([^"]+)"', html)
prices = re.findall(r'class="wl-price"[^>]*>([^<]+)<', html)
table = {s.upper(): p.strip() for s, p in zip(syms, prices)}

new = {
    "Europe new":    ["NVO","RACE","STLA","STM","ING","NOK"],
    "African Mkts":  ["MTNOY","NPSNY"],
    "Leveraged ETFs":["SOXL","TQQQ","UPRO"],
    "Thematic ETFs": ["ICLN","LIT","DRIV","SKYY","CLOU","AIQ","JETS","XBI","HACK"],
}

total_ok = total_wait = 0
for group, syms_list in new.items():
    ok   = [(s, table[s]) for s in syms_list if s in table]
    wait = [s for s in syms_list if s not in table]
    total_ok += len(ok)
    total_wait += len(wait)
    print(f"{group} — {len(ok)}/{len(syms_list)}")
    for s, p in ok:
        print(f"  OK   {s:20s}  {p}")
    for s in wait:
        print(f"  WAIT {s}")
    print()

print(f"Total symbols in table: {len(table)}")
print(f"New stocks with prices: {total_ok}/{total_ok + total_wait}")
