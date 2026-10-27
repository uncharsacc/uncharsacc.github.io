const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');
let W, H, particles = [], rings = [], nodes = [], trails = [], t = 0;
let mouse = { x: -1e4, y: -1e4, on: false }, infl = 0;

function resize() {
  W = canvas.width = innerWidth;
  H = canvas.height = innerHeight;
  rings = [];
  const base = Math.min(W, H) * 0.20;
  for (let i = 0; i < 6; i++) {
    rings.push({
      r: base * (0.5 + i * 0.32),
      sp: 0.08 + i * 0.055,
      dir: i % 2 ? -1 : 1,
      w: 1 + i * 0.3,
      a: 0.1 - i * 0.012,
      ph: Math.random() * 6.28,
      pulse: 0.8 + Math.random() * 0.6,
      dash: (i === 1 || i === 4) ? [6, 10] : null
    });
  }
  particles = [];
  const n = Math.min(100, Math.floor(W * H / 13000));
  for (let i = 0; i < n; i++) {
    particles.push({
      x: Math.random() * W, y: Math.random() * H,
      r: 0.4 + Math.random() * 1.6,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      a: 0.1 + Math.random() * 0.45, p: Math.random() * 6.28
    });
  }
  nodes = [];
  for (let i = 0; i < 18; i++) {
    nodes.push({
      ang: (i / 18) * 6.28,
      d: Math.min(W, H) * (0.14 + (i % 5) * 0.04 + Math.random() * 0.12),
      r: 2 + Math.random() * 2.5,
      sp: 0.15 + Math.random() * 0.3,
      ph: Math.random() * 6.28,
      orb: 0.6 + Math.random() * 0.8
    });
  }
}

