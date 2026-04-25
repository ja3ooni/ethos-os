"""Dashboard routes - serving the read-only UI."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


DASHBOARD_CSS = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
    .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    header { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    header h1 { font-size: 24px; color: #1a1a1a; }
    header .subtitle { color: #666; margin-top: 8px; }
    nav { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
    nav a { padding: 10px 20px; background: #fff; border-radius: 6px; text-decoration: none; color: #333; border: 1px solid #ddd; }
    nav a.active { background: #0066cc; color: #fff; border-color: #0066cc; }
    .panel { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .panel h2 { font-size: 18px; margin-bottom: 16px; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .stat-card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stat-card .value { font-size: 32px; font-weight: 700; color: #1a1a1a; }
    .stat-card .label { color: #666; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
    th { background: #f8f8f8; font-weight: 600; font-size: 13px; }
    .loading { text-align: center; padding: 40px; color: #666; }
    .error { background: #fee; color: #c00; padding: 12px; border-radius: 6px; }
    @media (max-width: 768px) { .container { padding: 12px; } }
</style>
"""


@router.get("", response_class=HTMLResponse)
async def dashboard_index(request: Request) -> HTMLResponse:
    """Main dashboard index page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EthosOS Dashboard</title>
""" + DASHBOARD_CSS + """
</head>
<body>
    <div class="container">
        <header>
            <h1>EthosOS Dashboard</h1>
            <div class="subtitle">Initiative-based OS - Read-only view</div>
        </header>
        
        <nav>
            <a href="/dashboard" class="active">Overview</a>
            <a href="/dashboard/tree">Initiative Tree</a>
            <a href="/dashboard/gates">Gate Status</a>
            <a href="/dashboard/heartbeats">Heartbeats</a>
            <a href="/dashboard/search">Search</a>
        </nav>
        
        <div class="stats-grid" id="stats">
            <div class="loading">Loading...</div>
        </div>
        
        <div class="panel">
            <h2>Quick Actions</h2>
            <p>Navigate to specific views using the links above.</p>
        </div>
    </div>
    
    <script>
        const API_BASE = '';
        
        async function loadStats() {
            const container = document.getElementById('stats');
            try {
                const [treeResp, gatesResp] = await Promise.all([
                    fetch(API_BASE + '/hierarchy/search?q='),
                    fetch(API_BASE + '/gates/dashboard')
                ]);
                
                const tree = await treeResp.json();
                const gates = await gatesResp.json();
                
                container.innerHTML = `
                    <div class="stat-card">
                        <div class="value">` + (tree.portfolios?.length || 0) + `</div>
                        <div class="label">Portfolios</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (tree.programs?.length || 0) + `</div>
                        <div class="label">Programs</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (tree.projects?.length || 0) + `</div>
                        <div class="label">Projects</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (tree.tasks?.length || 0) + `</div>
                        <div class="label">Tasks</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (gates.pending_count || 0) + `</div>
                        <div class="label">Pending Gates</div>
                    </div>`;
            } catch (e) {
                container.innerHTML = '<div class="error">Failed to load dashboard data</div>';
            }
        }
        
        loadStats();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/tree", response_class=HTMLResponse)
async def dashboard_tree(request: Request) -> HTMLResponse:
    """Initiative tree view page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Initiative Tree - EthosOS</title>
