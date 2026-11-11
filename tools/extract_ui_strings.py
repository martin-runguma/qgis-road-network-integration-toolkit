#!/usr/bin/env python3
"""Extract candidate user-facing string literals for localization review.

This is a candidate inventory, not an automatic translator: technical IDs,
file extensions, provider names, geometry tokens and code literals are filtered.
"""
import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT / 'gui' / 'main_dialog.py', ROOT / 'core' / 'controller.py',
           ROOT / 'core' / 'background_task.py', ROOT / 'core' / 'datasource_utils.py',
           ROOT / 'core' / 'legacy_engine.py', ROOT / 'road_network_integration_toolkit.py']

UI_METHODS = {'setText', 'setWindowTitle', 'setToolTip', 'setPlaceholderText',
              'setStatusTip', 'addItem', 'addButton', 'QLabel', 'QGroupBox',
              'QPushButton', 'QCheckBox', 'QMessageBox', 'QInputDialog',
              'QFileDialog', 'QAction', '_show_message', '_log'}
SKIP_EXACT = {'', 'en', 'fr', 'es', 'it', 'zh', 'ar', 'pt', 'de', 'ru', 'ja',
              'sw', 'sv', 'nb', 'da', 'hi', 'bn', 'ur', 'pa', 'mr', 'te',
              'ta', 'gu', 'id', 'tr', 'ko', 'vi', 'fa', 'th', 'pl', 'nl',
              'uk', 'am', 'ha', 'EPSG', 'gpkg', 'shp', 'gdb', 'utf-8'}

class Visitor(ast.NodeVisitor):
    def __init__(self, path): self.path, self.rows = path, []
    def visit_Expr(self, node):
        # Ignore docstrings.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str): return
        self.generic_visit(node)
    def visit_Constant(self, node):
        if not isinstance(node.value, str): return
        value = ' '.join(node.value.split())
        if len(value) < 2 or value in SKIP_EXACT: return
        if value.startswith(('http://', 'https://')): return
        if value.startswith(('Qgs', 'Qt.', 'QVariant', 'EPSG:')): return
        if value.startswith('__') or value.isidentifier(): return
        parent = getattr(node, 'parent', None)
        call = getattr(parent, 'parent', None)
        method = ''
        if isinstance(call, ast.Call):
            fn = call.func
            method = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else '')
        # Keep natural-language strings and anything passed to UI/log APIs.
        words = sum(1 for x in value.split() if any(c.isalpha() for c in x))
        if words < 2 and method not in UI_METHODS: return
        if value.startswith(('.', '/', '\\')) and words < 3: return
        self.rows.append((str(self.path.relative_to(ROOT)), node.lineno, method, value))

all_rows=[]
for path in SOURCES:
    if not path.exists(): continue
    tree=ast.parse(path.read_text(encoding='utf-8'))
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent): child.parent=parent
    v=Visitor(path); v.visit(tree); all_rows.extend(v.rows)
# Deduplicate exact text while retaining every source location.
seen=set(); rows=[]
for row in all_rows:
    key=(row[0],row[1],row[3])
    if key not in seen: seen.add(key); rows.append(row)
out=ROOT/'LOCALIZATION_STRING_INVENTORY.csv'
with out.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['source_file','line','ui_context','candidate_source_text']); w.writerows(rows)
print(f'Wrote {len(rows)} candidate string occurrences to {out.name}')
print(f'Unique candidate strings: {len(set(r[3] for r in rows))}')
