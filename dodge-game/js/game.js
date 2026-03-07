'use strict';

// ============================================================
//  DODGE MASTER  |  HTML5 Canvas Action Game
//  Controls: Arrow keys / WASD / Mouse / Touch
// ============================================================

const canvas = document.getElementById('gameCanvas');
const ctx    = canvas.getContext('2d');

// ---- Canvas sizing ----
function resizeCanvas() {
  const maxW  = Math.min(window.innerWidth - 20, 460);
  const maxH  = Math.min(window.innerHeight - 140, 700);
  const side  = Math.min(maxW, Math.floor(maxH / 1.5));
  canvas.width  = side;
  canvas.height = Math.floor(side * 1.5);
}
resizeCanvas();
window.addEventListener('resize', () => {
  resizeCanvas();
  player.x = canvas.width / 2;
  player.y = canvas.height - 80;
  initStars();
});

// ---- Stage configs ----
const STAGES = [
  { spawnEvery: 100, baseSpeed: 2.5, types: ['circle'],                        scoreGoal: 600  },
  { spawnEvery: 80,  baseSpeed: 3.2, types: ['circle', 'square'],              scoreGoal: 1400 },
  { spawnEvery: 62,  baseSpeed: 4.0, types: ['circle', 'square', 'zigzag'],   scoreGoal: 2400 },
  { spawnEvery: 46,  baseSpeed: 5.0, types: ['circle', 'square', 'zigzag'],   scoreGoal: 3800 },
  { spawnEvery: 32,  baseSpeed: 6.2, types: ['circle', 'square', 'zigzag'],   scoreGoal: 5500 },
];

// ---- State ----
let state     = 'title';   // title | playing | stageclear | gameover
let score     = 0;
let stage     = 1;
let lives     = 3;
let frame     = 0;
let enemies   = [];
let particles = [];
let stars     = [];
let highScore = parseInt(localStorage.getItem('dodgeMasterHS') || '0', 10);

// ---- Player ----
const player = {
  x: canvas.width / 2,
  y: canvas.height - 80,
  r: 16,
  speed: 6,
  invincible: false,
  invTimer: 0,
  color: '#4ecdc4',
  trail: [],
};

// ---- Input ----
const keys = {};
let touchPt = null;

document.addEventListener('keydown', e => { keys[e.code] = true; });
document.addEventListener('keyup',   e => { keys[e.code] = false; });

canvas.addEventListener('mousemove', e => {
  const r = canvas.getBoundingClientRect();
  const scaleX = canvas.width  / r.width;
  const scaleY = canvas.height / r.height;
  touchPt = { x: (e.clientX - r.left) * scaleX, y: (e.clientY - r.top) * scaleY };
});
canvas.addEventListener('mouseleave', () => { touchPt = null; });

canvas.addEventListener('touchmove', e => {
  e.preventDefault();
  const r  = canvas.getBoundingClientRect();
  const t  = e.touches[0];
  const scaleX = canvas.width  / r.width;
  const scaleY = canvas.height / r.height;
  touchPt = { x: (t.clientX - r.left) * scaleX, y: (t.clientY - r.top) * scaleY };
}, { passive: false });
canvas.addEventListener('touchend',   () => { touchPt = null; });

// Tap / click to advance state
canvas.addEventListener('click', onTap);
canvas.addEventListener('touchstart', e => { e.preventDefault(); onTap(); }, { passive: false });

function onTap() {
  if      (state === 'title')      startGame();
  else if (state === 'gameover')   { state = 'title'; }
  else if (state === 'stageclear') startStage();
}

// ---- Game flow ----
function startGame() {
  score   = 0;
  stage   = 1;
  lives   = 3;
  enemies = [];
  frame   = 0;
  resetPlayer();
  state = 'playing';
}

function startStage() {
  enemies = [];
  frame   = 0;
  resetPlayer();
  player.invincible = true;
  player.invTimer   = 90;
  state = 'playing';
}

