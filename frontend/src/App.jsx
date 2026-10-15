import React, { createContext, useContext, useEffect, useState } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeftRight, BadgeCheck, Building2, Calculator, ChartNoAxesCombined, ClipboardList, Command, FileClock, HandCoins, LayoutDashboard, LogOut, Menu, UserRound, Users, Wallet } from 'lucide-react';
import api from './services/api';

const AuthContext = createContext(null);
const money = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value || 0));
const isManager = user => user?.role === 'BRANCH_MANAGER';
const navigation = {
  BRANCH_MANAGER: [
    { title: 'BRANCH WORKSPACE', items: [
      ['Dashboard', '/manager/dashboard', LayoutDashboard], ['Customers', '/manager/customers', Users],
      ['Accounts', '/manager/accounts', Wallet], ['Transactions', '/manager/transactions', FileClock],
    ] },
    { title: 'LOAN MANAGEMENT', items: [['Applications & repayments', '/manager/loans', HandCoins]] },
  ],
  CUSTOMER: [
    { title: 'MY BANKING', items: [
      ['Dashboard', '/customer/dashboard', LayoutDashboard], ['My accounts', '/customer/accounts', Wallet],
      ['Transfer funds', '/customer/transfer', ArrowLeftRight], ['Transactions', '/customer/transactions', FileClock],
      ['My profile', '/customer/profile', UserRound],
    ] },
    { title: 'CREDIT & LOANS', items: [
      ['Credit Health', '/customer/credit-health', ChartNoAxesCombined],
      ['Apply for a Loan', '/customer/apply-loan', HandCoins],
      ['EMI Calculator', '/customer/emi-calculator', Calculator],
      ['My Loan Applications', '/customer/loan-applications', ClipboardList],
      ['Repayment Tracker', '/customer/repayments', BadgeCheck],
    ] },
  ],
};

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    api.get('/auth/me').then(response => setUser(response.data.user)).catch(() => setUser(null)).finally(() => setChecking(false));
  }, []);
  if (checking) return <div className="min-h-screen grid place-items-center text-slate-500">Checking your session…</div>;
  return <AuthContext.Provider value={{ user, setUser }}><Routes>
    <Route path="/login" element={<LoginPage/>}/>
    <Route path="/" element={<HomeRedirect/>}/>
    <Route path="/manager/*" element={<Protected role="BRANCH_MANAGER"><Workspace/></Protected>}/>
    <Route path="/customer/*" element={<Protected role="CUSTOMER"><Workspace/></Protected>}/>
    <Route path="*" element={<HomeRedirect/>}/>
  </Routes></AuthContext.Provider>;
}

function HomeRedirect() {
  const { user } = useContext(AuthContext);
  return <Navigate replace to={user ? (isManager(user) ? '/manager/dashboard' : '/customer/dashboard') : '/login'}/>;
}

function Protected({ role, children }) {
  const { user } = useContext(AuthContext);
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }}/>;
  if (user.role !== role) return <Navigate to={isManager(user) ? '/manager/dashboard' : '/customer/dashboard'} replace/>;
  return children;
}

