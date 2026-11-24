import json
import re
import urllib.request
import time

SYNC_ETFS = [
    "sh510300","sh510310","sh510050","sh563360","sz159352",
    "sh588000","sh588080","sh588190","sz159915","sz159949",
    "sh510500","sh512100","sz159845","sh563000","sh510210",
    "sh512890","sh510880","sh512880","sh560010","sz159919"
]

def make_slots():
    slots = []
    h, m = 9, 30
    for _ in range(121):
        slots.append(f"{h:02d}:{m:02d}")
        m += 1
        if m == 60:
            m = 0
            h += 1
    h, m = 13, 1
    for _ in range(120):
        slots.append(f"{h:02d}:{m:02d}")
        m += 1
        if m == 60:
            m = 0
            h += 1
    return slots

SLOTS = make_slots()

def fetch_etf_bars(sym, scale=1):
    url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_{sym}=/CN_MarketDataService.getKLineData?symbol={sym}&scale={scale}&datalen=1023"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read().decode('gbk', errors='ignore')
                s_idx = content.find('[')
                e_idx = content.rfind(']')
                if s_idx != -1 and e_idx != -1:
                    arr = json.loads(content[s_idx:e_idx+1])
                    return arr
        except Exception as e:
            time.sleep(1)
    return []

def run():
    print(f"Fetching 1-minute bars for {len(SYNC_ETFS)} ETFs...")
    day_minute_turnover = {}
    success_count = 0
    for sym in SYNC_ETFS:
        bars = fetch_etf_bars(sym, scale=1)
        if bars:
            success_count += 1
            for item in bars:
                day_time = item.get('day', '')
                if not day_time:
                    continue
                d = day_time[:10]
                t = day_time[11:16]
                amt = float(item.get('amount', 0)) / 1e8
                if d not in day_minute_turnover:
                    day_minute_turnover[d] = {}
                day_minute_turnover[d][t] = day_minute_turnover[d].get(t, 0.0) + amt
        print(f"  {sym}: {len(bars)} bars")
        time.sleep(0.1)

    print(f"Successfully fetched {success_count}/{len(SYNC_ETFS)} ETFs.")
    if success_count < 15:
        print("Too few ETFs succeeded, aborting update to protect data integrity.")
        return False

    curves = {}
    for d, m_map in day_minute_turnover.items():
        if len(m_map) >= 120:
            acc = 0.0
            curve = []
            for s in SLOTS:
                acc += m_map.get(s, 0.0)
                curve.append(round(acc))
            curves[d] = curve
            print(f"Generated curve for {d}: total {curve[-1]} 亿元, 11:30 {curve[120]} 亿元")

    # Load cumdays.json
    cumdays_path = 'cumdays.json'
    try:
        with open(cumdays_path, 'r', encoding='utf-8') as f:
            cumdays = json.load(f)
    except Exception:
        with open('etf-fund-flow-board/cumdays.json', 'r', encoding='utf-8') as f:
            cumdays = json.load(f)
        cumdays_path = 'etf-fund-flow-board/cumdays.json'

    # Update curves
    updated_days = []
    for d, curve in curves.items():
        cumdays[d] = curve
        updated_days.append(d)

    # Pad any 240 days
    for k, v in cumdays.items():
        if len(v) == 240:
            cumdays[k].append(v[-1])

    sorted_keys = sorted(cumdays.keys())
    last20_keys = sorted_keys[-20:]
    avg_from = last20_keys[0]
    avg_to = last20_keys[-1]

    avg20 = []
    for i in range(241):
        val_sum = sum(cumdays[k][i] for k in last20_keys)
        avg20.append(round(val_sum / 20.0, 2))

    # Save cumdays.json
    with open(cumdays_path, 'w', encoding='utf-8') as f:
        json.dump(cumdays, f, ensure_ascii=False)
    print(f"Updated {cumdays_path} with {len(updated_days)} days (Latest: {sorted_keys[-1]})")

    # Update index.html
    html_path = 'index.html' if cumdays_path == 'cumdays.json' else 'etf-fund-flow-board/index.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    m = re.search(r'window\.__CUMDAYS\s*=\s*\{', html)
    if m:
        start_pos = m.start()
        end_pos = html.find('};\n', start_pos)
        if end_pos == -1:
            end_pos = html.find('};', start_pos)
        end_pos += 2
        cumdays_json_str = json.dumps(cumdays, ensure_ascii=False, separators=(',', ':'))
        new_cumdays_stmt = f"window.__CUMDAYS = {cumdays_json_str};"
        html = html[:start_pos] + new_cumdays_stmt + html[end_pos:]

    avg20_json_str = json.dumps(avg20, separators=(',', ':'))
    m_cumdata = re.search(r'"avgDays":\d+,"avgFrom":"[^"]+","avgTo":"[^"]+","avg20":\[[^\]]+\]', html)
    if m_cumdata:
        new_sub = f'"avgDays":20,"avgFrom":"{avg_from}","avgTo":"{avg_to}","avg20":{avg20_json_str}'
        html = html[:m_cumdata.start()] + new_sub + html[m_cumdata.end():]
    else:
        m_alt = re.search(r'"avg20":\[[^\]]+\],"avgDays":\d+,"avgFrom":"[^"]+","avgTo":"[^"]+"', html)
        if m_alt:
            new_sub = f'"avg20":{avg20_json_str},"avgDays":20,"avgFrom":"{avg_from}","avgTo":"{avg_to}"'
            html = html[:m_alt.start()] + new_sub + html[m_alt.end():]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Updated {html_path} successfully!")
    return True

if __name__ == '__main__':
    run()
