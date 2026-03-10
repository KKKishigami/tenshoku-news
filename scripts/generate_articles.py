#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
転職プレス - 毎日記事自動生成スクリプト (Gemini API)

Usage: python scripts/generate_articles.py
Required env: GITHUB_TOKEN
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
SITEMAP_PATH = os.path.join(BASE_DIR, "sitemap.xml")
BASE_URL     = "https://tenshoku-press.com"
GA_ID        = "G-RW22NSV162"

TODAY     = date.today()
TODAY_STR = TODAY.strftime("%Y%m%d")
TODAY_ISO = TODAY.isoformat()

AD_HTML = '''\
<div class="pr-ad-section">
  <p class="pr-label">PR</p>
  <div class="pr-ad-row">
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+95U6OQ+5UK0+5YZ75" rel="nofollow"><img border="0" width="300" height="250" alt="" src="https://www20.a8.net/svt/bgt?aid=260228888554&wid=002&eno=01&mid=s00000027288001003000&mc=1"></a><img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4AXLW8+95U6OQ+5UK0+5YZ75" alt=""></div>
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+8XI47U+5BJK+5ZEMP" rel="nofollow"><img border="0" width="300" height="250" alt="" src="https://www27.a8.net/svt/bgt?aid=260228888540&wid=002&eno=01&mid=s00000024824001005000&mc=1"></a><img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4AXLW8+8XI47U+5BJK+5ZEMP" alt=""></div>
  </div>
</div>'''

IN_ARTICLE_AD = '''\
<div class="pr-ad-section">
  <p class="pr-label">PR</p>
  <div class="pr-ad-row">
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+95U6OQ+5UK0+5YZ75" rel="nofollow"><img border="0" width="300" height="250" alt="" src="https://www20.a8.net/svt/bgt?aid=260228888554&wid=002&eno=01&mid=s00000027288001003000&mc=1"></a><img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4AXLW8+95U6OQ+5UK0+5YZ75" alt=""></div>
    <div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+8XI47U+5BJK+5ZEMP" rel="nofollow"><img border="0" width="300" height="250" alt="" src="https://www27.a8.net/svt/bgt?aid=260228888540&wid=002&eno=01&mid=s00000024824001005000&mc=1"></a><img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4AXLW8+8XI47U+5BJK+5ZEMP" alt=""></div>
  </div>
</div>'''

SIDEBAR_AD_BLOCK = '''\
<div class="sidebar-block"><p style="font-size:0.7rem;color:#718096;font-weight:700;letter-spacing:0.08em;border:1px solid #cbd5e0;border-radius:3px;padding:1px 6px;display:inline-block;margin-bottom:0.8rem;">PR</p><div class="pr-ad-row" style="flex-direction:column;align-items:flex-start;gap:0.5rem;"><div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+8Y3JTM+50U0+5ZMCH" rel="nofollow"><img border="0" width="300" height="250" alt="安定のお仕事" src="https://www24.a8.net/svt/bgt?aid=260228888541&wid=002&eno=01&mid=s00000023436001006000&mc=1"></a><img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=4AXLW8+8Y3JTM+50U0+5ZMCH" alt=""></div><div class="pr-ad-item"><a href="https://px.a8.net/svt/ejp?a8mat=4AXLW8+97MHI2+5D9I+HVV0H" rel="nofollow"><img border="0" width="300" height="250" alt="テックゲート転職" src="https://www29.a8.net/svt/bgt?aid=260228888557&wid=002&eno=01&mid=s00000025047003004000&mc=1"></a><img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=4AXLW8+97MHI2+5D9I+HVV0H" alt=""></div></div></div>'''

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

