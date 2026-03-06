/**
 * 転職プレス — main.js
 * 記事一覧の表示・カテゴリフィルタ・ページネーション
 */

(function () {
  'use strict';

  var ARTICLES_PER_PAGE = 8;
  var currentCat = 'all';
  var currentPage = 1;
  var allArticles = [];

  /* ── 初期化 ─────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    fetchManifest();
    setupTabs();
    setupMobileMenu();
  });

  /* ── manifest.json 読み込み ─────────────── */
  function fetchManifest() {
    var grid = document.getElementById('articles-grid');
    if (!grid) return;

    fetch('articles/manifest.json?v=' + Date.now())
      .then(function (res) {
        if (!res.ok) throw new Error('manifest not found');
        return res.json();
      })
      .then(function (data) {
        allArticles = (data.articles || []).sort(function (a, b) {
          return new Date(b.date) - new Date(a.date);
        });
        renderArticles();
        updateSidebarCount();
      })
      .catch(function (err) {
        console.warn('manifest error:', err);
        grid.innerHTML = '<p class="no-articles">記事を読み込めませんでした。</p>';
      });
  }

  /* ── カテゴリフィルタ適用後の記事配列 ────── */
  function filteredArticles() {
    if (currentCat === 'all') return allArticles;
    return allArticles.filter(function (a) { return a.category === currentCat; });
  }

  /* ── 記事カードを描画 ────────────────────── */
  function renderArticles() {
    var grid = document.getElementById('articles-grid');
    if (!grid) return;

    var list = filteredArticles();
    var total = list.length;
    var pages = Math.ceil(total / ARTICLES_PER_PAGE);
    if (currentPage > pages) currentPage = 1;

    var start = (currentPage - 1) * ARTICLES_PER_PAGE;
    var slice = list.slice(start, start + ARTICLES_PER_PAGE);

    if (slice.length === 0) {
      grid.innerHTML = '<p class="no-articles">この条件の記事はまだありません。</p>';
      renderPagination(0, 0);
      return;
    }

    grid.innerHTML = slice.map(cardHTML).join('');
    renderPagination(total, pages);
    grid.style.opacity = 0;
    requestAnimationFrame(function () {
      grid.style.transition = 'opacity 0.3s';
      grid.style.opacity = 1;
    });
  }

  /* ── カードHTML生成 ─────────────────────── */
  var CAT_ICONS = {
    'IT転職':        '💻',
    '医療転職':      '🏥',
    'ハイクラス転職':  '👔',
    '転職コラム':    '📝',
    '金融・保険転職':  '💰',
    '製造・メーカー転職': '🏭',
    '介護・福祉転職':  '🤝',
    '外資系転職':    '🌐',
    '士業・専門職転職': '⚖️'
  };

  function cardHTML(a) {
    var icon  = CAT_ICONS[a.category] || '📄';
    var slug  = a.category ? a.category.replace(/\s/g, '') : '';
    var date  = formatDate(a.date);
    var desc  = a.description || '';
    var link  = 'articles/' + a.filename;
    var thumb = a.thumbnail
      ? '<img src="' + esc(a.thumbnail) + '" alt="' + esc(a.title) + '" loading="lazy">'
      : '<span class="card-thumb-icon">' + icon + '</span>';
    var newBadge = a.is_new ? '<span class="new-badge">NEW!</span>' : '';

    return [
      '<article class="article-card">',
      '  <a href="' + link + '" class="card-thumb" aria-label="' + esc(a.title) + '">',
      '    ' + thumb,
      '    ' + newBadge,
      '  </a>',
      '  <div class="card-body">',
      '    <div class="card-meta">',
      '      <span class="cat-badge cat-' + esc(slug) + '">' + esc(a.category) + '</span>',
      '      <time class="card-date" datetime="' + esc(a.date) + '">' + date + '</time>',
      '    </div>',
      '    <h2 class="card-title"><a href="' + link + '">' + esc(a.title) + '</a></h2>',
      '    <p class="card-desc">' + esc(desc) + '</p>',
      '    <a href="' + link + '" class="card-link">続きを読む →</a>',
      '  </div>',
      '</article>'
    ].join('\n');
  }

  /* ── ページネーション ────────────────────── */
  function renderPagination(total, pages) {
    var wrap = document.getElementById('pagination');
    if (!wrap) return;
    if (pages <= 1) { wrap.innerHTML = ''; return; }

    var WINDOW = 4;
    var half   = Math.floor(WINDOW / 2);
    var start  = Math.max(1, currentPage - half);
    var end    = Math.min(pages, start + WINDOW - 1);
    start      = Math.max(1, end - WINDOW + 1);   // 末尾に寄ったとき先頭を再計算

    var html = '';
    if (currentPage > 1) {
      html += '<button class="page-btn" data-p="' + (currentPage - 1) + '">‹</button>';
    }
    for (var i = start; i <= end; i++) {
      html += '<button class="page-btn' + (i === currentPage ? ' active' : '') +
              '" data-p="' + i + '">' + i + '</button>';
    }
    if (currentPage < pages) {
      html += '<button class="page-btn" data-p="' + (currentPage + 1) + '">›</button>';
    }
    wrap.innerHTML = html;
    wrap.querySelectorAll('.page-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        currentPage = parseInt(this.dataset.p);
        renderArticles();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  /* ── タブ切り替え ───────────────────────── */
  function setupTabs() {
    var tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('active'); });
        this.classList.add('active');
        currentCat  = this.dataset.cat || 'all';
        currentPage = 1;
        renderArticles();
      });
    });
  }

  /* ── サイドバー記事数更新 ──────────────── */
  function updateSidebarCount() {
    var el = document.getElementById('total-count');
    if (el) el.textContent = allArticles.length;
  }

  /* ── モバイルメニュー ──────────────────── */
  function setupMobileMenu() {
    var btn = document.querySelector('.hamburger');
    var nav = document.querySelector('.header-nav');
    if (!btn || !nav) return;

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = nav.classList.toggle('nav-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // 外側クリックで閉じる
    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !nav.contains(e.target)) {
        nav.classList.remove('nav-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    // ナビ内リンクをタップしたら閉じる
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('nav-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── ユーティリティ ─────────────────────── */
  function formatDate(str) {
    if (!str) return '';
    var d = new Date(str);
    if (isNaN(d)) return str;
    return d.getFullYear() + '年' +
           (d.getMonth() + 1) + '月' +
           d.getDate() + '日';
  }

  function esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

})();
