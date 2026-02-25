#!/usr/bin/env python3
"""
転職プレス — 記事自動生成スクリプト
Claude API を使って毎日新しい転職記事を生成し、manifest.json を更新する。

使い方:
  pip install anthropic
  export ANTHROPIC_API_KEY="your-key"
  python scripts/generate_articles.py
"""

import os
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic パッケージが必要です。pip install anthropic を実行してください。")
    sys.exit(1)


# ─── 設定 ────────────────────────────────────────────────────────────────────

ARTICLES_DIR = Path(__file__).parent.parent / "articles"
MANIFEST_PATH = ARTICLES_DIR / "manifest.json"
BASE_URL = "https://kkkishigami.github.io/tenshoku-news"
MODEL = "claude-opus-4-6"

# 記事テーマのローテーション（毎日1本生成）
ARTICLE_THEMES = [
    {"category": "IT転職",      "theme": "2025年のフロントエンドエンジニア需要と年収トレンド",       "tags": ["フロントエンド", "React", "年収", "IT転職"]},
    {"category": "医療転職",    "theme": "薬剤師の転職で年収アップを狙う方法【2025年版】",           "tags": ["薬剤師", "医療転職", "年収", "ドラッグストア"]},
    {"category": "IT転職",      "theme": "クラウドエンジニアのキャリアパスと資格の選び方",           "tags": ["AWS", "クラウド", "資格", "IT転職"]},
    {"category": "ハイクラス転職", "theme": "外資系コンサルへの転職を成功させる方法",               "tags": ["外資系", "コンサル", "ハイクラス", "MBA"]},
    {"category": "転職コラム",  "theme": "転職で失敗しないための企業選びの6つのチェックポイント",    "tags": ["企業選び", "転職失敗", "チェックリスト"]},
    {"category": "IT転職",      "theme": "AIエンジニアになるためのロードマップ【未経験者向け】",     "tags": ["AI", "機械学習", "未経験", "ロードマップ"]},
    {"category": "医療転職",    "theme": "医師の転職市場2025年：専門科別の需要と年収",              "tags": ["医師", "医療転職", "専門医", "年収"]},
    {"category": "ハイクラス転職", "theme": "スタートアップへの転職でストックオプションを活用する方法", "tags": ["スタートアップ", "ストックオプション", "ハイクラス"]},
    {"category": "IT転職",      "theme": "サイバーセキュリティエンジニアの年収と転職市場",          "tags": ["セキュリティ", "CISSP", "年収", "IT転職"]},
    {"category": "転職コラム",  "theme": "30代・40代の転職を成功させる戦略と注意点",               "tags": ["30代転職", "40代転職", "ミドル", "キャリア"]},
]


# ─── 記事生成プロンプト ────────────────────────────────────────────────────────

ARTICLE_PROMPT_TEMPLATE = """
あなたは転職情報メディア「転職プレス」の編集者です。
以下のテーマで、SEOに強い転職記事のコンテンツを生成してください。

テーマ: {theme}
カテゴリ: {category}

要件:
- 日本語で書く
- 文字数: 1200〜1800字程度（本文のみ）
- 見出し構成: h2見出しを3〜5個、必要に応じてh3を使用
- 具体的な数値・データを含める（年収相場、求人倍率、%など）
- 読者にとって実用的なアドバイスを含める
- 最後に「おすすめの転職エージェント」セクションを追加し、以下から2〜3つ紹介:
  - リクルートエージェント（業界最大級の求人数）
  - doda（デューダ）（求人数No.1クラス）
  - ビズリーチ（ハイクラス・スカウト型）
  - レバテックキャリア（ITエンジニア特化）
  - JACリクルートメント（外資・グローバル）
  - 看護roo!（看護師専門）
  - マイナビ看護師（医療転職）

出力形式（JSONで返してください）:
{{
  "title": "記事タイトル（30〜40字）",
  "description": "メタdescription（80〜100字）",
  "h2_sections": [
    {{
      "heading": "h2見出しテキスト",
      "content": "この見出しのHTML本文（<p>, <ul>, <li>, <h3>, <table>タグ使用可）"
    }}
  ],
  "highlight_points": ["ポイント1", "ポイント2", "ポイント3"],
  "warning_text": "注意点のテキスト（1〜2文）"
}}
"""


