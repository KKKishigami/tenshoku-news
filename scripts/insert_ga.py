#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, glob

GA_TAG = """  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-RW22NSV162"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-RW22NSV162');
  </script>"""

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = (
    glob.glob(os.path.join(base, '*.html')) +
    glob.glob(os.path.join(base, 'articles', '*.html'))
)

count = 0
skipped = 0
for path in sorted(files):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    if 'G-RW22NSV162' in html:
        skipped += 1
        continue
    new_html = html.replace('<head>', '<head>\n' + GA_TAG, 1)
    if new_html != html:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        count += 1
        print(f'Updated: {os.path.basename(path)}')

print(f'\n挿入完了: {count} ファイル')
print(f'スキップ（挿入済み）: {skipped} ファイル')