function draw() {
  const gx = W * 0.5 + Math.sin(t * 0.08) * 55;
  const gy = H * 0.42 + Math.cos(t * 0.07) * 35;
  const bg = ctx.createRadialGradient(gx, gy, 0, W * 0.5, H * 0.5, Math.max(W, H) * 0.95);
  bg.addColorStop(0, '#16122a');
  bg.addColorStop(0.4, '#0e0b1a');
  bg.addColorStop(1, '#05040a');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  const cx = W * 0.5, cy = H * 0.42;
  infl = mouse.on ? Math.min(1, infl + 0.04) : Math.max(0, infl - 0.02);
  const pulse = 0.85 + 0.15 * Math.sin(t * 1.1);
  const coreR = Math.min(W, H) * 0.42 * pulse;

  let g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 1.35);
  g.addColorStop(0, 'rgba(100, 70, 255, 0.09)');
  g.addColorStop(0.5, 'rgba(80, 50, 200, 0.03)');
  g.addColorStop(1, 'transparent');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 0.55);
  g.addColorStop(0, `rgba(160, 120, 255, ${0.2 * pulse})`);
  g.addColorStop(0.4, `rgba(120, 80, 240, ${0.08 * pulse})`);
  g.addColorStop(1, 'transparent');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  rings.forEach((ring, i) => {
    const rot = t * ring.sp * ring.dir + ring.ph;
    const pa = 0.7 + 0.3 * Math.sin(t * ring.pulse + i);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    ctx.beginPath();
    ctx.arc(0, 0, ring.r, 0, 6.28);
    ctx.strokeStyle = `rgba(170, 145, 255, ${ring.a * pa})`;
    ctx.lineWidth = ring.w;
    if (ring.dash) ctx.setLineDash(ring.dash);
    else ctx.setLineDash([]);
    ctx.stroke();
    ctx.setLineDash([]);
    const sh = t * 1.5 + i * 1.2;
    ctx.beginPath();
    ctx.arc(0, 0, ring.r, sh, sh + 0.55);
    ctx.strokeStyle = `rgba(220, 200, 255, ${0.28 * pa})`;
    ctx.lineWidth = ring.w + 1.5;
    ctx.lineCap = 'round';
    ctx.stroke();
    if (i % 2 === 0) {
      const dots = 6 + i;
      for (let j = 0; j < dots; j++) {
        const a = (j / dots) * 6.28;
        const px = Math.cos(a) * ring.r, py = Math.sin(a) * ring.r;
        const dg = 0.5 + 0.5 * Math.sin(t * 2.4 + j * 0.8 + i);
        ctx.beginPath();
        ctx.arc(px, py, 1.3 + dg * 1.1, 0, 6.28);
        ctx.fillStyle = `rgba(200, 185, 255, ${0.2 + dg * 0.35})`;
        ctx.fill();
      }
    }
    ctx.restore();
  });

  const pos = [];
  nodes.forEach(n => {
    let ang = n.ang + t * n.sp * n.orb, d = n.d;
    if (infl > 0.01) {
      const ma = Math.atan2(mouse.y - cy, mouse.x - cx);
      const md = Math.hypot(mouse.x - cx, mouse.y - cy);
      const inf = Math.max(0, 1 - md / (Math.min(W, H) * 0.5)) * infl;
      ang += Math.sin(ang - ma) * inf * 0.4;
      d *= 1 + inf * 0.15;
    }
    const wob = 0.05 * Math.sin(t * 0.9 + n.ph);
    pos.push({
      x: cx + Math.cos(ang) * d * (1 + wob),
      y: cy + Math.sin(ang) * d * (1 + wob * 0.6),
      r: n.r, ph: n.ph
    });
  });

  ctx.lineWidth = 0.8;
  for (let i = 0; i < pos.length; i++) {
    for (let j = i + 1; j < pos.length; j++) {
      const a = pos[i], b = pos[j];
      const dist = Math.hypot(a.x - b.x, a.y - b.y);
      if (dist < 170) {
        let al = (1 - dist / 170) * 0.22;
        if (infl > 0) {
          const md = Math.hypot(mouse.x - (a.x + b.x) / 2, mouse.y - (a.y + b.y) / 2);
          if (md < 120) al += (1 - md / 120) * 0.25 * infl;
        }
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = `rgba(175, 150, 255, ${al})`;
        ctx.stroke();
      }
    }
  }

  pos.forEach(n => {
    const gl = 0.5 + 0.5 * Math.sin(t * 2.2 + n.ph);
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r * 4, 0, 6.28);
    ctx.fillStyle = `rgba(140, 110, 255, ${0.07 * gl})`;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r * (0.9 + 0.2 * gl), 0, 6.28);
    ctx.fillStyle = `rgba(220, 205, 255, ${0.6 + 0.4 * gl})`;
    ctx.fill();
  });

  const coreSize = 6 + Math.sin(t * 1.5) * 2;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(t * 1.8);
  ctx.beginPath();
  ctx.arc(0, 0, 22 + Math.sin(t * 2) * 4, 0, Math.PI * 1.4);
  ctx.strokeStyle = 'rgba(180, 150, 255, 0.38)';
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.stroke();
  ctx.restore();
  ctx.beginPath();
  ctx.arc(cx, cy, coreSize, 0, 6.28);
  ctx.fillStyle = 'rgba(230, 220, 255, 0.75)';
  ctx.fill();
  ctx.beginPath();
  ctx.arc(cx, cy, coreSize * 2.5, 0, 6.28);
  ctx.strokeStyle = 'rgba(160, 130, 255, 0.22)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  trails = trails.filter(tr => tr.life > 0);
  particles.forEach(p => {
    p.x += p.vx; p.y += p.vy; p.p += 0.02;
    if (p.x < 0 || p.x > W) p.vx *= -1;
    if (p.y < 0 || p.y > H) p.vy *= -1;
    const dx = cx - p.x, dy = cy - p.y, d = Math.hypot(dx, dy) || 1;
    p.vx += (dx / d) * 0.002; p.vy += (dy / d) * 0.002;
    if (infl > 0.05) {
      const md = Math.hypot(mouse.x - p.x, mouse.y - p.y) || 1;
      if (md < 180) {
        const f = (1 - md / 180) * 0.08 * infl;
        p.vx -= ((mouse.x - p.x) / md) * f;
        p.vy -= ((mouse.y - p.y) / md) * f;
      }
    }
    const sp = Math.hypot(p.vx, p.vy);
    if (sp > 1.1) { p.vx = (p.vx / sp) * 1.1; p.vy = (p.vy / sp) * 1.1; }
    if (Math.random() < 0.08 && sp > 0.3)
      trails.push({ x: p.x, y: p.y, life: 1, r: p.r * 0.7, a: p.a * 0.5 });
    const a = p.a * (0.45 + 0.55 * Math.sin(p.p));
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, 6.28);
    ctx.fillStyle = `rgba(180, 160, 255, ${a})`;
    ctx.fill();
  });
  trails.forEach(tr => {
    tr.life -= 0.025;
    if (tr.life <= 0) return;
    ctx.beginPath();
    ctx.arc(tr.x, tr.y, tr.r * tr.life, 0, 6.28);
    ctx.fillStyle = `rgba(160, 140, 255, ${tr.a * tr.life})`;
    ctx.fill();
  });

  if (infl > 0.02) {
    const mg = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 100);
    mg.addColorStop(0, `rgba(180, 150, 255, ${0.12 * infl})`);
    mg.addColorStop(0.5, `rgba(140, 100, 255, ${0.04 * infl})`);
    mg.addColorStop(1, 'transparent');
    ctx.fillStyle = mg;
    ctx.beginPath();
    ctx.arc(mouse.x, mouse.y, 100, 0, 6.28);
    ctx.fill();
  }
}

