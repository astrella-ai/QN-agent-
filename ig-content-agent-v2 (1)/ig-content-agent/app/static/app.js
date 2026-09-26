/* IG Content Agent front-end. No inline scripts and no HTML injection: all text is set with textContent. */
(() => {
'use strict';

const csrf = document.querySelector('meta[name="csrf-token"]').content;
const view = document.getElementById('view');
const $ = (id) => document.getElementById(id);

// ---------- helpers ----------------------------------------------------------------------------
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'value' || k === 'checked' || k === 'disabled' || k === 'selected' || k === 'muted' || k === 'multiple') el[k] = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

async function api(path, opts = {}) {
  const init = { method: opts.method || 'GET', headers: {}, credentials: 'same-origin' };
  if (init.method !== 'GET') init.headers['X-CSRF-Token'] = csrf;
  if (opts.json !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(opts.json); }
  if (opts.form) init.body = opts.form;
  let r;
  try { r = await fetch(path, init); } catch (e) { throw new Error('Cannot reach the app. Is it still running on the PC?'); }
  if (r.status === 401) { location.href = '/login'; throw new Error('Signed out'); }
  let data = {};
  try { data = await r.json(); } catch (e) { /* not JSON */ }
  if (!r.ok) throw new Error(data.error || `Something went wrong (${r.status}).`);
  return data;
}

function toast(text, kind) {
  const t = h('div', { class: 'toast ' + (kind || ''), text });
  $('toasts').append(t);
  setTimeout(() => t.remove(), 6500);
}
const fmtTime = (iso) => { try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } };
const fmtDateTime = (iso) => { try { return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); } catch (e) { return ''; } };
function toLocalInput(iso) {
  if (!iso) return '';
  const d = new Date(iso), p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}
const timers = {};
function debounced(key, ms, fn) { clearTimeout(timers[key]); timers[key] = setTimeout(fn, ms); }

const LABEL = { DRAFT: 'Draft', RENDERING: 'Preparing', READY_FOR_REVIEW: 'Ready for review', APPROVED: 'Approved', PUBLISHING: 'Publishing',
  PUBLISHED: 'Published', DRY_RUN_COMPLETE: 'Dry run done', REJECTED: 'Rejected', FAILED: 'Failed' };

// ---------- preferences (stored only in this browser) ---------------------------------------------
const PREF_KEY = 'igagent.prefs.v1';
const defaults = { lang: 'en-IN', speak: true, alerts: true, rate: 1, voice: '', handsFree: true };
let prefs = (() => { try { return { ...defaults, ...JSON.parse(localStorage.getItem(PREF_KEY) || '{}') }; } catch (e) { return { ...defaults }; } })();
function savePrefs() { try { localStorage.setItem(PREF_KEY, JSON.stringify(prefs)); } catch (e) { /* private mode */ } }

// ---------- app state ----------------------------------------------------------------------------
const S = { state: null, posts: [], activity: [], lastActivity: 0, live: false, view: { name: 'live' }, feedList: null, boardBox: null, summaryBox: null };

async function refreshState() { try { S.state = await api('/api/state'); renderPills(); } catch (e) { /* offline */ } }
async function refreshPosts() { const r = await api('/api/posts'); S.posts = r.posts; }
async function loadActivity() {
  const r = await api('/api/activity');
  S.activity = r.activity.slice().reverse();
  S.lastActivity = r.activity.length ? r.activity[r.activity.length - 1].id : 0;
}

function renderPills() {
  const box = $('pills'); box.replaceChildren();
  const add = (text, kind) => box.append(h('span', { class: 'pill ' + kind, text }));
  const s = S.state && S.state.settings;
  if (s) add(s.dry_run ? 'Dry run: nothing is posted' : 'Live posting', s.dry_run ? 'warn' : 'ok');
  add(S.live ? 'Live updates on' : 'Reconnecting...', S.live ? 'ok' : 'warn');
  if (S.state) add(S.state.workers_alive ? 'Worker running' : 'Worker stopped', S.state.workers_alive ? 'ok' : 'bad');
  if (s) add('AI writer: ' + s.llm, s.llm === 'offline' ? 'warn' : 'ok');
}

// ---------- router ---------------------------------------------------------------------------------
async function route() {
  const hash = location.hash || '#/';
  document.querySelectorAll('#nav a').forEach((a) => {
    const r = a.dataset.route;
    a.classList.toggle('on', (r === 'live' && (hash === '#/' || hash.startsWith('#/post'))) || (r === 'new' && hash === '#/new') || (r === 'settings' && hash === '#/settings'));
  });
  if (hash.startsWith('#/post/')) return showPost(parseInt(hash.slice(7), 10));
  if (hash === '#/new') return showNew();
  if (hash === '#/settings') return showSettings();
  return showLive();
}
window.addEventListener('hashchange', route);