# ─── サイドバー・アフィリエイトマッピング ────────────────────────────────────

SIDEBAR_MAP = {
    "IT転職": {
        "title": "💻 IT転職におすすめ",
        "banners": [
            {"anchor": "levtech",  "label": "ITエンジニア特化",  "name": "レバテックキャリア",   "point": "技術理解の高いCA・高年収案件"},
            {"anchor": "rikunabi", "label": "業界最大級",        "name": "リクルートエージェント", "point": "50万件以上の求人・無料"},
        ]
    },
    "医療転職": {
        "title": "🏥 医療転職におすすめ",
        "banners": [
            {"anchor": "kangoro", "label": "看護師専門",       "name": "看護roo!（カンゴルー）", "point": "コンサルタントが看護師出身"},
            {"anchor": "mynavi",  "label": "求人数No.1クラス", "name": "マイナビ看護師",         "point": "全国対応・院内見学サポート"},
        ]
    },
    "ハイクラス転職": {
        "title": "👔 ハイクラス転職におすすめ",
        "banners": [
            {"anchor": "bizreach", "label": "スカウト型No.1",   "name": "ビズリーチ",          "point": "年収600万円以上・ハイクラス特化"},
            {"anchor": "jac",      "label": "外資系・グローバル", "name": "JACリクルートメント", "point": "外資・グローバル企業に強い"},
        ]
    },
    "転職コラム": {
        "title": "🏆 おすすめ転職エージェント",
        "banners": [
            {"anchor": "doda",     "label": "★★★★★ 総合評価", "name": "doda（デューダ）",       "point": "求人数No.1クラス・手厚いサポート"},
            {"anchor": "rikunabi", "label": "業界最大級",       "name": "リクルートエージェント", "point": "50万件以上の求人・全職種対応"},
        ]
    },
}

CAT_ICONS = {
    "IT転職":      "💻",
    "医療転職":    "🏥",
    "ハイクラス転職": "👔",
    "転職コラム":  "📝",
}

# ─── 画像マッピング（Unsplash / 商用利用無料）────────────────────────────────
# キーワード → Unsplash 直リンク
_IMG = "https://images.unsplash.com/photo-{id}?w=800&h=400&fit=crop&auto=format&q=80"

IMAGE_MAP = {
    # ── IT転職 ──────────────────────────────────────────────────────────────
    "フロントエンド":   _IMG.format(id="1587620962725-abab7fe55159"),  # MacBook with code
    "バックエンド":     _IMG.format(id="1461749280684-dccba630e2f6"),  # code on monitor
    "React":            _IMG.format(id="1587620962725-abab7fe55159"),
    "クラウド":         _IMG.format(id="1451187580459-43490279c0fa"),  # data center
    "AWS":              _IMG.format(id="1451187580459-43490279c0fa"),
    "Azure":            _IMG.format(id="1451187580459-43490279c0fa"),
    "セキュリティ":     _IMG.format(id="1550751827-4bd374c3f58b"),    # padlock/cyber
    "CISSP":            _IMG.format(id="1550751827-4bd374c3f58b"),
    "Python":           _IMG.format(id="1526374965328-7f61d4dc18c5"), # matrix code
    "AI":               _IMG.format(id="1555949963-aa79dcee981c"),    # neural network
    "機械学習":         _IMG.format(id="1555949963-aa79dcee981c"),
    "LLM":              _IMG.format(id="1555949963-aa79dcee981c"),
    "データ":           _IMG.format(id="1551288049-bebda4e38f71"),    # data analytics
    "エンジニア":       _IMG.format(id="1573164713714-d95e436ab8d6"), # developer at desk
    "プログラム":       _IMG.format(id="1461749280684-dccba630e2f6"),
    "未経験":           _IMG.format(id="1499750310107-5fef28a66643"), # person studying
    "ロードマップ":     _IMG.format(id="1499750310107-5fef28a66643"),
    # ── 医療転職 ────────────────────────────────────────────────────────────
    "看護師":           _IMG.format(id="1559757148-5c350d0d3c56"),    # smiling nurse
    "医師":             _IMG.format(id="1612349317150-e413f6a5b16d"), # doctor
    "薬剤師":           _IMG.format(id="1563213126-a4273aed2016"),    # pharmacy
    "ドラッグストア":   _IMG.format(id="1563213126-a4273aed2016"),
    "医療":             _IMG.format(id="1576091160399-112ba8d25d1d"), # healthcare worker
    "病院":             _IMG.format(id="1584432810601-6c7f27d2362b"), # hospital staff
    "介護":             _IMG.format(id="1576091160399-112ba8d25d1d"),
    # ── ハイクラス転職 ──────────────────────────────────────────────────────
    "コンサル":         _IMG.format(id="1600880292203-757bb62b4baf"), # business strategy
    "外資":             _IMG.format(id="1521791136064-7986c2920216"), # handshake
    "MBA":              _IMG.format(id="1521791136064-7986c2920216"),
    "スタートアップ":   _IMG.format(id="1559136555-9303baea8ebd"),    # startup office
    "ストックオプション": _IMG.format(id="1611974789855-9c2a0a7236a3"), # stock chart
    "年収1000万":       _IMG.format(id="1507003211169-0a1dd7228f2d"), # exec portrait
    "役員":             _IMG.format(id="1507003211169-0a1dd7228f2d"),
    "グローバル":       _IMG.format(id="1521791136064-7986c2920216"),
    # ── 転職コラム ──────────────────────────────────────────────────────────
    "面接":             _IMG.format(id="1573496359142-b8d87734a5a2"), # job interview
    "履歴書":           _IMG.format(id="1586281380349-632531db7ed4"), # resume writing
    "志望動機":         _IMG.format(id="1586281380349-632531db7ed4"),
    "企業選び":         _IMG.format(id="1542744173-8e7e53415bb0"),    # team discussion
    "30代":             _IMG.format(id="1499750310107-5fef28a66643"), # professional
    "40代":             _IMG.format(id="1499750310107-5fef28a66643"),
    "退職":             _IMG.format(id="1454165804606-c3d57bc86b40"), # desk meeting
    "転職活動":         _IMG.format(id="1454165804606-c3d57bc86b40"),
}

