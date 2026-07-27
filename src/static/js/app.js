const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;

const app = createApp({
    setup() {
        // ========== 状态 ==========
        const hasMasterKey = ref(false);
        const isUnlocked = ref(false);
        const masterPassword = ref('');
        const setupPassword = ref('');
        const setupPasswordConfirm = ref('');
        const lockError = ref('');

        const theme = ref(localStorage.getItem('theme') || 'light');
        function applyTheme() {
            document.documentElement.setAttribute('data-theme', theme.value);
        }
        function toggleTheme() {
            theme.value = theme.value === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', theme.value);
            applyTheme();
        }
        onMounted(() => {
            applyTheme();
            checkMasterKey();
        });

        const firstInput = ref(null);

        const countries = ref([]);
        const companies = ref([]);
        const websites = ref([]);
        const allAccounts = ref([]);
        
        const selectedAccountId = ref(null);
        const showAccountForm = ref(false);
        const listFilter = ref('active');
        const selectedCountryId = ref(null);
        const selectedCompanyId = ref(null);
        const selectedWebsiteId = ref(null);
        const sidebarCollapsed = ref(false);
        const expandedCountries = reactive({});
        const companySearch = ref('');
        const searchKeyword = ref('');
        const searchResults = ref([]);
        const searchFocused = ref(false);
        const stats = reactive({ websites: 0, accounts: 0, companies: 0, countries: 0 });

        const showCompanyModal = ref(false);
        const showWebsiteModal = ref(false);
        const showAccountModal = ref(false);
        const showDeleteModal = ref(false);
        const showAccountPwd = ref(false);
        const showCountryDropdown = ref(false);
        const showAddMenu = ref(false);
        const showPresetModal = ref(false);
        const showExportMenu = ref(false);
        const countrySearch = ref('');

        const editingCompany = ref(null);
        const editingWebsite = ref(null);
        const editingAccount = ref(null);
        const deletingAccount = ref(null);
        const deletingCompany = ref(null);
        const showDeleteCompanyModal = ref(false);

        const companyForm = reactive({ name: '', country_id: '' });
        const websiteForm = reactive({ name: '', url: '', company_id: '', type: 'web' });
        const accountForm = reactive({
            company_id: '', website_id: '',
            account_name: '', plain_password: '', status: 'active',
            phone: '', email: '', description: '', registered_at: ''
        });

        const toast = reactive({ visible: false, message: '', type: 'success' });
        let toastTimer = null;

        // 预设数据相关状态
        const presetData = ref([]);
        const presetSearch = ref('');
        const presetCountry = ref('');

        // 预设数据 CRUD 状态
        const showPresetCompanyModal = ref(false);
        const showPresetWebsiteModal = ref(false);
        const showPresetDeleteModal = ref(false);
        const editingPresetCompany = ref(null);
        const editingPresetWebsite = ref(null);
        const deletingPresetItem = ref(null);
        const presetCompanyForm = reactive({ name: '', country_code: '', description: '' });
        const presetWebsiteForm = reactive({ name: '', url: '', type: 'web', company_id: '' });
        const presetCountrySearch = ref('');
        const showPresetCountryDrop = ref(false);
        const filteredCountriesForPreset = computed(() => {
            const kw = (presetCountrySearch.value || '').trim().toLowerCase();
            if (!kw) return countries.value;
            return countries.value.filter(c => c.name.toLowerCase().includes(kw) || c.code.toLowerCase().includes(kw));
        });
        function pickPresetCountry(c) {
            presetCompanyForm.country_code = c.code;
            presetCountrySearch.value = '[' + c.code + '] ' + c.name;
            showPresetCountryDrop.value = false;
        }
        function onPresetCountryFocus() {
            // 聚焦时清空搜索文本以显示完整列表
            presetCountrySearch.value = '';
            showPresetCountryDrop.value = true;
        }
        function onPresetCountryBlur() {
            // 失焦时恢复已选国家的显示文本
            setTimeout(() => {
                showPresetCountryDrop.value = false;
                if (presetCompanyForm.country_code) {
                    const matched = countries.value.find(c => c.code === presetCompanyForm.country_code);
                    presetCountrySearch.value = matched ? '[' + matched.code + '] ' + matched.name : presetCompanyForm.country_code;
                }
            }, 200);
        }

        // 数据库查看器状态
        const showDbViewerModal = ref(false);
        const dbTables = ref([]);
        const selectedDbTable = ref('');
        const dbTableColumns = ref([]);
        const dbTableRows = ref([]);
        const dbSearchQuery = ref('');
        const dbSortKey = ref('');
        const dbSortOrder = ref('asc');
        const selectedDbTableDescription = computed(() => {
            const table = dbTables.value.find(tbl => tbl.name === selectedDbTable.value);
            return table ? (table.description || '') : '';
        });

        // 公司颜色列表
        const companyColors = [
            'linear-gradient(135deg, #4f46e5, #818cf8)',
            'linear-gradient(135deg, #059669, #34d399)',
            'linear-gradient(135deg, #d97706, #fbbf24)',
            'linear-gradient(135deg, #dc2626, #f87171)',
            'linear-gradient(135deg, #7c3aed, #a78bfa)',
            'linear-gradient(135deg, #0891b2, #67e8f9)',
            'linear-gradient(135deg, #be185d, #f472b6)',
            'linear-gradient(135deg, #475569, #94a3b8)',
        ];

        function showToast(message, type = 'success') {
            toast.message = message;
            toast.type = type;
            toast.visible = true;
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => { toast.visible = false; }, 2500);
        }

        // ========== API ==========
        const API = '/api';
        async function api(path, options = {}) {
            const res = await fetch(API + path, {
                headers: { 'Content-Type': 'application/json' },
                ...options,
                body: options.body ? JSON.stringify(options.body) : undefined,
            });
            const text = await res.text();
            let data;
            try {
                data = JSON.parse(text);
            } catch {
                console.error('API non-JSON response:', path, res.status, text.substring(0, 200));
                throw new Error('Server error: ' + res.status);
            }

            if (!res.ok) throw new Error(data.error || '请求失败');
            return data;
        }

        // ========== 主密码 ==========
        async function checkMasterKey() {
            const data = await api('/master-key/status');
            hasMasterKey.value = data.has_key;
            await nextTick();
            if (firstInput.value) firstInput.value.focus();
        }

        async function setupMasterKey() {
            lockError.value = '';
            if (setupPassword.value.length < 6) { lockError.value = '主密码至少6位'; return; }
            if (setupPassword.value !== setupPasswordConfirm.value) { lockError.value = '两次输入不一致'; return; }
            try {
                await api('/master-key/setup', { method: 'POST', body: { password: setupPassword.value } });
                masterPassword.value = setupPassword.value;
                isUnlocked.value = true;
                showToast('主密码设置成功');
                loadData();
            } catch (e) { lockError.value = e.message; }
        }

        async function unlock() {
            lockError.value = '';
            try {
                const data = await api('/master-key/verify', { method: 'POST', body: { password: masterPassword.value } });
                if (data.valid) { isUnlocked.value = true; loadData(); }
                else { lockError.value = '主密码不正确'; }
            } catch (e) { lockError.value = e.message; }
        }

        function lockApp() {
            isUnlocked.value = false;
            masterPassword.value = '';
            setupPassword.value = '';
            setupPasswordConfirm.value = '';
            lockError.value = '';
        }

        function lockKeyup(e) {
            if (e.key === 'Enter') {
                if (hasMasterKey.value) { unlock(); } else { setupMasterKey(); }
            }
        }

        // ========== 数据加载 ==========
        async function loadData() {
            try {
                const [c, co, w, s] = await Promise.all([
                    api('/countries'),
                    api('/companies'),
                    api('/websites'),
                    api('/stats'),
                ]);
                countries.value = c || [];
                companies.value = co || [];
                websites.value = w || [];
                Object.assign(stats, s || { websites:0, accounts:0, companies:0, countries:0 });
                await loadAllAccounts();

                if (c && c.length > 0 && !selectedCountryId.value) {
                    selectedCountryId.value = c[0].id;
                }
            } catch (e) {
                console.error('loadData error:', e);
                showToast('加载数据失败: ' + e.message, 'error');
            }
        }

        async function loadStats() {
            const s = await api('/stats');
            Object.assign(stats, s);
        }

        async function loadAllAccounts() {
            try {
                const data = await api('/accounts');
                allAccounts.value = data.map(a => ({ ...a, _showPwd: false, _decryptedPwd: '', _copied: false }));
            } catch (e) {
                console.error('Failed to load accounts:', e);
                allAccounts.value = [];
            }
        }

        async function loadAccountsForWebsite(websiteId) {
            try {
                const data = await api(`/websites/${websiteId}/accounts`);
                const mapped = data.map(a => ({ ...a, _showPwd: false, _decryptedPwd: '', _copied: false }));
                allAccounts.value = allAccounts.value.filter(a => a.website_id !== websiteId).concat(mapped);
            } catch (e) { showToast('加载账号失败', 'error'); }
        }

        // ========== 计算属性 ==========
        
        const selectedAccount = computed(() => {
            if (!selectedAccountId.value) return null;
            return allAccounts.value.find(a => a.id === selectedAccountId.value) || null;
        });

        const filteredCountryList = computed(() => {
            if (!countrySearch.value.trim()) return countries.value;
            const kw = countrySearch.value.toLowerCase();
            return countries.value.filter(c => c.name.toLowerCase().includes(kw));
        });

        const countriesWithCompanies = computed(() => {
            // 只显示有公司的国家，避免新建账号时国家下拉为空
            const countryIds = new Set(companies.value.map(co => co.country_id));
            return countries.value.filter(c => countryIds.has(c.id));
        });

        const filteredCompanies = computed(() => {
            let list = companies.value;
            if (selectedCountryId.value) {
                list = list.filter(co => co.country_id === selectedCountryId.value);
            }
            // 只显示有账户列表的公司
            list = list.filter(co => getAccountsForCompany(co.id).length > 0);
            
            if (companySearch.value.trim()) {
                const kw = companySearch.value.toLowerCase();
                list = list.filter(co => co.name.toLowerCase().includes(kw));
            }
            return list;
        });

        // 选中公司的网站列表
        const currentCompanyWebsites = computed(() => {
            if (!selectedCompanyId.value) return [];
            return websites.value.filter(w => w.company_id === selectedCompanyId.value);
        });

        const displayedAccounts = computed(() => {
            let accs = allAccounts.value;
            
            // 状态过滤
            if (listFilter.value === 'active') {
                accs = accs.filter(a => !a.is_deleted && a.status !== 'banned');
            } else if (listFilter.value === 'banned') {
                accs = accs.filter(a => !a.is_deleted && a.status === 'banned');
            } else if (listFilter.value === 'deleted') {
                accs = accs.filter(a => a.is_deleted === 1 || a.is_deleted === true);
            }
            
            if (selectedCompanyId.value) {
                const wids = websites.value.filter(w => w.company_id === selectedCompanyId.value).map(w => w.id);
                accs = accs.filter(a => wids.includes(a.website_id));
            } else if (selectedCountryId.value) {
                const coIds = companies.value.filter(co => co.country_id === selectedCountryId.value).map(co => co.id);
                const wids = websites.value.filter(w => coIds.includes(w.company_id)).map(w => w.id);
                accs = accs.filter(a => wids.includes(a.website_id));
            }
            return accs;
        });
        const displayedAccountsForCountry = computed(() => {
            if (!selectedCountryId.value) return 0;
            const coIds = companies.value.filter(co => co.country_id === selectedCountryId.value).map(co => co.id);
            const wids = websites.value.filter(w => coIds.includes(w.company_id)).map(w => w.id);
            let accs = allAccounts.value.filter(a => wids.includes(a.website_id));
            
            // 状态过滤
            if (listFilter.value === 'active') {
                accs = accs.filter(a => !a.is_deleted && a.status !== 'banned');
            } else if (listFilter.value === 'banned') {
                accs = accs.filter(a => !a.is_deleted && a.status === 'banned');
            } else if (listFilter.value === 'deleted') {
                accs = accs.filter(a => a.is_deleted === 1 || a.is_deleted === true);
            }
            
            return accs.length;
        });

        const contentTitle = computed(() => {
            if (selectedWebsiteId.value) {
                const w = websites.value.find(w => w.id === selectedWebsiteId.value);
                return w ? w.name : '';
            }
            if (selectedCompanyId.value) {
                const co = companies.value.find(co => co.id === selectedCompanyId.value);
                return co ? co.name : '';
            }
            if (selectedCountryId.value) {
                const c = countries.value.find(c => c.id === selectedCountryId.value);
                return c ? c.name : '';
            }
            return '';
        });

        const contentSubtitle = computed(() => {
            if (selectedWebsiteId.value) {
                const w = websites.value.find(w => w.id === selectedWebsiteId.value);
                return w && w.url ? shortenUrl(w.url) : '';
            }
            if (selectedCompanyId.value) {
                const wc = getWebCountForCompany(selectedCompanyId.value);
                const ac = getAppCountForCompany(selectedCompanyId.value);
                return wc + ' 个网站 / ' + ac + ' 个应用';
            }
            return '';
        });

        // 账号表单中根据选中的公司筛选网站
        const websitesForAccountForm = computed(() => {
            if (!accountForm.company_id) return [];
            return websites.value.filter(w => w.company_id === accountForm.company_id);
        });

        const presetCountryCodes = computed(() => {
            const codes = new Set();
            presetData.value.forEach(g => codes.add(g.code));
            return Array.from(codes);
        });

        const filteredPresetGroups = computed(() => {
            let groups = presetData.value;
            if (presetCountry.value) {
                groups = groups.filter(g => g.code === presetCountry.value);
            }
            if (presetSearch.value.trim()) {
                const kw = presetSearch.value.toLowerCase();
                groups = groups.map(g => {
                    const filteredCompanies = g.companies.filter(co =>
                        co.name.toLowerCase().includes(kw) ||
                        co.websites.some(w => w.name.toLowerCase().includes(kw))
                    );
                    return {
            listFilter, restoreAccount,
            displayedAccountsForCountry,
            theme, toggleTheme, closeDetail,
            selectedAccountId, showAccountForm, selectedAccount, selectAccount, closeAccountForm, ...g, companies: filteredCompanies };
                }).filter(g => g.companies.length > 0);
            }
            return groups;
        });

        const filteredAndSortedDbRows = computed(() => {
            let result = [...dbTableRows.value];

            // 检索/过滤
            if (dbSearchQuery.value.trim()) {
                const query = dbSearchQuery.value.toLowerCase();
                result = result.filter(row => {
                    return Object.values(row).some(val => 
                        val !== null && String(val).toLowerCase().includes(query)
                    );
                });
            }

            // 排序
            if (dbSortKey.value) {
                const key = dbSortKey.value;
                const order = dbSortOrder.value === 'asc' ? 1 : -1;
                result.sort((a, b) => {
                    let valA = a[key];
                    let valB = b[key];

                    if (valA === null || valA === undefined) valA = '';
                    if (valB === null || valB === undefined) valB = '';

                    const numA = Number(valA);
                    const numB = Number(valB);
                    if (!isNaN(numA) && !isNaN(numB) && valA !== '' && valB !== '') {
                        return (numA - numB) * order;
                    }

                    return String(valA).localeCompare(String(valB), 'zh-CN', { numeric: true }) * order;
                });
            }

            return result;
        });

        // ========== 选择操作 ==========
        function selectCompany(id) {
            if (id === null) {
                selectedCompanyId.value = null;
                selectedWebsiteId.value = null;
            } else if (selectedCompanyId.value === id) {
                selectedCompanyId.value = null;
                selectedWebsiteId.value = null;
            } else {
                selectedCompanyId.value = id;
                // Auto-select first website as active tab
                const ws = websites.value.filter(w => w.company_id === id);
                selectedWebsiteId.value = ws.length > 0 ? ws[0].id : null;
            }
        }

        function selectWebsite(id) {
            if (id === null) {
                selectedWebsiteId.value = null;
            } else if (selectedWebsiteId.value === id) {
                selectedWebsiteId.value = null;
            } else {
                selectedWebsiteId.value = id;
            }
        }

        // ========== 辅助函数 ==========
        const initialCountryOptions = Array.isArray(window.__COUNTRY_OPTIONS__) ? window.__COUNTRY_OPTIONS__ : [];
        const allRegionsOptions = computed(() => {
            const source = countries.value.length > 0 ? countries.value : initialCountryOptions;
            return source.map(r => ({ code: r.code, name: r.name }));
        });

        function getCountryFlag(code) {
            const flags = { CN:'🇨🇳', US:'🇺🇸', JP:'🇯🇵', KR:'🇰🇷', GB:'🇬🇧', DE:'🇩🇪', FR:'🇫🇷', SG:'🇸🇬', AU:'🇦🇺', CA:'🇨🇦' };
            return flags[code] || '🌐';
        }
        
        function getCountryNameByCode(code) {
            const matched = allRegionsOptions.value.find(r => r.code === code);
            return matched ? matched.name : code;
        }

        function getCompaniesForCountry(countryId) {
            return companies.value.filter(co => co.country_id === countryId);
        }

        function getCompanyCountForCountry(countryId) {
            return companies.value.filter(co => co.country_id === countryId).length;
        }

        function getWebsitesForCompany(companyId) {
            return websites.value.filter(w => w.company_id === companyId);
        }

        function getWebCountForCompany(companyId) {
            return websites.value.filter(w => w.company_id === companyId && w.type === 'web').length;
        }

        function getAppCountForCompany(companyId) {
            return websites.value.filter(w => w.company_id === companyId && w.type === 'app').length;
        }

        function getCompanyName(companyId) {
            const co = companies.value.find(co => co.id === companyId);
            return co ? co.name : '';
        }

        function getAccountsForWebsite(websiteId) {
            return allAccounts.value.filter(a => a.website_id === websiteId);
        }

        function getAccountsForCompany(companyId) {
            const wids = websites.value.filter(w => w.company_id === companyId).map(w => w.id);
            return allAccounts.value.filter(a => wids.includes(a.website_id));
        }

        function getWebsiteName(websiteId) {
            const w = websites.value.find(w => w.id === websiteId);
            return w ? w.name : '';
        }

        function getWebsiteType(websiteId) {
            const w = websites.value.find(w => w.id === websiteId);
            return w ? w.type : 'web';
        }

        function getCompanyColor(index) {
            return companyColors[index % companyColors.length];
        }

        function shortenUrl(url) {
            try { return new URL(url).hostname; } catch { return url; }
        }

        function statusLabel(status, is_deleted) {
            if (is_deleted) return '删除 (回收站)';
            const map = { active: '使用中', unregistered: '未注册', deprecated: '已废弃', banned: '封禁' };
            return map[status] || '正常';
        }

        // ========== 字段复制 ==========
        async function copyField(text, label) {
            try {
                await navigator.clipboard.writeText(text);
                showToast(label + '已复制');
            } catch (e) {
                showToast('复制失败', 'error');
            }
        }

        function getWebsiteUrl(websiteId) {
            const w = websites.value.find(w => w.id === websiteId);
            return (w && w.url) ? w.url : '';
        }

        // ========== 国家操作 ==========
        function toggleCountryDropdown() {
            showCountryDropdown.value = !showCountryDropdown.value;
            countrySearch.value = '';
            showAddMenu.value = false;
        }

        function toggleCountryExpand(id) {
            expandedCountries[id] = !expandedCountries[id];
        }

        function selectCountry(id) {
            selectedCountryId.value = id;
            selectedCompanyId.value = null;
            selectedWebsiteId.value = null;
            showCountryDropdown.value = false;
            searchKeyword.value = '';
            searchResults.value = [];
        }

        function getSelectedCountryName() {
            const c = countries.value.find(c => c.id === selectedCountryId.value);
            return c ? c.name : '选择国家';
        }

        function getSelectedCountryCode() {
            if (selectedCompanyId.value) {
                const co = companies.value.find(co => co.id === selectedCompanyId.value);
                if (co) {
                    const c = countries.value.find(c => c.id === co.country_id);
                    return c ? c.code : '';
                }
            }
            const c = countries.value.find(c => c.id === selectedCountryId.value);
            return c ? c.code : '';
        }

        function onSearchBlur() {
            searchFocused.value = false;
        }

        // ========== 添加账号（带公司/网站选择器） ==========
        function openAddAccount() {
            editingAccount.value = null;
            accountForm.company_id = selectedCompanyId.value || '';
            accountForm.website_id = selectedWebsiteId.value || '';
            accountForm.account_name = '';
            accountForm.plain_password = '';
            accountForm.status = 'active';
            accountForm.phone = '';
            accountForm.email = '';
            accountForm.description = '';
            accountForm.registered_at = new Date().toISOString().slice(0, 10);
            showAccountPwd.value = false;
            showAccountForm.value = true;
            selectedAccountId.value = null;
        }

        
        
        function closeDetail() {
            selectedAccountId.value = null;
            showAccountForm.value = false;
            editingAccount.value = null;
        }
function selectAccount(acc) {
            selectedAccountId.value = acc.id;
            showAccountForm.value = false;
            editingAccount.value = null;
        }
        function closeAccountForm() {
            showAccountForm.value = false;
            editingAccount.value = null;
        }

        function onAccountCompanyChange() {
            accountForm.website_id = '';
        }

        // ========== 公司 CRUD ==========
        function openAddCompany() {
            editingCompany.value = null;
            companyForm.name = '';
            companyForm.country_id = selectedCountryId.value || '';
            showCompanyModal.value = true;
        }

        function openEditCompany(co) {
            editingCompany.value = co;
            companyForm.name = co.name;
            companyForm.country_id = co.country_id;
            showCompanyModal.value = true;
        }

        async function saveCompany() {
            if (!companyForm.name) { showToast('请输入公司名称', 'error'); return; }
            if (!companyForm.country_id) { showToast('请选择国家', 'error'); return; }
            try {
                if (editingCompany.value) {
                    await api(`/companies/${editingCompany.value.id}`, { method: 'PUT', body: { ...companyForm } });
                    showToast('公司已更新');
                } else {
                    await api('/companies', { method: 'POST', body: { ...companyForm } });
                    showToast('公司已添加');
                }
                showCompanyModal.value = false;
                loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        function confirmDeleteCompany() {
            if (!editingCompany.value) return;
            deletingCompany.value = editingCompany.value;
            showDeleteCompanyModal.value = true;
        }

        async function doDeleteCompany() {
            if (!deletingCompany.value) return;
            try {
                await api(`/companies/${deletingCompany.value.id}`, { method: 'DELETE' });
                showToast('公司已删除');
                showDeleteCompanyModal.value = false;
                showCompanyModal.value = false;
                if (selectedCompanyId.value === deletingCompany.value.id) {
                    selectedCompanyId.value = null;
                    selectedWebsiteId.value = null;
                }
                loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        // ========== 网站 CRUD ==========
        function openAddWebsite(companyId) {
            editingWebsite.value = null;
            websiteForm.name = '';
            websiteForm.url = '';
            websiteForm.type = 'web';
            websiteForm.company_id = companyId || (selectedCompanyId.value || '');
            showWebsiteModal.value = true;
        }

        function openEditWebsite(w) {
            editingWebsite.value = w;
            websiteForm.name = w.name;
            websiteForm.url = w.url || '';
            websiteForm.type = w.type;
            websiteForm.company_id = w.company_id;
            showWebsiteModal.value = true;
        }

        async function saveWebsite() {
            if (!websiteForm.name) { showToast('请输入名称', 'error'); return; }
            if (!websiteForm.company_id) { showToast('请选择公司', 'error'); return; }
            try {
                if (editingWebsite.value) {
                    await api(`/websites/${editingWebsite.value.id}`, { method: 'PUT', body: { ...websiteForm } });
                    showToast('已更新');
                } else {
                    await api('/websites', { method: 'POST', body: { ...websiteForm } });
                    showToast('已添加');
                }
                showWebsiteModal.value = false;
                loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        // ========== 账号 CRUD ==========
        function openEditAccount(acc) {
            editingAccount.value = acc;
            const website = websites.value.find(w => w.id === acc.website_id);
            const companyId = website ? website.company_id : '';
            Object.assign(accountForm, {
                company_id: companyId,
                website_id: acc.website_id,
                account_name: acc.account_name,
                plain_password: '',
                status: acc.status || 'active',
                phone: acc.phone || '',
                email: acc.email || '',
                description: acc.description || '',
                registered_at: acc.registered_at ? acc.registered_at.split(' ')[0] : '',
            });
            showAccountPwd.value = false;
            showAccountForm.value = true;
        }

        async function saveAccount() {
            if (!accountForm.company_id) { showToast('请选择公司', 'error'); return; }
            if (!accountForm.website_id) { showToast('请选择网站/应用', 'error'); return; }
            if (!accountForm.account_name) { showToast('请输入账号名称', 'error'); return; }
            if (!editingAccount.value && !accountForm.plain_password) { showToast('请输入密码', 'error'); return; }
            const payload = { ...accountForm, master_password: masterPassword.value };
            try {
                if (editingAccount.value) {
                    if (!payload.plain_password) delete payload.plain_password;
                    await api(`/accounts/${editingAccount.value.id}`, { method: 'PUT', body: payload });
                    showToast('账号已更新');
                } else {
                    const wid = accountForm.website_id;
                    await api(`/websites/${wid}/accounts`, { method: 'POST', body: payload });
                    showToast('账号已添加');
                }
                showAccountForm.value = false;
                const wid = editingAccount.value ? editingAccount.value.website_id : accountForm.website_id;
                loadAccountsForWebsite(wid);
                loadStats();
            } catch (e) { showToast(e.message, 'error'); }
        }

        
        async function restoreAccount(acc) {
            try {
                await api(`/accounts/${acc.id}/restore`, { method: 'PUT' });
                showToast('账号已恢复');
                if (selectedAccountId.value === acc.id) {
                    selectedAccountId.value = null;
                }
                loadAccountsForWebsite(acc.website_id);
                loadStats();
            } catch (e) { showToast(e.message, 'error'); }
        }
function confirmDeleteAccount(acc) {
            deletingAccount.value = acc;
            showDeleteModal.value = true;
        }

        async function doDeleteAccount() {
            if (!deletingAccount.value) return;
            try {
                await api(`/accounts/${deletingAccount.value.id}`, { method: 'DELETE' });
                showToast('账号已删除');
                showDeleteModal.value = false;
                if (selectedAccountId.value === deletingAccount.value.id) {
                    selectedAccountId.value = null;
                }
                loadAccountsForWebsite(deletingAccount.value.website_id);
                loadStats();
            } catch (e) { showToast(e.message, 'error'); }
        }

        async function viewPassword(acc) {
            if (acc._showPwd) { acc._showPwd = false; acc._decryptedPwd = ''; return; }
            try {
                const data = await api(`/accounts/${acc.id}/decrypt`, { method: 'POST', body: { master_password: masterPassword.value } });
                acc._decryptedPwd = data.password;
                acc._showPwd = true;
            } catch (e) { showToast('解密失败：' + e.message, 'error'); }
        }

        async function copyPassword(acc) {
            try {
                const data = await api(`/accounts/${acc.id}/decrypt`, { method: 'POST', body: { master_password: masterPassword.value } });
                await navigator.clipboard.writeText(data.password);
                acc._copied = true;
                showToast('密码已复制');
                setTimeout(() => { acc._copied = false; }, 2000);
            } catch (e) { showToast('复制失败：' + e.message, 'error'); }
        }

        async function copySearchPwd(a) {
            try {
                const data = await api(`/accounts/${a.id}/decrypt`, { method: 'POST', body: { master_password: masterPassword.value } });
                await navigator.clipboard.writeText(data.password);
                showToast('密码已复制');
            } catch (e) { showToast('复制失败', 'error'); }
        }

        function generatePassword() {
            const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
            const len = 16;
            let pwd = '';
            const arr = new Uint32Array(len);
            crypto.getRandomValues(arr);
            for (let i = 0; i < len; i++) { pwd += chars[arr[i] % chars.length]; }
            accountForm.plain_password = pwd;
            showAccountPwd.value = true;
            showToast('已生成随机密码');
        }

        // ========== 搜索 ==========
        let searchTimer = null;
        function doSearch() {
            clearTimeout(searchTimer);
            if (!searchKeyword.value.trim()) { searchResults.value = []; return; }
            searchTimer = setTimeout(() => {
                const kw = searchKeyword.value.trim().toLowerCase();
                // Filter displayedAccounts instead of allAccounts to respect tab filters
                searchResults.value = displayedAccounts.value.filter(a => {
                    const wName = getWebsiteName(a.website_id).toLowerCase();
                    const cName = getCompanyName(websites.value.find(w => w.id === a.website_id)?.company_id).toLowerCase();
                    const statusStr = statusLabel(a.status, a.is_deleted).toLowerCase();
                    return a.account_name.toLowerCase().includes(kw) 
                        || wName.includes(kw)
                        || cName.includes(kw)
                        || (a.phone && a.phone.includes(kw))
                        || (a.email && a.email.toLowerCase().includes(kw))
                        || (a.created_at && a.created_at.includes(kw))
                        || statusStr.includes(kw);
                });
            }, 300);
        }

        function clearSearch() { searchKeyword.value = ''; searchResults.value = []; }

        // ========== 导出 ==========
        function buildExportRows() {
            return displayedAccounts.value.map(acc => {
                const w = websites.value.find(x => x.id === acc.website_id);
                const co = w ? companies.value.find(x => x.id === w.company_id) : null;
                return {
            listFilter, restoreAccount,
            displayedAccountsForCountry,
            theme, toggleTheme, closeDetail,
            selectedAccountId, showAccountForm, selectedAccount, selectAccount, closeAccountForm,
                    company: co ? co.name : '',
                    website: w ? w.name : '',
                    url: w ? (w.url || '') : '',
                    type: w ? (w.type === 'web' ? '网站' : '应用') : '',
                    account_name: acc.account_name || '',
                    status: statusLabel(acc.status || 'active'),
                    phone: acc.phone || '',
                    email: acc.email || '',
                    description: acc.description || '',
                    registered_at: acc.registered_at || '',
                    created_at: acc.created_at || '',
                    updated_at: acc.updated_at || '',
                };
            });
        }

        function exportExcel() {
            const rows = buildExportRows();
            if (!rows.length) { showToast('无数据可导出', 'error'); return; }

            // 简易生成 CSV（Excel 可直接打开 UTF-8 BOM CSV）
            const headers = ['公司', '网站/应用', '网址', '类型', '登录名', '状态', '手机号', '邮箱', '描述', '注册时间', '创建时间', '更新时间'];
            const keys = ['company', 'website', 'url', 'type', 'account_name', 'status', 'phone', 'email', 'description', 'registered_at', 'created_at', 'updated_at'];
            const escape = (v) => {
                const s = String(v);
                if (s.includes(',') || s.includes('"') || s.includes('\n')) {
                    return '"' + s.replace(/"/g, '""') + '"';
                }
                return s;
            };
            let csv = '\uFEFF'; // BOM for Excel UTF-8
            csv += headers.map(escape).join(',') + '\n';
            rows.forEach(row => {
                csv += keys.map(k => escape(row[k])).join(',') + '\n';
            });

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'EasyPass_' + new Date().toISOString().slice(0, 10) + '.csv';
            a.click();
            URL.revokeObjectURL(url);
            showToast('已导出 Excel (CSV)');
        }

        function exportMarkdown() {
            const rows = buildExportRows();
            if (!rows.length) { showToast('无数据可导出', 'error'); return; }

            let md = '# EasyPass 账号导出\n\n';
            md += '> 导出时间: ' + new Date().toLocaleString('zh-CN') + '\n\n';

            // 按公司 → 网站分组
            const grouped = {};
            rows.forEach(row => {
                const compKey = row.company || '未分组';
                if (!grouped[compKey]) grouped[compKey] = {};
                const webKey = row.website || '未分类';
                if (!grouped[compKey][webKey]) grouped[compKey][webKey] = [];
                grouped[compKey][webKey].push(row);
            });

            Object.keys(grouped).forEach(company => {
                md += '## ' + company + '\n\n';
                const webGroup = grouped[company];
                Object.keys(webGroup).forEach(website => {
                    md += '### ' + website + '\n\n';
                    webGroup[website].forEach((r, idx) => {
                        md += '**[' + (idx + 1) + '] ' + r.account_name + '**\n\n';
                        md += '| 字段 | 值 |\n';
                        md += '| --- | --- |\n';
                        md += '| 状态 | ' + r.status + ' |\n';
                        if (r.phone) md += '| 手机号 | ' + r.phone + ' |\n';
                        if (r.email) md += '| 邮箱 | ' + r.email + ' |\n';
                        if (r.url) md += '| 网址 | [' + shortenUrl(r.url) + '](' + r.url + ') |\n';
                        if (r.registered_at) md += '| 注册时间 | ' + r.registered_at + ' |\n';
                        if (r.created_at) md += '| 创建时间 | ' + r.created_at + ' |\n';
                        if (r.updated_at && r.updated_at !== r.created_at) md += '| 更新时间 | ' + r.updated_at + ' |\n';
                        if (r.description) md += '| 描述 | ' + r.description + ' |\n';
                        md += '\n';
                    });
                    md += '---\n\n';
                });
            });

            const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'EasyPass_' + new Date().toISOString().slice(0, 10) + '.md';
            a.click();
            URL.revokeObjectURL(url);
            showToast('已导出 Markdown');
        }

        // ========== 预设数据操作 ==========
        async function loadPresetData() {
            try {
                presetData.value = await api('/preset');
            } catch (e) { console.error('Failed to load preset data:', e); }
        }

        async function togglePresetCompany(presetId, isChecked) {
            try {
                await api(`/preset/companies/${presetId}/toggle`, { method: 'PUT', body: { is_visible: isChecked } });
                showToast(isChecked ? '已启用' : '已隐藏');
                await loadPresetData();
                await loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        async function togglePresetWebsite(presetId, isChecked) {
            try {
                await api(`/preset/websites/${presetId}/toggle`, { method: 'PUT', body: { is_visible: isChecked } });
                showToast(isChecked ? '已启用' : '已隐藏');
                await loadPresetData();
                await loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        // ---- 预设公司 CRUD ----
        function openAddPresetCompany() {
            editingPresetCompany.value = null;
            presetCompanyForm.name = '';
            presetCompanyForm.country_code = presetCountry.value || '';
            presetCompanyForm.description = '';
            presetCountrySearch.value = '';
            showPresetCountryDrop.value = false;
            showPresetCompanyModal.value = true;
        }

        function openEditPresetCompany(co) {
            editingPresetCompany.value = co;
            presetCompanyForm.name = co.name;
            presetCompanyForm.country_code = co.country_code || '';
            presetCompanyForm.description = co.description || '';
            const matched = countries.value.find(c => c.code === co.country_code);
            presetCountrySearch.value = matched ? '[' + matched.code + '] ' + matched.name : (co.country_code || '');
            showPresetCountryDrop.value = false;
            showPresetCompanyModal.value = true;
        }


        function openAddPresetCompanyFromMain() {
            editingPresetCompany.value = null;
            presetCompanyForm.name = '';
            presetCompanyForm.description = '';
            // ??????????????????
            if (selectedCountryId.value) {
                const c = countries.value.find(x => x.id === selectedCountryId.value);
                presetCompanyForm.country_code = c ? c.code : '';
                presetCountrySearch.value = c ? '[' + c.code + '] ' + c.name : '';
            } else {
                presetCompanyForm.country_code = '';
                presetCountrySearch.value = '';
            }
            showPresetCountryDrop.value = false;
            showPresetCompanyModal.value = true;
        }

        function openEditCompanyFromMain(co) {
            // 现在主界面列表只包含真实公司，直接编辑即可
            openEditCompany(co);
        }

        async function savePresetCompany() {
            if (!presetCompanyForm.name) { showToast('请输入公司名称', 'error'); return; }
            if (!presetCompanyForm.country_code) { showToast('请选择国家', 'error'); return; }
            try {
                if (editingPresetCompany.value) {
                    await api(`/preset/companies/${editingPresetCompany.value.id}`, { method: 'PUT', body: { ...presetCompanyForm } });
                    showToast('已更新');
                } else {
                    const result = await api('/preset/companies', { method: 'POST', body: { ...presetCompanyForm } });
                    // 新添加的公司自动设为可见
                    if (result && result.id) {
                        await api(`/preset/companies/${result.id}/toggle`, { method: 'PUT', body: { is_visible: true } });
                    }
                    showToast('已添加');
                }
                showPresetCompanyModal.value = false;
                await loadPresetData();
                await loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        function confirmDeletePresetCompany(co) {
            deletingPresetItem.value = { type: 'company', id: co.id, name: co.name };
            showPresetDeleteModal.value = true;
        }

        // ---- 预设网站 CRUD ----
        function openAddPresetWebsite(companyId) {
            editingPresetWebsite.value = null;
            presetWebsiteForm.name = '';
            presetWebsiteForm.url = '';
            presetWebsiteForm.type = 'web';
            presetWebsiteForm.company_id = companyId || '';
            showPresetWebsiteModal.value = true;
        }

        async function savePresetWebsite() {
            if (!presetWebsiteForm.name) { showToast('请输入名称', 'error'); return; }
            if (!presetWebsiteForm.company_id) { showToast('请选择所属公司', 'error'); return; }
            try {
                if (editingPresetWebsite.value) {
                    await api(`/preset/websites/${editingPresetWebsite.value.id}`, { method: 'PUT', body: { ...presetWebsiteForm } });
                    showToast('已更新');
                } else {
                    await api('/preset/websites', { method: 'POST', body: { ...presetWebsiteForm } });
                    showToast('已添加');
                }
                showPresetWebsiteModal.value = false;
                await loadPresetData();
                await loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        function confirmDeletePresetWebsite(w) {
            deletingPresetItem.value = { type: 'website', id: w.id, name: w.name };
            showPresetDeleteModal.value = true;
        }

        async function doDeletePresetItem() {
            if (!deletingPresetItem.value) return;
            try {
                if (deletingPresetItem.value.type === 'company') {
                    await api(`/preset/companies/${deletingPresetItem.value.id}`, { method: 'DELETE' });
                } else {
                    await api(`/preset/websites/${deletingPresetItem.value.id}`, { method: 'DELETE' });
                }
                showToast('已删除');
                showPresetDeleteModal.value = false;
                showPresetCompanyModal.value = false;
                showPresetWebsiteModal.value = false;
                await loadPresetData();
                await loadData();
            } catch (e) { showToast(e.message, 'error'); }
        }

        // ========== 数据库查看器操作 ==========
        async function openDbViewer() {
            try {
                const tables = await api('/db/tables');
                dbTables.value = (tables || []).map(tbl => (
                    typeof tbl === 'string'
                        ? { name: tbl, description: '' }
                        : tbl
                ));
                showDbViewerModal.value = true;
                if (dbTables.value.length > 0) {
                    const selectedExists = selectedDbTable.value && dbTables.value.some(tbl => tbl.name === selectedDbTable.value);
                    if (!selectedExists) {
                        selectedDbTable.value = dbTables.value[0].name;
                    }
                    await loadDbTableData(selectedDbTable.value);
                } else {
                    selectedDbTable.value = '';
                    await loadDbTableData('');
                }
            } catch (e) {
                showToast('加载数据库表失败: ' + e.message, 'error');
            }
        }

        async function loadDbTableData(tableName) {
            if (!tableName) {
                dbTableColumns.value = [];
                dbTableRows.value = [];
                return;
            }
            try {
                dbSearchQuery.value = '';
                dbSortKey.value = '';
                dbSortOrder.value = 'asc';

                const data = await api(`/db/table/${tableName}`);
                dbTableColumns.value = data.columns || [];
                dbTableRows.value = data.rows || [];
            } catch (e) {
                showToast('加载表数据失败: ' + e.message, 'error');
            }
        }

        async function onDbTableChange() {
            await loadDbTableData(selectedDbTable.value);
        }

        function setDbSort(col) {
            if (dbSortKey.value === col) {
                dbSortOrder.value = dbSortOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                dbSortKey.value = col;
                dbSortOrder.value = 'asc';
            }
        }

        // ========== 全局点击关闭下拉 ==========
        function handleGlobalClick(e) {
            if (showCountryDropdown.value) {
                const sel = document.querySelector('.country-select');
                if (sel && !sel.contains(e.target)) {
                    showCountryDropdown.value = false;
                }
            }
            if (showAddMenu.value) {
                const wrap = document.querySelector('.topbar-add-wrap');
                if (wrap && !wrap.contains(e.target)) {
                    showAddMenu.value = false;
                }
            }
            if (showExportMenu.value) {
                const wrap = document.querySelector('.export-wrap');
                if (wrap && !wrap.contains(e.target)) {
                    showExportMenu.value = false;
                }
            }
        }

        // ========== 生命周期 ==========
        onMounted(() => {
            checkMasterKey();
            document.addEventListener('click', handleGlobalClick);
        });

        // 监听预设弹窗打开时加载数据
        watch(showPresetModal, (val) => {
            if (val) loadPresetData();
        });

        return {
            listFilter, restoreAccount,
            displayedAccountsForCountry,
            theme, toggleTheme, closeDetail,
            selectedAccountId, showAccountForm, selectedAccount, selectAccount, closeAccountForm,
            hasMasterKey, isUnlocked, masterPassword, setupPassword, setupPasswordConfirm,
            lockError, firstInput,
            setupMasterKey, unlock, lockApp, lockKeyup,
            countries, companies, websites, allAccounts, stats,
            selectedCountryId, selectedCompanyId, selectedWebsiteId,
            sidebarCollapsed, companySearch,
            filteredCompanies, filteredCountryList, countriesWithCompanies,
            currentCompanyWebsites,
            displayedAccounts, contentTitle, contentSubtitle,
            websitesForAccountForm,
            searchKeyword, searchResults, searchFocused,
            showCountryDropdown, showAddMenu, countrySearch,
            toggleCountryDropdown, selectCountry, toggleCountryExpand, expandedCountries,
            getSelectedCountryName, getSelectedCountryCode,
            onSearchBlur,
            selectCompany, selectWebsite,
            getCountryFlag, getCountryNameByCode, getCompaniesForCountry,
            getCompanyCountForCountry, getWebCountForCompany, getAppCountForCompany,
            getWebsitesForCompany, getCompanyName, getCompanyColor,
            getWebsiteName, getWebsiteType, shortenUrl, statusLabel,
            getAccountsForWebsite, getAccountsForCompany, getWebsiteUrl,
            copyField,
            openAddAccount, onAccountCompanyChange,
            showCompanyModal, showWebsiteModal, showAccountModal, showDeleteModal,
            showAccountPwd, editingCompany, editingWebsite, editingAccount, deletingAccount,
            deletingCompany, showDeleteCompanyModal,
            companyForm, websiteForm, accountForm,
            showExportMenu,
            exportExcel, exportMarkdown,
            openAddCompany, openEditCompany, saveCompany, openAddPresetCompanyFromMain, openEditCompanyFromMain, confirmDeleteCompany, doDeleteCompany,
            openAddWebsite, openEditWebsite, saveWebsite,
            openEditAccount, saveAccount,
            confirmDeleteAccount, doDeleteAccount,
            viewPassword, copyPassword, copySearchPwd, generatePassword,
            doSearch, clearSearch,
            toast,
            // 预设数据相关
            showPresetModal, presetData, presetSearch, presetCountry,
            presetCountryCodes, filteredPresetGroups, allRegionsOptions,
            loadPresetData, togglePresetCompany, togglePresetWebsite,
            // 预设数据 CRUD
            showPresetCompanyModal, showPresetWebsiteModal, showPresetDeleteModal,
            editingPresetCompany, editingPresetWebsite, deletingPresetItem,
            presetCompanyForm, presetWebsiteForm,
            openAddPresetCompany, openEditPresetCompany, savePresetCompany,
            presetCountrySearch, showPresetCountryDrop, filteredCountriesForPreset, pickPresetCountry, onPresetCountryFocus, onPresetCountryBlur,
            confirmDeletePresetCompany,
            openAddPresetWebsite, savePresetWebsite,
            confirmDeletePresetWebsite, doDeletePresetItem,
            // 数据库查看器
            showDbViewerModal, dbTables, selectedDbTable, selectedDbTableDescription, dbTableColumns, dbTableRows,
            dbSearchQuery, dbSortKey, dbSortOrder, filteredAndSortedDbRows,
            openDbViewer, loadDbTableData, onDbTableChange, setDbSort,
        };
    }
});

app.mount('#app');