CATEGORY_INSTRUCTIONS = {
    "IT転職": (
        "- プログラミング言語別平均年収データを含める（例：Python系エンジニア平均年収680万円など）\n"
        "- リモートワーク求人の割合に言及（例：IT求人の約60%がリモート可など）\n"
        "- 未経験からの転職可否と必要なスキル・学習期間を明記"
    ),
    "医療転職": (
        "- 職種別（看護師・薬剤師・理学療法士等）の需要データを含める\n"
        "- 勤務形態（常勤・パート・派遣）の違いと給与差を解説\n"
        "- 必要な資格要件と取得難易度を明記"
    ),
    "ハイクラス転職": (
        "- 年収600万以上の求人数トレンドと前年比を含める\n"
        "- 業界別のハイクラス需要（コンサル・金融・IT等）を解説\n"
        "- ヘッドハンティング・スカウト事例と成功のポイントを含める"
    ),
    "金融・保険転職": (
        "- 証券・銀行・保険別の採用動向と平均年収データを含める\n"
        "- フィンテック関連職の需要増加データに言及\n"
        "- 資格（FP・証券外務員等）の有無による年収差を具体的に示す"
    ),
    "製造・メーカー転職": (
        "- EV・半導体・DX関連の求人増加データを含める\n"
        "- 技術系エンジニアの人材不足状況と採用競争を解説\n"
        "- 地方求人と都市部求人の待遇比較を含める"
    ),
    "介護・福祉転職": (
        "- 介護職の人手不足データ（何万人不足か）を具体的に含める\n"
        "- 処遇改善加算の影響と給与改善の実態を解説\n"
        "- 資格なしOK求人の割合と無資格からのキャリアパスを明記"
    ),
    "外資系転職": (
        "- 英語力レベル別（TOEIC点数目安）の求人数と年収を含める\n"
        "- 外資系の平均年収と日系企業との具体的な比較データを示す\n"
        "- 日本進出している主要外資系企業の採用動向に言及"
    ),
    "士業・専門職転職": (
        "- 弁護士・会計士・税理士の需要データと求人数トレンドを含める\n"
        "- インハウス（企業内弁護士・企業内税理士等）転職のトレンドを解説\n"
        "- 資格別の年収レンジを具体的な数字で示す"
    ),
}


def build_prompt(cat, related):
    """プロンプトを構築"""
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

    cat_instruction = CATEGORY_INSTRUCTIONS.get(cat["name"], "- カテゴリの最新動向と具体的な数字・統計を含める")

    return f"""あなたは転職専門メディア「転職プレス」のプロSEOライターです。
{cat["name"]}に関する記事を以下の条件で作成してください。

【必須条件】
- 2026年の最新転職市場トレンドと具体的な統計・数字を必ず含める
  例：「〇〇職の平均年収は△△万円（2026年調査）」「転職成功率が□□%上昇」など
- 本文の文字数：2000文字以上（日本語）
- 読者の悩みを冒頭で明示する
- 構成は以下を厳守：
  1. リード文（読者の悩みに共感し、この記事で解決できることを明示）
  2. 「この記事でわかること」ボックス（3〜5項目のリスト）
  3. h2見出し（4〜6個）、各h2の下にh3や詳細本文
  4. FAQ（よくある質問）セクション（3問以上）
  5. まとめ（次のアクションを促すCTA文を含める）

【カテゴリ別専門データの追加】
{cat_instruction}

【内部リンク】
{link_instruction}

【出力形式】
以下のJSON形式のみで出力してください（コードブロック記号不要）:
{{
  "title": "記事タイトル（40〜60文字、検索キーワードを含む）",
  "description": "meta description（100〜120文字、検索者向けの要約）",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"],
  "body_html": "記事本文HTML。必ず以下を含めること：①冒頭に読者の悩みへの共感文、②<div class='article-points'><p><strong>この記事でわかること</strong></p><ul><li>項目</li></ul></div>、③h2/h3/p/ul/ol/strong/aタグを使った本文（数字・統計を含む）、④<div class='faq-section'><h2>よくある質問</h2><div class='faq-item'><p class='faq-q'>Q. 質問</p><p class='faq-a'>A. 回答</p></div></div>、⑤<div class='article-cta'><h2>まとめ</h2><p>内容</p><a href='../ranking.html'>転職サービスを比較する</a></div>"
}}"""


# (model, api_version) の組み合わせ。上から順に試す
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"
GITHUB_MODEL = "gpt-4o-mini"