CATEGORY_DEFAULT_IMAGES = {
    "IT転職":         _IMG.format(id="1573164713714-d95e436ab8d6"),
    "医療転職":       _IMG.format(id="1584432810601-6c7f27d2362b"),
    "ハイクラス転職": _IMG.format(id="1560179707-f14e90ef3623"),
    "転職コラム":     _IMG.format(id="1454165804606-c3d57bc86b40"),
}


def pick_image_url(category: str, theme: str) -> str:
    """テーマ文字列のキーワードからUnsplash画像URLを返す。"""
    for keyword, url in IMAGE_MAP.items():
        if keyword in theme:
            return url
    return CATEGORY_DEFAULT_IMAGES.get(
        category,
        _IMG.format(id="1454165804606-c3d57bc86b40")
    )


# ─── HTML テンプレート ──────────────────────────────────────────────────────────

def build_article_html(article_id, title, description, category, pub_date,
                       highlight_points, sections, warning_text, sidebar_info,
                       related_articles, image_url=""):
    cat_icon = CAT_ICONS.get(category, "📄")
    cat_slug = category.replace(" ", "")
    date_formatted = datetime.strptime(pub_date, "%Y-%m-%d").strftime("%Y年%-m月%-d日") if sys.platform != "win32" else \
                     datetime.strptime(pub_date, "%Y-%m-%d").strftime("%Y年%#m月%#d日")

    # highlight points
    hl_items = "\n".join(f"              <li>{p}</li>" for p in highlight_points)

    # sections HTML（最初のh2直後に記事内画像を挿入）
    figure_html = f"""          <figure class="article-img">
            <img src="{image_url}" alt="{title}" loading="lazy">
            <figcaption>Photo by Unsplash</figcaption>
          </figure>""" if image_url else ""

    sections_html = []
    for i, sec in enumerate(sections, 1):
        sections_html.append(f"          <h2>{i}. {sec['heading']}</h2>")
        if i == 1 and figure_html:
            sections_html.append(figure_html)
        sections_html.append(f"          {sec['content']}")
    sections_str = "\n".join(sections_html)

    # warning box
    warning_html = f"""
          <div class="warning-box">
            <strong>⚠️ 注意点</strong>
            <p style="margin-top:0.5rem;margin-bottom:0;">{warning_text}</p>
          </div>
""" if warning_text else ""

    # sidebar banners
    banner_html = []
    for b in sidebar_info["banners"]:
        banner_html.append(f"""              <a href="../ranking.html#{b['anchor']}" class="affiliate-banner">
                <p class="aff-label">{b['label']}</p>
                <p class="aff-name">{b['name']}</p>
                <p class="aff-point">{b['point']}</p>
              </a>""")
    banners_str = "\n".join(banner_html)

    # related articles
    related_html = "\n".join(
        f"""                <li class="rank-item">
                  <a href="{r['filename']}" style="font-size:0.85rem;font-weight:600;color:#1a3a5c;">{r['title']}</a>
                </li>"""
        for r in related_articles[:2]
    )

    # JSON-LD keywords
    keywords = f"{category},{title[:20]}"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description}">
  <title>{title} | 転職プレス</title>

  <meta property="og:type"        content="article">
  <meta property="og:title"       content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:site_name"   content="転職プレス">
  <meta name="twitter:card"       content="summary_large_image">

  <link rel="canonical" href="{BASE_URL}/articles/{article_id}.html">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "datePublished": "{pub_date}",
    "dateModified": "{pub_date}",
    "author": {{ "@type": "Organization", "name": "転職プレス編集部" }},
    "publisher": {{ "@type": "Organization", "name": "転職プレス" }},
    "description": "{description}",
    "keywords": "{keywords}"
  }}
  </script>
