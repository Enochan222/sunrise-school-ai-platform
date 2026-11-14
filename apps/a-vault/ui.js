/* SUNRISE WP07 · Candidate UI Port · IMPLEMENTED_UNTESTED */
'use strict';

const $ = (id) => document.getElementById(id);

class GatewayError extends Error {
  constructor(status) {
    super('Gateway request failed');
    this.status = status;
  }
}

// Browser owns the signed HttpOnly session cookie. Session CSRF stays in JS
// memory only; never persist auth material in browser storage or URL parameters.
const api = (() => {
  let csrf = '';
  const shells = '/vault/v1/shells';
  const shellPath = (id) => shells + '/' + encodeURIComponent(id);
  const materials = (id) => shellPath(id) + '/materials';

  async function request(path, { method = 'GET', json, body, key, protectedWrite = true, pdf = false } = {}) {
    const headers = new Headers({ Accept: pdf ? 'application/pdf' : 'application/json' });
    if (json !== undefined) {
      headers.set('Content-Type', 'application/json');
      body = JSON.stringify(json);
    }
    if (method !== 'GET' && protectedWrite) {
      if (!csrf) throw new GatewayError(401);
      headers.set('X-CSRF-Token', csrf);
    }
    if (key) headers.set('Idempotency-Key', key);

    const timeout = new AbortController();
    const timer = window.setTimeout(() => timeout.abort(), 90_000);
    try {
      const response = await fetch(path, {
        method, headers, body, mode: 'same-origin', credentials: 'same-origin',
        cache: 'no-store', redirect: 'error', signal: timeout.signal
      });
      if (!response.ok) throw new GatewayError(response.status);
      const type = response.headers.get('Content-Type') || '';
      if (pdf && type.split(';')[0].trim().toLowerCase() === 'application/pdf') return await response.blob();
      if (!pdf && type.includes('application/json')) return await response.json();
      throw new GatewayError(0);
    } catch (error) {
      throw error instanceof GatewayError ? error : new GatewayError(0);
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    setCsrf(value) { csrf = value; },
    login: (body) => request('/auth/login', { method: 'POST', body, protectedWrite: false }),
    session: () => request('/auth/me'),
    switchSchool: (school_id) => request('/auth/school', { method: 'POST', json: {school_id} }),
    logout: () => request('/auth/logout', { method: 'POST' }),
    listShells: () => request(shells),
    getShell: (id) => request(shellPath(id)),
    create: (json, key) => request(shells, { method: 'POST', json, key }),
    listMaterials: (id) => request(materials(id)),
    upload: (id, body, key) => request(materials(id), { method: 'POST', body, key }),
    search: (id, query) => request(shellPath(id) + '/search', { method: 'POST', json: { query } }),
    archive: (id) => request(shellPath(id) + '/archive', { method: 'POST' }),
    download: (id, source) => request(materials(id) + '/' + encodeURIComponent(source) + '/download', { pdf: true })
  };
})();

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function notice(id, text, error = false) {
  const node = $(id);
  node.textContent = text;
  node.dataset.error = String(error);
}

function errorMessage(error, login = false) {
  switch (error.status) {
    case 401: return login ? '管理員密碼不正確。' : '登入已失效，請重新登入。';
    case 403: return login ? '登入驗證已失效或不獲允許，請重新載入登入頁。' : '權限或請求驗證不獲通過。請重新核對登入狀態。';
    case 404: return '找不到資料，或目前帳戶無權查閱。';
    case 409: return '資料與現有記錄有衝突。請重新整理並核對結果。';
    case 413: return 'PDF 大小超出教材庫的限制。';
    case 422: return '資料格式或內容不符要求。請核對欄位、檔名和 PDF 內容。';
    case 429: return '請求過於頻密。請稍候再手動重試。';
    case 503: return '教材庫暫時未能確認結果。';
    case 0: return '連線中斷、逾時或回應格式有誤。請稍後核對結果。';
    default: return error.status >= 500 ? '教材庫暫時未能完成請求。' : '未能完成請求。請核對資料。';
  }
}

function setupLogin() {
  const form = $('login');
  const submit = form.querySelector('button');
  const password = $('password');
  let busy = false;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy) return;
    const csrf = form.elements.namedItem('csrf').value;
    if (!csrf || csrf === '__SUNRISE_LOGIN_CSRF__') {
      notice('login-status', '未取得有效的登入頁，請重新載入。', true);
      $('reload-login').hidden = false;
      password.value = '';
      return;
    }

    busy = true;
    submit.disabled = true;
    const body = new FormData(form);
    password.value = '';
    notice('login-status', '正在登入…');
    try {
      const result = await api.login(body);
      if (result.authenticated !== true) throw new GatewayError(0);
      window.location.replace('/admin');
    } catch (error) {
      notice('login-status', errorMessage(error, true), true);
      $('reload-login').hidden = error.status !== 403;
      password.focus();
    } finally {
      body.delete('password');
      busy = false;
      submit.disabled = false;
    }
  });
}