function loop() { t += 0.016; draw(); requestAnimationFrame(loop); }
addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; mouse.on = true; });
addEventListener('mouseleave', () => { mouse.on = false; });
addEventListener('touchmove', e => {
  if (e.touches[0]) { mouse.x = e.touches[0].clientX; mouse.y = e.touches[0].clientY; mouse.on = true; }
}, { passive: true });
addEventListener('touchend', () => { mouse.on = false; });
addEventListener('resize', resize);
resize(); loop();

/* ---- data ---- */
async function load(path) {
  try { const r = await fetch(path); return r.ok ? await r.json() : null; }
  catch { return null; }
}

/* ---- iconos: emoji | URL https://... | atajo "si:python" o "si:github/ffffff" (Simple Icons) ---- */
function resolveIcon(ic) {
  ic = (ic || '').trim();
  if (/^si:/i.test(ic)) return 'https://cdn.simpleicons.org/' + ic.slice(3).trim();
  return ic;
}
function iconTag(ic) {
  ic = resolveIcon(ic);
  if (!ic) return '';
  if (/^https?:\/\//i.test(ic))
    return `<img class="ico-img" src="${ic}" alt="" loading="lazy" onerror="this.remove()" />`;
  return `<span class="ico-emoji">${ic}</span>`;
}

/* ---- proyectos: si no caben de costado, se vuelve carrusel que se mueve solo ---- */
let _projVP = null;
let _projStop = null;
function setupProjCarousel(vp) {
  if (!vp) return;
  _projVP = vp;
  if (_projStop) { _projStop(); _projStop = null; }
  const track = vp.querySelector('.proj-track');
  const group = vp.querySelector('.proj-group:not(.clone)');
  if (!track || !group) return;
  track.querySelectorAll('.proj-group.clone').forEach(n => n.remove());
  vp.classList.remove('scrolling');
  vp.scrollLeft = 0;
  if (group.scrollWidth <= vp.clientWidth - 48) return;   // caben: quietas y centradas

  // no caben: duplicamos el grupo para un bucle sin saltos
  const clone = group.cloneNode(true);
  clone.classList.add('clone');
  clone.setAttribute('aria-hidden', 'true');
  track.appendChild(clone);
  vp.classList.add('scrolling');
  const loop = group.offsetWidth;                          // ancho de un grupo completo

  const SPEED = 40;                                        // px por segundo
  let pos = 0, paused = false, last = performance.now(), raf = 0, timer = 0;
  const pause = () => { paused = true; clearTimeout(timer); };
  const resume = ms => {
    clearTimeout(timer);
    timer = setTimeout(() => { pos = vp.scrollLeft; paused = false; last = performance.now(); }, ms);
  };
  const step = now => {
    const dt = Math.min(64, now - last) / 1000;
    last = now;
    if (!paused) {
      pos += SPEED * dt;
      if (pos >= loop) pos -= loop;
      vp.scrollLeft = pos;
    }
    raf = requestAnimationFrame(step);
  };
  // si el usuario arrastra la barra hasta el final, vuelve al inicio sin salto
  const onScroll = () => { if (paused && vp.scrollLeft >= loop) vp.scrollLeft -= loop; };
  const onEnter = () => pause();
  const onLeave = () => resume(600);
  const onTouchEnd = () => resume(2500);
  vp.addEventListener('mouseenter', onEnter);
  vp.addEventListener('mouseleave', onLeave);
  vp.addEventListener('touchstart', onEnter, { passive: true });
  vp.addEventListener('touchend', onTouchEnd);
  vp.addEventListener('touchcancel', onTouchEnd);
  vp.addEventListener('focusin', onEnter);
  vp.addEventListener('focusout', onLeave);
  vp.addEventListener('scroll', onScroll, { passive: true });
  raf = requestAnimationFrame(step);

  _projStop = () => {
    cancelAnimationFrame(raf); clearTimeout(timer);
    vp.removeEventListener('mouseenter', onEnter);
    vp.removeEventListener('mouseleave', onLeave);
    vp.removeEventListener('touchstart', onEnter);
    vp.removeEventListener('touchend', onTouchEnd);
    vp.removeEventListener('touchcancel', onTouchEnd);
    vp.removeEventListener('focusin', onEnter);
    vp.removeEventListener('focusout', onLeave);
    vp.removeEventListener('scroll', onScroll);
  };
}
let _rz;
addEventListener('resize', () => { clearTimeout(_rz); _rz = setTimeout(() => setupProjCarousel(_projVP), 200); });

function render(profile, projects) {
  if (!profile) return;
  document.getElementById('nav-logo').textContent = profile.shortName || 'UN';
  document.getElementById('hero-name').textContent = profile.name || 'Uncharsacc';
  document.getElementById('hero-subtitle').textContent = profile.heroSubtitle || profile.tagline || '';
  document.getElementById('footer-name').textContent = profile.name || 'Uncharsacc';
  document.getElementById('year').textContent = new Date().getFullYear();
  if (profile.github) document.getElementById('btn-github').href = profile.github;

  // Curriculum / CV
  const cvBtn = document.getElementById('btn-cv');
  if (cvBtn) {
    const cv = profile.cv || profile.cvUrl || '';
    if (cv) {
      cvBtn.href = cv;
      cvBtn.hidden = false;
      // force download for same-origin files
      if (!/^https?:\/\//i.test(cv)) {
        cvBtn.setAttribute('download', '');
      } else {
        cvBtn.removeAttribute('download');
        cvBtn.target = '_blank';
        cvBtn.rel = 'noopener';
      }
    } else {
      cvBtn.hidden = true;
    }
  }

  const st = profile.stats || {};
  document.getElementById('hero-stats').innerHTML = `
    <div class="stat"><strong>${st.years || '—'}</strong><span>${st.yearsLabel || 'Años'}</span></div>
    <div class="stat"><strong>${st.projects || '—'}</strong><span>${st.projectsLabel || 'Proyectos'}</span></div>
    <div class="stat"><strong>${st.skills || '—'}</strong><span>${st.skillsLabel || 'Skills'}</span></div>
  `;

  // Marquee seamless full-width
  const tech = profile.techMarquee || ['HTML', 'CSS', 'JS'];
  let items = [...tech];
  while (items.length < 16) items = items.concat(tech);
  const spans = items.map(x => `<span>${x}</span>`).join('');
  document.getElementById('tech-track').innerHTML =
    `<div class="tech-group">${spans}</div><div class="tech-group">${spans}</div>`;

  document.getElementById('about-text').textContent = profile.about || '';

  // Skill icons (habilidades clave como en la referencia)
  const icons = profile.skillIcons || (profile.skills || []).map(s => ({ name: s.name, icon: '◆' }));
  document.getElementById('skill-icons').innerHTML = icons.map(s => {
    const ic = resolveIcon(s.icon || '◆');
    const icoHtml = /^https?:\/\//i.test(ic)
      ? `<img src="${ic}" alt="" style="width:28px;height:28px;object-fit:contain;margin:0 auto 0.35rem;display:block;border-radius:4px;" />`
      : `<div class="ico">${ic}</div>`;
    return `<div class="skill-icon-card">${icoHtml}${s.name}</div>`;
  }).join('');

  // Side cards
  const highs = profile.highlights || [
    { num: st.years, label: st.yearsLabel },
    { num: st.projects, label: st.projectsLabel },
    { num: st.skills, label: st.skillsLabel }
  ];
  document.getElementById('about-side').innerHTML = highs.filter(h => h && h.num).map(h => `
    <div class="side-card"><div class="num">${h.num}</div><div class="lbl">${h.label || ''}</div></div>
  `).join('');

  // Experience: pestañas por empresa + tarjeta
  const exps = profile.experience || [];
  const expEl = document.getElementById('experience-container');
  if (!exps.length) {
    expEl.innerHTML = '<p style="color:var(--muted)">Aún no hay experiencia.</p>';
  } else {
    const panelHtml = e => `
      <article class="exp-panel">
        <div class="exp-head">
          <div class="exp-ico">${iconTag(e.icon)}</div>
          <div>
            <div class="exp-title">${e.title || ''}</div>
            <div class="exp-company">${e.company || ''}</div>
            ${e.description ? `<div class="exp-sub">${e.description}</div>` : ''}
          </div>
        </div>
        <div class="exp-badges">
          ${e.period ? `<span class="exp-badge">${e.period}</span>` : ''}
          ${e.location ? `<span class="exp-loc">${e.location}</span>` : ''}
        </div>
        ${e.bullets && e.bullets.length ? `<hr class="exp-divider" /><ul class="exp-points">${e.bullets.map(b => `<li>${b}</li>`).join('')}</ul>` : ''}
        ${(e.tech || []).length ? `<div class="tags">${e.tech.map(t => `<span class="tag">${t}</span>`).join('')}</div>` : ''}
      </article>`;
    expEl.innerHTML = `
      <div class="exp-tabs" role="tablist">${exps.map((e, i) =>
        `<button class="exp-tab${i === 0 ? ' active' : ''}" role="tab" aria-selected="${i === 0}" data-i="${i}">${e.company || e.title || 'Experiencia'}</button>`
      ).join('')}</div>
      <div id="exp-panel"></div>`;
    const panel = expEl.querySelector('#exp-panel');
    const tabs = [...expEl.querySelectorAll('.exp-tab')];
    const showExp = i => {
      tabs.forEach((t, k) => { t.classList.toggle('active', k === i); t.setAttribute('aria-selected', k === i); });
      panel.innerHTML = panelHtml(exps[i]);
      tabs[i].scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
    };
    tabs.forEach((t, i) => t.addEventListener('click', () => showExp(i)));
    expEl.querySelector('.exp-tabs').addEventListener('keydown', ev => {
      const cur = tabs.findIndex(t => t.classList.contains('active'));
      if (ev.key === 'ArrowRight' && cur < tabs.length - 1) { showExp(cur + 1); tabs[cur + 1].focus(); }
      if (ev.key === 'ArrowLeft' && cur > 0) { showExp(cur - 1); tabs[cur - 1].focus(); }
    });
    panel.innerHTML = panelHtml(exps[0]);
  }

  // Projects (fila de costado; carrusel automático si no caben)
  const list = [...(projects || [])].sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0));
  const projEl = document.getElementById('projects-container');
  if (list.length) {
    const cards = list.map(p => `
      <article class="proj-card${p.featured ? ' featured' : ''}">
        ${p.featured ? '<div class="proj-badge">★ Destacado</div>' : ''}
        <h3>${iconTag(p.icon)}<span>${p.name}</span></h3>
        <p>${p.description || ''}</p>
        <div class="tags">${(p.tech || []).map(t => `<span class="tag">${t}</span>`).join('')}</div>
        <div class="proj-links">
          ${p.github ? `<a class="main" href="${p.github}" target="_blank" rel="noopener">GitHub</a>` : ''}
          ${p.demo ? `<a href="${p.demo}" target="_blank" rel="noopener">Demo</a>` : ''}
        </div>
      </article>`).join('');
    projEl.innerHTML = `<div class="proj-track"><div class="proj-group">${cards}</div></div>`;
    setupProjCarousel(projEl);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => setupProjCarousel(projEl));
  } else {
    projEl.innerHTML = '<p style="color:var(--muted)">Sin proyectos todavía.</p>';
  }

  // Education
  document.getElementById('education-container').innerHTML = (profile.education || []).map(e => `
    <div class="edu-card">
      <h3>${e.title || ''}</h3>
      <div class="edu-inst">${e.institution || ''}</div>
      <div class="edu-meta">${[e.period, e.status].filter(Boolean).join(' · ')}</div>
    </div>
  `).join('') || '<p style="color:var(--muted)">Agrega educación en el script</p>';

  // Certifications (faltaba)
  document.getElementById('certs-container').innerHTML = (profile.certifications || []).filter(c => c && c.name).map(c => `
    <div class="cert-card">
      <div class="name">${c.name || ''}</div>
      <div class="org">${c.org || ''}</div>
    </div>
  `).join('') || '<p style="color:var(--muted)"></p>';

  // Skills: icono + nombre (+ nivel), la caja se ajusta sola
  document.getElementById('skills-container').innerHTML = (profile.skills || []).map(s => `
    <div class="skill-chip">${iconTag(s.icon)}<span>${s.name}</span>${s.level ? `<span class="lvl">${s.level}%</span>` : ''}</div>
  `).join('');

  // Tecnologías: grupos sin fondo; cada tech = icono + nombre. Acepta "Python" o {name, icon}
  const stack = profile.techStack || {};
  document.getElementById('stack-container').innerHTML = Object.entries(stack).map(([k, v]) => `
    <div class="stack-group">
      <h4>${k}</h4>
      <div class="stack-items">${(v || []).map(t => {
        const o = typeof t === 'string' ? { name: t, icon: '' } : t;
        return `<div class="tech-tile">${iconTag(o.icon)}<span>${o.name}</span></div>`;
      }).join('')}</div>
    </div>
  `).join('');

  // Contact — soporta contact.items[{label,value,url,icon}] o campos clásicos
  const c = profile.contact || {};
  let itemsC = [];
  if (Array.isArray(c.items) && c.items.length) {
    itemsC = c.items.map(it => ({
      l: it.label || it.l || '',
      v: it.value || it.v || '',
      h: it.url || it.href || '',
      icon: it.icon || ''
    }));
  } else {
    if (c.email) itemsC.push({ l: 'Email', v: c.email, h: 'mailto:' + c.email, icon: c.emailIcon || '✉️' });
    if (c.phone) itemsC.push({ l: 'Teléfono', v: c.phone, h: 'tel:' + c.phone, icon: c.phoneIcon || '📞' });
    if (c.location) itemsC.push({ l: 'Ubicación', v: c.location, h: '', icon: c.locationIcon || '📍' });
    if (c.github) itemsC.push({ l: 'GitHub', v: '@' + (c.github.split('/').pop() || ''), h: c.github, icon: c.githubIcon || '🐙' });
    if (c.linkedin) itemsC.push({ l: 'LinkedIn', v: 'Perfil', h: c.linkedin, icon: c.linkedinIcon || 'in' });
  }
  function iconHtml(ic) {
    ic = resolveIcon(ic);
    if (!ic) return '';
    if (/^https?:\/\//i.test(ic))
      return `<div class="c-icon"><img src="${ic}" alt="" /></div>`;
    return `<div class="c-icon">${ic}</div>`;
  }
  document.getElementById('contact-container').innerHTML = itemsC.length ? itemsC.map(i => `
    <div class="contact-item">
      ${iconHtml(i.icon)}
      <div class="c-body">
        <div class="lbl">${i.l}</div>
        <div class="val">${i.h ? `<a href="${i.h}" target="_blank" rel="noopener">${i.v}</a>` : i.v}</div>
      </div>
    </div>
  `).join('') : '<p style="color:var(--muted);text-align:center">Completa contacto en el editor</p>';

  // ---- Secciones: visibilidad + orden (controlado desde el editor) ----
  applySections(profile);
}

