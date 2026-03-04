#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
転職プレス - 毎日記事自動生成スクリプト (Gemini API)

Usage: python scripts/generate_articles.py
Required env: GROQ_API_KEY
"""

import os
import json
import re
import time
from datetime import date

import urllib.request
import urllib.error

# ── 定数 ─────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")
MANIFEST     = os.path.join(ARTICLES_DIR, "manifest.json")
BASE_URL     = "https://tenshoku-press.com"
GA_ID        = "G-RW22NSV162"

TODAY     = date.today()
TODAY_STR = TODAY.strftime("%Y%m%d")
TODAY_ISO = TODAY.isoformat()

AD_HTML = '''\
<div class="pr-ad-section">
  <p class="pr-label">広告</p>
  <div class="pr-ad-row">
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+8Y3JTM+50U0+5ZMCH" rel="nofollow"><img border="0" width="300" height="250" alt="安定のお仕事" src="https://www24.a8.net/svt/bgt?aid=260228888541&wid=002&eno=01&mid=s00000023436001006000&mc=1"></a><img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=4AXLW8+8Y3JTM+50U0+5ZMCH" alt=""></div>
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+97MHI2+5D9I+HVV0H" rel="nofollow"><img border="0" width="300" height="250" alt="テックゲート転職" src="https://www29.a8.net/svt/bgt?aid=260228888557&wid=002&eno=01&mid=s00000025047003004000&mc=1"></a><img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=4AXLW8+97MHI2+5D9I+HVV0H" alt=""></div>
  </div>
</div>'''

# ── カテゴリ設定 ──────────────────────────────────────────────────
CATEGORIES = [
    {
        "name": "IT転職",
        "slug": "it",
        "icon": "💻",
        "badge": "cat-IT転職",
        "sidebar": [
            ("IT特化No.1",  "レバテックキャリア",    "ITエンジニア専門の転職支援"),
            ("大手実績",     "リクルートエージェント", "IT求人数業界最大級"),
            ("ハイクラスIT", "Geekly",              "IT・ゲーム・Web業界専門"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "医療転職",
        "slug": "iryo",
        "icon": "🏥",
        "badge": "cat-医療転職",
        "sidebar": [
            ("看護師特化",   "マイナビ看護師",    "病院・クリニックの看護師求人多数"),
            ("医師・薬剤師",  "エムスリーキャリア", "医師・薬剤師・医療技術職の転職"),
            ("リハビリ職",   "PTOTSTワーカー",   "理学・作業・言語療法士の転職"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1584515933487-779824d29309?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "ハイクラス転職",
        "slug": "highclass",
        "icon": "👔",
        "badge": "cat-ハイクラス転職",
        "sidebar": [
            ("スカウト型No.1", "ビズリーチ",              "年収800万超のハイクラス求人"),
            ("エグゼクティブ",  "リクルートダイレクトスカウト", "管理職・役員クラスの転職"),
            ("外資・コンサル",  "JACリクルートメント",       "ハイクラス・外資系転職に強み"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "金融・保険転職",
        "slug": "finance",
        "icon": "💰",
        "badge": "cat-金融・保険転職",
        "sidebar": [
            ("業界特化No.1", "マイナビ金融",        "銀行・証券・保険専門の転職支援"),
            ("ハイクラス特化", "JACリクルートメント", "年収600万以上の金融求人"),
            ("士業・金融専門", "MS-Japan",          "会計・法律・金融のプロ転職"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1560472355-536de3962603?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "製造・メーカー転職",
        "slug": "mfg",
        "icon": "🏭",
        "badge": "cat-製造・メーカー転職",
        "sidebar": [
            ("製造業特化",  "メイテックネクスト",   "機械・電気・化学エンジニア専門"),
            ("業界最大級", "リクルートエージェント", "メーカー求人50万件以上"),
            ("技術系特化",  "タレントスクエア",     "理系エンジニア転職支援"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1565343077257-3d5e0b1e5073?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "介護・福祉転職",
        "slug": "care",
        "icon": "🤝",
        "badge": "cat-介護・福祉転職",
        "sidebar": [
            ("介護特化No.1", "カイゴジョブ",  "介護・福祉の求人数最大級"),
            ("手厚いサポート", "マイナビ介護職", "介護専任CAによる転職支援"),
            ("好条件求人多数", "きらケア",     "未経験・資格なしOKの求人多数"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1576765607924-3f7b8410a787?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1584515933487-779824d29309?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "外資系転職",
        "slug": "global",
        "icon": "🌐",
        "badge": "cat-外資系転職",
        "sidebar": [
            ("外資系No.1",  "JACリクルートメント", "外資・グローバル求人に強み"),
            ("ハイクラス特化", "ロバートハーフ",     "外資系管理職・専門職"),
            ("グローバル展開", "マイケルペイジ",     "英語力を活かした転職"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1444653614773-995cb1ef9efa?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
    {
        "name": "士業・専門職転職",
        "slug": "pro",
        "icon": "⚖️",
        "badge": "cat-士業・専門職転職",
        "sidebar": [
            ("士業専門",   "MS-Japan",         "弁護士・会計士・税理士の転職"),
            ("会計特化",   "ヒュープロ",         "会計・税務・法務のプロ転職"),
            ("専門職",    "JACリクルートメント", "専門職の高年収求人多数"),
        ],
        "thumbnails": [
            "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&h=400&fit=crop&auto=format&q=80",
            "https://images.unsplash.com/photo-1521791055366-0d553872952f?w=600&h=400&fit=crop&auto=format&q=80",
        ],
    },
]


# ── Gemini API ────────────────────────────────────────────────────

def build_prompt(cat, related):
    """Gemini へのプロンプトを構築"""
    if related:
        links_text = "\n".join(
            f'- {a["title"]}（リンク: {a["filename"]}）'
            for a in related
        )
        link_instruction = (
            "以下の既存記事へ内部リンクを本文中に2〜3個自然に組み込んでください:\n"
            + links_text
            + '\n内部リンクは <a href="ファイル名">テキスト</a> 形式で記述してください。'
        )
    else:
        link_instruction = "内部リンクは今回省略してください。"

    return f"""あなたは転職専門メディア「転職プレス」のSEOライターです。
{cat["name"]}に関する記事を以下の条件で作成してください。