// ---------- live board -----------------------------------------------------------------------------
const COLS = [
  { title: 'Being prepared', states: ['DRAFT', 'RENDERING'] },
  { title: 'Needs you', states: ['READY_FOR_REVIEW'] },
  { title: 'Approved, going out', states: ['APPROVED', 'PUBLISHING'] },
  { title: 'Done', states: ['PUBLISHED', 'DRY_RUN_COMPLETE'] },
  { title: 'Needs attention', states: ['FAILED', 'REJECTED'] },
];

function postCard(p) {
  let thumb;
  if (p.thumb && p.thumb_kind === 'image') thumb = h('img', { src: p.thumb, alt: '', loading: 'lazy' });
  else if (p.thumb) thumb = h('video', { src: p.thumb + '#t=0.1', preload: 'metadata', muted: true, playsinline: '' });
  else thumb = 'No media yet';
  return h('a', { class: 'pcard', href: '#/post/' + p.id },
    h('div', { class: 'thumb' }, thumb),
    h('div', { class: 'body' },
      h('div', { class: 'title', text: p.title || 'Post ' + p.id }),
      h('div', {}, h('span', { class: 'badge ' + p.state, text: LABEL[p.state] || p.state }), h('span', { class: 'badge', text: p.media_type.toLowerCase() })),
      p.error ? h('div', { class: 'small form-error', text: p.error }) : null));
}

function drawSummary() {
  if (!S.summaryBox) return;
  const c = (S.state && S.state.counts) || {};
  const n = (...k) => k.reduce((a, s) => a + (c[s] || 0), 0);
  const stat = (label, val, hot) => h('div', { class: 'stat' + (hot && val ? ' hot' : '') }, h('b', { text: String(val) }), label);
  S.summaryBox.replaceChildren(stat('Need you', n('READY_FOR_REVIEW'), true), stat('Preparing', n('DRAFT', 'RENDERING')),
    stat('Going out', n('APPROVED', 'PUBLISHING')), stat('Done', n('PUBLISHED', 'DRY_RUN_COMPLETE')), stat('Problems', n('FAILED')));
}
function drawBoard() {
  if (!S.boardBox) return;
  S.boardBox.replaceChildren(...COLS.map((col) => {
    const items = S.posts.filter((p) => col.states.includes(p.state));
    return h('section', { class: 'col' + (items.length ? '' : ' empty') },
      h('h2', {}, col.title, h('span', { text: String(items.length) })), ...items.map(postCard));
  }));
}
function feedItem(a) {
  return h('li', { class: 'lv-' + a.level }, h('time', { text: fmtTime(a.created_at) + (a.permission_level && a.permission_level !== 'Observe' ? '  |  ' + a.permission_level : '') }), a.message);
}

async function showLive() {
  S.view = { name: 'live' };
  view.replaceChildren(h('p', { class: 'muted', text: 'Loading...' }));
  try { await Promise.all([refreshState(), refreshPosts(), loadActivity()]); } catch (e) { view.replaceChildren(h('p', { class: 'form-error', text: e.message })); return; }
  S.summaryBox = h('div', { class: 'summary' });
  S.boardBox = h('div', { class: 'board' });
  S.feedList = h('ul', {}, ...S.activity.slice().reverse().slice(0, 60).map(feedItem));
  const empty = !S.posts.length
    ? h('div', { class: 'card' }, h('h2', { text: 'Nothing here yet' }),
        h('p', { class: 'muted', text: 'Start a post from a short brief, or drop an export from Swishy into the inbox folder and it will appear here by itself.' }),
        h('a', { class: 'btn primary', href: '#/new', text: 'New post' }))
    : null;
  view.replaceChildren(h('div', { class: 'live' },
    h('div', {}, S.summaryBox, empty, S.boardBox),
    h('aside', { class: 'card' }, h('h2', { text: 'Activity, live' }), h('div', { class: 'feed' }, S.feedList))));
  drawSummary(); drawBoard();
}

// ---------- confirm dialog -------------------------------------------------------------------------
function confirmDialog(title, body, okText) {
  return new Promise((resolve) => {
    const d = $('dlg');
    $('dlg-title').textContent = title; $('dlg-body').textContent = body; $('dlg-ok').textContent = okText;
    d.returnValue = 'cancel';
    d.addEventListener('close', () => resolve(d.returnValue === 'ok'), { once: true });
    d.showModal();
  });
}