def call_gemini(api_key, prompt, retries=2):
    """GitHub Models API を呼び出し、JSON をパースして返す"""
    body = json.dumps({
        "model": GITHUB_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                GITHUB_MODELS_ENDPOINT,
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
def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def insert_ad_in_body(body_html):
    """body_html内の2番目のh2見出しの後ろにIN_ARTICLE_ADを挿入"""
    count = 0
    pos = 0
    while True:
        found = body_html.find('</h2>', pos)
        if found == -1:
            break
        count += 1
        if count == 2:
            idx = found + 5
            return body_html[:idx] + IN_ARTICLE_AD + body_html[idx:]
        pos = found + 5
    return body_html


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
        f'          {SIDEBAR_AD_BLOCK}\n'
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
    body_html = insert_ad_in_body(data["body_html"])

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
  <meta property="og:url" content="{BASE_URL}/articles/{filename}">
  <meta property="og:site_name" content="転職プレス">
  <meta property="og:image" content="{thumb}">
  <meta property="og:image:width" content="600">
  <meta property="og:image:height" content="400">
  <meta property="og:image:alt" content="{title_esc}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_esc}">
  <meta name="twitter:description" content="{desc_esc}">
  <meta name="twitter:image" content="{thumb}">
  <link rel="canonical" href="{BASE_URL}/articles/{filename}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"Article","headline":"{title_esc}","datePublished":"{TODAY_ISO}","dateModified":"{TODAY_ISO}","author":{{"@type":"Organization","name":"転職プレス編集部"}},"publisher":{{"@type":"Organization","name":"転職プレス","logo":{{"@type":"ImageObject","url":"https://tenshoku-press.com/favicon.ico"}}}},"image":"{thumb}","url":"{BASE_URL}/articles/{filename}","description":"{desc_esc}","keywords":"{keywords}"}}
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
    (function(){{
      var btn=document.querySelector('.hamburger'), nav=document.querySelector('.header-nav');
      if(!btn||!nav) return;
      btn.addEventListener('click',function(e){{e.stopPropagation();var o=nav.classList.toggle('nav-open');btn.setAttribute('aria-expanded',o?'true':'false');}});
      document.addEventListener('click',function(e){{if(!btn.contains(e.target)&&!nav.contains(e.target)){{nav.classList.remove('nav-open');btn.setAttribute('aria-expanded','false');}}}});
    }})();
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



STATIC_URLS = [
    ("https://tenshoku-press.com/",                  "daily",   "1.0"),
    ("https://tenshoku-press.com/tools/",             "monthly", "0.85"),
    ("https://tenshoku-press.com/tools/nenshu.html",  "monthly", "0.85"),
    ("https://tenshoku-press.com/tools/rirekisho.html","monthly","0.85"),
    ("https://tenshoku-press.com/tools/mensetsu.html", "monthly","0.85"),
    ("https://tenshoku-press.com/ranking.html",        "weekly",  "0.9"),
    ("https://tenshoku-press.com/about.html",          "monthly", "0.5"),
    ("https://tenshoku-press.com/privacy.html",        "monthly", "0.3"),
]


def update_sitemap(manifest):
    """manifest.json から sitemap.xml を再生成する"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, pri in STATIC_URLS:
        lines += [
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{TODAY_ISO}</lastmod>",
            f"    <changefreq>{freq}</changefreq>",
            f"    <priority>{pri}</priority>",
            "  </url>",
        ]
    for i, art in enumerate(manifest["articles"]):
        lastmod = art.get("date", TODAY_ISO)
        loc = f"{BASE_URL}/articles/{art['filename']}"
        # 新しい記事ほど優先度を高く、古い記事は下げる
        priority = "0.9" if i < 8 else ("0.8" if i < 24 else "0.7")
        changefreq = "daily" if i < 8 else "weekly"
        lines += [
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{lastmod}</lastmod>",
            f"    <changefreq>{changefreq}</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  sitemap.xml 更新: {len(manifest['articles'])} 記事")


def main():
    api_key = os.environ.get("GITHUB_TOKEN")
    if not api_key:
        raise SystemExit("ERROR: GITHUB_TOKEN が設定されていません")

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
        except Exception as exc:
            print(f"    ERROR: {exc}")
            errors.append(cat["name"])
            continue

        # Gemini 無料枠のレート制限対策（最後の記事以外は待機）
        if i < len(CATEGORIES) - 1:
            time.sleep(4)

    # manifest 更新（新記事を先頭に追加）
    manifest["articles"] = new_entries + manifest["articles"]
    manifest["generated"] = f"{TODAY_ISO}T00:00:00+09:00"

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    update_sitemap(manifest)
    print(f"\n完了: {len(new_entries)} 記事を生成しました。")
    if errors:
        print(f"失敗カテゴリ: {', '.join(errors)}")


if __name__ == "__main__":
    main()
