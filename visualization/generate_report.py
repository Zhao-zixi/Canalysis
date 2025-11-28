import json
import os
from pathlib import Path

def generate_report(json_path: str, output_path: str):
    print(f"Generating report from {json_path} to {output_path}")
    # Read the analysis data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {json_path}")
        return
    
    # Load libraries
    libs_dir = Path(output_path).parent / "libs"
    cytoscape_js = ""
    dagre_js = ""
    cytoscape_dagre_js = ""
    
    try:
        with open(libs_dir / "cytoscape.min.js", "r", encoding="utf-8") as f:
            cytoscape_js = f.read()
        with open(libs_dir / "dagre.min.js", "r", encoding="utf-8") as f:
            dagre_js = f.read()
        with open(libs_dir / "cytoscape-dagre.min.js", "r", encoding="utf-8") as f:
            cytoscape_dagre_js = f.read()
    except Exception as e:
        print(f"Warning: Could not read local libraries: {e}. Report may not work offline.")

    # Prepare the HTML content
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canalysis Report</title>
    <script>
        /* CYTOSCAPE_LIB */
    </script>
    <script>
        /* DAGRE_LIB */
    </script>
    <script>
        /* CYTOSCAPE_DAGRE_LIB */
    </script>
    <style>
        :root {
            --border-color: #e1e4e8;
            --bg-color: #ffffff;
            --sidebar-bg: #f6f8fa;
            --text-primary: #24292e;
            --text-secondary: #586069;
            --accent-color: #0366d6;
            --accent-hover: #005cc5;
            --header-height: 56px;
            --sidebar-width: 300px;
            --shadow: 0 1px 3px rgba(0,0,0,0.12);
            --node-kernel-bg: #fff0f0;
            --node-kernel-border: #d73a49;
            --node-user-bg: #f1f8ff;
            --node-user-border: #0366d6;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            color: var(--text-primary);
            background: var(--bg-color);
        }

        header {
            height: var(--header-height);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            padding: 0 24px;
            background: #fff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            z-index: 10;
        }

        h1 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-right: auto;
        }
        
        h1::before {
            content: '🔍';
            font-size: 20px;
        }

        .view-controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            background: #f1f3f5;
            padding: 4px;
            border-radius: 6px;
            margin-left: 12px;
        }

        button {
            padding: 6px 16px;
            border: none;
            background: transparent;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            transition: all 0.2s;
        }

        button:hover {
            color: var(--text-primary);
            background: rgba(0,0,0,0.05);
        }

        button.active {
            background: #fff;
            color: var(--accent-color);
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        #main-container {
            flex: 1;
            display: flex;
            overflow: hidden;
        }

        .sidebar {
            width: var(--sidebar-width);
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
        }

        .sidebar-right {
            border-right: none;
            border-left: 1px solid var(--border-color);
            background: #fff;
        }

        .resizer {
            width: 4px;
            background: transparent;
            cursor: col-resize;
            flex-shrink: 0;
            transition: background 0.2s;
            z-index: 10;
        }

        .resizer:hover {
            background: var(--accent-color);
        }

        #center-pane {
            flex: 1;
            background: #fafbfc;
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.02);
        }

        #cy {
            width: 100%;
            height: 100%;
        }
        
        #context-menu {
            position: absolute;
            background: white;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 4px;
            display: none;
            z-index: 100;
            border-radius: 6px;
            min-width: 150px;
        }
        
        #context-menu button {
            display: block;
            width: 100%;
            text-align: left;
            border: none;
            padding: 8px 12px;
            margin: 0;
            border-radius: 4px;
        }
        
        #context-menu button:hover {
            background: var(--accent-color);
            color: white;
        }

        /* Left Sidebar Styles */
        .search-box {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            background: #fff;
        }

        .search-box input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 13px;
            transition: border-color 0.2s;
            outline: none;
        }
        
        .search-box input:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
        }

        .file-tree {
            flex: 1;
            overflow-y: auto;
            padding: 10px 0;
        }

        .tree-item {
            cursor: pointer;
            padding: 6px 12px 6px 28px;
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .tree-item::before {
            content: 'ƒ';
            font-style: italic;
            font-family: serif;
            color: #a0a0a0;
            font-size: 11px;
        }

        .tree-item:hover {
            background: #ebf0f4;
            color: var(--text-primary);
        }

        .tree-item.selected {
            background: #e6f6ff; /* Lightest blue */
            color: var(--accent-color);
            border-left: 3px solid var(--accent-color);
            padding-left: 25px;
        }

        .folder-group {
            margin-bottom: 2px;
        }

        .folder-header {
            padding: 6px 12px;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
            user-select: none;
        }

        .folder-header:hover {
            background: rgba(0,0,0,0.03);
        }

        .folder-icon {
            width: 16px;
            height: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: #6a737d;
            transition: transform 0.2s;
        }

        .folder-header.collapsed .folder-icon {
            transform: rotate(-90deg);
        }
        
        .folder-content {
            display: block;
            transition: all 0.2s;
        }
        
        .folder-header.collapsed + .folder-content {
            display: none;
        }
        
        /* Fix for File collapse */
        .file-header {
            padding: 6px 12px 6px 24px;
            cursor: pointer;
            color: var(--text-primary);
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .file-header:hover {
            background: rgba(0,0,0,0.03);
        }
        
        .file-header.collapsed .folder-icon {
            transform: rotate(-90deg);
        }
        
        .file-header.collapsed + .folder-content {
            display: none;
        }
        
        .file-icon {
            color: #6a737d;
        }

        /* Right Sidebar Styles */
        .details-panel {
            padding: 24px;
            overflow-y: auto;
            height: 100%;
        }

        .detail-section {
            margin-bottom: 24px;
            background: #fff;
            border-radius: 8px;
        }

        .detail-title {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 8px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .detail-content {
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-primary);
        }
        
        .function-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .code-block {
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 12px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre;
            border: 1px solid #e1e4e8;
            color: #24292e;
        }

        .call-link {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin-bottom: 8px;
            text-decoration: none;
            color: var(--accent-color);
            font-weight: 500;
            font-size: 13px;
            transition: all 0.2s;
        }

        .call-link:hover {
            border-color: var(--accent-color);
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .call-condition {
            font-size: 11px;
            color: var(--text-secondary);
            background: rgba(0,0,0,0.05);
            padding: 2px 6px;
            border-radius: 4px;
            max-width: 150px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .tag {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .tag.kernel { 
            background: var(--node-kernel-bg); 
            color: var(--node-kernel-border);
            border: 1px solid rgba(215, 58, 73, 0.2);
        }
        
        .tag.user { 
            background: var(--node-user-bg); 
            color: var(--node-user-border);
            border: 1px solid rgba(3, 102, 214, 0.2);
        }

        .node-controls {
            margin-top: 12px;
        }
        
        .btn-primary {
            background: var(--accent-color);
            color: white;
            padding: 8px 16px;
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
            color: white;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: #d1d5da;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #959da5;
        }

    </style>
</head>
<body>
    <header>
        <h1 data-i18n="title">Canalysis Report</h1>
        <div class="view-controls">
            <div class="control-group">
                <button id="btn-global" class="active" onclick="switchView('global')" data-i18n="global_view">Global Map</button>
                <button id="btn-local" onclick="switchView('local')" data-i18n="local_view">Local Focus</button>
            </div>
            <div class="control-group">
                <button id="btn-lang-en" class="active" onclick="setLanguage('en')">EN</button>
                <button id="btn-lang-zh" onclick="setLanguage('zh')">中文</button>
            </div>
        </div>
    </header>
    <div id="main-container">
        <div class="sidebar" id="left-sidebar">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Filter functions..." onkeyup="filterFunctions()" data-i18n-placeholder="search_placeholder">
            </div>
            <div class="file-tree" id="file-tree">
                <!-- Tree content generated by JS -->
            </div>
        </div>
        <div class="resizer" id="resizer-left"></div>
        
        <div id="center-pane">
            <div id="cy"></div>
            <div id="context-menu">
                <button onclick="expandNode(contextNodeId, 'parents')" data-i18n="expand_callers">Expand Callers</button>
                <button onclick="expandNode(contextNodeId, 'children')" data-i18n="expand_callees">Expand Callees</button>
                <button onclick="collapseNode(contextNodeId)" data-i18n="collapse_neighbors">Collapse Neighbors</button>
            </div>
        </div>
        
        <div class="resizer" id="resizer-right"></div>
        <div class="sidebar sidebar-right" id="right-sidebar">
            <div class="details-panel" id="details-panel">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary); text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">👈</div>
                    <p data-i18n="select_hint">Select a function node to view details</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const rawData = DATA_PLACEHOLDER;
        
        // I18N Configuration
        const i18n = {
            en: {
                title: "Canalysis Report",
                global_view: "Global Map",
                local_view: "Local Focus",
                search_placeholder: "Filter functions...",
                expand_callers: "Expand Callers (Upstream)",
                expand_callees: "Expand Callees (Downstream)",
                collapse_neighbors: "Collapse Neighbors",
                select_hint: "Select a function node to view details",
                summary: "Summary",
                location: "Location",
                callers: "Callers",
                calls: "Calls",
                code: "Code",
                notes: "Notes",
                focus_view: "Focus View",
                no_summary: "No summary available",
                no_calls: "No outgoing calls",
                no_callers: "No incoming callers",
                function: "Function"
            },
            zh: {
                title: "函数分析报告",
                global_view: "全局视图",
                local_view: "局部聚焦",
                search_placeholder: "搜索函数...",
                expand_callers: "展开调用方 (上游)",
                expand_callees: "展开被调用方 (下游)",
                collapse_neighbors: "收起邻居节点",
                select_hint: "选择一个函数节点以查看详情",
                summary: "功能摘要",
                location: "代码位置",
                callers: "被调用 (Callers)",
                calls: "调用 (Calls)",
                code: "源码内容",
                notes: "备注",
                focus_view: "聚焦视图",
                no_summary: "暂无摘要",
                no_calls: "无出站调用",
                no_callers: "无入站调用",
                function: "函数"
            }
        };
        
        let currentLang = 'en';

        function setLanguage(lang) {
            currentLang = lang;
            
            // Update buttons
            document.getElementById('btn-lang-en').classList.toggle('active', lang === 'en');
            document.getElementById('btn-lang-zh').classList.toggle('active', lang === 'zh');
            
            // Update static elements
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (i18n[lang][key]) el.textContent = i18n[lang][key];
            });
            
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const key = el.getAttribute('data-i18n-placeholder');
                if (i18n[lang][key]) el.placeholder = i18n[lang][key];
            });
            
            // Refresh Details Panel if selected
            if (selectedNodeId) {
                renderDetails(selectedNodeId);
            } else {
                // Refresh hint
                 const panel = document.getElementById('details-panel');
                 panel.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary); text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 16px;">👈</div>
                        <p>${i18n[lang].select_hint}</p>
                    </div>`;
            }
        }
        
        // Process data
        const nodesMap = {}; // id -> node data
        const edges = [];
        
        // Helper to generate ID
        function getId(item) {
            return item.file_path + "::" + item.function_name;
        }

        // 1. Build Nodes Map and File Structure
        rawData.forEach(item => {
            const id = getId(item);
            item.id = id;
            nodesMap[id] = item;
        });

        // Re-building file structure
        const treeData = {};
        rawData.forEach(item => {
            const pathParts = item.file_path.replace(/\\\\/g, '/').split('/');
            const fileName = pathParts.pop();
            let currentDir = treeData;
            
            pathParts.forEach(dir => {
                if (!currentDir[dir]) currentDir[dir] = { _type: 'dir', _children: {} };
                currentDir = currentDir[dir]._children;
            });
            
            if (!currentDir[fileName]) currentDir[fileName] = { _type: 'file', _funcs: [] };
            currentDir[fileName]._funcs.push(item);
        });

        // 2. Build Edges
        rawData.forEach(item => {
            const sourceId = item.id;
            if (item.calls) {
                item.calls.forEach(call => {
                    // Find target in our data
                    const candidates = rawData.filter(n => n.function_name === call.callee);
                    if (candidates.length > 0) {
                        candidates.forEach(target => {
                            edges.push({
                                data: {
                                    source: sourceId,
                                    target: target.id,
                                    label: call.condition !== 'unconditional' ? call.condition : ''
                                }
                            });
                        });
                    } else {
                        // External or missing node
                        const ghostId = "external::" + call.callee;
                        if (!nodesMap[ghostId]) {
                            const ghostNode = {
                                id: ghostId,
                                function_name: call.callee,
                                origin: "external",
                                file_path: "external",
                                line_number: 0,
                                summary: "External or unanalyzed function",
                                content: "",
                                calls: [],
                                notes: "Auto-generated external node"
                            };
                            nodesMap[ghostId] = ghostNode;
                            edges.push({
                                data: {
                                    source: sourceId,
                                    target: ghostId,
                                    label: call.condition !== 'unconditional' ? call.condition : ''
                                }
                            });
                        } else {
                            edges.push({
                                data: {
                                    source: sourceId,
                                    target: ghostId,
                                    label: call.condition !== 'unconditional' ? call.condition : ''
                                }
                            });
                        }
                    }
                });
            }
        });

        let cy = null;
        let currentView = 'global';
        let selectedNodeId = null;
        let contextNodeId = null;
        let visibleNodeIds = new Set();

        // Init Cytoscape
        function initCy() {
            try {
                if (typeof cytoscape === 'undefined') return;
                
                cy = cytoscape({
                    container: document.getElementById('cy'),
                    minZoom: 0.1,
                    maxZoom: 3,
                    wheelSensitivity: 0.2,
                    style: [
                        {
                            selector: 'node',
                            style: {
                                'label': 'data(label)',
                                'background-color': '#ffffff',
                                'border-width': 2,
                                'border-color': '#0366d6',
                                'color': '#24292e',
                                'font-size': '12px',
                                'font-weight': '600',
                                'text-valign': 'center',
                                'text-halign': 'center',
                                'width': 'label',
                                'height': 'label',
                                'padding': '12px',
                                'shape': 'round-rectangle',
                                'text-margin-y': 0,
                                'shadow-blur': 4,
                                'shadow-color': 'rgba(0,0,0,0.1)',
                                'shadow-offset-y': 2,
                                'transition-property': 'background-color, border-color, border-width',
                                'transition-duration': '0.2s'
                            }
                        },
                        {
                            selector: 'node.kernel',
                            style: { 
                                'border-color': '#d73a49', 
                                'background-color': '#fff0f0',
                                'color': '#cf222e'
                            }
                        },
                        {
                            selector: 'node.user',
                            style: { 
                                'border-color': '#0366d6', 
                                'background-color': '#f1f8ff',
                                'color': '#0969da'
                            }
                        },
                        {
                            selector: 'node.external',
                            style: { 
                                'border-color': '#6a737d', 
                                'background-color': '#fafbfc',
                                'color': '#586069',
                                'border-style': 'dashed'
                            }
                        },
                        {
                            selector: ':selected',
                            style: {
                                'border-width': 4,
                                'shadow-blur': 12,
                                'shadow-color': 'rgba(0,0,0,0.2)',
                                'shadow-offset-y': 4
                            }
                        },
                        {
                            selector: 'edge',
                            style: {
                                'width': 2,
                                'line-color': '#d1d5da',
                                'target-arrow-color': '#d1d5da',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'arrow-scale': 1.2,
                                'label': 'data(label)',
                                'font-size': '10px',
                                'color': '#586069',
                                'text-background-color': '#ffffff',
                                'text-background-opacity': 0.9,
                                'text-background-padding': '3px',
                                'text-rotation': 'autorotate',
                                'text-margin-y': -8
                            }
                        },
                        {
                            selector: 'edge.highlighted',
                            style: {
                                'line-color': '#0366d6',
                                'target-arrow-color': '#0366d6',
                                'width': 3
                            }
                        }
                    ],
                    layout: { name: 'dagre', rankDir: 'LR' }
                });

                cy.on('tap', 'node', function(evt){
                    const node = evt.target;
                    selectNode(node.id());
                    hideContextMenu();
                });
                
                cy.on('tap', function(evt){
                    if (evt.target === cy) hideContextMenu();
                });

                cy.on('dbltap', 'node', function(evt){
                    const node = evt.target;
                    selectNode(node.id());
                    switchView('local');
                });
                
                cy.on('cxttap', 'node', function(evt){
                    const node = evt.target;
                    contextNodeId = node.id();
                    showContextMenu(evt.originalEvent.clientX, evt.originalEvent.clientY);
                });

            } catch (e) {
                console.error("Cytoscape init failed:", e);
            }
        }
        
        function showContextMenu(x, y) {
            const menu = document.getElementById('context-menu');
            menu.style.display = 'block';
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';
        }
        
        function hideContextMenu() {
            document.getElementById('context-menu').style.display = 'none';
        }

        function runLayout(options = {}) {
            try {
                const defaultOptions = { 
                    name: 'dagre', 
                    rankDir: 'LR',
                    nodeSep: 60,
                    rankSep: 120,
                    padding: 50,
                    animate: true,
                    animationDuration: 500,
                    fit: true
                };
                const layout = cy.layout({ ...defaultOptions, ...options });
                layout.run();
                return layout;
            } catch (e) {
                cy.layout({ name: 'grid' }).run();
            }
        }

        function renderGlobal() {
            cy.elements().remove();
            const nodes = Object.values(nodesMap).map(item => ({
                data: { id: item.id, label: item.function_name, origin: item.origin },
                classes: item.origin
            }));
            cy.add(nodes);
            cy.add(edges);
            runLayout();
        }

        function renderLocal(centerId) {
            if (!centerId) return;
            visibleNodeIds.clear();
            visibleNodeIds.add(centerId);
            edges.forEach(e => {
                if (e.data.source === centerId) visibleNodeIds.add(e.data.target);
                if (e.data.target === centerId) visibleNodeIds.add(e.data.source);
            });
            refreshLocalGraph(centerId);
        }
        
        function refreshLocalGraph(centerId) {
            cy.elements().remove();
            const nodesToAdd = [];
            visibleNodeIds.forEach(id => {
                const item = nodesMap[id];
                if (item) {
                    nodesToAdd.push({
                        data: { id: id, label: item.function_name, origin: item.origin },
                        classes: item.origin
                    });
                }
            });
            cy.add(nodesToAdd);
            const edgesToAdd = [];
            edges.forEach(e => {
                if (visibleNodeIds.has(e.data.source) && visibleNodeIds.has(e.data.target)) {
                    edgesToAdd.push(e);
                }
            });
            cy.add(edgesToAdd);
            
            // Run layout with a callback to adjust zoom cleanly
            const layout = cy.layout({
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 60,
                rankSep: 120,
                padding: 50,
                animate: true,
                animationDuration: 500,
                fit: true,
                stop: function() {
                    // Post-layout adjustment
                    if (centerId) {
                        cy.getElementById(centerId).select();
                        // Smoothly zoom out a bit if it's too tight
                        // Note: dagre 'fit' puts it in view. We want to shrink 20%.
                        const currentZoom = cy.zoom();
                        cy.animate({
                            zoom: currentZoom * 0.8,
                            center: { eles: cy.getElementById(centerId) }
                        }, { duration: 300 });
                    }
                }
            });
            layout.run();
        }
        
        function expandNode(nodeId, direction) {
            hideContextMenu();
            if (!nodeId) return;
            let added = false;
            if (direction === 'parents' || !direction) {
                edges.forEach(e => {
                    if (e.data.target === nodeId && !visibleNodeIds.has(e.data.source)) {
                        visibleNodeIds.add(e.data.source);
                        added = true;
                    }
                });
            }
            if (direction === 'children' || !direction) {
                edges.forEach(e => {
                    if (e.data.source === nodeId && !visibleNodeIds.has(e.data.target)) {
                        visibleNodeIds.add(e.data.target);
                        added = true;
                    }
                });
            }
            if (added) refreshLocalGraph(selectedNodeId);
        }
        
        function collapseNode(nodeId) {
            hideContextMenu();
            if (!nodeId) return;
            const neighbors = new Set();
            edges.forEach(e => {
                if (e.data.source === nodeId && visibleNodeIds.has(e.data.target)) neighbors.add(e.data.target);
                if (e.data.target === nodeId && visibleNodeIds.has(e.data.source)) neighbors.add(e.data.source);
            });
            let removed = false;
            neighbors.forEach(nId => {
                if (nId === selectedNodeId) return; 
                let degree = 0;
                edges.forEach(e => {
                    if (visibleNodeIds.has(e.data.source) && visibleNodeIds.has(e.data.target)) {
                        if (e.data.source === nId || e.data.target === nId) degree++;
                    }
                });
                if (degree <= 1) {
                    visibleNodeIds.delete(nId);
                    removed = true;
                }
            });
            if (removed) refreshLocalGraph(selectedNodeId);
        }

        function switchView(mode) {
            currentView = mode;
            document.querySelectorAll('.view-controls button').forEach(b => {
                if (b.id.startsWith('btn-global') || b.id.startsWith('btn-local')) {
                    b.classList.remove('active');
                }
            });
            document.getElementById('btn-' + mode).classList.add('active');
            
            if (mode === 'global') {
                renderGlobal();
                if (selectedNodeId && cy.getElementById(selectedNodeId).length > 0) {
                    cy.getElementById(selectedNodeId).select();
                    // Just center, don't force zoom unless needed
                    cy.animate({
                        center: { eles: cy.getElementById(selectedNodeId) },
                        zoom: 1
                    }, { duration: 500 });
                }
            } else {
                if (selectedNodeId) renderLocal(selectedNodeId);
                else cy.elements().remove();
            }
        }

        function selectNode(id) {
            if (selectedNodeId === id) return;
            selectedNodeId = id;
            
            // Update tree selection
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            if (!id.startsWith("external::")) {
                const treeEl = document.getElementById('tree-' + id.replace(/[^a-zA-Z0-9]/g, '_'));
                if (treeEl) {
                    treeEl.classList.add('selected');
                    let parent = treeEl.parentElement;
                    while (parent && !parent.classList.contains('file-tree')) {
                        if (parent.classList.contains('folder-content')) {
                            const header = parent.previousElementSibling;
                            if (header && header.classList.contains('collapsed')) {
                                toggleFolder(header);
                            }
                        }
                        parent = parent.parentElement;
                    }
                    treeEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
                }
            }
            
            renderDetails(id);
            
            if (currentView === 'global') {
                cy.$(':selected').unselect();
                const el = cy.getElementById(id);
                if (el.length > 0) el.select();
            } else {
                if (cy.getElementById(id).length > 0) {
                    cy.$(':selected').unselect();
                    cy.getElementById(id).select();
                } else {
                    // Implicitly switch if not in view (from sidebar click)
                    // We'll let the sidebar click handler do the switchView call explicitly
                }
            }
        }

        function renderDetails(id) {
            const item = nodesMap[id];
            const panel = document.getElementById('details-panel');
            
            let callsHtml = '';
            if (item.calls && item.calls.length > 0) {
                callsHtml = item.calls.map(c => {
                    const target = rawData.find(n => n.function_name === c.callee);
                    const clickAction = target ? `onclick="jumpTo('${target.id}')"` : '';
                    const style = target ? '' : 'style="color:#666; cursor:default; text-decoration:none;"';
                    return `<a class="call-link" ${style} ${clickAction}>
                        <span>${c.callee}</span>
                        ${c.condition !== 'unconditional' ? `<span class="call-condition">${c.condition}</span>` : ''}
                    </a>`;
                }).join('');
            } else {
                callsHtml = `<span style="color:#586069; font-style: italic;">${i18n[currentLang].no_calls}</span>`;
            }

            // Calculate callers
            let callersHtml = '';
            const callerList = [];
            rawData.forEach(other => {
                if (other.calls) {
                    other.calls.forEach(c => {
                        if (c.callee === item.function_name) {
                            callerList.push({
                                id: other.id,
                                name: other.function_name,
                                condition: c.condition
                            });
                        }
                    });
                }
            });
            
            if (callerList.length > 0) {
                callersHtml = callerList.map(c => {
                    return `<a class="call-link" onclick="jumpTo('${c.id}')" style="border-left: 3px solid #28a745;">
                        <span>${c.name}</span>
                        ${c.condition !== 'unconditional' ? `<span class="call-condition">${c.condition}</span>` : ''}
                    </a>`;
                }).join('');
            } else {
                callersHtml = `<span style="color:#586069; font-style: italic;">${i18n[currentLang].no_callers}</span>`;
            }

            panel.innerHTML = `
                <div class="function-title">
                    ${item.function_name}
                    <span class="tag ${item.origin}">${item.origin}</span>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].summary}</div>
                    <div class="detail-content">
                        ${item.summary || i18n[currentLang].no_summary}
                    </div>
                    <div class="node-controls">
                        <button class="btn-primary" onclick="switchView('local'); selectNode('${id}');">${i18n[currentLang].focus_view}</button>
                    </div>
                </div>

                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].location}</div>
                    <div class="detail-content" style="font-family: monospace;">
                        ${item.file_path}:${item.line_number}
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].callers}</div>
                    <div class="detail-content">
                        ${callersHtml}
                    </div>
                </div>

                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].calls}</div>
                    <div class="detail-content">
                        ${callsHtml}
                    </div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].code}</div>
                    <div class="code-block">${item.content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                </div>
                
                <div class="detail-section">
                    <div class="detail-title">${i18n[currentLang].notes}</div>
                    <div class="detail-content" style="color:#586069;">
                        ${item.notes || '-'}
                    </div>
                </div>
            `;
        }

        function jumpTo(id) {
            selectNode(id);
            switchView('local');
        }

        function toggleFolder(element) {
            element.classList.toggle('collapsed');
        }

        function renderTree(data, container) {
            const keys = Object.keys(data).sort((a, b) => {
                const aIsDir = data[a]._type === 'dir';
                const bIsDir = data[b]._type === 'dir';
                if (aIsDir && !bIsDir) return -1;
                if (!aIsDir && bIsDir) return 1;
                return a.localeCompare(b);
            });
            
            keys.forEach(key => {
                const item = data[key];
                
                if (item._type === 'dir') {
                    const group = document.createElement('div');
                    group.className = 'folder-group';
                    
                    const header = document.createElement('div');
                    header.className = 'folder-header'; 
                    header.innerHTML = '<span class="folder-icon">▼</span> ' + key;
                    header.onclick = () => toggleFolder(header);
                    
                    const content = document.createElement('div');
                    content.className = 'folder-content';
                    content.style.paddingLeft = '12px';
                    
                    group.appendChild(header);
                    group.appendChild(content);
                    container.appendChild(group);
                    
                    renderTree(item._children, content);
                } else if (item._type === 'file') {
                    const group = document.createElement('div');
                    group.className = 'folder-group';
                    
                    const header = document.createElement('div');
                    header.className = 'file-header collapsed'; 
                    header.innerHTML = '<span class="folder-icon">▼</span> <span style="color:#24292e">' + key + '</span>';
                    header.onclick = () => toggleFolder(header);

                    const content = document.createElement('div');
                    content.className = 'folder-content'; 
                    
                    group.appendChild(header);
                    group.appendChild(content);
                    
                    item._funcs.forEach(func => {
                        const funcDiv = document.createElement('div');
                        funcDiv.className = 'tree-item function-node';
                        funcDiv.textContent = func.function_name;
                        funcDiv.id = 'tree-' + func.id.replace(/[^a-zA-Z0-9]/g, '_');
                        funcDiv.onclick = (e) => {
                            e.stopPropagation();
                            selectNode(func.id);
                            switchView('local');
                        };
                        content.appendChild(funcDiv);
                    });
                    
                    container.appendChild(group);
                }
            });
        }

        function filterFunctions() {
            const term = document.getElementById('search-input').value.toLowerCase();
            const items = document.querySelectorAll('.function-node');
            const isFiltering = term.length > 0;
            
            items.forEach(item => {
                if (item.textContent.toLowerCase().includes(term)) {
                    item.style.display = 'flex';
                    if (isFiltering) {
                        let parent = item.parentElement;
                        while(parent && !parent.classList.contains('file-tree')) {
                            if (parent.classList.contains('folder-content')) {
                                parent.previousElementSibling.classList.remove('collapsed');
                            }
                            parent = parent.parentElement;
                        }
                    }
                } else {
                    item.style.display = 'none';
                }
            });
        }

        function initResizers() {
            const makeResizable = (resizerId, prevSiblingId, isLeft) => {
                const resizer = document.getElementById(resizerId);
                let x = 0;
                let w = 0;
                const mouseDownHandler = (e) => {
                    x = e.clientX;
                    const sidebar = document.getElementById(isLeft ? 'left-sidebar' : 'right-sidebar');
                    w = sidebar.getBoundingClientRect().width;
                    document.addEventListener('mousemove', mouseMoveHandler);
                    document.addEventListener('mouseup', mouseUpHandler);
                    resizer.style.background = '#0366d6';
                };
                const mouseMoveHandler = (e) => {
                    const dx = e.clientX - x;
                    const sidebar = document.getElementById(isLeft ? 'left-sidebar' : 'right-sidebar');
                    const newW = isLeft ? w + dx : w - dx; 
                    if (newW > 150 && newW < 600) sidebar.style.width = `${newW}px`;
                };
                const mouseUpHandler = () => {
                    document.removeEventListener('mousemove', mouseMoveHandler);
                    document.removeEventListener('mouseup', mouseUpHandler);
                    resizer.style.background = 'transparent';
                };
                resizer.addEventListener('mousedown', mouseDownHandler);
            };
            makeResizable('resizer-left', 'left-sidebar', true);
            makeResizable('resizer-right', 'right-sidebar', false);
        }

        window.onload = function() {
            renderTree(treeData, document.getElementById('file-tree'));
            initResizers();
            setTimeout(initCy, 100); 
            setTimeout(renderGlobal, 200);
        };

    </script>
</body>
</html>"""

    # Inject libraries and data
    html_content = html_template.replace("/* CYTOSCAPE_LIB */", cytoscape_js)
    html_content = html_content.replace("/* DAGRE_LIB */", dagre_js)
    html_content = html_content.replace("/* CYTOSCAPE_DAGRE_LIB */", cytoscape_dagre_js)
    
    # Inject JSON data using proper escaping
    json_str = json.dumps(data, ensure_ascii=False)
    html_content = html_content.replace("DATA_PLACEHOLDER", json_str)

    # Write HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Successfully generated report at {output_path}")

if __name__ == "__main__":
    # Default paths
    root = Path(__file__).resolve().parent.parent
    print(f"Root path: {root}")
    json_file = root / "llm" / "function_analysis.json"
    # Check if json exists, fallback to serial/async if needed
    if not json_file.exists():
        print(f"Warning: {json_file} not found. Checking alternatives...")
        alt1 = root / "llm" / "function_analysis_serial.json"
        alt2 = root / "llm" / "function_analysis_async.json"
        if alt1.exists():
            json_file = alt1
        elif alt2.exists():
            json_file = alt2
    
    output_file = root / "visualization" / "report.html"
    generate_report(str(json_file), str(output_file))
