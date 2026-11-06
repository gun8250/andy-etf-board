#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 资金看板本地全功能免密服务器 (完全脱离原网站·官方直连引擎)
- 实时行情：直接对接新浪财经/东财官方行情源
- 分时走势：直接对接官方 1 分钟分时 K 线源
- 原网站改密码/下线没有任何影响，实现 100% 自主运行
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import ssl
import re
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
REMOTE_ORIGIN = "https://etf-fund-flow-board.app.workbuddy.host"
AUTH_COOKIE_NAME = "etf_auth"
AUTH_COOKIE_VALUE = "3c5f948d8857b1dfea8ab691"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_sina_kline(symbol, datalen=260):
    """直接从官方财经数据源获取 1 分钟分时行情数据"""
    url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_{symbol}=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=1&datalen={datalen}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            text = resp.read().decode("utf-8")
            match = re.search(r'\[(.*)\]', text, re.DOTALL)
            if match:
                raw_json = "[" + match.group(1) + "]"
                items = json.loads(raw_json)
                return [{
                    "day": x.get("day"),
                    "open": str(x.get("open")),
                    "high": str(x.get("high")),
                    "low": str(x.get("low")),
                    "close": str(x.get("close")),
                    "volume": str(x.get("volume")),
                    "amount": str(x.get("amount"))
                } for x in items]
    except Exception as e:
        pass
    return []

def fetch_official_hq(codes_str):
    """直接从官方财经数据源获取批量实时行情快照"""
    codes = [c.strip() for c in codes_str.split(',') if c.strip()]
    if not codes:
        return {"rc": 0, "data": {"total": 0, "diff": []}}

    url = 'https://hq.sinajs.cn/list=' + ','.join(codes)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'})
    diff = []
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            text = resp.read().decode('gbk', errors='ignore')
            for line in text.splitlines():
                m = re.match(r'var hq_str_([a-z0-9]+)="(.*)";', line.strip())
                if m:
                    full_sym = m.group(1)
                    raw_parts = m.group(2).split(',')
                    if len(raw_parts) > 9:
                        name = raw_parts[0]
                        pre_close = float(raw_parts[2]) if raw_parts[2] else 0.0
                        price = float(raw_parts[3]) if raw_parts[3] else 0.0
                        amount = float(raw_parts[9]) if raw_parts[9] else 0.0
                        pct = round((price - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0.0
                        code = full_sym[2:]  # 截取 sh/sz 后面的代码
                        diff.append({
                            'f12': code,
                            'f14': name,
                            'f2': price,
                            'f3': pct,
                            'f6': amount,
                            'f18': pre_close
                        })
    except Exception as e:
        pass
    return {'rc': 0, 'data': {'total': len(diff), 'diff': diff}}

class ETFBoardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api/verify":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path
        query = urllib.parse.parse_qs(url_parts.query)

        if path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        # 官方直连实时行情路由
        if path == "/api/kline":
            symbol = query.get("symbol", ["sh000001"])[0]
            datalen = int(query.get("datalen", [260])[0])
            kline_data = fetch_sina_kline(symbol, datalen)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(kline_data).encode("utf-8"))
            return

        if path == "/api/ktrends":
            symbols = query.get("symbols", ["sh000001"])[0].split(",")
            datalen = int(query.get("datalen", [260])[0])
            res = {}
            for s in symbols:
                s = s.strip()
                if s:
                    res[s] = fetch_sina_kline(s, datalen)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        if path == "/api/hq":
            codes = query.get("codes", ["sh000001"])[0]
            hq_data = fetch_official_hq(codes)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(hq_data).encode("utf-8"))
            return

        # 首页免密直接展示看板
        if path in ["/", "/index.html"]:
            index_path = os.path.join(DIRECTORY, "index.html")
            with open(index_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        return super().do_GET()

def run():
    print(f"==================================================")
    print(f"  ETF资金看板本地免密服务器启动中...")
    print(f"  访问地址: http://127.0.0.1:{PORT}")
    print(f"  数据引擎: 官方直连引擎 (完全脱离原网站，实时更新)")
    print(f"==================================================")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ETFBoardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止。")

if __name__ == "__main__":
    run()
