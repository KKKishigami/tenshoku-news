/**
 * ゲームプレス - main.js
 */

const ARTICLES = [
  {
    id: "article-001",
    title: "マリオカート ワールド 発売直前レポート：Switch 2の幕開けを飾る期待作",
    cat: "Switch",
    date: "2026-03-29",
    img: "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["Switch 2", "マリオカート", "任天堂", "レース"],
    platforms: ["Switch 2"]
  },
  {
    id: "article-002",
    title: "Nintendo Switch 2 発売まであと数日！スペック・新機能・対応タイトルを総まとめ",
    cat: "ゲームニュース",
    date: "2026-03-28",
    img: "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["Switch 2", "任天堂", "新ハード", "ニュース"],
    platforms: ["Switch 2"]
  },
  {
    id: "article-003",
    title: "【レビュー】モンスターハンターワイルズ：シリーズ最高傑作か？40時間プレイして分かったこと",
    cat: "ゲームレビュー",
    date: "2026-03-27",
    img: "https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["モンハン", "PS5", "PC", "レビュー", "カプコン"],
    platforms: ["PS5", "PC"]
  },
  {
    id: "article-004",
    title: "Elden Ring: Nightreign 体験版レポート：協力プレイで変わる魂ゲーの新境地",
    cat: "PS5/PS4",
    date: "2026-03-26",
    img: "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["エルデンリング", "フロム", "PS5", "Xbox", "協力プレイ"],
    platforms: ["PS5", "Xbox", "PC"]
  },
  {
    id: "article-005",
    title: "PlayStation 5 Pro 購入者レビュー：通常PS5との違いは？4Kゲーマー必見",
    cat: "PS5/PS4",
    date: "2026-03-25",
    img: "https://images.unsplash.com/photo-1607853202273-797f1c22a38e?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["PS5 Pro", "ソニー", "ハードウェア", "4K"],
    platforms: ["PS5"]
  },
  {
    id: "article-006",
    title: "原神 Ver.5.x 新キャラ・新エリア完全解説：無課金でも楽しめる？",
    cat: "スマホゲーム",
    date: "2026-03-24",
    img: "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["原神", "HoYoverse", "スマホ", "RPG", "無課金"],
    platforms: ["iOS", "Android", "PC"]
  },
  {
    id: "article-007",
    title: "ブルーアーカイブ 周年記念イベント攻略ガイド：報酬を全回収する方法",
    cat: "スマホゲーム",
    date: "2026-03-23",
    img: "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["ブルアカ", "nexon", "スマホ", "攻略", "イベント"],
    platforms: ["iOS", "Android"]
  },
  {
    id: "article-008",
    title: "【攻略】モンスターハンターワイルズ：序盤おすすめ武器種と最初に選ぶべきスタイル",
    cat: "攻略・ヒント",
    date: "2026-03-22",
    img: "https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["モンハン", "攻略", "武器", "初心者"],
    platforms: ["PS5", "PC"]
  },
  {
    id: "article-009",
    title: "Xbox Game Pass 2026年4月の新着タイトル発表：注目作3本を紹介",
    cat: "PC/Xbox",
    date: "2026-03-21",
    img: "https://images.unsplash.com/photo-1619715767536-6b1b52e9e8fe?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["Xbox", "Game Pass", "PC", "Microsoft", "サブスク"],
    platforms: ["Xbox", "PC"]
  },
  {
    id: "article-010",
    title: "崩壊：スターレイル 最新アップデート情報：新キャラ「火主」実装と限定ガチャ解説",
    cat: "スマホゲーム",
    date: "2026-03-20",
    img: "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["スターレイル", "HoYoverse", "スマホ", "ガチャ", "最新情報"],
    platforms: ["iOS", "Android", "PC"]
  },
  {
    id: "article-011",
    title: "スマホゲームとコンシューマーの垣根がなくなる？クロスプレイ対応タイトルが急増中",
    cat: "ゲームコラム",
    date: "2026-03-19",
    img: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["クロスプレイ", "業界動向", "コラム"],
    platforms: []
  },
  {
    id: "article-012",
    title: "ゲーム業界ニュースまとめ（3月第4週）：Switch 2値下げ噂・大手スタジオ買収報道など",
    cat: "ゲームニュース",
    date: "2026-03-18",
    img: "https://images.unsplash.com/photo-1580327344181-c1163234e5a0?w=600&h=338&fit=crop&auto=format&q=80",
    tags: ["週刊まとめ", "業界ニュース", "Switch 2"],
    platforms: []
  }
];

