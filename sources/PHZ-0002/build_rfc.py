"""Builds rfcs/PHZ-0002/source.html: trilingual RFC page with shared code samples and Mermaid diagrams.

Run from this folder:  python3 build_rfc.py
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "rfcs", "PHZ-0002", "source.html")
LANGS = [("pt", "pt-BR"), ("en", "en-US"), ("zh", "zh-CN")]

J = lambda o: json.dumps(o, ensure_ascii=False, indent=2)

# ---------- code samples (shared by all languages) ----------
CODE = {
"auth_old": ("http", """# Today: four different logins, each with its own token and renewal
POST {road_info.url}/AuthCredPay            # checkout, pre-auth, TEF, card-vault
POST {road_info.url}/oauth/token            # PIX and bank transfer
POST {road_info.url}autenticacao/gerar-token # 3DS (platform API)
POST https://api-services.credpay.com.br/AuthCredPay/   # reconciliation (hard-coded URL)"""),
"auth_new": ("bash", """# New: one API Key (gpk_...) on every call, no login, no renewal
curl -X GET "https://api2-homolog.grupag.com.br/v1/pagamento/consulta/nit?nit=$NIT" \\
  -H "Authorization: Bearer $GRUPAG_API_KEY" \\
  -H "Cliente-Id: $CLIENTE_ID"   # same value on every call of the flow"""),
"pay_old": ("json", J({"nomeDoCliente": "JOAO DA SILVA", "documento": "12345678901", "quantidadeDeParcelas": 1,
                        "valorInicial": 150.00, "token": "TOKEN_DO_CARTAO", "numeroInterno": "PED-4711",
                        "subDominioId": 1234, "lojaId": 1})),
"pay_new": ("json", J({"merchantChargeId": "20260901010707410895669", "orderId": "PED-4711", "installments": "1",
                        "authorizerId": "2", "amount": "15000", "typeTransaction": "C", "card": {"token": "crd_d6dc9c299d15…"}})),
"pay_new_resp": ("json", J({"status": 200, "message": "Sucesso", "data": {"nit": "pag_59c416ca3552…", "orderId": "PED-4711",
                             "merchantChargeId": "20260901010707410895669", "amount": "15000", "status": "CONFIRMADO",
                             "authorizationCode": "965481", "date": "2026-09-01T01:11:20.925Z"}})),
"pix_new": ("bash", """curl -X POST "https://api2-homolog.grupag.com.br/transacional/pix/qrcode" \\
  -H "Authorization: Bearer $GRUPAG_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{ "amount": 15.00, "description": "Pedido PED-12345", "expirationSeconds": 3600 }'
# 200 → { "transactionId": "a1b2…", "status": "GERADO", "pixCopyAndPaste": "000201…", "destination": "TRANSACIONAL-PIX-SICREDI" }"""),
"cancel_new": ("bash", """# Full or partial refund (card). Only until 23:59 on the capture day (Brasília time).
curl -X DELETE "https://api2-homolog.grupag.com.br/v1/pagamento/cancelar" \\
  -H "Authorization: Bearer $GRUPAG_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{ "nit": "pag_59c416ca3552…", "amount": "5000" }'"""),
"amount_conv": ("java", """// Single conversion point in the channel's GruPag adapter
static String toCents(BigDecimal reais) {           // card: cents as a string
    return reais.setScale(2, RoundingMode.UNNECESSARY).movePointRight(2).toPlainString();
}
static BigDecimal toPixReais(BigDecimal reais) {      // PIX: reais as a decimal
    return reais.setScale(2, RoundingMode.UNNECESSARY);
}"""),
}


def hl_json(src):
    out = []
    tok = re.compile(r'("(?:[^"\\]|\\.)*")(\s*:)?|(-?\b\d+(?:\.\d+)?\b)|\b(true|false|null)\b|([{}\[\],:])|(\s+)|(.)', re.S)
    for m in tok.finditer(src):
        s, colon, num, kw, punct, ws, other = m.groups()
        if s is not None:
            cls = "k" if colon else "s"
            out.append(f'<span class="t-{cls}">{html.escape(s)}</span>' + (html.escape(colon) if colon else ""))
        elif num is not None:
            out.append(f'<span class="t-n">{num}</span>')
        elif kw is not None:
            out.append(f'<span class="t-b">{kw}</span>')
        else:
            out.append(html.escape(punct or ws or other))
    return "".join(out)


def hl_generic(src, lang):
    esc = html.escape(src)
    if lang in ("bash", "http"):
        esc = re.sub(r'(&#x27;[^\n]*?&#x27;|&quot;[^&\n]*?&quot;)', r'<span class="t-s">\1</span>', esc)
        esc = re.sub(r'(?m)(#[^\n]*)$', r'<span class="t-c">\1</span>', esc)
    if lang == "http":
        esc = re.sub(r'(?m)^(GET|POST|PUT|PATCH|DELETE)( )', r'<span class="t-k">\1</span>\2', esc)
    if lang == "java":
        esc = re.sub(r'(?m)(//[^\n]*)$', r'<span class="t-c">\1</span>', esc)
        esc = re.sub(r'\b(static|return|new)\b', r'<span class="t-k">\1</span>', esc)
    return esc


def code_block(name):
    lang, src = CODE[name]
    body = hl_json(src) if lang == "json" else hl_generic(src, lang)
    return (f'<figure class="code"><figcaption><span>{lang.upper()}</span>'
            f'<button type="button" class="copy" data-copy>COPY</button></figcaption>'
            f'<pre><code>{body}</code></pre></figure>')


def render_lang(lang):
    src = open(os.path.join(HERE, f"content_{lang}.html"), encoding="utf-8").read()
    src = src.replace('id="§', f'id="{lang}-').replace('href="#§', f'href="#{lang}-')
    src = re.sub(r"\{CODE:(\w+)\}", lambda m: code_block(m.group(1)), src)
    toc = []
    for m in re.finditer(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', src):
        label = re.sub("<[^>]+>", "", re.sub(r'<span class="n">.*?</span>', "", m.group(2)))
        toc.append(f'<li><a href="#{m.group(1)}">{label}</a></li>')
    return src, "".join(toc)


def main():
    css = open(os.path.join(HERE, "page.css"), encoding="utf-8").read()
    shell = open(os.path.join(HERE, "shell.html"), encoding="utf-8").read()
    blocks, tocs, ids = [], [], []
    for l, bcp in LANGS:
        body, toc = render_lang(l)
        ids.append([re.sub(rf"^{l}-", "", i) for i in re.findall(r'<h2 id="([^"]+)"', body)])
        blocks.append(f'<div class="lang" data-lang="{l}" lang="{bcp}">{body}</div>')
        tocs.append(f'<ol class="toc-list" data-lang="{l}" lang="{bcp}">{toc}</ol>')
    if not (ids[0] == ids[1] == ids[2]):
        raise SystemExit(f"section ids differ between languages: {ids}")
    page = shell.replace("/*CSS*/", css).replace("<!--CONTENT-->", "\n".join(blocks)).replace("<!--TOC-->", "\n".join(tocs))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("sections", len(ids[0]), "bytes", len(page.encode()))


if __name__ == "__main__":
    main()
