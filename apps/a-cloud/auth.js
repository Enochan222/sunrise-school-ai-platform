'use strict';
const byId = id => document.getElementById(id);
const page = document.body.dataset.page;
let csrfToken = '';
function notice(text) {
  const target = byId(page === 'login' ? 'login-status' : 'account-status');
  target.textContent = text;
}
async function call(path, {method='GET', body}={}) {
  const headers = {Accept:'application/json'};
  if (method !== 'GET' && csrfToken) headers['X-CSRF-Token'] = csrfToken;
  const response = await fetch(path,{method,headers,body,credentials:'same-origin',
    mode:'same-origin',cache:'no-store',redirect:'error'});
  if (!response.ok) {
    const messages = {400:'請核對輸入資料。',401:'登入資料不正確或已失效，請重新登入。',
      403:'請求驗證未通過，請重新登入後再試。',409:'設定狀態已改變，請重新載入。',
      422:'請核對格式、密碼長度及兩次輸入是否一致。',429:'嘗試太頻密，請稍候再試。'};
    throw new Error(messages[response.status] || '服務暫時未能完成請求，請稍後再試。');
  }
  return response.json();
}
function bind(id, path, after) {
  const form = byId(id);
  let busy = false;
  form.addEventListener('submit',async event => {
    event.preventDefault();
    if (busy) return;
    busy = true;
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    const body = new FormData(form);
    for (const input of form.querySelectorAll('input[type="password"], input[autocomplete="one-time-code"]')) input.value='';
    notice('正在處理…');
    try {
      const result = await call(path,{method:'POST',body});
      after(result);
    } catch(error) {
      notice(error.message || '連線失敗，請稍後再試。');
    } finally {
      for (const key of Array.from(body.keys())) body.delete(key);
      busy = false;
      button.disabled = false;
    }
  });
}
const navigate = result => {
  if (!['/admin','/auth/mfa','/auth/login'].includes(result.next)) throw new Error('未能確認下一步。');
  location.replace(result.next);
};
async function initialize() {
  if (page === 'login') {
    bind('login','/auth/login',navigate);
    const link=document.createElement('a');link.href='/auth/activate';link.textContent='首次使用／以 Owner 啟用碼重設密碼';
    byId('login').after(link);
  } else if (page === 'password') {
    byId('account-title').textContent='更改密碼';
    const state=await call('/auth/me');csrfToken=state.csrf_token;
    byId('password-panel').hidden=false;
    bind('password-form','/account/password',navigate);
  } else if (page === 'activate') {
    byId('account-title').textContent='設定管理員密碼';
    const state=await call('/auth/activation-csrf');csrfToken=state.csrf_token;
    byId('activate-panel').hidden=false;
    // A private Owner fragment is removed before any network request. Never
    // persist activation secrets in browser storage or analytics.
    if (location.hash.startsWith('#code=')) {
      byId('activation-code').value=decodeURIComponent(location.hash.slice(6));
      history.replaceState(null,'','/auth/activate');
    }
    bind('activate-form','/auth/activate',navigate);
  } else if (page === 'mfa') {
    byId('account-title').textContent='兩步驗證';
    const state=await call('/auth/mfa/state');csrfToken=state.csrf_token;
    byId('mfa-panel').hidden=false;
    if (state.factor_id) {
      byId('factor-id').value=state.factor_id;byId('mfa-form').hidden=false;
    } else byId('enroll-panel').hidden=false;
    byId('enroll').addEventListener('click',async () => {
      byId('enroll').disabled=true;
      try {
        const result=await call('/auth/mfa/enroll',{method:'POST'});
        byId('factor-id').value=result.factor_id;
        byId('totp-secret').textContent=result.secret;
        const svg=result.qr_code;
        byId('qr').src=svg.startsWith('data:image/svg+xml;') ? svg : 'data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(svg)));
        byId('qr').hidden=false;byId('manual-key').hidden=false;byId('mfa-form').hidden=false;
        notice('請用自己的驗證器掃描，再輸入六位數字。');
      } catch(error) {
        notice(error.message);byId('enroll').disabled=false;
      }
    });
    bind('mfa-form','/auth/mfa/verify',navigate);
  }
}
initialize().catch(error=>notice(error.message || '未能載入登入設定，請重新登入。'));