function setupAdmin() {
  const state = {
    session: null, sessionBusy: false, sessionEpoch: 0, listVersion: 0,
    detailVersion: 0, materialsVersion: 0, searchVersion: 0,
    shells: [], shell: null, selectedId: null, receipt: null,
    mutation: null, writing: false, searching: false, downloads: new Set()
  };
  const fields = [
    ['學年', 'academic_year'], ['年級', 'grade'],
    ['科目', 'subject'], ['課程類別', 'curriculum_stream']
  ];

  function clearPrivate() {
    state.sessionEpoch++;
    state.session = null;
    state.shells = [];
    state.shell = null;
    state.selectedId = null;
    state.mutation = null;
    state.receipt = null;
    api.setCsrf('');
    for (const id of ['shells', 'shell-meta', 'materials', 'search-results']) $(id).replaceChildren();
    for (const id of ['create', 'upload', 'search']) $(id).reset();
    for (const id of ['active-school', 'detail-title', 'shell-summary', 'detail-status',
      'materials-status', 'search-status', 'upload-receipt', 'pending-message']) $(id).textContent = '';
    $('filter').value = '';
    $('school-choice').replaceChildren();
    $('detail').hidden = true;
    $('retry-detail').hidden = true;
    $('workspace').hidden = true;
    $('logout').hidden = true;
  }

  function showError(id, error) {
    if (error.status === 401) {
      clearPrivate();
      notice('notice', errorMessage(error), true);
      $('retry-session').hidden = true;
      $('sign-in-again').hidden = false;
      $('sign-in-again').focus();
    } else {
      notice(id, errorMessage(error), true);
      if (error.status === 403) $('retry-session').hidden = false;
    }
  }

  function assertOwned(shell, expectedId) {
    if (!shell || typeof shell.shell_id !== 'string' || !shell.shell_id ||
        (expectedId !== undefined && shell.shell_id !== expectedId) ||
        shell.school_id !== state.session.school_id) throw new GatewayError(403);
    return shell;
  }

  function syncControls() {
    // Session hydration is asynchronous: visible workspace is not yet write-ready.
    // Prevent an early click from being silently discarded by canWrite().
    const blocked = !state.session || state.sessionBusy || state.writing || Boolean(state.mutation);
    $('create-submit').disabled = blocked;
    $('upload-submit').disabled = blocked || !state.shell || Boolean(state.shell.archived);
    $('archive').disabled = blocked || !state.shell || Boolean(state.shell.archived);
    $('search-submit').disabled = state.sessionBusy || state.searching || !state.shell;
    $('logout').disabled = state.writing || state.sessionBusy;
    $('switch-school-submit').disabled = blocked || state.sessionBusy;
    $('reconcile').disabled = state.writing;
    $('pending').hidden = !state.mutation;
    $('reconcile').textContent = state.mutation?.kind === 'archive'
      ? '重新查閱封存狀態' : '以原有請求核對結果';
  }

  function renderList() {
    const filter = $('filter').value.trim().toLocaleLowerCase('zh-HK');
    const list = $('shells');
    list.replaceChildren();
    const matches = state.shells.filter((shell) => fields
      .map(([, key]) => shell[key]).join(' ').toLocaleLowerCase('zh-HK').includes(filter));
    for (const shell of matches) {
      const title = [shell.subject, shell.grade, shell.academic_year, shell.curriculum_stream].join(' · ');
      const button = element('button', title + (shell.archived ? '（已封存）' : ''), 'secondary');
      button.type = 'button';
      button.setAttribute('aria-pressed', String(shell.shell_id === state.selectedId));
      button.addEventListener('click', () => openShell(shell.shell_id, true));
      const item = element('li');
      item.append(button);
      list.append(item);
    }
    notice('shell-summary', matches.length ? '顯示 ' + matches.length + ' 個容器。'
      : state.shells.length ? '沒有符合條件的容器。' : '目前未有教材容器。');
  }

  async function refreshShells() {
    if (!state.session) return;
    const version = ++state.listVersion;
    const epoch = state.sessionEpoch;
    const current = () => epoch === state.sessionEpoch && version === state.listVersion;
    $('refresh-shells').disabled = true;
    notice('shell-summary', '正在載入容器…');
    try {
      const data = await api.listShells();
      if (!current()) return;
      if (!Array.isArray(data.shells)) throw new GatewayError(0);
      state.shells = data.shells.map((shell) => assertOwned(shell));
      renderList();
    } catch (error) {
      if (current()) {
        state.shells = [];
        $('shells').replaceChildren();
        showError('shell-summary', error);
      }
    } finally {
      if (version === state.listVersion) $('refresh-shells').disabled = false;
    }
  }

  function renderShell(shell) {
    $('detail-title').textContent = shell.subject + ' · ' + shell.grade;
    const meta = $('shell-meta');
    meta.replaceChildren();
    const rows = [['學校', shell.school_id], ...fields.map(([label, key]) => [label, shell[key]]),
      ['容器編號', shell.shell_id], ['Notebook 編號', shell.notebook_id || '未提供'],
      ['狀態', shell.archived ? '已封存' : '使用中']];
    for (const [label, value] of rows) meta.append(element('dt', label), element('dd', value));
    $('archive').hidden = Boolean(shell.archived);
    $('archive-note').hidden = !shell.archived;
    $('upload').hidden = Boolean(shell.archived);
    $('detail').hidden = false;
    syncControls();
  }

  function showReceipt(id) {
    const receipt = state.receipt;
    $('upload-receipt').hidden = !receipt || receipt.shellId !== id;
    if (!$('upload-receipt').hidden) {
      notice('upload-receipt', '已提交處理。來源 ' + receipt.source_id + '，版本 '
        + receipt.version + '，SHA-256 ' + receipt.sha256 + '。目前未有處理完成確認。');
    }
  }

  async function openShell(id, focus = false) {
    if (!state.session) return;
    const version = ++state.detailVersion;
    const epoch = state.sessionEpoch;
    const current = () => epoch === state.sessionEpoch && version === state.detailVersion;
    state.selectedId = id;
    state.shell = null;
    state.searching = false;
    $('detail').hidden = true;
    $('retry-detail').hidden = true;
    $('upload').reset();
    $('search').reset();
    $('materials').replaceChildren();
    $('search-results').replaceChildren();
    notice('search-status', '');
    notice('materials-status', '');
    renderList();
    syncControls();
    notice('detail-status', '正在載入容器詳情…');
    try {
      const shell = await api.getShell(id);
      if (!current()) return;
      state.shell = assertOwned(shell, id);
      renderShell(shell);
      showReceipt(id);
      notice('detail-status', '');
      if (focus) $('detail-title').focus();
      await refreshMaterials();
    } catch (error) {
      if (current()) {
        showError('detail-status', error);
        if (state.session) $('retry-detail').hidden = false;
      }
    }
  }

  function downloadButton(id, sourceId, title) {
    const button = element('button', '下載原始 PDF', 'secondary');
    button.type = 'button';
    button.setAttribute('aria-label', '下載原始 PDF：' + title);
    button.addEventListener('click', () => download(id, sourceId, button));
    return button;
  }

  async function download(id, sourceId, button) {
    if (!state.session || state.shell?.shell_id !== id) return;
    const key = id + '/' + sourceId;
    if (state.downloads.has(key)) return;
    state.downloads.add(key);
    button.disabled = true;
    const epoch = state.sessionEpoch;
    const version = state.detailVersion;
    try {
      const blob = await api.download(id, sourceId);
      if (epoch !== state.sessionEpoch || version !== state.detailVersion) return;
      const url = URL.createObjectURL(blob);
      const link = element('a');
      link.href = url;
      // The gateway currently serves a fixed attachment filename.
      link.download = 'source.pdf';
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (error) {
      if (epoch === state.sessionEpoch && version === state.detailVersion) showError('detail-status', error);
    } finally {
      state.downloads.delete(key);
      button.disabled = false;
    }
  }

  async function refreshMaterials() {
    const id = state.shell?.shell_id;
    if (!state.session || !id) return;
    const epoch = state.sessionEpoch;
    const detail = state.detailVersion;
    const version = ++state.materialsVersion;
    const current = () => epoch === state.sessionEpoch && detail === state.detailVersion && version === state.materialsVersion;
    $('refresh-materials').disabled = true;
    $('materials').replaceChildren();
    notice('materials-status', '正在載入材料…');
    try {
      const data = await api.listMaterials(id);
      if (!current()) return;
      if (!Array.isArray(data.materials)) throw new GatewayError(0);
      for (const material of data.materials) {
        if (typeof material.source_id !== 'string' || !material.source_id) throw new GatewayError(0);
        const item = element('li');
        const title = String(material.title || material.source_id);
        // Normalized by the authenticated A Gateway after live Native ownership
        // re-check; incomplete/ambiguous Worker states must never appear READY.
        const status = ({
          READY: '已確認 Native 文字抽取完成。',
          PROCESSING: 'Native Worker 已排隊或正在處理，請稍後手動更新。',
          FAILED: 'Native 處理失敗；請交管理員核對，系統不會自動重送。',
          UNKNOWN: 'Native 處理狀態未能確認，請稍後手動更新。',
          PENDING: '已提交處理，尚未確認 Worker 結果。',
          SUBMITTED_NATIVE_PROCESSING: '已提交處理，尚未確認 Worker 結果。'
        })[material.state] || '處理狀態未能確認。';
        const meta = element('dl', undefined, 'metadata');
        for (const [label, value] of [['來源編號', material.source_id], ['原始檔名', material.original_name],
          ['版本', material.version], ['SHA-256', material.sha256], ['授權', material.license], ['保留資料', material.retention]]) {
          if (value !== undefined && value !== null) meta.append(element('dt', label), element('dd', String(value)));
        }
        item.append(element('strong', title), meta, element('p', status),
          downloadButton(id, material.source_id, title));
        $('materials').append(item);
      }
      notice('materials-status', data.materials.length ? '共 ' + data.materials.length + ' 份材料。'
        : '此容器未有可查閱的材料。');
    } catch (error) {
      if (current()) {
        $('materials').replaceChildren();
        showError('materials-status', error);
      }
    } finally {
      if (version === state.materialsVersion) $('refresh-materials').disabled = false;
    }
  }

  async function search(event) {
    event.preventDefault();
    const id = state.shell?.shell_id;
    const query = $('query').value.trim();
    if (!state.session || !id || state.searching) return;
    if (!query) {
      notice('search-status', '請輸入文字關鍵字。', true);
      return;
    }
    const epoch = state.sessionEpoch;
    const detail = state.detailVersion;
    const version = ++state.searchVersion;
    const current = () => epoch === state.sessionEpoch && detail === state.detailVersion && version === state.searchVersion;
    state.searching = true;
    syncControls();
    $('search-results').replaceChildren();
    notice('search-status', '正在搜尋此容器…');
    try {
      const data = await api.search(id, query);
      if (!current()) return;
      if (data.search_type !== 'text' || !Array.isArray(data.results)) throw new GatewayError(0);
      for (const result of data.results) {
        if (typeof result.source_id !== 'string' || !result.source_id) throw new GatewayError(0);
        const item = element('li');
        const title = String(result.title || result.source_id);
        item.append(element('strong', title), element('p', '來源編號 ' + result.source_id),
          downloadButton(id, result.source_id, title));
        $('search-results').append(item);
      }
      notice('search-status', data.results.length ? '找到 ' + data.results.length + ' 項結果。'
        : '此容器沒有符合條件的材料。');
    } catch (error) {
      if (current()) {
        $('search-results').replaceChildren();
        showError('search-status', error);
      }
    } finally {
      if (current()) {
        state.searching = false;
        syncControls();
      }
    }
  }

  function makeKey() {
    if (typeof globalThis.crypto?.randomUUID !== 'function') throw new GatewayError(0);
    return globalThis.crypto.randomUUID();
  }

  function canWrite() {
    return state.session && !state.sessionBusy && !state.writing && !state.mutation;
  }

  async function sendMutation(operation, reconcile = false) {
    if (!state.session || state.sessionBusy || state.writing || state.mutation !== operation) return;
    const epoch = state.sessionEpoch;
    const current = () => epoch === state.sessionEpoch;
    state.writing = true;
    syncControls();
    notice('notice', reconcile ? '正在核對原有請求…' : '正在提交…');

    let result;
    try {
      if (operation.kind === 'create') {
        result = await api.create(operation.body, operation.key);
        if (!current()) return;
        assertOwned(result);
        if (typeof result.notebook_id !== 'string' || !result.notebook_id.startsWith('notebook:')) {
          throw new GatewayError(0);
        }
      } else if (operation.kind === 'upload') {
        result = await api.upload(operation.shellId, operation.body, operation.key);
        if (!current()) return;
        if (result.state !== 'SUBMITTED_NATIVE_PROCESSING' || typeof result.source_id !== 'string' ||
            !result.source_id.startsWith('source:') || result.version !== 1 ||
            typeof result.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(result.sha256)) {
          throw new GatewayError(0);
        }
      } else {
        result = reconcile ? await api.getShell(operation.shellId) : await api.archive(operation.shellId);
        if (!current()) return;
        assertOwned(result, operation.shellId);
        if (!reconcile && !result.archived) throw new GatewayError(0);
      }
    } catch (error) {
      if (!current()) return;
      showError('notice', error);
      if (!current()) return;
      if ([400, 404, 413, 422].includes(error.status) || (error.status === 409 && !reconcile)) {
        state.mutation = null;
        if (error.status === 409) {
          await refreshShells();
          if (operation.shellId && state.selectedId === operation.shellId) await openShell(operation.shellId);
        }
      } else {
        notice('pending-message', operation.kind === 'archive'
          ? '封存結果未獲確認。請先查閱容器狀態。'
          : '結果未獲確認。請以相同資料及識別鍵核對原有請求。若仍未能確認，請交由管理員跟進。');
      }
      return;
    } finally {
      state.writing = false;
      syncControls();
    }

    if (!current()) return;
    state.mutation = null;
    syncControls();
    if (operation.kind === 'create') {
      $('create').reset();
      $('filter').value = '';
      notice('notice', '教材容器已建立，並已配對 Notebook。');
      await refreshShells();
      if (current()) await openShell(result.shell_id, true);
    } else if (operation.kind === 'upload') {
      state.receipt = { ...result, shellId: operation.shellId };
      notice('notice', '教材庫已確認上載提交。');
      if (state.shell?.shell_id === operation.shellId) {
        $('upload').reset();
        showReceipt(operation.shellId);
        await refreshMaterials();
      }
    } else {
      notice('notice', result.archived ? '教材容器已封存。' : '容器目前未封存。請核對後再決定是否封存。');
      await refreshShells();
      if (current() && state.selectedId === operation.shellId) await openShell(operation.shellId, true);
    }
  }

  $('create').addEventListener('submit', (event) => {
    event.preventDefault();
    if (!canWrite()) return;
    const form = new FormData(event.currentTarget);
    const body = Object.fromEntries(fields.map(([, name]) => [name, String(form.get(name)).trim()]));
    if (Object.values(body).some((value) => !value)) {
      notice('notice', '請填寫所有分類欄位。', true);
      return;
    }
    try {
      state.mutation = { kind: 'create', body, key: makeKey() };
      void sendMutation(state.mutation);
    } catch (error) {
      showError('notice', error);
    }
  });

  $('upload').addEventListener('submit', (event) => {
    event.preventDefault();
    if (!canWrite() || !state.shell || state.shell.archived) return;
    const body = new FormData(event.currentTarget);
    const file = body.get('file');
    if (!(file instanceof File) || !file.size || !/\.pdf$/i.test(file.name) ||
        file.name.length > 180 || /[\\/]/.test(file.name)) {
      notice('notice', '請選擇一個有效檔名的 PDF。', true);
      return;
    }
    for (const name of ['title', 'license', 'retention']) {
      const value = String(body.get(name)).trim();
      if (!value) {
        notice('notice', '請填寫教材標題、授權和保留資料。', true);
        return;
      }
      body.set(name, value);
    }
    try {
      state.mutation = { kind: 'upload', shellId: state.shell.shell_id, body, key: makeKey() };
      void sendMutation(state.mutation);
    } catch (error) {
      showError('notice', error);
    }
  });

  $('archive').addEventListener('click', () => {
    if (!canWrite() || !state.shell || state.shell.archived) return;
    if (!window.confirm('封存後將不能再向此容器上載材料。確定封存？')) return;
    state.mutation = { kind: 'archive', shellId: state.shell.shell_id };
    void sendMutation(state.mutation);
  });

  $('reconcile').addEventListener('click', () => {
    if (state.mutation) void sendMutation(state.mutation, true);
  });

  async function checkSession() {
    if (state.sessionBusy || state.writing) return;
    state.sessionBusy = true;
    const epoch = state.sessionEpoch;
    $('retry-session').disabled = true;
    $('workspace').hidden = true;
    $('logout').hidden = true;
    syncControls();
    notice('notice', '正在核對登入狀態…');
    try {
      const session = await api.session();
      if (epoch !== state.sessionEpoch) return;
      if (typeof session.school_id !== 'string' || !session.school_id ||
          typeof session.actor_id !== 'string' || !session.actor_id ||
          typeof session.csrf_token !== 'string' || !session.csrf_token) throw new GatewayError(403);
      if (state.session && (state.session.school_id !== session.school_id ||
          state.session.actor_id !== session.actor_id || state.session.csrf_token !== session.csrf_token)) {
        clearPrivate();
      }
      state.session = session;
      api.setCsrf(session.csrf_token);
      if (!Array.isArray(session.available_schools) ||
          session.available_schools.some((id) => typeof id !== 'string' || !id) ||
          !session.available_schools.includes(session.school_id)) throw new GatewayError(403);
      const select = $('school-choice');
      select.replaceChildren();
      for (const id of session.available_schools) {
        const option=element('option',id);
        option.value=id;
        select.append(option);
      }
      select.value=session.school_id;
      // Single-school demo hides the switcher; the server session still owns identity.
      // Synthetic A/B authorization mode continues to display trusted choices.
      $('switch-school').hidden = session.available_schools.length === 1;
      $('active-school').textContent = session.school_id;
      $('workspace').hidden = false;
      $('logout').hidden = false;
      $('sign-in-again').hidden = true;
      $('retry-session').hidden = true;
      notice('notice', '');
      if (!state.selectedId) notice('detail-status', '請先選擇教材容器。');
      await refreshShells();
      if (state.selectedId) await openShell(state.selectedId);
    } catch (error) {
      if (epoch !== state.sessionEpoch) return;
      if (error.status !== 401) {
        $('retry-session').hidden = false;
        $('sign-in-again').hidden = false;
      }
      showError('notice', error);
    } finally {
      state.sessionBusy = false;
      $('retry-session').disabled = false;
      syncControls();
    }
  }

  $('switch-school').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!state.session || state.sessionBusy || state.writing || state.mutation) return;
    const choice=$('school-choice').value;
    if (!state.session.available_schools?.includes(choice)) {
      notice('notice','沒有伺服器授權的學校選項。',true);
      return;
    }
    if (choice===state.session.school_id) return;
    state.writing=true;
    syncControls();
    notice('notice','正在更新受信任的學校 Session…');
    try {
      const changed=await api.switchSchool(choice);
      if (!changed || changed.school_id!==choice || !changed.csrf_token) {
        throw new GatewayError(0);
      }
    } catch(error) {
      // A lost response may mean CSRF/session school already rotated.
      // Never operate using an optimistic client-selected school.
      notice('notice',errorMessage(error),true);
    } finally {
      state.writing=false;
      clearPrivate();
      $('sign-in-again').hidden=false;
      void checkSession(); // only the server returns the actual active school
    }
  });

  $('logout').addEventListener('click', async () => {
    if (!state.session || state.writing || state.sessionBusy) return;
    if (state.mutation && !window.confirm('登出後，本頁不會保留未確認的請求。確定登出？')) return;
    state.writing = true;
    syncControls();
    notice('notice', '正在登出…');
    try {
      await api.logout();
      clearPrivate();
      window.location.replace('/auth/login');
    } catch (error) {
      showError('notice', error);
    } finally {
      state.writing = false;
      syncControls();
    }
  });

  $('filter').addEventListener('input', renderList);
  $('refresh-shells').addEventListener('click', () => void refreshShells());
  $('refresh-materials').addEventListener('click', () => void refreshMaterials());
  $('retry-detail').addEventListener('click', () => {
    if (state.selectedId) void openShell(state.selectedId, true);
  });
  $('search').addEventListener('submit', search);
  $('retry-session').addEventListener('click', () => void checkSession());
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      clearPrivate();
      void checkSession();
    }
  });
  void checkSession();
}

if (document.body.dataset.page === 'login') setupLogin();
if (document.body.dataset.page === 'admin') setupAdmin();