// ---------- post review ------------------------------------------------------------------------------
async function showPost(id) {
  S.view = { name: 'post', id, dirty: false, safe: false, idx: 0 };
  view.replaceChildren(h('p', { class: 'muted', text: 'Loading...' }));
  try { drawPost(await api('/api/posts/' + id)); }
  catch (e) { view.replaceChildren(h('p', { class: 'form-error', text: e.message }), h('a', { href: '#/' }, 'Back to the board')); }
}

async function reloadPost(id, keep) {
  try { const p = await api('/api/posts/' + id); if (S.view.name === 'post' && S.view.id === id) drawPost(p, keep); } catch (e) { toast(e.message, 'bad'); }
}

function drawPost(p, keep) {
  const V = S.view;
  const locked = p.locked;
  const val = (k, fallback) => (keep && keep[k] !== undefined ? keep[k] : fallback);
  const title = h('input', { id: 'f-title', value: val('title', p.title), disabled: locked, maxlength: '120', 'aria-label': 'Title' });
  const caption = h('textarea', { id: 'f-caption', value: val('caption', p.caption), disabled: locked, maxlength: '2200', rows: '7' });
  const tags = h('input', { id: 'f-tags', value: val('tags', p.hashtags), disabled: locked, placeholder: '#example #tags' });
  const when = h('input', { id: 'f-when', type: 'datetime-local', value: val('when', toLocalInput(p.scheduled_for)), disabled: locked });
  const count = h('div', { class: 'count' });
  const save = h('button', { class: 'btn primary', text: 'Save changes', disabled: true });
  const updateCount = () => {
    const n = (caption.value.trim() + (tags.value.trim() ? '\n\n' + tags.value.trim() : '')).length;
    count.textContent = n + ' of 2200';
    count.classList.toggle('over', n > 2200);
  };
  const markDirty = () => { V.dirty = true; save.disabled = false; updateCount(); };
  [title, caption, tags, when].forEach((el) => el.addEventListener('input', markDirty));
  if (keep) { V.dirty = true; save.disabled = false; }
  updateCount();

  const doSave = async () => {
    save.disabled = true;
    try {
      const np = await api('/api/posts/' + p.id, { method: 'PATCH', json: { title: title.value, caption: caption.value, hashtags: tags.value, scheduled_for: when.value ? new Date(when.value).toISOString() : '' } });
      V.dirty = false; toast('Saved', 'good'); drawPost(np);
    } catch (e) { toast(e.message, 'bad'); save.disabled = false; }
  };
  save.addEventListener('click', doSave);

  const act = async (label, fn) => {
    if (V.dirty) { toast('Save your changes first.', 'bad'); return; }
    try { const np = await fn(); drawPost(np); if (label) toast(label, 'good'); } catch (e) { toast(e.message, 'bad'); }
  };
  const post = (path, json) => () => api('/api/posts/' + p.id + path, { method: 'POST', json: json || {} });

  // media preview
  const a = p.assets[Math.min(V.idx, p.assets.length - 1)];
  let media;
  if (!a) media = h('div', { class: 'empty', text: p.busy ? 'Preparing the media...' : 'No media yet. Add a file or make a text video.' });
  else if (a.status !== 'ready') media = h('div', { class: 'empty', text: a.status === 'error' ? 'This file could not be prepared.' : 'Preparing the media...' });
  else if (a.kind === 'image') media = h('img', { src: a.url, alt: 'Preview of the post' });
  else media = h('video', { src: a.url, controls: '', playsinline: '', preload: 'metadata' });
  const safeT = h('div', { class: 'safe t' }), safeB = h('div', { class: 'safe b' });
  safeT.hidden = safeB.hidden = !V.safe;
  const safeToggle = h('input', { type: 'checkbox', id: 'safe-toggle', checked: V.safe, onchange: (e) => { V.safe = e.target.checked; safeT.hidden = safeB.hidden = !V.safe; } });
  const thumbs = p.assets.length > 1 ? h('div', { class: 'thumbs' }, ...p.assets.map((x, i) => h('button', { class: i === V.idx ? 'on' : '', type: 'button', 'aria-label': 'File ' + (i + 1), onclick: () => { V.idx = i; drawPost(p, V.dirty ? { title: title.value, caption: caption.value, tags: tags.value, when: when.value } : null); } },
    x.kind === 'image' ? h('img', { src: x.url, alt: '' }) : h('video', { src: x.url + '#t=0.1', preload: 'metadata', muted: true })))) : null;

  // uploads
  const fileInput = h('input', { type: 'file', multiple: true, accept: '.mp4,.mov,.m4v,.webm,.gif,.jpg,.jpeg,.png,video/*,image/*', 'aria-label': 'Choose files' });
  const upBtn = h('button', { class: 'btn', text: p.media_type === 'CAROUSEL' ? 'Add files' : (a ? 'Replace file' : 'Upload file'), disabled: locked });
  upBtn.addEventListener('click', async () => {
    if (!fileInput.files.length) { toast('Choose a file first.', 'bad'); return; }
    if (V.dirty) { toast('Save your changes first.', 'bad'); return; }
    upBtn.disabled = true; upBtn.textContent = 'Uploading...';
    const fd = new FormData(); for (const f of fileInput.files) fd.append('file', f);
    try { drawPost(await api(`/api/posts/${p.id}/assets`, { method: 'POST', form: fd })); toast('Uploaded. Preparing it for Instagram.', 'good'); }
    catch (e) { toast(e.message, 'bad'); upBtn.disabled = false; upBtn.textContent = 'Upload file'; }
  });

  // checks
  const checks = h('ul', { class: 'checks' }, ...p.checks.map((c) => h('li', { class: c.level, text: c.text })));

  // actions
  const dry = p.dry_run;
  const btns = [];
  const confirmPublish = async () => {
    if (V.dirty) { toast('Save your changes first.', 'bad'); return; }
    const when = p.scheduled_for ? ' It is scheduled for ' + fmtDateTime(p.scheduled_for) + ' and will go out then.' : '';
    const ok = await confirmDialog(dry ? 'Run a dry run?' : 'Publish to Instagram?',
      dry ? 'Dry run is on. This approves this exact video and caption and rehearses publishing. Nothing will be posted to Instagram.'
          : 'This approves this exact video and caption and posts it to your Instagram account.' + when, dry ? 'Approve and dry run' : 'Approve and publish');
    if (ok) act(dry ? 'Dry run started' : 'Publishing started', post('/publish'));
  };
  if (p.state === 'READY_FOR_REVIEW') {
    btns.push(h('button', { class: 'btn approve', text: dry ? 'Approve and dry run' : 'Approve and publish', disabled: !p.can_approve, onclick: confirmPublish }));
    btns.push(h('button', { class: 'btn', text: 'Approve only', disabled: !p.can_approve, onclick: () => act('Approved', post('/approve')) }));
    btns.push(h('button', { class: 'btn', text: 'Send back for edits', onclick: () => act('', post('/send-back')) }));
    btns.push(h('button', { class: 'btn danger', text: 'Reject', onclick: async () => { if (await confirmDialog('Reject this post?', 'It moves to Needs attention. You can edit it later.', 'Reject')) act('Rejected', post('/reject')); } }));
  } else if (['APPROVED', 'FAILED', 'DRY_RUN_COMPLETE'].includes(p.state)) {
    btns.push(h('button', { class: 'btn approve', text: p.state === 'DRY_RUN_COMPLETE' && !dry ? 'Publish for real' : (dry ? 'Run dry run again' : 'Publish now'), onclick: confirmPublish }));
    btns.push(h('button', { class: 'btn', text: 'Send back for edits', onclick: () => act('', post('/send-back')) }));
  } else if (p.state === 'PUBLISHED' && p.permalink) {
    btns.push(h('a', { class: 'btn primary', href: p.permalink, target: '_blank', rel: 'noopener noreferrer', text: 'Open on Instagram' }));
  }
  if (!locked) btns.push(h('button', { class: 'btn danger', text: 'Remove from board', onclick: async () => { if (await confirmDialog('Remove this post?', 'It disappears from the board. Published posts on Instagram are not affected.', 'Remove')) { try { await api('/api/posts/' + p.id, { method: 'DELETE' }); location.hash = '#/'; } catch (e) { toast(e.message, 'bad'); } } } }));

  const tools = locked ? null : h('div', { class: 'row' },
    p.media_type !== 'IMAGE' ? h('button', { class: 'btn', text: 'Make a text video', onclick: () => act('Building the video', post('/render-text')) }) : null,
    h('button', { class: 'btn', text: 'Write caption again', onclick: () => act('Writing a new caption', post('/regenerate')) }),
    p.assets.some((x) => x.source !== 'rendered') ? h('button', { class: 'btn', text: 'Prepare media again', onclick: () => act('Preparing again', post('/reprocess')) }) : null);

  view.replaceChildren(h('div', {},
    h('div', { class: 'row', style: null }, h('a', { href: '#/', class: 'btn ghost', text: 'Back to the board' }),
      h('span', { class: 'badge ' + p.state, text: LABEL[p.state] || p.state }), h('span', { class: 'badge', text: p.media_type.toLowerCase() }),
      p.busy ? h('span', { class: 'muted small', text: 'Working on it...' }) : null),
    p.error ? h('p', { class: 'form-error', text: p.error }) : null,
    h('div', { class: 'post' },
      h('div', {}, h('div', { class: 'phone' }, media, safeT, safeB), thumbs,
        h('label', { for: 'safe-toggle', class: 'small' }, safeToggle, ' Show where Instagram covers the video')),
      h('div', { class: 'card' },
        h('label', { for: 'f-title', text: 'Title (only you see this)' }), title,
        h('label', { for: 'f-caption', text: 'Caption' }), caption, count,
        h('label', { for: 'f-tags', text: 'Hashtags' }), tags,
        h('label', { for: 'f-when', text: 'Publish later (optional, needs approval first)' }), when,
        h('div', { class: 'row', style: null }, save),
        h('h3', { text: 'Media' }), h('div', { class: 'row' }, fileInput, upBtn), tools,
        h('h3', { text: 'Checks' }), checks,
        h('div', { class: 'actions' }, ...btns)))));
}