</head>
<body>

  <header id="site-header">
    <div class="header-inner">
      <a href="../index.html" class="site-logo">転職<span>ナビ</span></a>
      <nav class="header-nav">
        <a href="../index.html">ホーム</a>
        <a href="../ranking.html" class="nav-ranking">🏆 転職サイト比較</a>
      </nav>
    </div>
  </header>

  <header class="article-header">
    <div class="container">
      <nav class="breadcrumb">
        <a href="../index.html">トップ</a> ›
        <a href="../index.html?cat={category}">{category}</a> ›
        <span>{title}</span>
      </nav>
      <div class="article-meta">
        <span class="cat-badge cat-{cat_slug}">{cat_icon} {category}</span>
        <time datetime="{pub_date}">{date_formatted}</time>
      </div>
      <h1>{title}</h1>
    </div>
  </header>

  <main>
    <div class="container">
      <div class="article-layout">

        <article class="article-body">

          <div class="highlight-box">
            <strong>📌 この記事のポイント</strong>
            <ul style="margin-top:0.5rem;padding-left:1.2rem;">
{hl_items}
            </ul>
          </div>

{sections_str}
{warning_html}
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
          <div class="sidebar-block">
            <div class="sidebar-title">{sidebar_info['title']}</div>
            <div class="sidebar-content">
{banners_str}
              <a href="../ranking.html" class="btn-register" style="display:block;text-align:center;margin-top:0.5rem;">転職サイト比較を見る →</a>
            </div>
          </div>
          <div class="sidebar-block">
            <div class="sidebar-title">📰 関連記事</div>
            <div class="sidebar-content">
              <ul class="rank-list">
{related_html}
              </ul>
            </div>
          </div>
        </aside>

      </div>
    </div>
  </main>

  <footer id="site-footer">
    <div class="footer-inner">
      <div>
        <div class="footer-logo">転職<span>ナビ</span></div>
        <p class="footer-desc">IT・医療・ハイクラスの最新転職情報をお届けするメディアです。</p>
      </div>
      <div>
        <p class="footer-heading">カテゴリ</p>
        <ul class="footer-links">
          <li><a href="../index.html">トップ</a></li>
          <li><a href="../index.html?cat=IT転職">IT転職</a></li>
          <li><a href="../index.html?cat=医療転職">医療転職</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-heading">サイト情報</p>
        <ul class="footer-links">
          <li><a href="../ranking.html">転職サイト比較</a></li>
          <li><a href="../privacy.html">プライバシーポリシー</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>本サイトはアフィリエイト広告を利用しています。&nbsp;|&nbsp;&copy; 2025 転職プレス All Rights Reserved.</p>
    </div>
  </footer>

  <script>
    function shareX() {{
      var text = encodeURIComponent(document.title + ' | 転職プレス');
      var url  = encodeURIComponent(location.href);
      window.open('https://twitter.com/intent/tweet?text=' + text + '&url=' + url, '_blank');
    }}
    function copyURL() {{
      navigator.clipboard.writeText(location.href).then(function() {{
        alert('URLをコピーしました');
      }});
    }}
  </script>