function resetPlayer() {
  player.x = canvas.width / 2;
  player.y = canvas.height - 80;
  player.invincible = false;
  player.invTimer   = 0;
  player.trail      = [];
}

// ---- Stars (background) ----
function initStars() {
  stars = [];
  for (let i = 0; i < 55; i++) {
    stars.push({
      x:    Math.random() * canvas.width,
      y:    Math.random() * canvas.height,
      r:    Math.random() * 1.5 + 0.4,
      vy:   Math.random() * 0.4 + 0.1,
      alpha: Math.random() * 0.6 + 0.2,
    });
  }
}

function updateStars() {
  for (const s of stars) {
    s.y += s.vy;
    if (s.y > canvas.height) { s.y = 0; s.x = Math.random() * canvas.width; }
  }
}

// ---- Enemies ----
function spawnEnemy() {
  const cfg  = STAGES[stage - 1];
  const type = cfg.types[Math.floor(Math.random() * cfg.types.length)];
  const speed = cfg.baseSpeed + Math.random() * 1.5;
  const r = 12 + Math.floor(Math.random() * 8);
  const x = r + Math.random() * (canvas.width - r * 2);
  const color = `hsl(${Math.floor(Math.random() * 360)},85%,62%)`;

  let vx = 0;
  if (type === 'zigzag') vx = (Math.random() > 0.5 ? 1 : -1) * (1.5 + Math.random());

  enemies.push({ type, x, y: -r - 5, vx, vy: speed, r, color, zigTimer: 0 });
}

function updateEnemies() {
  const cfg = STAGES[stage - 1];
  if (frame % cfg.spawnEvery === 0) spawnEnemy();

  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i];

    if (e.type === 'zigzag') {
      e.zigTimer++;
      if (e.zigTimer % 55 === 0) e.vx *= -1;
      e.x += e.vx;
      if (e.x < e.r)                  { e.x = e.r;                e.vx = Math.abs(e.vx); }
      if (e.x > canvas.width - e.r)   { e.x = canvas.width - e.r; e.vx = -Math.abs(e.vx); }
    }

    e.y += e.vy;

    // Off screen — award points
    if (e.y > canvas.height + e.r + 10) {
      enemies.splice(i, 1);
      score += 8;
      continue;
    }

    // Collision
    if (!player.invincible && hitTest(player, e)) {
      enemies.splice(i, 1);
      damagePlayer();
    }
  }
}

function hitTest(p, e) {
  const dx = p.x - e.x;
  const dy = p.y - e.y;
  return Math.sqrt(dx * dx + dy * dy) < (p.r + e.r - 6);
}

function damagePlayer() {
  lives--;
  player.invincible = true;
  player.invTimer   = 130;
  burst(player.x, player.y, '#ff5555', 18);

  if (lives <= 0) {
    saveHigh();
    state = 'gameover';
  }
}

function saveHigh() {
  if (score > highScore) {
    highScore = score;
    localStorage.setItem('dodgeMasterHS', highScore);
  }
}

// ---- Player update ----
function updatePlayer() {
  const spd = player.speed;

  if (keys['ArrowLeft']  || keys['KeyA']) player.x -= spd;
  if (keys['ArrowRight'] || keys['KeyD']) player.x += spd;
  if (keys['ArrowUp']    || keys['KeyW']) player.y -= spd;
  if (keys['ArrowDown']  || keys['KeyS']) player.y += spd;

  if (touchPt) {
    const dx   = touchPt.x - player.x;
    const dy   = touchPt.y - player.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 4) {
      const mv = Math.min(spd * 1.6, dist);
      player.x += (dx / dist) * mv;
      player.y += (dy / dist) * mv;
    }
  }

  player.x = Math.max(player.r, Math.min(canvas.width  - player.r, player.x));
  player.y = Math.max(player.r, Math.min(canvas.height - player.r, player.y));

  if (player.invincible) {
    player.invTimer--;
    if (player.invTimer <= 0) player.invincible = false;
  }

  player.trail.unshift({ x: player.x, y: player.y });
  if (player.trail.length > 10) player.trail.pop();
}