// ---------- new post -----------------------------------------------------------------------------------
function showNew() {
  S.view = { name: 'new' };
  const title = h('input', { id: 'n-title', maxlength: '120', placeholder: 'For example: 3 tips for better sleep' });
  const brief = h('textarea', { id: 'n-brief', maxlength: '4000', placeholder: 'What should the post say? A few sentences is enough. Any language.' });
  const type = h('select', { id: 'n-type' }, ...[['REEL', 'Reel (vertical video)'], ['IMAGE', 'Image'], ['CAROUSEL', 'Carousel (2 to 10 files)'], ['STORY', 'Story']].map(([v, t]) => h('option', { value: v, text: t })));
  const mode = h('select', { id: 'n-mode' }, h('option', { value: 'auto', text: 'Make a text video for me' }), h('option', { value: 'own', text: 'I will add my own files' }));
  const files = h('input', { type: 'file', id: 'n-files', multiple: true, accept: '.mp4,.mov,.m4v,.webm,.gif,.jpg,.jpeg,.png,video/*,image/*' });
  const go = h('button', { class: 'btn primary', text: 'Create post' });
  const sync = () => { const canAuto = type.value === 'REEL' || type.value === 'STORY'; mode.disabled = !canAuto; if (!canAuto) mode.value = 'own'; };
  type.addEventListener('change', sync); sync();
  go.addEventListener('click', async () => {
    go.disabled = true; go.textContent = 'Creating...';
    try {
      const p = await api('/api/posts', { method: 'POST', json: { title: title.value, brief: brief.value, media_type: type.value, auto_render: mode.value === 'auto' } });
      if (files.files.length) {
        const fd = new FormData(); for (const f of files.files) fd.append('file', f);
        try { await api(`/api/posts/${p.id}/assets`, { method: 'POST', form: fd }); } catch (e) { toast(e.message, 'bad'); }
      }
      location.hash = '#/post/' + p.id;
    } catch (e) { toast(e.message, 'bad'); go.disabled = false; go.textContent = 'Create post'; }
  });
  const inbox = S.state ? S.state.settings.inbox_dir : '';
  view.replaceChildren(h('div', { class: 'card', style: null },
    h('h1', { text: 'New post' }),
    h('p', { class: 'muted', text: 'Write a brief and the agent writes the caption and builds the video. You review it before anything is posted.' }),
    h('label', { for: 'n-title', text: 'Title' }), title, h('label', { for: 'n-brief', text: 'Brief' }), brief,
    h('label', { for: 'n-type', text: 'Post type' }), type, h('label', { for: 'n-mode', text: 'Visual' }), mode,
    h('label', { for: 'n-files', text: 'Files (optional)' }), files,
    inbox ? h('p', { class: 'muted small', text: 'Tip: files dropped into ' + inbox + ' (for example a Swishy export) become draft posts automatically.' }) : null,
    h('div', { class: 'actions' }, go)));
}