</body>
</html>
"""


# ─── manifest 更新 ──────────────────────────────────────────────────────────────

def load_manifest():
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"articles": []}


def save_manifest(manifest):
    manifest["generated"] = datetime.now().astimezone().isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"manifest.json を更新しました（合計 {len(manifest['articles'])} 件）")


def next_article_id(manifest):
    ids = [a["id"] for a in manifest["articles"]]
    nums = []
    for a_id in ids:
        m = re.search(r"(\d+)$", a_id)
        if m:
            nums.append(int(m.group(1)))
    return max(nums, default=0) + 1


def pick_theme(manifest):
    """使用済みテーマを避けて次のテーマを選ぶ"""
    used_titles = {a["title"] for a in manifest["articles"]}
    for theme in ARTICLE_THEMES:
        if theme["theme"] not in used_titles:
            return theme
    # 全部使い切ったら先頭から再利用
    return ARTICLE_THEMES[len(manifest["articles"]) % len(ARTICLE_THEMES)]


def get_related_articles(manifest, category, exclude_id):
    """同カテゴリ or 最新記事から関連記事を2件取得"""
    articles = manifest.get("articles", [])
    same_cat = [a for a in articles if a["category"] == category and a["id"] != exclude_id]
    others   = [a for a in articles if a["category"] != category and a["id"] != exclude_id]
    candidates = (same_cat + others)[:2]
    return [{"filename": a["filename"], "title": a["title"]} for a in candidates]


# ─── メイン処理 ────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: 環境変数 ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    manifest = load_manifest()

    theme_info = pick_theme(manifest)
    category   = theme_info["category"]
    theme      = theme_info["theme"]
    tags       = theme_info["tags"]
    pub_date   = date.today().isoformat()
    article_num = next_article_id(manifest)
    article_id  = f"article-{article_num:03d}"

    print(f"記事生成中: [{category}] {theme}")

    # Claude API 呼び出し
    prompt = ARTICLE_PROMPT_TEMPLATE.format(theme=theme, category=category)
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text

    # JSON 抽出
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        print("Error: Claude の応答から JSON を抽出できませんでした。")
        print(raw[:500])
        sys.exit(1)

    data = json.loads(json_match.group())
    title       = data.get("title", theme)
    description = data.get("description", "")
    sections    = data.get("h2_sections", [])
    highlights  = data.get("highlight_points", [])
    warning     = data.get("warning_text", "")

    sidebar_info = SIDEBAR_MAP.get(category, SIDEBAR_MAP["転職コラム"])
    related      = get_related_articles(manifest, category, article_id)
    image_url    = pick_image_url(category, theme)

    # HTML 生成 & 保存
    html = build_article_html(
        article_id=article_id,
        title=title,
        description=description,
        category=category,
        pub_date=pub_date,
        highlight_points=highlights,
        sections=sections,
        warning_text=warning,
        sidebar_info=sidebar_info,
        related_articles=related,
        image_url=image_url,
    )

    out_path = ARTICLES_DIR / f"{article_id}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"記事を保存しました: {out_path}")

    # manifest 更新
    manifest["articles"].insert(0, {
        "id":          article_id,
        "title":       title,
        "category":    category,
        "date":        pub_date,
        "description": description,
        "filename":    f"{article_id}.html",
        "thumbnail":   image_url,
        "tags":        tags,
    })
    save_manifest(manifest)

    # sitemap 更新（簡易）
    update_sitemap(manifest)


def update_sitemap(manifest):
    sitemap_path = MANIFEST_PATH.parent.parent / "sitemap.xml"
    urls = []
    urls.append(f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")
    urls.append(f"""  <url>
    <loc>{BASE_URL}/ranking.html</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""")
    for a in manifest["articles"]:
        urls.append(f"""  <url>
    <loc>{BASE_URL}/articles/{a['filename']}</loc>
    <lastmod>{a['date']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>\n"
    sitemap_path.write_text(xml, encoding="utf-8")
    print(f"sitemap.xml を更新しました（{len(manifest['articles'])} 記事）")


if __name__ == "__main__":
    main()