// ---- Particles ----
function burst(x, y, color, count) {
  for (let i = 0; i < count; i++) {
    const a  = Math.random() * Math.PI * 2;
    const sp = Math.random() * 5 + 2;
    particles.push({
      x, y,
      vx: Math.cos(a) * sp,
      vy: Math.sin(a) * sp,
      life: 55 + Math.floor(Math.random() * 20),
      maxLife: 75,
      color,
      r: Math.random() * 3 + 1,
    });
  }
}

function updateParticles() {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.x  += p.vx;
    p.y  += p.vy;
    p.vy += 0.18;
    p.vx *= 0.97;
    p.life--;
    if (p.life <= 0) particles.splice(i, 1);
  }
}

// ---- Stage check ----
function checkStage() {
  const goal = STAGES[stage - 1].scoreGoal;
  if (score < goal) return;

  saveHigh();

  if (stage >= STAGES.length) {
    state = 'gameover';  // all clear → game over screen shows victory
  } else {
    stage++;
    state = 'stageclear';
    burst(canvas.width / 2, canvas.height / 2, '#ffd93d', 35);
  }
}

// ---- Draw helpers ----
function drawBg() {
  const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
  g.addColorStop(0, '#08081a');
  g.addColorStop(1, '#12082a');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (const s of stars) {
    ctx.globalAlpha = s.alpha;
    ctx.fillStyle   = '#fff';
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawPlayer() {
  // Trail
  for (let i = 1; i < player.trail.length; i++) {
    const t     = player.trail[i];
    const ratio = 1 - i / player.trail.length;
    ctx.globalAlpha = ratio * 0.35;
    ctx.fillStyle   = player.color;
    ctx.beginPath();
    ctx.arc(t.x, t.y, player.r * ratio, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;

  // Flash when invincible
  if (player.invincible && Math.floor(player.invTimer / 8) % 2 === 0) return;

  ctx.shadowColor = player.color;
  ctx.shadowBlur  = 22;
  ctx.fillStyle   = player.color;
  ctx.beginPath();
  ctx.arc(player.x, player.y, player.r, 0, Math.PI * 2);
  ctx.fill();

  // Inner shine
  ctx.shadowBlur  = 0;
  ctx.fillStyle   = 'rgba(255,255,255,0.55)';
  ctx.beginPath();
  ctx.arc(player.x - 4, player.y - 4, player.r * 0.38, 0, Math.PI * 2);
  ctx.fill();
}

function drawEnemies() {
  for (const e of enemies) {
    ctx.shadowColor = e.color;
    ctx.shadowBlur  = 14;
    ctx.fillStyle   = e.color;

    if (e.type === 'square') {
      const hw = e.r;
      ctx.fillRect(e.x - hw, e.y - hw, hw * 2, hw * 2);
      ctx.strokeStyle = 'rgba(255,255,255,0.3)';
      ctx.lineWidth   = 1.5;
      ctx.strokeRect(e.x - hw, e.y - hw, hw * 2, hw * 2);
    } else {
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;
  }
}

function drawParticles() {
  for (const p of particles) {
    ctx.globalAlpha = p.life / p.maxLife;
    ctx.fillStyle   = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawHUD() {
  const fs = Math.max(12, Math.floor(canvas.width * 0.045));
  ctx.font = `bold ${fs}px 'Segoe UI', sans-serif`;

  // Score (left)
  ctx.textAlign = 'left';
  ctx.fillStyle = '#fff';
  ctx.shadowBlur = 0;
  ctx.fillText(`SCORE: ${score}`, 10, fs + 6);

  // Stage (center)
  ctx.textAlign = 'center';
  ctx.fillText(`STAGE ${stage}`, canvas.width / 2, fs + 6);

  // Lives (right) — hearts
  ctx.textAlign = 'right';
  for (let i = 0; i < 3; i++) {
    ctx.fillStyle = i < lives ? '#ff6b6b' : 'rgba(255,107,107,0.18)';
    const hx = canvas.width - 12 - i * (fs + 6);
    const hy = 8;
    drawHeart(hx, hy, fs * 0.55);
  }

  // Progress bar
  const goal    = STAGES[stage - 1].scoreGoal;
  const prog    = Math.min(score / goal, 1);
  const barY    = fs + 14;
  const barW    = canvas.width - 20;

  ctx.fillStyle = 'rgba(255,255,255,0.08)';
  ctx.fillRect(10, barY, barW, 5);

  const barG = ctx.createLinearGradient(10, barY, barW + 10, barY);
  barG.addColorStop(0, '#4ecdc4');
  barG.addColorStop(1, '#44cf6c');
  ctx.fillStyle = barG;
  ctx.fillRect(10, barY, barW * prog, 5);
}

function drawHeart(cx, cy, size) {
  ctx.beginPath();
  ctx.moveTo(cx, cy + size * 0.35);
  ctx.bezierCurveTo(cx, cy,            cx - size, cy,            cx - size, cy + size * 0.35);
  ctx.bezierCurveTo(cx - size, cy + size * 0.7, cx, cy + size * 1.2, cx, cy + size * 1.5);
  ctx.bezierCurveTo(cx, cy + size * 1.2, cx + size, cy + size * 0.7, cx + size, cy + size * 0.35);
  ctx.bezierCurveTo(cx + size, cy,      cx, cy,                 cx, cy + size * 0.35);
  ctx.fill();
}

// ---- Overlay screens ----
function overlayRect() {
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawTitle() {
  overlayRect();
  const W = canvas.width, H = canvas.height;
  const pulse = 0.7 + 0.3 * Math.sin(frame * 0.06);

  ctx.textAlign  = 'center';
  ctx.shadowColor = '#4ecdc4';
  ctx.shadowBlur  = 28;
  ctx.fillStyle   = '#4ecdc4';
  ctx.font = `bold ${Math.floor(W * 0.13)}px 'Segoe UI', sans-serif`;
  ctx.fillText('DODGE',  W / 2, H * 0.28);
  ctx.fillText('MASTER', W / 2, H * 0.28 + W * 0.15);

  ctx.shadowBlur = 0;
  ctx.fillStyle  = '#ffd93d';
  ctx.font = `${Math.floor(W * 0.052)}px 'Segoe UI', sans-serif`;
  ctx.fillText(`BEST: ${highScore}`, W / 2, H * 0.55);

  ctx.globalAlpha = pulse;
  ctx.fillStyle   = '#fff';
  ctx.font = `${Math.floor(W * 0.058)}px 'Segoe UI', sans-serif`;
  ctx.fillText('タップ / クリックでスタート', W / 2, H * 0.68);
  ctx.globalAlpha = 1;

  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = `${Math.floor(W * 0.038)}px 'Segoe UI', sans-serif`;
  ctx.fillText('PC: 矢印キー / マウス移動', W / 2, H * 0.8);
  ctx.fillText('スマホ: タッチ操作', W / 2, H * 0.855);

  // Stage list
  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  ctx.font = `${Math.floor(W * 0.034)}px 'Segoe UI', sans-serif`;
  ctx.fillText('全5ステージ制  ❤️×3', W / 2, H * 0.93);
}

function drawStageClear() {
  overlayRect();
  const W = canvas.width, H = canvas.height;
  const pulse = 0.65 + 0.35 * Math.sin(frame * 0.07);

  ctx.textAlign  = 'center';
  ctx.shadowColor = '#ffd93d';
  ctx.shadowBlur  = 26;
  ctx.fillStyle   = '#ffd93d';
  ctx.font = `bold ${Math.floor(W * 0.1)}px 'Segoe UI', sans-serif`;
  ctx.fillText('STAGE CLEAR!', W / 2, H * 0.38);

  ctx.shadowBlur = 0;
  ctx.fillStyle  = '#fff';
  ctx.font = `${Math.floor(W * 0.062)}px 'Segoe UI', sans-serif`;
  ctx.fillText(`スコア: ${score}`, W / 2, H * 0.52);

  ctx.font = `${Math.floor(W * 0.05)}px 'Segoe UI', sans-serif`;
  ctx.fillText(`STAGE ${stage} へ進む`, W / 2, H * 0.62);

  ctx.globalAlpha = pulse;
  ctx.fillStyle   = '#4ecdc4';
  ctx.font = `${Math.floor(W * 0.054)}px 'Segoe UI', sans-serif`;
  ctx.fillText('タップ / クリック', W / 2, H * 0.76);
  ctx.globalAlpha = 1;
}

function drawGameOver() {
  overlayRect();
  const W = canvas.width, H = canvas.height;
  const allClear = stage > STAGES.length;
  const pulse    = 0.65 + 0.35 * Math.sin(frame * 0.06);

  ctx.textAlign = 'center';

  if (allClear) {
    ctx.shadowColor = '#ffd93d';
    ctx.shadowBlur  = 30;
    ctx.fillStyle   = '#ffd93d';
    ctx.font = `bold ${Math.floor(W * 0.1)}px 'Segoe UI', sans-serif`;
    ctx.fillText('ALL CLEAR!', W / 2, H * 0.3);
  } else {
    ctx.shadowColor = '#ff6b6b';
    ctx.shadowBlur  = 28;
    ctx.fillStyle   = '#ff6b6b';
    ctx.font = `bold ${Math.floor(W * 0.1)}px 'Segoe UI', sans-serif`;
    ctx.fillText('GAME OVER', W / 2, H * 0.3);
  }

  ctx.shadowBlur = 0;
  ctx.fillStyle  = '#fff';
  ctx.font = `${Math.floor(W * 0.065)}px 'Segoe UI', sans-serif`;
  ctx.fillText(`スコア: ${score}`, W / 2, H * 0.46);

  if (score >= highScore && score > 0) {
    ctx.fillStyle = '#ffd93d';
    ctx.font = `${Math.floor(W * 0.05)}px 'Segoe UI', sans-serif`;
    ctx.fillText('NEW RECORD!', W / 2, H * 0.56);
  }

  ctx.fillStyle = 'rgba(255,255,255,0.55)';
  ctx.font = `${Math.floor(W * 0.046)}px 'Segoe UI', sans-serif`;
  ctx.fillText(`ベスト: ${highScore}`, W / 2, H * 0.64);

  ctx.globalAlpha = pulse;
  ctx.fillStyle   = '#fff';
  ctx.font = `${Math.floor(W * 0.052)}px 'Segoe UI', sans-serif`;
  ctx.fillText('タップでタイトルへ', W / 2, H * 0.78);
  ctx.globalAlpha = 1;
}

// ---- Main loop ----
function loop() {
  requestAnimationFrame(loop);
  frame++;

  updateStars();
  drawBg();

  if (state === 'playing') {
    updatePlayer();
    updateEnemies();
    updateParticles();
    score++;
    checkStage();

    drawEnemies();
    drawParticles();
    drawPlayer();
    drawHUD();

  } else if (state === 'title') {
    updateParticles();
    drawParticles();
    drawTitle();

  } else if (state === 'stageclear') {
    updateParticles();
    drawParticles();
    drawStageClear();

  } else if (state === 'gameover') {
    drawEnemies();
    updateParticles();
    drawParticles();
    drawPlayer();
    drawGameOver();
  }
}

// ---- Init ----
initStars();
loop();