// ---------- settings -----------------------------------------------------------------------------------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const LANGS = [['en-IN', 'English (India)'], ['hi-IN', 'Hindi'], ['or-IN', 'Odia (some browsers do not support it)'], ['en-US', 'English (US)'], ['en-GB', 'English (UK)']];

async function showSettings() {
  S.view = { name: 'settings' };
  await refreshState();
  const s = S.state ? S.state.settings : {};
  const row = (k, v, kind) => [h('dt', { text: k }), h('dd', {}, v, kind ? h('span', { class: 'pill ' + kind, text: kind === 'ok' ? 'OK' : kind === 'warn' ? 'Check' : 'Fix' }) : null)];
  const langSel = h('select', { id: 's-lang', onchange: (e) => { prefs.lang = e.target.value; savePrefs(); fillVoices(); } }, ...LANGS.map(([v, t]) => h('option', { value: v, text: t, selected: v === prefs.lang })));
  const voiceSel = h('select', { id: 's-voice', onchange: (e) => { prefs.voice = e.target.value; savePrefs(); } });
  function fillVoices() {
    voiceSel.replaceChildren(h('option', { value: '', text: 'Automatic' }));
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.getVoices().filter((v) => v.lang.slice(0, 2) === prefs.lang.slice(0, 2)).forEach((v) => voiceSel.append(h('option', { value: v.name, text: v.name + ' (' + v.lang + ')', selected: v.name === prefs.voice })));
  }
  fillVoices();
  if ('speechSynthesis' in window) speechSynthesis.onvoiceschanged = fillVoices;
  const check = (label, key) => h('label', { class: 'small' }, h('input', { type: 'checkbox', checked: !!prefs[key], style: null, onchange: (e) => { prefs[key] = e.target.checked; savePrefs(); } }), ' ' + label);
  const rate = h('input', { type: 'range', min: '0.7', max: '1.4', step: '0.1', value: String(prefs.rate), 'aria-label': 'Speaking speed', oninput: (e) => { prefs.rate = parseFloat(e.target.value); savePrefs(); } });
  const secure = window.isSecureContext;
  view.replaceChildren(h('div', { class: 'card' }, h('h1', { text: 'Settings' }),
    h('h2', { text: 'System' }),
    h('dl', { class: 'kv' },
      ...row('Video tools (FFmpeg)', s.ffmpeg ? 'Installed' : 'Not found. Install FFmpeg and restart.', s.ffmpeg ? 'ok' : 'bad'),
      ...row('Background worker', S.state && S.state.workers_alive ? 'Running' : 'Not running', S.state && S.state.workers_alive ? 'ok' : 'bad'),
      ...row('Posting mode', s.dry_run ? 'Dry run: nothing is posted' : 'Live posting', s.dry_run ? 'warn' : 'ok'),
      ...row('Instagram account', s.ig_connected ? 'Connected' : 'Not connected yet', s.ig_connected ? 'ok' : 'warn'),
      ...row('Public media link', s.public_media ? 'Configured' : 'Not set (needed for live posting)', s.public_media ? 'ok' : 'warn'),
      ...row('AI writer', s.llm === 'offline' ? 'Offline fallback (add an AI key for better captions and conversation)' : s.llm, s.llm === 'offline' ? 'warn' : 'ok'),
      ...row('Speak on this PC', s.local_tts ? (s.local_tts_available ? 'On' : 'On, but no speech tool found') : 'Off (LOCAL_TTS=1 in .env)', s.local_tts && s.local_tts_available ? 'ok' : ''),
      ...row('Phone alerts (Telegram)', s.telegram ? 'On' : 'Off', ''),
      ...row('Inbox folder', s.inbox_dir || ''),
      ...row('Upload limit', (s.max_upload_mb || 0) + ' MB per file')),
    h('h2', { text: 'Voice' }),
    !SR ? h('p', { class: 'muted', text: 'This browser cannot listen. Use Chrome or Edge to talk to the assistant, or type instead. It can still speak.' }) : null,
    SR && !secure ? h('p', { class: 'form-error', text: 'Microphone use needs a secure address (https, or localhost on the PC). See docs/REMOTE_ACCESS.md to use voice on your phone.' }) : null,
    h('label', { for: 's-lang', text: 'Language for listening and speaking' }), langSel,
    h('label', { for: 's-voice', text: 'Voice' }), voiceSel,
    h('label', { text: 'Speaking speed' }), rate,
    h('div', { class: 'actions' }, check('Speak replies out loud', 'speak'), check('Keep listening after each reply (hands-free)', 'handsFree'), check('Alert me when something needs me', 'alerts')),
    h('div', { class: 'row' },
      h('button', { class: 'btn', text: 'Test the voice', onclick: () => speak('Hello. This is how I sound.') }),
      'Notification' in window ? h('button', { class: 'btn', text: 'Allow desktop notifications', onclick: async () => { const r = await Notification.requestPermission(); toast(r === 'granted' ? 'Notifications are on.' : 'Notifications were not allowed.', r === 'granted' ? 'good' : 'bad'); } }) : null),
    h('h2', { text: 'Account' }),
    h('div', { class: 'row' },
      h('a', { class: 'btn', href: '/api/activity/export', text: 'Download activity log (CSV)' }),
      h('form', { method: 'post', action: '/logout' }, h('input', { type: 'hidden', name: 'csrf_token', value: csrf }), h('button', { class: 'btn danger', type: 'submit', text: 'Sign out' })))));
}