【必須条件】
- 最新の転職市場トレンドを踏まえた2026年の内容を書いてください
- 本文の文字数：1500文字以上（日本語）
- SEOキーワードを自然に含める
- 構成：リード文 → h2見出し（3〜5個） → 各h2の下にh3や詳細本文 → まとめ
- {link_instruction}

【出力形式】
以下のJSON形式のみで出力してください（コードブロック記号不要）:
{{
  "title": "記事タイトル（40〜60文字、検索キーワードを含む）",
  "description": "meta description（100〜120文字、検索者向けの要約）",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"],
  "body_html": "記事本文のHTML文字列。h2/h3/p/ul/ol/strong/aタグを使用。改行は\\nで表現。"
}}"""


# (model, api_version) の組み合わせ。上から順に試す
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = "llama-3.3-70b-versatile"


def call_gemini(api_key, prompt, retries=2):
    """Groq API を呼び出し、JSON をパースして返す"""
    body = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                GROQ_ENDPOINT,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"].strip()
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
            return json.loads(text)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            exc_msg = f"HTTP {e.code}: {err_body}"
            if attempt < retries:
                print(f"    リトライ ({attempt + 1}/{retries}): {exc_msg[:150]}")
                time.sleep(8)
            else:
                raise Exception(exc_msg)
        except Exception as exc:
            if attempt < retries:
                print(f"    リトライ ({attempt + 1}/{retries}): {exc}")
                time.sleep(8)
            else:
                raise
    raise Exception(f"全モデル失敗: {last_exc}")
def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_sidebar_html(cat):
    items = ""
    for label, name, point in cat["sidebar"]:
        items += (
            f'              <a href="../ranking.html" class="affiliate-banner">\n'
            f'                <p class="aff-label">{label}</p>\n'
            f'                <p class="aff-name">{name}</p>\n'
            f'                <p class="aff-point">{point}</p>\n'
            f'              </a>\n'
        )
    return (
        f'          <div class="sidebar-block">\n'
        f'            <div class="sidebar-title">{cat["icon"]} {cat["name"]}におすすめ</div>\n'
        f'            <div class="sidebar-content">\n'
        f'              <div class="disclaimer">※ 本サイトはアフィリエイトプログラムを利用しています</div>\n'
        f'{items}'
        f'              <a href="../ranking.html" class="btn-register" style="display:block;text-align:center;margin-top:0.5rem;">転職サイト比較を見る →</a>\n'
        f'            </div>\n'
        f'          </div>'
    )


def build_related_html(cat, related):
    items = ""
    for art in related[:3]:
        short = art["title"][:28] + "…" if len(art["title"]) > 28 else art["title"]
        items += (
            f'                <li class="rank-item">'
            f'<a href="{art["filename"]}" style="font-size:0.85rem;font-weight:600;color:#1a3a5c;">{short}</a>'
            f'</li>\n'
        )
    items += (
        f'                <li class="rank-item">'
        f'<a href="../index.html?cat={cat["name"]}" style="font-size:0.85rem;font-weight:600;color:#1a3a5c;">'
        f'{cat["name"]}の記事一覧を見る</a>'
        f'</li>\n'
    )
    return (
        f'          <div class="sidebar-block">\n'
        f'            <div class="sidebar-title">📰 関連記事</div>\n'
        f'            <div class="sidebar-content">\n'
        f'              <ul class="rank-list">\n'
        f'{items}'
        f'              </ul>\n'
        f'            </div>\n'
        f'          </div>'
    )


def build_article_html(cat, slug, data, related, thumb):
    """完全な記事 HTML を生成して返す"""
    filename  = f"{slug}-{TODAY_STR}.html"
    title_esc = _esc(data["title"])
    desc_esc  = _esc(data["description"])
    keywords  = ",".join(data.get("keywords", [cat["name"]]))
    pub_ja    = f"{TODAY.year}年{TODAY.month}月{TODAY.day}日"
    sidebar   = build_sidebar_html(cat)
    rel_html  = build_related_html(cat, related)
    body_html = data["body_html"]

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_ID}');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{desc_esc}">
  <title>{title_esc} | 転職プレス</title>
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title_esc}">
  <meta property="og:description" content="{desc_esc}">
  <meta property="og:site_name" content="転職プレス">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{BASE_URL}/articles/{filename}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"Article","headline":"{title_esc}","datePublished":"{TODAY_ISO}","dateModified":"{TODAY_ISO}","author":{{"@type":"Organization","name":"転職プレス編集部"}},"publisher":{{"@type":"Organization","name":"転職プレス"}},"description":"{desc_esc}","keywords":"{keywords}"}}
  </script>
</head>
<body>
  <header id="site-header">
    <div class="header-inner">
      <a href="../index.html" class="site-logo">転職<span>プレス</span></a>
      <button class="hamburger" aria-label="メニュー" aria-expanded="false">☰</button>
      <nav class="header-nav">
        <a href="../index.html">ホーム</a>
        <a href="../index.html?cat=IT転職">IT転職</a>
        <a href="../index.html?cat=医療転職">医療転職</a>
        <a href="../index.html?cat=ハイクラス転職">ハイクラス</a>
        <a href="../index.html?cat=金融・保険転職">金融・保険</a>
        <a href="../index.html?cat=製造・メーカー転職">製造・メーカー</a>
        <a href="../index.html?cat=介護・福祉転職">介護・福祉</a>
        <a href="../index.html?cat=外資系転職">外資系</a>
        <a href="../index.html?cat=士業・専門職転職">士業・専門職</a>
        <a href="../ranking.html" class="nav-ranking">🏆 転職サイト比較</a>
        <a href="../tools/index.html" class="nav-tool-sm">🔧 ツール</a>
      </nav>
    </div>
  </header>
  <header class="article-header">
    <div class="container">
      <nav class="breadcrumb">
        <a href="../index.html">トップ</a> ›
        <a href="../index.html?cat={cat["name"]}">{cat["name"]}</a> ›
        <span>{data["title"][:30]}…</span>
      </nav>
      <div class="article-meta">
        <span class="cat-badge {cat["badge"]}">{cat["icon"]} {cat["name"]}</span>
        <time datetime="{TODAY_ISO}">{pub_ja}</time>
      </div>
      <h1>{data["title"]}</h1>
    </div>
  </header>
  <main>
    <div class="container">
      <div class="article-layout">
        <article class="article-body">
          <figure class="article-img">
            <img src="{thumb}" alt="{title_esc}" loading="lazy">
            <figcaption>Photo by Unsplash — {cat["name"]}の最新動向</figcaption>
          </figure>
          {body_html}
          <div class="article-share">
            <p class="share-title">この記事をシェアする</p>
            <div class="share-btns">
              <button class="share-btn share-x" onclick="shareX()">𝕏 でシェア</button>
              <button class="share-btn share-copy" onclick="copyURL()">🔗 URLをコピー</button>
            </div>
          </div>
          <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid #e2e8f0;">
            <a href="../index.html" style="color:#1a3a5c;font-weight:700;font-size:0.9rem;">← 記事一覧に戻る</a>
          </div>
        </article>
        <aside class="sidebar">
{sidebar}
{rel_html}
        </aside>
      </div>
    </div>
{AD_HTML}
  </main>
  <footer id="site-footer">
    <div class="footer-inner">
      <div>
        <div class="footer-logo">転職<span>プレス</span></div>
        <p class="footer-desc">IT・医療・金融・製造・介護・外資系・士業など幅広い転職情報をお届けするメディアです。</p>
      </div>
      <div>
        <p class="footer-heading">カテゴリ</p>
        <ul class="footer-links">
          <li><a href="../index.html?cat=IT転職">IT転職</a></li>
          <li><a href="../index.html?cat=医療転職">医療転職</a></li>
          <li><a href="../index.html?cat=ハイクラス転職">ハイクラス転職</a></li>
          <li><a href="../index.html?cat=金融・保険転職">金融・保険転職</a></li>
          <li><a href="../index.html?cat=製造・メーカー転職">製造・メーカー転職</a></li>
          <li><a href="../index.html?cat=介護・福祉転職">介護・福祉転職</a></li>
          <li><a href="../index.html?cat=外資系転職">外資系転職</a></li>
          <li><a href="../index.html?cat=士業・専門職転職">士業・専門職転職</a></li>
          <li><a href="../index.html?cat=転職コラム">転職コラム</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-heading">サイト情報</p>
        <ul class="footer-links">
          <li><a href="../ranking.html">転職サイト比較</a></li>
          <li><a href="../privacy.html">プライバシーポリシー</a></li>
          <li><a href="../about.html">サイトについて</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>本サイトはアフィリエイト広告を利用しています。&nbsp;|&nbsp;&copy; 2026 転職プレス All Rights Reserved.</p>
    </div>
  </footer>
  <script>
    function shareX() {{ var t=encodeURIComponent(document.title+' | 転職プレス'),u=encodeURIComponent(location.href); window.open('https://twitter.com/intent/tweet?text='+t+'&url='+u,'_blank'); }}
    function copyURL() {{ navigator.clipboard.writeText(location.href).then(function(){{ alert('URLをコピーしました'); }}); }}
  </script>
</body>
</html>'''


# ── メイン処理 ────────────────────────────────────────────────────

def get_related(manifest, category, exclude_filename, limit=3):
    """同カテゴリの既存記事を最大 limit 件返す"""
    result = []
    for art in manifest["articles"]:
        if art["category"] == category and art.get("filename") != exclude_filename:
            result.append(art)
            if len(result) >= limit:
                break
    return result


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: 環境変数 GROQ_API_KEY が設定されていません")

    # manifest 読み込み
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    # 前日以前のis_newフラグを全削除
    for art in manifest["articles"]:
        art.pop("is_new", None)

    new_entries = []
    errors = []

    for i, cat in enumerate(CATEGORIES):
        slug     = cat["slug"]
        filename = f"{slug}-{TODAY_STR}.html"
        filepath = os.path.join(ARTICLES_DIR, filename)

        # 既に当日記事があればスキップ（is_new だけ付与）
        if os.path.exists(filepath):
            print(f"[{i+1}/8] SKIP: {filename} (既に存在)")
            for art in manifest["articles"]:
                if art.get("filename") == filename:
                    art["is_new"] = True
            continue

        print(f"[{i+1}/8] {cat['name']} 記事を生成中...")

        related = get_related(manifest, cat["name"], filename)
        prompt  = build_prompt(cat, related)

        try:
            data = call_gemini(api_key, prompt)
        except Exception as exc:
            print(f"    ERROR: {exc}")
            errors.append(cat["name"])
            continue

        # サムネイルをローテーション
        thumb = cat["thumbnails"][TODAY.day % len(cat["thumbnails"])]

        html = build_article_html(cat, slug, data, related, thumb)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"    CREATED: {filename}")

        new_entries.append({
            "id":          f"{slug}-{TODAY_STR}",
            "title":       data["title"],
            "category":    cat["name"],
            "date":        TODAY_ISO,
            "description": data["description"],
            "filename":    filename,
            "thumbnail":   thumb,
            "tags":        data.get("keywords", [cat["name"]]),
            "is_new":      True,
        })

        # Gemini 無料枠のレート制限対策（最後の記事以外は待機）
        if i < len(CATEGORIES) - 1:
            time.sleep(4)

    # manifest 更新（新記事を先頭に追加）
    manifest["articles"] = new_entries + manifest["articles"]
    manifest["generated"] = f"{TODAY_ISO}T00:00:00+09:00"

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {len(new_entries)} 記事を生成しました。")
    if errors:
        print(f"失敗カテゴリ: {', '.join(errors)}")


if __name__ == "__main__":
    main()