""" + DASHBOARD_CSS + """
    <style>
        .tree { list-style: none; padding-left: 20px; }
        .tree-node { margin: 8px 0; }
        .tree-label { display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f8f8f8; border-radius: 4px; cursor: pointer; }
        .tree-label:hover { background: #eee; }
        .tree-type { font-size: 11px; text-transform: uppercase; color: #666; padding: 2px 6px; background: #ddd; border-radius: 3px; }
        .tree-status-approved { color: #007c4d; }
        .tree-status-pending { color: #b8860b; }
        .tree-status-rejected { color: #c00; }
        .tree-status-active { color: #0066cc; }
        .tree-children { display: none; padding-left: 20px; }
        .tree-children.expanded { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Initiative Tree</h1>
        </header>
        
        <nav>
            <a href="/dashboard">Overview</a>
            <a href="/dashboard/tree" class="active">Initiative Tree</a>
            <a href="/dashboard/gates">Gate Status</a>
            <a href="/dashboard/heartbeats">Heartbeats</a>
            <a href="/dashboard/search">Search</a>
        </nav>
        
        <div class="panel">
            <h2>Hierarchy</h2>
            <div id="tree">
                <div class="loading">Loading initiative tree...</div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '';
        
        function getStatusClass(status) {
            if (status === 'approved' || status === 'complete') return 'tree-status-approved';
            if (status === 'pending') return 'tree-status-pending';
            if (status === 'rejected') return 'tree-status-rejected';
            if (status === 'active') return 'tree-status-active';
            return '';
        }
        
        function renderNode(node) {
            const statusClass = node.status ? getStatusClass(node.status) : '';
            let html = '<li class="tree-node">' +
                '<div class="tree-label" onclick="toggle(this)">' +
                    '<span class="tree-type">' + node.type + '</span>' +
                    '<span class="' + statusClass + '">' + node.name + '</span>' +
                '</div>';
            
            if (node.children && node.children.length > 0) {
                html += '<ul class="tree-children">';
                for (const child of node.children) {
                    html += renderNode(child);
                }
                html += '</ul>';
            }
            
            html += '</li>';
            return html;
        }
        
        function toggle(el) {
            const siblings = el.nextElementSibling;
            if (siblings) {
                siblings.classList.toggle('expanded');
            }
        }
        
        async function loadTree() {
            try {
                const resp = await fetch(API_BASE + '/hierarchy/tree');
                const data = await resp.json();
                
                const container = document.getElementById('tree');
                if (data.length === 0) {
                    container.innerHTML = '<p>No initiatives found.</p>';
                    return;
                }
                
                let html = '<ul class="tree">';
                for (const node of data) {
                    html += renderNode(node);
                }
                html += '</ul>';
                
                container.innerHTML = html;
            } catch (e) {
                document.getElementById('tree').innerHTML = '<div class="error">Failed to load tree</div>';
            }
        }
        
        loadTree();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/gates", response_class=HTMLResponse)
async def dashboard_gates(request: Request) -> HTMLResponse:
    """Gate status board page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gate Status - EthosOS</title>
""" + DASHBOARD_CSS + """
    <style>
        .gate-type { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .gate-type-scope { background: #e3f2fd; color: #1976d2; }
        .gate-type-budget { background: #fff3e0; color: #f57c00; }
        .status-pending { color: #b8860b; font-weight: 600; }
        .age-warning { background: #fff3e0; padding: 4px 8px; border-radius: 4px; }
        .age-critical { background: #ffebee; color: #c00; }
        .theater-warning { background: #fff3e0; border: 1px solid #ffcc02; padding: 12px; border-radius: 6px; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Gate Status Board</h1>
        </header>
        
        <nav>
            <a href="/dashboard">Overview</a>
            <a href="/dashboard/tree">Initiative Tree</a>
            <a href="/dashboard/gates" class="active">Gate Status</a>
            <a href="/dashboard/heartbeats">Heartbeats</a>
            <a href="/dashboard/search">Search</a>
        </nav>
        
        <div class="panel">
            <h2>Summary</h2>
            <div class="stats-grid" id="stats">
                <div class="loading">Loading...</div>
            </div>
            <div id="theater-warning"></div>
        </div>
        
        <div class="panel">
            <h2>Pending Gates</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Entity</th>
                        <th>Age</th>
                        <th>Approver</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="gates-body">
                    <tr><td colspan="5" class="loading">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const API_BASE = '';
        
        function getAgeClass(ageHours, timeoutHours) {
            const ratio = ageHours / timeoutHours;
            if (ratio >= 0.9) return 'age-critical';
            if (ratio >= 0.75) return 'age-warning';
            return '';
        }
        
        async function loadGates() {
            try {
                const resp = await fetch(API_BASE + '/gates/dashboard');
                const data = await resp.json();
                
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">
                        <div class="value">` + (data.pending_count || 0) + `</div>
                        <div class="label">Pending</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (data.pending_by_type?.scope || 0) + `</div>
                        <div class="label">Scope</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + (data.pending_by_type?.budget || 0) + `</div>
                        <div class="label">Budget</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">` + Math.round((data.approval_rate_30d || 0) * 100) +'%' + `</div>
                        <div class="label">30d Approval Rate</div>
                    </div>`;
                
                if (data.approval_rate_30d >= 1.0) {
                    document.getElementById('theater-warning').innerHTML = `
                        <div class="theater-warning">
                            <strong>Gate Theater Detected:</strong> 100% approval rate - gates may be theatrical rather than substantive.
                        </div>`;
                }
                
                const tbody = document.getElementById('gates-body');
                if (!data.pending_gates || data.pending_gates.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5">No pending gates</td></tr>';
                    return;
                }
                
                tbody.innerHTML = data.pending_gates.map(gate => {
                    const ageClass = getAgeClass(gate.age_hours, gate.timeout_hours);
                    return '<tr>' +
                        '<td><span class="gate-type gate-type-' + gate.gate_type + '">' + gate.gate_type + '</span></td>' +
                        '<td>' + gate.entity_type + ':' + gate.entity_id.slice(0,8) + '</td>' +
                        '<td><span class="' + ageClass + '">' + Math.round(gate.age_hours * 10) / 10 + 'h</span></td>' +
                        '<td>' + (gate.approver || '-') + '</td>' +
                        '<td><span class="status-pending">' + gate.status + '</span></td>' +
                    '</tr>';
                }).join('');
            } catch (e) {
                document.getElementById('gates-body').innerHTML = '<tr><td colspan="5">Failed to load gates</td></tr>';
            }
        }
        
        loadGates();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/heartbeats", response_class=HTMLResponse)
async def dashboard_heartbeats(request: Request) -> HTMLResponse:
    """Heartbeat timeline page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heartbeat Timeline - EthosOS</title>
""" + DASHBOARD_CSS + """
    <style>
        .agent-select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; margin-bottom: 16px; }
        .timeline { border-left: 3px solid #ddd; padding-left: 20px; margin-left: 12px; }
        .heartbeat { position: relative; margin: 16px 0; padding: 12px 16px; background: #f8f8f8; border-radius: 6px; }
        .heartbeat::before { content: ''; position: absolute; left: -26px; top: 16px; width: 10px; height: 10px; border-radius: 50%; background: #ddd; }
        .heartbeat.status-idle::before { background: #666; }
        .heartbeat.status-working::before { background: #1976d2; }
        .heartbeat.status-blocked::before { background: #f57c00; }
        .heartbeat.status-complete::before { background: #388e3c; }
        .heartbeat .time { font-size: 12px; color: #666; }
        .heartbeat .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .status-idle { background: #e0e0e0; color: #616161; }
        .status-working { background: #e3f2fd; color: #1976d2; }
        .status-blocked { background: #fff3e0; color: #f57c00; }
        .status-complete { background: #e8f5e9; color: #388e3c; }
        .heartbeat .task { color: #666; margin-top: 4px; }
        .heartbeat .note { margin-top: 8px; font-style: italic; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Heartbeat Timeline</h1>
        </header>
        
        <nav>
            <a href="/dashboard">Overview</a>
            <a href="/dashboard/tree">Initiative Tree</a>
            <a href="/dashboard/gates">Gate Status</a>
            <a href="/dashboard/heartbeats" class="active">Heartbeats</a>
            <a href="/dashboard/search">Search</a>
        </nav>
        
        <div class="panel">
            <h2>Select Agent</h2>
            <select class="agent-select" id="agent-select" onchange="loadHeartbeats()">
                <option value="">Select an agent...</option>
            </select>
            
            <div id="timeline">
                <p>Select an agent to view heartbeat timeline.</p>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '';
        
        async function loadAgents() {
            try {
                const resp = await fetch(API_BASE + '/agents');
                const agents = await resp.json();
                
                const select = document.getElementById('agent-select');
                agents.forEach(agent => {
                    const opt = document.createElement('option');
                    opt.value = agent.id;
                    opt.textContent = agent.name + ' (' + agent.status + ')';
                    select.appendChild(opt);
                });
            } catch (e) {
                console.error('Failed to load agents:', e);
            }
        }
        
        async function loadHeartbeats() {
            const agentId = document.getElementById('agent-select').value;
            const timeline = document.getElementById('timeline');
            
            if (!agentId) {
                timeline.innerHTML = '<p>Select an agent to view heartbeat timeline.</p>';
                return;
            }
            
            try {
                timeline.innerHTML = '<div class="loading">Loading heartbeats...</div>';
                
                const resp = await fetch(API_BASE + '/agents/' + agentId + '/heartbeats?limit=50');
                const heartbeats = await resp.json();
                
                if (heartbeats.length === 0) {
                    timeline.innerHTML = '<p>No heartbeats recorded for this agent.</p>';
                    return;
                }
                
                let html = '<div class="timeline">';
                heartbeats.forEach(hb => {
                    html += '<div class="heartbeat status-' + hb.status + '">' +
                        '<div>' +
                            '<span class="status status-' + hb.status + '">' + hb.status + '</span>' +
                            '<span class="time">' + hb.timestamp + '</span>' +
                        '</div>' +
                        (hb.task_id ? '<div class="task">Task: ' + hb.task_id.slice(0,8) + '...</div>' : '') +
                        (hb.progress_note ? '<div class="note">' + hb.progress_note + '</div>' : '') +
                    '</div>';
                });
                html += '</div>';
                
                timeline.innerHTML = html;
            } catch (e) {
                timeline.innerHTML = '<div class="error">Failed to load heartbeats</div>';
            }
        }
        
        loadAgents();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/search", response_class=HTMLResponse)
async def dashboard_search(request: Request) -> HTMLResponse:
    """Basic search page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search - EthosOS</title>
""" + DASHBOARD_CSS + """
    <style>
        .search-form { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .search-input { flex: 1; min-width: 200px; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }
        .search-select { padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }
        .search-btn { padding: 12px 24px; background: #0066cc; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
        .results-grid { display: grid; gap: 16px; }
        .result-section h3 { font-size: 14px; text-transform: uppercase; color: #666; margin-bottom: 12px; }
        .result-item { padding: 12px; background: #f8f8f8; border-radius: 6px; margin-bottom: 8px; }
        .result-item a { color: #0066cc; text-decoration: none; font-weight: 500; }
        .result-type { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Search Initiatives</h1>
        </header>
        
        <nav>
            <a href="/dashboard">Overview</a>
            <a href="/dashboard/tree">Initiative Tree</a>
            <a href="/dashboard/gates">Gate Status</a>
            <a href="/dashboard/heartbeats">Heartbeats</a>
            <a href="/dashboard/search" class="active">Search</a>
        </nav>
        
        <div class="panel">
            <form class="search-form" onsubmit="doSearch(event)">
                <input type="text" class="search-input" id="search-input" placeholder="Search by name..." />
                <select class="search-select" id="type-filter">
                    <option value="">All types</option>
                    <option value="portfolio">Portfolio</option>
                    <option value="program">Program</option>
                    <option value="project">Project</option>
                    <option value="sprint">Sprint</option>
                    <option value="task">Task</option>
                </select>
                <button type="submit" class="search-btn">Search</button>
            </form>
            
            <div id="results">
                <p>Enter a search term to find initiatives.</p>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '';
        
        async function doSearch(e) {
            e.preventDefault();
            
            const q = document.getElementById('search-input').value.trim();
            const type = document.getElementById('type-filter').value;
            const results = document.getElementById('results');
            
            if (!q) {
                results.innerHTML = '<p>Enter a search term.</p>';
                return;
            }
            
            try {
                results.innerHTML = '<div class="loading">Searching...</div>';
                
                const url = API_BASE + '/hierarchy/search?q=' + encodeURIComponent(q);
                const resp = await fetch(url);
                const data = await resp.json();
                
                let html = '<div class="results-grid">';
                
                const sections = [
                    {key: 'portfolios', label: 'Portfolios'},
                    {key: 'programs', label: 'Programs'},
                    {key: 'projects', label: 'Projects'},
                    {key: 'sprints', label: 'Sprints'},
                    {key: 'tasks', label: 'Tasks'}
                ];
                
                let hasResults = false;
                for (const section of sections) {
                    const items = data[section.key] || [];
                    if (items.length > 0) {
                        hasResults = true;
                        html += '<div class="result-section"><h3>' + section.label + ' (' + items.length + ')</h3>';
                        for (const item of items) {
                            html += '<div class="result-item">' +
                                '<a href="#">' + item.name + '</a>' +
                                '<div class="result-type">' + item.type + '</div>' +
                            '</div>';
                        }
                        html += '</div>';
                    }
                }
                
                if (!hasResults) {
                    html += '<p>No results found.</p>';
                }
                
                html += '</div>';
                results.innerHTML = html;
            } catch (e) {
                results.innerHTML = '<div class="error">Search failed</div>';
            }
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)