// ---------- assistant: voice and chat ------------------------------------------------------------------
const A = { open: false, mode: 'idle', convo: false, rec: null, err: '', noSpeech: 0, historyLoaded: false, interimEl: null };

function setMode(m) {
  A.mode = m;
  $('orb').className = 'orb big' + (m !== 'idle' ? ' ' + m : '');
  $('orb-mini').className = 'orb' + (m !== 'idle' ? ' ' + m : '');
  $('orb-status').textContent = { idle: 'Ready', listening: 'Listening...', thinking: 'Thinking...', speaking: 'Speaking...' }[m];
  $('mic').classList.toggle('on', m === 'listening');
  $('mic').textContent = m === 'listening' ? 'Stop' : 'Mic';
}
function addMsg(role, text) {
  const m = h('div', { class: 'msg ' + (role === 'user' ? 'user' : ''), text });
  $('msgs').append(m); $('msgs').scrollTop = $('msgs').scrollHeight; return m;
}
function hint(text) { $('voice-hint').textContent = text || ''; }

function pickVoice() {
  if (!('speechSynthesis' in window)) return null;
  const vs = speechSynthesis.getVoices();
  return vs.find((v) => v.name === prefs.voice) || vs.find((v) => v.lang === prefs.lang) || vs.find((v) => v.lang.slice(0, 2) === prefs.lang.slice(0, 2)) || null;
}
function stopSpeech() { if ('speechSynthesis' in window) speechSynthesis.cancel(); }
function speak(text) {
  return new Promise((resolve) => {
    if (!prefs.speak || !('speechSynthesis' in window) || !text) { resolve(); return; }
    stopSpeech();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = prefs.lang; u.rate = prefs.rate;
    const v = pickVoice(); if (v) u.voice = v;
    const done = () => { clearTimeout(guard); resolve(); };
    const guard = setTimeout(done, Math.min(45000, 3000 + text.length * 110)); // some browsers never fire 'end'
    u.onend = done; u.onerror = done;
    speechSynthesis.speak(u);
  });
}