const TICKER_ITEMS = [
  "🎮 Nintendo Switch 2、4月3日いよいよ発売！マリオカート ワールドが同時リリース",
  "📱 原神 Ver.5.xアップデート配信中 — 新エリア・新キャラが追加",
  "🏆 モンスターハンターワイルズ 累計出荷900万本突破",
  "🔥 Elden Ring: Nightreign 体験版が好評 — 正式版は5月リリース予定",
  "💻 Xbox Game Pass 4月ラインナップ発表 — 話題の新作3本追加"
];

const PER_PAGE = 9;
let currentCat = "all";
let currentPage = 1;

function formatDate(str) {
  const [y, m, d] = str.split("-");
  return `${y}年${m}月${d}日`;
}

function platformBadge(p) {
  const map = {
    "PS5": "badge-ps5", "PS4": "badge-ps5",
    "Switch": "badge-switch", "Switch 2": "badge-switch",
    "PC": "badge-pc", "Xbox": "badge-xbox",
    "iOS": "badge-mobile", "Android": "badge-mobile"
  };
  const cls = map[p] || "badge-news";
  return `<span class="platform-badge ${cls}">${p}</span>`;
}

function renderArticles() {
  const grid = document.getElementById("articles-grid");
  if (!grid) return;

  const filtered = currentCat === "all"
    ? ARTICLES
    : ARTICLES.filter(a => a.cat === currentCat);

  const total = filtered.length;
  const totalPages = Math.ceil(total / PER_PAGE);
  if (currentPage > totalPages) currentPage = 1;

  const start = (currentPage - 1) * PER_PAGE;
  const paged = filtered.slice(start, start + PER_PAGE);

  if (paged.length === 0) {
    grid.innerHTML = '<p class="no-articles">このカテゴリの記事はありません。</p>';
    renderPagination(0, 0);
    return;
  }

  grid.innerHTML = paged.map(a => `
    <article class="article-card">
      <a href="articles/${a.id}.html">
        <img class="card-thumb" src="${a.img}" alt="${a.title}" loading="lazy">
        <div class="card-body">
          <div class="card-meta">
            <span class="card-cat">${a.cat}</span>
            <span class="card-date">${formatDate(a.date)}</span>
          </div>
          <h2 class="card-title">${a.title}</h2>
          <div class="card-tags">
            ${a.platforms.slice(0,2).map(platformBadge).join("")}
          </div>
        </div>
      </a>
    </article>
  `).join("");

  renderPagination(totalPages, currentPage);
}

function renderPagination(totalPages, current) {
  const nav = document.getElementById("pagination");
  if (!nav) return;
  if (totalPages <= 1) { nav.innerHTML = ""; return; }

  let html = "";
  if (current > 1) html += `<button onclick="goPage(${current - 1})">‹ 前へ</button>`;
  for (let i = 1; i <= totalPages; i++) {
    html += `<button class="${i === current ? "active" : ""}" onclick="goPage(${i})">${i}</button>`;
  }
  if (current < totalPages) html += `<button onclick="goPage(${current + 1})">次へ ›</button>`;
  nav.innerHTML = html;
}

function goPage(p) {
  currentPage = p;
  renderArticles();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => { t.classList.remove("active"); t.setAttribute("aria-selected", "false"); });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      currentCat = btn.dataset.cat;
      currentPage = 1;
      renderArticles();
    });
  });
}

function initURLCat() {
  const params = new URLSearchParams(window.location.search);
  const cat = params.get("cat");
  if (cat) {
    const btn = document.querySelector(`[data-cat="${cat}"]`);
    if (btn) btn.click();
  }
}

function initTicker() {
  const el = document.getElementById("news-ticker-text");
  if (!el) return;
  let i = 0;
  el.textContent = TICKER_ITEMS[0];
  setInterval(() => {
    i = (i + 1) % TICKER_ITEMS.length;
    el.style.opacity = "0";
    setTimeout(() => {
      el.textContent = TICKER_ITEMS[i];
      el.style.opacity = "1";
    }, 300);
  }, 5000);
  el.style.transition = "opacity 0.3s";
}

function initHamburger() {
  const btn = document.querySelector(".hamburger");
  const nav = document.querySelector(".header-nav");
  if (!btn || !nav) return;
  btn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", open);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderArticles();
  initTabs();
  initURLCat();
  initTicker();
  initHamburger();
});
