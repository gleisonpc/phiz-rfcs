#!/usr/bin/env python3
"""Render the Developer-area mockups (PT source) to PNG in pt/en/zh.
usage: render_mocks.py <mockups-design dir> <i18n.json> <out dir>"""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC, I18N, OUT = Path(sys.argv[1]).resolve(), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), Path(sys.argv[3]).resolve()
NAMES = {"Main":"01-visao-geral","NovaIntegracao":"02-nova-integracao","Integracao":"03-detalhe-integracao",
         "SegredoCriado":"04-segredo-criado","Webhooks":"05-webhooks","Remetentes":"06-remetentes","CanalMigracao":"07-canal-migracao"}
LANGS = {"pt": (None, "pt-BR"), "en": (0, "en"), "zh": (1, "zh-CN")}
CJK = 'body{font-family:-apple-system,"SF Pro Text","Segoe UI","PingFang SC","Noto Sans CJK SC","Noto Sans SC",system-ui,sans-serif}'
PHRASE = "Olá! Seu pedido saiu para entrega."

def tr(s, idx):
    return I18N[s][idx] if idx is not None and s in I18N else s

def translate(body, idx):
    if idx is None:
        return body
    def node(m):
        raw = m.group(1); core = raw.strip()
        if core in I18N:
            lead = raw[:len(raw)-len(raw.lstrip())]; trail = raw[len(raw.rstrip()):]
            return ">" + lead + I18N[core][idx] + trail + "<"
        return m.group(0)
    body = re.sub(r">([^<>]+)<", node, body)
    body = re.sub(r'(aria-label|title|value)="([^"]+)"', lambda m: f'{m.group(1)}="{tr(m.group(2), idx)}"', body)
    return body.replace(PHRASE, I18N[PHRASE][idx])

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":1440,"height":600})
    for lang, (idx, bcp) in LANGS.items():
        (OUT/lang).mkdir(parents=True, exist_ok=True)
        for k, v in NAMES.items():
            t = (SRC/f"{k}.dc.html").read_text(encoding="utf-8")
            helm = re.search(r"<helmet>(.*?)</helmet>", t, re.S).group(1)
            body = re.search(r"<x-dc>(.*?)</x-dc>", t, re.S).group(1)
            body = translate(re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S), idx)
            extra = f"<style>{CJK}</style>" if lang == "zh" else ""
            html = f'<!doctype html><html lang="{bcp}"><head><meta charset="utf-8">{helm}{extra}</head><body>{body}</body></html>'
            f = OUT/lang/f"{v}.html"; f.write_text(html, encoding="utf-8")
            pg.set_viewport_size({"width":1440,"height":600}); pg.goto(f.as_uri()); pg.wait_for_timeout(250)
            h = pg.evaluate("document.documentElement.scrollHeight"); pg.set_viewport_size({"width":1440,"height":h})
            pg.wait_for_timeout(80); pg.screenshot(path=str(OUT/lang/f"{v}.png"), full_page=True)
            print(lang, v, h, flush=True)