function stopListening() { if (A.rec) { try { A.rec.abort(); } catch (e) { /* already stopped */ } A.rec = null; } if (A.mode === 'listening') setMode('idle'); }
function clearInterim() { if (A.interimEl) { A.interimEl.remove(); A.interimEl = null; } }

function listen() {
  if (!SR) { hint('This browser cannot listen. Use Chrome or Edge, or type your message.'); return; }
  if (A.mode === 'listening' || A.mode === 'thinking') return;
  stopSpeech();
  const rec = new SR();
  A.rec = rec; A.err = '';
  rec.lang = prefs.lang; rec.interimResults = true; rec.continuous = false; rec.maxAlternatives = 1;
  let finalText = '';
  rec.onstart = () => { setMode('listening'); hint(''); };
  rec.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) { const r = e.results[i]; if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript; }
    if (!A.interimEl) A.interimEl = addMsg('user', '');
    A.interimEl.classList.add('interim'); A.interimEl.textContent = (finalText + interim).trim();
  };
  rec.onerror = (e) => {
    A.err = e.error;
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') { A.convo = false; hint('The microphone is blocked. Allow it in the browser. Phones also need the secure (https) address.'); }
    else if (e.error === 'language-not-supported') { A.convo = false; hint('This browser does not support listening in that language. Pick another in Settings.'); }
    else if (e.error === 'network') { A.convo = false; hint('Listening needs an internet connection in this browser.'); }
  };
  rec.onend = () => {
    const wasAborted = A.rec !== rec;
    clearInterim();
    if (A.mode === 'listening') setMode('idle');
    if (wasAborted) return;
    A.rec = null;
    const t = finalText.trim();
    if (t) { A.noSpeech = 0; submit(t, true); }
    else if (A.convo && (A.err === '' || A.err === 'no-speech') && ++A.noSpeech < 3) setTimeout(listen, 300);
    else if (A.convo) { A.convo = false; addMsg('assistant', 'I am here when you need me. Press the mic to talk.'); }
  };
  try { rec.start(); } catch (e) { /* already started */ }
}

