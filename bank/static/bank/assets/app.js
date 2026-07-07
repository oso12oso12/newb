/* ===================== City Prime Bank — Shared App Logic ===================== */

const CPB = (() => {
  const STORAGE_KEY = 'cpb_dashboard_state';

  const defaultState = {
    balances: { checking: 12480.32, savings: 34912.10, credit: 1204.55 },
    transactions: [
      {name:'Whole Foods Market', meta:'Groceries • Jul 5', amount:-84.21, icon:'cart', color:'#e2661a'},
      {name:'Payroll Deposit', meta:'Direct Deposit • Jul 4', amount:3250.00, icon:'arrow-down', color:'#149775'},
      {name:'Netflix', meta:'Subscription • Jul 3', amount:-15.99, icon:'tv', color:'#c23c76'},
      {name:'Transfer to Savings', meta:'Internal Transfer • Jul 2', amount:-500.00, icon:'swap', color:'#0f6fb8'},
      {name:'Shell Gas Station', meta:'Fuel • Jul 1', amount:-46.10, icon:'fuel', color:'#e2661a'},
      {name:'Amazon Refund', meta:'Refund • Jun 30', amount:22.50, icon:'arrow-down', color:'#149775'},
    ]
  };

  function loadState(){
    try{
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if(saved && saved.balances && saved.transactions) return saved;
    }catch(e){}
    return JSON.parse(JSON.stringify(defaultState));
  }

  let state = loadState();

  function saveState(){
    try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }catch(e){}
  }

  function resetState(){
    state = JSON.parse(JSON.stringify(defaultState));
    saveState();
  }

  const fmt = n => (Number(n) || 0).toLocaleString('en-US', {style:'currency', currency:'USD'});

  const icons = {
    cart:'<path d="M3 3h2l2.4 12.2A2 2 0 0 0 9.4 17H18a2 2 0 0 0 2-1.6L21 8H6"/><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/>',
    'arrow-down':'<path d="M12 4v13m0 0 5-5m-5 5-5-5"/>',
    tv:'<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8"/>',
    swap:'<path d="M7 10 3 6l4-4M3 6h13a4 4 0 0 1 4 4v1M17 14l4 4-4 4M21 18H8a4 4 0 0 1-4-4v-1"/>',
    fuel:'<path d="M4 21V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v15M4 10h10M16 8l3 2v6a1.5 1.5 0 0 0 3 0V9l-3-3"/>',
    bill:'<path d="M4 19V6a2 2 0 0 1 2-2h9l5 5v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/>'
  };

  function addTransaction(name, meta, amount, icon, color){
    state.transactions.unshift({name, meta, amount, icon, color});
    saveState();
  }

  function initChrome(){
    const menuBtn = document.getElementById('menuBtn');
    const sidebar = document.getElementById('sidebar');
    const sideScrim = document.getElementById('sideScrim');
    if(menuBtn && sidebar && sideScrim){
      menuBtn.addEventListener('click', () => { sidebar.classList.add('open'); sideScrim.classList.add('show'); document.body.style.overflow = 'hidden'; });
      sideScrim.addEventListener('click', closeSidebar);
      sidebar.querySelectorAll('a').forEach(a => a.addEventListener('click', closeSidebar));
    }
    function closeSidebar(){
      sidebar.classList.remove('open');
      sideScrim.classList.remove('show');
      document.body.style.overflow = '';
    }
  }

  function showToast(title, body){
    const t = document.getElementById('toast');
    if(!t) return;
    document.getElementById('toastTitle').textContent = title;
    document.getElementById('toastBody').textContent = body;
    t.classList.add('show');
    clearTimeout(window._cpbToastTimer);
    window._cpbToastTimer = setTimeout(() => t.classList.remove('show'), 3800);
  }

  function txRowHtml(t){
    return `
      <div class="tx-row">
        <div class="tx-ic" style="background:${t.color}"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">${icons[t.icon] || icons.bill}</svg></div>
        <div class="tx-info"><div class="nm">${t.name}</div><div class="meta">${t.meta}</div></div>
        <div class="tx-amt ${t.amount < 0 ? 'neg' : 'pos'}">${t.amount < 0 ? '-' : '+'}${fmt(Math.abs(t.amount))}</div>
      </div>`;
  }

  return {
    get state(){ return state; },
    saveState, resetState, fmt, icons, addTransaction, initChrome, showToast, txRowHtml
  };
})();