function LoginPage() {
  const { user, setUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  if (user) return <HomeRedirect/>;
  async function submit(event) {
    event.preventDefault(); setError(''); setLoading(true);
    try {
      const response = await api.post('/auth/login', form);
      setUser(response.data.user);
      navigate(response.data.user.role === 'BRANCH_MANAGER' ? '/manager/dashboard' : '/customer/dashboard', { replace: true });
    } catch (problem) { setError(problem.response?.data?.error || 'Could not sign in. Check that Flask is running.'); }
    finally { setLoading(false); }
  }
  return <main className="min-h-screen grid lg:grid-cols-2 bg-cloud">
    <section className="hidden lg:flex flex-col justify-between p-12 bg-powder">
      <div className="flex items-center gap-3"><span className="h-11 w-11 rounded-xl bg-blue text-white grid place-items-center shadow-card"><Command/></span><div><b className="text-xl text-navy">Meridian</b><p className="text-xs text-slate-500 m-0">BANKING PORTAL</p></div></div>
      <div className="max-w-lg"><p className="text-xs uppercase tracking-[.22em] text-blue">Secure workspace</p><h1 className="text-5xl font-bold leading-tight text-navy">Banking made clear.</h1><p className="text-slate-600 text-lg">A single place for branch operations and personal accounts.</p><div className="mt-8 h-1 w-20 rounded-full bg-champagne"/></div>
      <p className="text-xs text-slate-500">College demonstration • Fictional data only</p>
    </section>
    <section className="flex items-center justify-center px-6 py-12 bg-cloud">
      <form onSubmit={submit} className="card p-7 sm:p-9 w-full max-w-md">
        <div className="lg:hidden flex items-center gap-3 mb-8"><span className="h-10 w-10 rounded-xl bg-blue text-white grid place-items-center"><Command/></span><b className="text-navy">Meridian Banking</b></div>
        <p className="text-xs uppercase tracking-[.18em] font-bold text-blue mb-2">Welcome back</p><h2 className="text-3xl font-bold text-navy m-0">Sign in</h2><p className="text-sm text-slate-500 mt-2 mb-7">Use your manager or customer demo account.</p>
        {error && <div role="alert" className="rounded-lg bg-rose-50 text-rose-700 p-3 text-sm mb-4">{error}</div>}
        <label className="block text-sm font-semibold mb-4">Username or email<input className="field mt-1.5" autoComplete="username" required value={form.username} onChange={event => setForm({ ...form, username: event.target.value })}/></label>
        <label className="block text-sm font-semibold mb-6">Password<input className="field mt-1.5" type="password" autoComplete="current-password" required value={form.password} onChange={event => setForm({ ...form, password: event.target.value })}/></label>
        <button className="btn w-full py-3" disabled={loading}>{loading ? 'Signing in…' : 'Sign in securely'}</button>
        <div className="mt-6 border-t pt-5 text-xs leading-6 text-slate-500"><b className="text-slate-700">Demo credentials</b><br/>Manager: <code>manager</code> / <code>Manager123!</code><br/>Customer: <code>aarav</code> / <code>Customer123!</code></div>
      </form>
    </section>
  </main>;
}

function Workspace() {
  const { user, setUser } = useContext(AuthContext);
  const [mobileOpen, setMobileOpen] = useState(false);
  const links = navigation[user.role] || [];
  async function logout() { await api.post('/auth/logout').catch(() => {}); setUser(null); }
  return <div className="min-h-screen">
    <aside className={`${mobileOpen ? 'fixed' : 'hidden'} lg:block fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-slate-200 px-5 py-6`}>
      <div className="flex items-center gap-3 mb-10"><div className="h-10 w-10 rounded-xl bg-blue text-white grid place-items-center"><Command/></div><div><b className="text-navy">Meridian</b><div className="text-[11px] text-slate-400">BANKING PORTAL</div></div></div>
      <nav className="space-y-5">{links.map(group => <div key={group.title}><div className="text-[10px] tracking-widest font-bold text-slate-400 mb-2 px-3">{group.title}</div><div className="space-y-1">{group.items.map(([label, path, Icon]) => <NavLink onClick={() => setMobileOpen(false)} key={path} to={path} className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm ${isActive ? 'bg-blue/10 text-blue' : 'text-slate-500 hover:bg-slate-50'}`}><Icon size={18}/>{label}</NavLink>)}</div></div>)}</nav>
      <div className="absolute bottom-6 left-5 right-5 card p-4 bg-slate-50 text-xs"><b>{user.customer_name || user.username}</b><div className="text-slate-400 mt-1">{isManager(user) ? user.branch_name : 'Customer'}</div></div>
    </aside>
    <main className="lg:ml-64 min-h-screen">
      <header className="h-[72px] bg-white border-b px-5 md:px-9 flex items-center justify-between sticky top-0 z-20"><button className="lg:hidden" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu"><Menu/></button><div className="hidden lg:block text-xs text-slate-400">Meridian　›　{isManager(user) ? 'Branch Manager' : 'Customer'}</div><div className="flex items-center gap-4"><span className="hidden sm:inline text-xs text-slate-500">{user.branch_name || 'Personal banking'}</span><button className="text-xs font-semibold text-slate-600 flex items-center gap-2" onClick={logout}><LogOut size={16}/> Sign out</button></div></header>
      <section className="px-5 md:px-9 py-7 max-w-[1440px] mx-auto">
        {isManager(user) ? <Routes>
          <Route path="dashboard" element={<ManagerDashboard/>}/>
          <Route path="customers" element={<ManagerCustomers/>}/>
          <Route path="accounts" element={<ManagerAccounts/>}/>
          <Route path="transactions" element={<ManagerTransactions/>}/>
          <Route path="loans" element={<ManagerLoans/>}/>
          <Route path="*" element={<Navigate replace to="/manager/dashboard"/>}/>
        </Routes> : <Routes>
          <Route path="dashboard" element={<CustomerDashboard/>}/>
          <Route path="accounts" element={<CustomerAccounts/>}/>
          <Route path="transfer" element={<CustomerTransfer/>}/>
          <Route path="transactions" element={<CustomerTransactions/>}/>
          <Route path="profile" element={<CustomerProfile/>}/>
          <Route path="credit-health" element={<CreditHealth/>}/>
          <Route path="apply-loan" element={<LoanApplication/>}/>
          <Route path="emi-calculator" element={<EmiCalculator/>}/>
          <Route path="loan-applications" element={<CustomerLoanApplications/>}/>
          <Route path="repayments" element={<RepaymentTracker/>}/>
          <Route path="*" element={<Navigate replace to="/customer/dashboard"/>}/>
        </Routes>}
      </section>
    </main>
  </div>;
}

function Heading({ eyebrow, title, sub, action }) { return <div className="flex flex-wrap justify-between items-end gap-4 mb-6"><div><div className="uppercase text-[10px] tracking-[.18em] font-bold text-blue mb-2">{eyebrow}</div><h1 className="text-2xl md:text-[28px] font-bold text-navy m-0">{title}</h1><p className="text-sm text-slate-500 mt-2 mb-0">{sub}</p></div>{action}</div>; }
function Alert({ error, success }) { if (!error && !success) return null; return <div role="status" className={`rounded-xl p-3 mb-4 text-sm ${error ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}`}>{error || success}</div>; }
function useLoad(url, params = {}) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [loading, setLoading] = useState(true), [version, setVersion] = useState(0);
  useEffect(() => { let mounted = true; setLoading(true); api.get(url, { params }).then(response => { if (mounted) { setData(response.data); setError(''); } }).catch(problem => { if (mounted) setError(problem.response?.data?.error || 'Could not load data'); }).finally(() => { if (mounted) setLoading(false); }); return () => { mounted = false; }; }, [url, JSON.stringify(params), version]);
  return { data, error, loading, reload: () => setVersion(value => value + 1), setError };
}
function Metric({ label, value, detail }) { return <div className="card p-5"><span className="text-xs text-slate-500">{label}</span><div className="text-2xl font-bold text-navy mt-4">{value}</div>{detail && <small className="text-emerald-600">{detail}</small>}</div>; }
function Loading({ text = 'Loading…' }) { return <div className="card p-6 text-sm text-slate-500">{text}</div>; }
function Empty({ children = 'No records found.' }) { return <div className="text-center text-sm text-slate-400 py-10">{children}</div>; }

function ManagerDashboard() {
  const { data, error, loading } = useLoad('/dashboard/stats');
  const { data: report } = useLoad('/reports/branch');
  if (loading) return <Loading text="Loading branch dashboard…"/>;
  if (error) return <Alert error={error}/>;
  return <><Heading eyebrow="Branch manager" title={`Good day${data.branch_name ? `, ${data.branch_name}` : ''}`} sub="Your branch at a glance."/>
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6"><Metric label="Branch customers" value={data.customers} detail="Assigned branch only"/><Metric label="Accounts" value={data.accounts}/><Metric label="Active accounts" value={data.active_accounts}/><Metric label="Branch balances" value={money(data.total_balance)}/></div>
    <div className="grid xl:grid-cols-3 gap-5"><section className="card xl:col-span-2"><div className="px-5 py-4 border-b font-bold text-sm">Recent branch transactions</div><TransactionTable rows={data.recent_transactions}/></section>
      <section className="card p-5"><b className="text-sm">Branch account statistics</b>{(report?.accounts || []).map(row => <div key={`${row.account_type}-${row.status}`} className="flex justify-between border-b py-3 text-sm"><span className="capitalize">{row.account_type} · {row.status}</span><b>{row.account_count}</b></div>)}<div className="grid grid-cols-2 gap-3 mt-5"><div className="rounded-lg bg-emerald-50 p-3 text-xs">DEPOSITS<b className="block mt-2">{money(data.deposits)}</b></div><div className="rounded-lg bg-orange-50 p-3 text-xs">WITHDRAWALS<b className="block mt-2">{money(data.withdrawals)}</b></div></div><p className="text-xs text-slate-400 mt-4">Monthly reports are available from the Transactions page.</p></section></div>
  </>;
}

function TransactionTable({ rows, customer = false }) {
  return <div className="table-wrap"><table className="w-full"><thead><tr>{customer ? <><th>Account</th><th>Type</th><th>Amount</th><th>Date</th><th>Reference</th></> : <><th>Customer</th><th>Account</th><th>Type</th><th>Amount</th><th>Date</th></>}</tr></thead><tbody>{rows?.map(row => <tr key={row.transaction_id}>{customer ? <><td>{row.account_number}</td><td className="capitalize">{String(row.transaction_type).replace('_', ' ')}</td><td>{money(row.amount)}</td><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.reference_code || '—'}</td></> : <><td>{row.customer_name}</td><td>{row.account_number}</td><td className="capitalize">{String(row.transaction_type).replace('_', ' ')}</td><td>{money(row.amount)}</td><td>{new Date(row.created_at).toLocaleString()}</td></>}</tr>)}</tbody></table>{!rows?.length && <Empty>No transactions match these filters.</Empty>}</div>;
}

function ManagerCustomers() {
  const { data: customers, error, loading, reload, setError } = useLoad('/customers');
  const [show, setShow] = useState(false), [success, setSuccess] = useState(''), [saving, setSaving] = useState(false);
  async function create(event) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    try { const response = await api.post('/customers', payload); setSuccess(`Customer login “${payload.username}” and ${payload.account_type} account ${response.data.account_number} created.`); setShow(false); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not create customer'); }
    finally { setSaving(false); }
  }
  async function edit(row) {
    const full_name = window.prompt('Full name', row.full_name); if (full_name === null) return;
    const email = window.prompt('Email', row.email); if (email === null) return;
    const phone = window.prompt('Phone number', row.phone); if (phone === null) return;
    const address = window.prompt('Address', row.address); if (address === null) return;
    try { await api.put(`/customers/${row.customer_id}`, { ...row, full_name, email, phone, address }); setSuccess('Customer details updated.'); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not update customer'); }
  }
  return <><Heading eyebrow="Branch management" title="Customers" sub="Manage customer profiles assigned to your branch." action={<button className="btn" onClick={() => setShow(!show)}>{show ? 'Close' : '+ Add customer'}</button>}/><Alert error={error} success={success}/>
    {show && <form onSubmit={create} className="card p-5 mb-5 grid sm:grid-cols-2 lg:grid-cols-4 gap-3"><Field label="Full name" name="full_name" required/><Field label="Email" name="email" type="email" required/><Field label="Phone" name="phone" required/><Field label="Address" name="address" required/><Field label="Login username" name="username" required/><Field label="Initial password (8+ characters)" name="password" type="password" required/><label className="text-xs font-semibold">First account<select name="account_type" className="field mt-1"><option value="savings">Savings</option><option value="current">Current</option></select></label><button className="btn self-end" disabled={saving}>{saving ? 'Saving…' : 'Create customer'}</button></form>}
    {loading ? <Loading/> : error && !customers ? null : <div className="card table-wrap"><table className="w-full"><thead><tr><th>Customer</th><th>Email</th><th>Phone</th><th>Branch accounts</th><th>Action</th></tr></thead><tbody>{customers?.map(row => <tr key={row.customer_id}><td className="font-semibold">{row.full_name}</td><td>{row.email}</td><td>{row.phone}</td><td>{row.account_count}</td><td><button className="text-blue text-xs font-semibold" onClick={() => edit(row)}>Edit contact</button></td></tr>)}</tbody></table>{!customers?.length && <Empty>No customers in this branch yet.</Empty>}</div>}
  </>;
}

function ManagerAccounts() {
  const { data: accounts, error, loading, reload, setError } = useLoad('/accounts');
  const { data: customers } = useLoad('/customers');
  const [show, setShow] = useState(false), [success, setSuccess] = useState('');
  async function create(event) {
    event.preventDefault(); setError(''); setSuccess(''); const payload = Object.fromEntries(new FormData(event.currentTarget));
    try { const result = await api.post('/accounts', payload); setSuccess(`Account ${result.data.account_number} created.`); setShow(false); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not create account'); }
  }
  async function toggle(row) {
    const status = String(row.status).toLowerCase() === 'active' ? 'inactive' : 'active';
    if (!window.confirm(`${status === 'active' ? 'Activate' : 'Deactivate'} account ${row.account_number}?`)) return;
    try { await api.put(`/accounts/${row.account_id}`, { status }); setSuccess(`Account ${status}.`); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not update account'); }
  }
  return <><Heading eyebrow="Branch management" title="Accounts" sub="Create accounts and manage account status in your branch." action={<button className="btn" onClick={() => setShow(!show)}>{show ? 'Close' : '+ Add account'}</button>}/><Alert error={error} success={success}/>
    {show && <form onSubmit={create} className="card p-5 mb-5 grid sm:grid-cols-3 gap-3"><label className="text-xs font-semibold">Customer<select name="customer_id" className="field mt-1" required>{customers?.map(row => <option key={row.customer_id} value={row.customer_id}>{row.full_name} · {row.email}</option>)}</select></label><label className="text-xs font-semibold">Account type<select name="account_type" className="field mt-1"><option value="savings">Savings</option><option value="current">Current</option></select></label><button className="btn self-end">Create account</button></form>}
    {loading ? <Loading/> : <div className="card table-wrap"><table className="w-full"><thead><tr><th>Account number</th><th>Customer</th><th>Type</th><th>Balance</th><th>Status</th><th>Action</th></tr></thead><tbody>{accounts?.map(row => { const active = String(row.status).toLowerCase() === 'active'; return <tr key={row.account_id}><td className="font-mono">{row.account_number}</td><td>{row.customer_name}</td><td className="capitalize">{String(row.account_type).toLowerCase()}</td><td>{money(row.balance)}</td><td className="capitalize">{String(row.status).toLowerCase()}</td><td><button className="text-blue text-xs font-semibold" onClick={() => toggle(row)}>{active ? 'Deactivate' : 'Activate'}</button></td></tr>; })}</tbody></table>{!accounts?.length && <Empty>No accounts in this branch yet.</Empty>}</div>}
  </>;
}

function ManagerTransactions() {
  const [filters, setFilters] = useState({ type: '', from: '', to: '' });
  const { data: rows, error, loading, reload, setError } = useLoad('/transactions', filters);
  const { data: accounts } = useLoad('/accounts');
  const { data: report } = useLoad('/reports/branch');
  const [success, setSuccess] = useState('');
  async function operation(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    if (!window.confirm(`Confirm ${data.kind} of ${money(data.amount)}?`)) return;
    try { await api.post(`/transactions/${data.kind}`, { account_id: data.account_id, amount: data.amount }); setSuccess(`${data.kind} completed.`); setError(''); form.reset(); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Operation failed'); }
  }
  return <><Heading eyebrow="Branch operations" title="Transactions" sub="Branch activity, manager-operated deposits and withdrawals."/><Alert error={error} success={success}/>
    <form onSubmit={operation} className="card p-4 mb-5 grid sm:grid-cols-4 gap-3"><select className="field" name="kind"><option value="deposit">Deposit</option><option value="withdraw">Withdrawal</option></select><select className="field" name="account_id" required>{accounts?.filter(row => String(row.status).toLowerCase() === 'active').map(row => <option key={row.account_id} value={row.account_id}>{row.account_number} · {row.customer_name}</option>)}</select><input className="field" name="amount" type="number" min="0.01" step="0.01" placeholder="Amount (INR)" required/><button className="btn">Confirm operation</button></form>
    <div className="card p-4 mb-4 grid sm:grid-cols-4 gap-3"><select className="field" value={filters.type} onChange={event => setFilters({ ...filters, type: event.target.value })}><option value="">All types</option>{['deposit', 'withdrawal', 'transfer_in', 'transfer_out'].map(type => <option key={type} value={type}>{type.replace('_', ' ')}</option>)}</select><input className="field" type="date" value={filters.from} onChange={event => setFilters({ ...filters, from: event.target.value })}/><input className="field" type="date" value={filters.to} onChange={event => setFilters({ ...filters, to: event.target.value })}/><button className="btn secondary" onClick={() => setFilters({ type: '', from: '', to: '' })}>Clear filters</button></div>
    {loading ? <Loading/> : <div className="card"><TransactionTable rows={rows}/></div>}
    <div className="card p-5 mt-5"><h2 className="text-base font-bold mt-0">Monthly branch report</h2><p className="text-sm text-slate-500">Deposit and withdrawal totals for the latest months.</p><div className="table-wrap"><table className="w-full"><thead><tr><th>Month</th><th>Deposits</th><th>Withdrawals</th></tr></thead><tbody>{report?.monthly_activity?.map(row => <tr key={row.month}><td>{row.month}</td><td>{money(row.deposits)}</td><td>{money(row.withdrawals)}</td></tr>)}</tbody></table>{!report?.monthly_activity?.length && <Empty>No monthly activity yet.</Empty>}</div><Link className="inline-block mt-3 text-blue text-sm font-semibold" to="/manager/dashboard">Return to branch dashboard →</Link></div>
  </>;
}

function CustomerDashboard() {
  const { data, error, loading } = useLoad('/customer/dashboard');
  if (loading) return <Loading text="Loading your accounts…"/>;
  if (error) return <Alert error={error}/>;
  return <><Heading eyebrow="Personal banking" title={`Welcome, ${data.customer_name}`} sub="A clear view of your accounts and recent activity."/>
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-6"><Metric label="Total balance" value={money(data.total_balance)} detail={`${data.accounts} account${data.accounts === 1 ? '' : 's'}`}/>{data.distribution.map(row => <Metric key={row.account_type} label={`${String(row.account_type).toLowerCase()} accounts`} value={row.count}/>)}</div>
    <h2 className="text-base font-bold mb-3">Your accounts</h2><div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">{data.accounts_list.map(account => <div className="card p-5" key={account.account_id}><div className="flex justify-between items-start"><span className="text-xs text-slate-500 capitalize">{String(account.account_type).toLowerCase()} account</span><span className={`text-xs rounded-full px-2 py-1 ${String(account.status).toLowerCase() === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{String(account.status).toLowerCase()}</span></div><div className="font-mono font-semibold mt-3">{account.account_number}</div><div className="text-2xl font-bold text-navy mt-5">{money(account.balance)}</div><div className="text-xs text-slate-400 mt-2">{account.branch_name}</div></div>)}</div>
    <section className="card"><div className="px-5 py-4 border-b font-bold text-sm">Recent activity</div><TransactionTable rows={data.recent_transactions} customer/></section>
  </>;
}

function CustomerAccounts() {
  const { data, error, loading } = useLoad('/accounts');
  return <><Heading eyebrow="Personal banking" title="My accounts" sub="Only accounts linked to your customer profile are shown."/>{error && <Alert error={error}/ >}{loading ? <Loading/> : <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{data?.map(account => <div className="card p-5" key={account.account_id}><div className="text-xs text-slate-500 capitalize">{String(account.account_type).toLowerCase()} account</div><div className="font-mono font-semibold mt-3">{account.account_number}</div><div className="text-xl font-bold mt-5">{money(account.balance)}</div><div className="flex justify-between mt-4 text-xs"><span>{account.branch_name}</span><span className="capitalize">{String(account.status).toLowerCase()}</span></div></div>)}</div>}</>;
}

function CustomerTransfer() {
  const { data: accounts } = useLoad('/accounts');
  const [error, setError] = useState(''), [success, setSuccess] = useState(null), [loading, setLoading] = useState(false);
  async function submit(event) {
    event.preventDefault(); setError(''); setSuccess(null); const form = event.currentTarget; const data = Object.fromEntries(new FormData(form));
    if (!window.confirm(`Transfer ${money(data.amount)} to account ${data.destination_account_number}?`)) return;
    setLoading(true);
    try { const response = await api.post('/transactions/transfer', data); setSuccess(response.data.reference_code); form.reset(); }
    catch (problem) { setError(problem.response?.data?.error || 'Transfer failed. No funds were moved.'); }
    finally { setLoading(false); }
  }
  const eligible = accounts?.filter(account => String(account.status).toLowerCase() === 'active') || [];
  return <><Heading eyebrow="Personal banking" title="Transfer funds" sub="Send money from your account to another active account. Transfers are recorded together or rolled back."/><Alert error={error}/>
    {success && <div className="card p-5 mb-5 border-emerald-200 bg-emerald-50"><b className="text-emerald-800">Transfer complete</b><p className="text-sm text-emerald-700 mb-2">Both account balances and transaction records were updated.</p><div className="text-xs">Receipt reference: <code>{success}</code></div><button className="text-blue text-sm font-semibold mt-3" onClick={() => window.print()}>Print receipt</button></div>}
    <div className="grid lg:grid-cols-2 gap-5"><form onSubmit={submit} className="card p-6 space-y-4"><label className="block text-sm font-semibold">From your account<select className="field mt-1" name="source_account_id" required disabled={!eligible.length}>{eligible.map(account => <option key={account.account_id} value={account.account_id}>{account.account_number} · {money(account.balance)}</option>)}</select></label><label className="block text-sm font-semibold">Recipient account number<input className="field mt-1" name="destination_account_number" inputMode="numeric" autoComplete="off" required placeholder="Enter recipient account number"/></label><label className="block text-sm font-semibold">Amount (INR)<input className="field mt-1" name="amount" type="number" min="0.01" step="0.01" required placeholder="0.00"/></label><button className="btn w-full" disabled={loading || !eligible.length}>{loading ? 'Processing…' : 'Review and transfer'}</button>{!eligible.length && <p className="text-xs text-amber-700">You need an active account to send a transfer.</p>}</form><div className="card p-6 bg-blue/5"><b>Transfer checks</b><ul className="text-sm text-slate-600 space-y-3 pl-5 mt-4"><li>Your source account must belong to you and be active.</li><li>The recipient account must exist and be active; it may belong to another customer.</li><li>The accounts must be different.</li><li>The amount must be positive and within your available balance.</li><li>Deposits and withdrawals are handled by your branch manager.</li></ul></div></div>
  </>;
}

function CustomerTransactions() {
  const [filters, setFilters] = useState({ type: '', from: '', to: '' });
  const { data: rows, error, loading } = useLoad('/transactions', filters);
  return <><Heading eyebrow="Personal banking" title="Transaction history" sub="Your account activity, with optional type and date filters."/>{error && <Alert error={error}/ >}<div className="card p-4 mb-4 grid sm:grid-cols-3 gap-3"><select className="field" value={filters.type} onChange={event => setFilters({ ...filters, type: event.target.value })}><option value="">All types</option>{['deposit', 'withdrawal', 'transfer_in', 'transfer_out'].map(type => <option key={type} value={type}>{type.replace('_', ' ')}</option>)}</select><input className="field" type="date" value={filters.from} onChange={event => setFilters({ ...filters, from: event.target.value })}/><input className="field" type="date" value={filters.to} onChange={event => setFilters({ ...filters, to: event.target.value })}/></div>{loading ? <Loading/> : <div className="card"><TransactionTable rows={rows} customer/></div>}</>;
}

function CustomerProfile() {
  const { data, error, loading, reload, setError } = useLoad('/profile');
  const [success, setSuccess] = useState('');
  async function submit(event) { event.preventDefault(); setError(''); setSuccess(''); const payload = Object.fromEntries(new FormData(event.currentTarget)); try { await api.put('/profile', payload); setSuccess('Your contact details were updated.'); reload(); } catch (problem) { setError(problem.response?.data?.error || 'Could not update profile'); } }
  return <><Heading eyebrow="Personal banking" title="My profile" sub="View your profile and update your phone number or address."/><Alert error={error} success={success}/>{loading ? <Loading/> : data && <form className="card p-6 max-w-2xl grid sm:grid-cols-2 gap-4" onSubmit={submit}><ReadOnly label="Full name" value={data.full_name}/><ReadOnly label="Email" value={data.email}/><Field label="Phone" name="phone" defaultValue={data.phone} required/><Field label="Address" name="address" defaultValue={data.address} required/><div className="sm:col-span-2"><button className="btn">Save contact details</button></div></form>}</>;
}

const loanRates = { PERSONAL: 12.5, HOME: 8.5, EDUCATION: 7.5, VEHICLE: 10.5 };
function estimateEmi(principal, annualRate, months) {
  const amount = Number(principal), period = Number(months), monthly = Number(annualRate) / 1200;
  if (!amount || !period || amount <= 0 || period <= 0) return 0;
  return monthly ? amount * monthly * ((1 + monthly) ** period) / (((1 + monthly) ** period) - 1) : amount / period;
}
function StatusPill({ status }) {
  const key = String(status || '').toUpperCase();
  const style = ['APPROVED', 'DISBURSED', 'ACTIVE', 'PAID'].includes(key) ? 'bg-emerald-50 text-emerald-700' :
    ['REJECTED', 'OVERDUE'].includes(key) ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700';
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${style}`}>{key.replace('_', ' ') || '—'}</span>;
}

function CreditHealth() {
  const { data, error, loading } = useLoad('/customer/credit-health');
  if (loading) return <Loading text="Calculating your simulated credit health…"/>;
  if (error) return <Alert error={error}/>;
  return <><Heading eyebrow="Credit & loans" title="Credit Health" sub="A simulated educational score based on Meridian demo records."/>
    <div className="grid lg:grid-cols-3 gap-4 mb-5">
      <section className="card p-5 lg:col-span-1"><div className="text-sm text-slate-500">Simulated score</div><div className="mt-3 flex items-end gap-2"><strong className="text-5xl text-navy">{data.score}</strong><span className="text-slate-400 mb-1">/ {data.maximum}</span></div><div className="mt-3"><StatusPill status={data.rating}/></div><p className="text-xs text-slate-500 mt-4 mb-0">This is a simulated educational estimate, not an official CIBIL score, credit bureau report, or lending decision.</p></section>
      <section className="card p-5 lg:col-span-2"><h2 className="text-sm font-bold mt-0">Score factors</h2><div className="space-y-4">{data.factors?.map(factor => <div key={factor.name}><div className="flex justify-between gap-3 text-sm"><b>{factor.name}</b><span>{factor.points} / {factor.out_of}</span></div><div className="h-2 bg-slate-100 rounded-full mt-2"><div className="h-2 bg-blue rounded-full" style={{ width: `${Math.round(factor.points / factor.out_of * 100)}%` }}/></div><p className="text-xs text-slate-500 mt-1 mb-0">{factor.detail}</p></div>)}</div></section>
    </div>
    <div className="grid lg:grid-cols-2 gap-5 mb-5"><section className="card p-5"><h2 className="text-sm font-bold mt-0">Debt and affordability</h2><div className="grid sm:grid-cols-2 gap-3"><Metric label="Outstanding Meridian loans" value={money(data.existing_debt)}/><Metric label="Monthly loan EMIs" value={money(data.monthly_loan_emis)}/></div><p className="text-xs text-slate-500 mt-4 mb-0">Affordability uses the latest income and existing EMI details supplied in a loan application.</p></section><section className="card p-5"><h2 className="text-sm font-bold mt-0">Ways to improve your profile</h2>{data.suggestions?.length ? <ul className="text-sm text-slate-600 space-y-3 pl-5">{data.suggestions.map(item => <li key={item}>{item}</li>)}</ul> : <p className="text-sm text-slate-500">Your available recorded factors are in good shape.</p>}{data.missing_data?.length > 0 && <div className="mt-4 rounded-lg bg-amber-50 p-3 text-xs text-amber-800"><b>Data not available</b><ul className="list-disc pl-5 mb-0">{data.missing_data.map(item => <li key={item}>{item}</li>)}</ul></div>}</section></div>
    <section className="card"><div className="px-5 py-4 border-b font-bold text-sm">Repayment history</div><div className="table-wrap"><table className="w-full"><thead><tr><th>Loan</th><th>Instalment</th><th>Due date</th><th>Due</th><th>Paid</th><th>Status</th></tr></thead><tbody>{data.repayment_history?.map(row => <tr key={row.installment_id}><td>LN-{row.loan_id}</td><td>{row.installment_no}</td><td>{String(row.due_date).slice(0,10)}</td><td>{money(row.amount_due)}</td><td>{money(row.amount_paid)}</td><td><StatusPill status={row.status === 'DUE' && new Date(`${String(row.due_date).slice(0,10)}T00:00:00`) < new Date(new Date().toDateString()) ? 'OVERDUE' : row.status}/></td></tr>)}</tbody></table>{!data.repayment_history?.length && <Empty>No Meridian loan repayment history is recorded yet.</Empty>}</div></section>
  </>;
}

function EmiCalculator() {
  const [form, setForm] = useState({ loan_type: 'PERSONAL', amount: '500000', tenure_months: '36' });
  const rate = loanRates[form.loan_type], emi = estimateEmi(form.amount, rate, form.tenure_months);
  const total = emi * Number(form.tenure_months || 0);
  return <><Heading eyebrow="Credit & loans" title="EMI Calculator" sub="Estimate an instalment before applying. Rates are illustrative for this college demo."/>
    <div className="grid lg:grid-cols-2 gap-5"><form className="card p-6 space-y-4" onSubmit={event => event.preventDefault()}><label className="block text-sm font-semibold">Loan type<select className="field mt-1" value={form.loan_type} onChange={event => setForm({ ...form, loan_type: event.target.value })}>{Object.keys(loanRates).map(type => <option key={type} value={type}>{type[0] + type.slice(1).toLowerCase()} · {loanRates[type]}% p.a.</option>)}</select></label><label className="block text-sm font-semibold">Loan amount (INR)<input className="field mt-1" type="number" min="1000" step="1000" value={form.amount} onChange={event => setForm({ ...form, amount: event.target.value })}/></label><label className="block text-sm font-semibold">Tenure (months)<input className="field mt-1" type="number" min="3" max="360" value={form.tenure_months} onChange={event => setForm({ ...form, tenure_months: event.target.value })}/></label></form>
      <section className="card p-6"><div className="text-sm text-slate-500">Estimated monthly EMI</div><div className="text-3xl font-bold text-navy mt-2">{money(emi)}</div><div className="grid sm:grid-cols-2 gap-3 mt-6"><Metric label="Estimated total interest" value={money(Math.max(0, total - Number(form.amount || 0)))}/><Metric label="Estimated total repayment" value={money(total)}/></div><p className="text-xs text-slate-500 mt-5">Estimate uses a fixed annual rate of {rate}% and monthly reducing-balance calculation. Actual offers may differ and require human review.</p><Link className="text-blue text-sm font-semibold" to="/customer/apply-loan">Continue to loan application →</Link></section>
    </div>
  </>;
}

function LoanApplication() {
  const [form, setForm] = useState({ loan_type: 'PERSONAL', requested_amount: '', tenure_months: '36', monthly_income: '', existing_emis: '0' });
  const [error, setError] = useState(''), [success, setSuccess] = useState(null), [saving, setSaving] = useState(false);
  const emi = estimateEmi(form.requested_amount, loanRates[form.loan_type], form.tenure_months);
  async function submit(event) {
    event.preventDefault(); setError(''); setSuccess(null); setSaving(true);
    try { const result = await api.post('/customer/loan-applications', form); setSuccess(result.data); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not submit loan application'); }
    finally { setSaving(false); }
  }
  return <><Heading eyebrow="Credit & loans" title="Apply for a Loan" sub="Submit an application for branch review. The simulated score is one input, not an automatic decision."/><Alert error={error}/>
    {success && <div className="card p-5 mb-5 border-emerald-200 bg-emerald-50"><b className="text-emerald-800">Application submitted</b><p className="text-sm text-emerald-700">Reference {success.application_reference} · Status: Pending · Estimated EMI {money(success.estimated_emi)}</p><Link to="/customer/loan-applications" className="text-blue text-sm font-semibold">Track application →</Link></div>}
    <div className="grid lg:grid-cols-2 gap-5"><form className="card p-6 grid sm:grid-cols-2 gap-4" onSubmit={submit}><label className="block text-sm font-semibold sm:col-span-2">Loan type<select className="field mt-1" value={form.loan_type} onChange={event => setForm({ ...form, loan_type: event.target.value })}>{Object.keys(loanRates).map(type => <option key={type} value={type}>{type[0] + type.slice(1).toLowerCase()} · {loanRates[type]}% p.a.</option>)}</select></label><label className="block text-sm font-semibold">Requested amount (INR)<input className="field mt-1" name="requested_amount" type="number" min="1000" step="1000" required value={form.requested_amount} onChange={event => setForm({ ...form, requested_amount: event.target.value })}/></label><label className="block text-sm font-semibold">Tenure (3–360 months)<input className="field mt-1" name="tenure_months" type="number" min="3" max="360" required value={form.tenure_months} onChange={event => setForm({ ...form, tenure_months: event.target.value })}/></label><label className="block text-sm font-semibold">Monthly income (INR)<input className="field mt-1" name="monthly_income" type="number" min="1" step="0.01" required value={form.monthly_income} onChange={event => setForm({ ...form, monthly_income: event.target.value })}/></label><label className="block text-sm font-semibold">Existing monthly EMIs (INR)<input className="field mt-1" name="existing_emis" type="number" min="0" step="0.01" value={form.existing_emis} onChange={event => setForm({ ...form, existing_emis: event.target.value })}/></label><button className="btn sm:col-span-2" disabled={saving}>{saving ? 'Submitting…' : 'Submit for review'}</button></form><section className="card p-6"><h2 className="text-sm font-bold mt-0">Estimated repayment</h2><Metric label="Estimated monthly EMI" value={money(emi)}/><p className="text-xs text-slate-500 mt-4">This estimate uses the demo rate of {loanRates[form.loan_type]}% p.a. A branch manager reviews financial details and records the decision and reason.</p><p className="text-xs text-slate-500">The Meridian score is simulated for learning and is not an official CIBIL score or a credit decision.</p></section></div>
  </>;
}

function CustomerLoanApplications() {
  const { data, error, loading } = useLoad('/customer/loan-applications');
  return <><Heading eyebrow="Credit & loans" title="My Loan Applications" sub="Track each request and read the branch manager’s decision notes."/>{error && <Alert error={error}/ >}{loading ? <Loading/> : <div className="space-y-4">{data?.map(row => <section className="card p-5" key={row.application_id}><div className="flex flex-wrap justify-between gap-3"><div><b>{row.application_reference} · {row.loan_type[0] + row.loan_type.slice(1).toLowerCase()}</b><p className="text-xs text-slate-500 mt-1">Submitted {new Date(row.created_at).toLocaleDateString()}</p></div><StatusPill status={row.status}/></div><div className="grid sm:grid-cols-4 gap-3 mt-4 text-sm"><div>Requested<b className="block mt-1">{money(row.requested_amount)}</b></div><div>Tenure<b className="block mt-1">{row.tenure_months} months</b></div><div>Monthly income<b className="block mt-1">{money(row.monthly_income)}</b></div><div>Simulated score<b className="block mt-1">{row.simulated_score} / 900</b></div></div>{row.decision_reason && <p className="mt-4 mb-0 rounded-lg bg-slate-50 p-3 text-sm text-slate-600"><b>Manager note:</b> {row.decision_reason}</p>}</section>)}{!data?.length && <div className="card"><Empty>You have not submitted a loan application.</Empty></div>}</div>}</>;
}

function RepaymentTracker() {
  const { data, error, loading } = useLoad('/customer/loans');
  if (loading) return <Loading text="Loading your loan schedule…"/>;
  return <><Heading eyebrow="Credit & loans" title="Repayment Tracker" sub="View disbursed loan balances, paid instalments and upcoming due dates."/>{error && <Alert error={error}/ >}
    <div className="space-y-5">{data?.map(loan => <section className="card" key={loan.loan_id}><div className="p-5 border-b flex flex-wrap justify-between gap-3"><div><b>Loan LN-{loan.loan_id} · {loan.loan_type[0] + loan.loan_type.slice(1).toLowerCase()}</b><p className="text-xs text-slate-500 mt-1">Application {loan.application_reference}</p></div><StatusPill status={loan.status}/></div><div className="p-5 grid sm:grid-cols-2 lg:grid-cols-4 gap-4"><Metric label="Original principal" value={money(loan.principal)}/><Metric label="Outstanding principal" value={money(loan.outstanding_balance)}/><Metric label="Monthly EMI" value={money(loan.monthly_emi)}/><Metric label="Interest rate" value={`${loan.annual_rate}% p.a.`}/></div><div className="table-wrap"><table className="w-full"><thead><tr><th>Instalment</th><th>Due date</th><th>Amount due</th><th>Principal portion</th><th>Status</th><th>Paid date</th></tr></thead><tbody>{loan.installments?.map(item => { const overdue = item.status === 'DUE' && new Date(`${String(item.due_date).slice(0,10)}T00:00:00`) < new Date(new Date().toDateString()); return <tr key={item.installment_id}><td>{item.installment_no}</td><td>{String(item.due_date).slice(0,10)}</td><td>{money(item.amount_due)}</td><td>{money(item.principal_due)}</td><td><StatusPill status={overdue ? 'OVERDUE' : item.status}/></td><td>{item.paid_at ? new Date(item.paid_at).toLocaleDateString() : '—'}</td></tr>; })}</tbody></table></div></section>)}{!data?.length && <div className="card"><Empty>Approved loans appear here after the branch manager disburses them.</Empty></div>}</div>
  </>;
}

function ManagerLoans() {
  const { data: applications, error, loading, reload, setError } = useLoad('/manager/loan-applications');
  const { data: loans, reload: reloadLoans } = useLoad('/manager/loans');
  const [reasons, setReasons] = useState({}), [success, setSuccess] = useState(''), [busy, setBusy] = useState('');
  async function decide(row, status) {
    const reason = (reasons[row.application_id] || '').trim();
    if (reason.length < 4) { setError('Enter a short decision reason before saving.'); return; }
    if (!window.confirm(`${status === 'MORE_INFO' ? 'Request more information for' : status.toLowerCase()} ${row.application_reference}?`)) return;
    setBusy(`application-${row.application_id}`); setError(''); setSuccess('');
    try { await api.post(`/manager/loan-applications/${row.application_id}/decision`, { status, reason }); setSuccess(`${row.application_reference}: ${status.replace('_', ' ').toLowerCase()}.`); reload(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not save decision'); }
    finally { setBusy(''); }
  }
  async function disburse(row) {
    if (!window.confirm(`Disburse the approved loan for ${row.application_reference} and create its instalment schedule?`)) return;
    setBusy(`application-${row.application_id}`); setError(''); setSuccess('');
    try { const result = await api.post(`/manager/loan-applications/${row.application_id}/disburse`); setSuccess(`Loan disbursed. Loan ID ${result.data.loan_id}; EMI ${money(result.data.monthly_emi)}.`); reload(); reloadLoans(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not disburse loan'); }
    finally { setBusy(''); }
  }
  async function recordRepayment(event, loan) {
    event.preventDefault(); const installment_no = new FormData(event.currentTarget).get('installment_no');
    if (!window.confirm(`Record instalment ${installment_no} for loan LN-${loan.loan_id} as paid?`)) return;
    setBusy(`loan-${loan.loan_id}`); setError(''); setSuccess('');
    try { await api.post(`/manager/loans/${loan.loan_id}/repayments`, { installment_no }); setSuccess(`Repayment recorded for loan LN-${loan.loan_id}.`); reloadLoans(); }
    catch (problem) { setError(problem.response?.data?.error || 'Could not record repayment'); }
    finally { setBusy(''); }
  }
  return <><Heading eyebrow="Loan management" title="Application review & servicing" sub="Review applications in your assigned branch, record human decisions, disburse approved loans and post scheduled repayments."/><Alert error={error} success={success}/>
    <section className="mb-7"><h2 className="text-base font-bold mb-3">Loan applications</h2>{loading ? <Loading/> : <div className="space-y-4">{applications?.map(row => <article className="card p-5" key={row.application_id}><div className="flex flex-wrap justify-between gap-3"><div><b>{row.application_reference} · {row.customer_name}</b><p className="text-xs text-slate-500 mt-1">{row.customer_email} · {row.loan_type} · applied {new Date(row.created_at).toLocaleDateString()}</p></div><StatusPill status={row.status}/></div><div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 my-4 text-sm"><div>Requested<b className="block mt-1">{money(row.requested_amount)}</b></div><div>Tenure<b className="block mt-1">{row.tenure_months} mo.</b></div><div>Income<b className="block mt-1">{money(row.monthly_income)}</b></div><div>Existing EMIs<b className="block mt-1">{money(row.existing_emis)}</b></div><div>Simulated score<b className="block mt-1">{row.simulated_score} / 900</b></div></div><div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">Estimated EMI {money(row.estimated_emi)} · Existing EMIs plus proposed EMI are {(Number(row.proposed_emi_ratio) * 100).toFixed(1)}% of stated monthly income. Score is educational and supports human review only.</div>{row.decision_reason && <p className="text-sm text-slate-600"><b>Recorded reason:</b> {row.decision_reason}</p>}{['PENDING','MORE_INFO'].includes(row.status) && <div className="mt-4 grid md:grid-cols-[1fr_auto_auto_auto] gap-2"><input className="field" placeholder="Reason required for decision" value={reasons[row.application_id] || ''} onChange={event => setReasons({ ...reasons, [row.application_id]: event.target.value })}/><button className="btn secondary" disabled={busy === `application-${row.application_id}`} onClick={() => decide(row, 'MORE_INFO')}>Request information</button><button className="btn" disabled={busy === `application-${row.application_id}`} onClick={() => decide(row, 'APPROVED')}>Approve</button><button className="btn secondary" disabled={busy === `application-${row.application_id}`} onClick={() => decide(row, 'REJECTED')}>Reject</button></div>}{row.status === 'APPROVED' && <button className="btn mt-4" disabled={busy === `application-${row.application_id}`} onClick={() => disburse(row)}>{busy === `application-${row.application_id}` ? 'Disbursing…' : 'Disburse loan'}</button>}</article>)}{!applications?.length && <div className="card"><Empty>No loan applications for this branch.</Empty></div>}</div>}</section>
    <section><h2 className="text-base font-bold mb-3">Disbursed loans & repayments</h2>{loans?.length ? <div className="space-y-4">{loans.map(loan => <article className="card p-5" key={loan.loan_id}><div className="flex flex-wrap justify-between gap-3"><b>LN-{loan.loan_id} · {loan.customer_name}</b><StatusPill status={loan.status}/></div><div className="grid sm:grid-cols-3 gap-3 mt-4 text-sm"><div>Outstanding<b className="block mt-1">{money(loan.outstanding_balance)}</b></div><div>Monthly EMI<b className="block mt-1">{money(loan.monthly_emi)}</b></div><div>Unpaid instalments<b className="block mt-1">{loan.unpaid_installments}</b></div></div>{loan.status === 'ACTIVE' && <form className="grid sm:grid-cols-[1fr_auto] gap-2 mt-4" onSubmit={event => recordRepayment(event, loan)}><select className="field" name="installment_no" required><option value="">Select due instalment</option>{loan.installments?.filter(item => item.status === 'DUE').map(item => <option key={item.installment_no} value={item.installment_no}>#{item.installment_no} · due {String(item.due_date).slice(0,10)} · {money(item.amount_due)}</option>)}</select><button className="btn" disabled={busy === `loan-${loan.loan_id}` || !loan.installments?.some(item => item.status === 'DUE')}>{busy === `loan-${loan.loan_id}` ? 'Recording…' : 'Record repayment'}</button></form>}</article>)}</div> : <div className="card"><Empty>No loans have been disbursed in this branch.</Empty></div>}</section>
  </>;
}

function Field({ label, name, type = 'text', required = false, defaultValue }) { return <label className="block text-xs font-semibold">{label}<input className="field mt-1" name={name} type={type} required={required} defaultValue={defaultValue}/></label>; }
function ReadOnly({ label, value }) { return <label className="block text-xs font-semibold">{label}<div className="field mt-1 bg-slate-50 text-slate-500">{value || '—'}</div></label>; }

export default App;