async function submit(text, viaVoice) {
  text = text.trim(); if (!text) return;
  addMsg('user', text);
  if (/^(stop|goodbye|bye|that'?s all|cancel|quiet)\b/i.test(text)) { A.convo = false; stopSpeech(); stopListening(); addMsg('assistant', 'Okay. Press the mic when you need me.'); setMode('idle'); return; }
  setMode('thinking');
  let speech = '';
  try {
    const r = await api('/api/assistant', { method: 'POST', json: { message: text } });
    speech = r.speech; addMsg('assistant', r.speech);
    if (r.confirm) showConfirmCard(r.confirm);
    if (r.navigate) location.hash = r.navigate;
  } catch (e) { speech = e.message; addMsg('assistant', e.message); }
  setMode('speaking'); await speak(speech); setMode('idle');
  if (A.open && A.convo && SR) listen();
}

function showConfirmCard(c) {
  const card = $('confirm-card');
  const ok = h('button', { class: 'btn approve', text: 'Confirm' });
  const no = h('button', { class: 'btn', text: 'Cancel', onclick: () => { card.hidden = true; } });
  ok.addEventListener('click', async () => {
    ok.disabled = true;
    try { const r = await api('/api/assistant/confirm', { method: 'POST', json: { token: c.token } }); addMsg('assistant', r.speech); card.hidden = true; toast(r.speech, 'good'); speak(r.speech); }
    catch (e) { addMsg('assistant', e.message); card.hidden = true; }
  });
  card.replaceChildren(h('p', { text: c.summary }), h('div', { class: 'row' }, ok, no));
  card.hidden = false;
}

async function openAssistant() {
  $('assistant').hidden = false; A.open = true;
  if (!A.historyLoaded) {
    A.historyLoaded = true;
    try { (await api('/api/assistant/history')).messages.slice(-6).forEach((m) => addMsg(m.role, m.content)); } catch (e) { /* ignore */ }
  }
  hint(!SR ? 'This browser cannot listen. Type your message instead.' : (!window.isSecureContext ? 'Voice input needs https on phones. Typing works everywhere.' : ''));
  try {
    const b = await api('/api/briefing');
    addMsg('assistant', b.text);
    setMode('speaking'); await speak(b.text); setMode('idle');
  } catch (e) { addMsg('assistant', e.message); }
  if (A.open && SR && window.isSecureContext) { A.convo = prefs.handsFree; if (A.convo) listen(); }
}
function closeAssistant() { A.open = false; A.convo = false; stopListening(); stopSpeech(); $('assistant').hidden = true; setMode('idle'); }

$('orb-open').addEventListener('click', () => (A.open ? closeAssistant() : openAssistant()));
$('assistant-close').addEventListener('click', closeAssistant);
$('mic').addEventListener('click', () => { if (A.mode === 'listening') { A.convo = false; stopListening(); } else { A.convo = prefs.handsFree; listen(); } });
$('send').addEventListener('click', () => { const v = $('say').value; $('say').value = ''; submit(v, false); });
$('say').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); $('send').click(); } });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && A.open && !$('dlg').open) closeAssistant(); });

// ---------- live events (server-sent) -------------------------------------------------------------------
function onActivity(a) {
  if (a.id <= S.lastActivity) return;
  S.lastActivity = a.id; S.activity.push(a);
  if (S.view.name === 'live' && S.feedList) { S.feedList.prepend(feedItem(a)); while (S.feedList.children.length > 80) S.feedList.lastChild.remove(); }
  if (a.level === 'attention' || a.level === 'error') {
    toast(a.message, a.level === 'error' ? 'bad' : '');
    if (prefs.alerts) {
      if ('Notification' in window && Notification.permission === 'granted' && document.hidden) { try { new Notification('IG Content Agent', { body: a.message }); } catch (e) { /* ignore */ } }
      else if (!document.hidden && A.mode === 'idle' && (!navigator.userActivation || navigator.userActivation.hasBeenActive)) speak(a.message);
    }
  }
}
function onPost(d) {
  debounced('sync', 300, async () => {
    await refreshState();
    if (S.view.name === 'live') { try { await refreshPosts(); } catch (e) { return; } drawSummary(); drawBoard(); }
    else if (S.view.name === 'post' && S.view.id === d.id) {
      const keep = S.view.dirty ? { title: $('f-title').value, caption: $('f-caption').value, tags: $('f-tags').value, when: $('f-when').value } : null;
      reloadPost(d.id, keep);
    }
  });
}
function connectEvents() {
  const es = new EventSource('/api/events');
  es.addEventListener('hello', () => { S.live = true; renderPills(); });
  es.addEventListener('activity', (ev) => { try { onActivity(JSON.parse(ev.data)); } catch (e) { /* ignore */ } });
  es.addEventListener('post', (ev) => { try { onPost(JSON.parse(ev.data)); } catch (e) { /* ignore */ } });
  es.onerror = () => { S.live = false; renderPills(); };
}

// ---------- start ---------------------------------------------------------------------------------------
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => { /* needs https or localhost */ });
setMode('idle');
connectEvents();
setInterval(refreshState, 15000);
route();
})();