/** Config de secciones: order + visible. Auto-oculta vacías. */
function applySections(profile) {
  const DEFAULT_ORDER = [
    "sobre-mi", "experiencia", "proyectos", "educacion",
    "certs", "tecnologias", "skills", "contacto"
  ];
  const cfg = profile.sections || {};
  const order = Array.isArray(cfg.order) && cfg.order.length ? cfg.order.slice() : DEFAULT_ORDER.slice();
  const visible = Object.assign(
    Object.fromEntries(DEFAULT_ORDER.map(id => [id, true])),
    cfg.visible || {}
  );

  // Auto-hide vacías (a menos que el usuario las fuerza visibles con datos)
  const skills = profile.skills;
  const certs = profile.certifications || [];
  if (!Array.isArray(skills) || skills.length === 0) visible.skills = false;
  if (!certs.filter(c => c && c.name).length) visible.certs = false;

  // Asegurar que todos los ids conocidos estén en order
  DEFAULT_ORDER.forEach(id => { if (!order.includes(id)) order.push(id); });

  const footer = document.querySelector("footer");
  const parent = footer ? footer.parentElement : document.body;

  order.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const show = visible[id] !== false;
    el.hidden = !show;
    el.style.display = show ? "" : "none";
    if (show && footer) parent.insertBefore(el, footer);
  });

  // Nav links
  document.querySelectorAll(".nav-links a").forEach(a => {
    const href = a.getAttribute("href") || "";
    if (!href.startsWith("#")) return;
    const id = href.slice(1);
    if (id === "inicio") return; // siempre visible
    if (!(id in visible) && !DEFAULT_ORDER.includes(id)) return;
    const show = visible[id] !== false;
    const li = a.closest("li") || a;
    li.style.display = show ? "" : "none";
  });
}

const toggle = document.querySelector('.nav-toggle');
const links = document.querySelector('.nav-links');
if (toggle) {
  toggle.onclick = () => links.classList.toggle('open');
  links.querySelectorAll('a').forEach(a => (a.onclick = () => links.classList.remove('open')));
}
const secs = document.querySelectorAll('section, .hero');
addEventListener('scroll', () => {
  let cur = '';
  secs.forEach(s => { if (scrollY >= s.offsetTop - 80) cur = s.id || ''; });
  document.querySelectorAll('.nav-links a').forEach(a =>
    a.classList.toggle('active', a.getAttribute('href') === '#' + cur)
  );
});

(async () => {
  const [profile, projects] = await Promise.all([load('data/profile.json'), load('data/projects.json')]);
  render(profile, projects);
})();