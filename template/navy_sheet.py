"""Navy's result-sheet template v2 (7D2 project, 2026-11-24; v1 kept as navy_sheet_v1.py).
Dark technical page. Inspired by professional data graphics (FT / Economist / Bloomberg / product dashboards):
kicker line -> headline that states the finding -> credit -> optional hero-number tiles -> optional photo with corner marks
and labels -> ONE content block (bars / table / kv) -> spec strip -> source line + credit.
Fonts: Inter (text, 400-600) + Consolas Bold (numbers / technical labels); falls back to DejaVu if missing.
Run:  python navy_sheet.py <spec.json>   (needs matplotlib + Pillow; fonts Inter + Consolas if installed)
Spec keys: title (used as headline if no headline), headline, kicker, tag, credit (default EXPERIMENTAL BUILD BY NAVY), out,
  width_in (20), kpis [[label, big value, small sub], ...] (<= 4; first is blue), image, image_labels [tl, tr, bl, br],
  block {type bars: title, rows [[label, value, hl]], unit, pct_of, xmax | type table: title, columns, rows, highlight_rows
         | type kv: title, items}, specs [[label, value], ...] (<= 4), note (source / method, '\\n' allowed)."""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import matplotlib.font_manager as fm

BG = '#121212'; PANEL = '#1b1b1b'; INK = '#f4f3ef'; MUTED = '#b4b2a9'; DIM = '#7d7c76'; GRID = '#2b2b29'; BLUE = '#3d8bea'; GRAY = '#8f8d86'
_names = {f.name for f in fm.fontManager.ttflist}
SANS = 'Inter' if 'Inter' in _names else 'DejaVu Sans'
MONO = 'Consolas' if 'Consolas' in _names else 'DejaVu Sans Mono'


def _block_h(b):
    if not b: return 0.0
    if b['type'] == 'bars': return 0.8 * len(b['rows']) + 1.2
    if b['type'] == 'table': return 0.52 * (len(b['rows']) + 1) + 0.6
    if b['type'] == 'kv': return 0.48 * len(b['items']) + 0.4
    raise ValueError(b['type'])


def make_sheet(S):
    W = float(S.get('width_in', 20.0)); img = None; img_h = 0.0
    if S.get('image'):
        from PIL import Image
        img = Image.open(S['image']); img_h = W * 0.94 * img.height / img.width
    b = S.get('block'); bh = _block_h(b); kp = S.get('kpis') or []
    note = S.get('note', ''); nl = note.count('\n') + 1 if note else 0
    H = 2.05 + (1.9 if kp else 0) + (img_h + 0.55 if img is not None else 0) + (0.7 + bh if b else 0) + (1.45 if S.get('specs') else 0) + 0.36 * nl + 0.95
    fig = plt.figure(figsize=(W, H), dpi=150); fig.patch.set_facecolor(BG)
    fy = lambda y: 1 - y / H
    # header: kicker, headline, credit, tag
    fig.text(0.03, fy(0.42), (S.get('kicker') or '').upper(), color=BLUE, fontsize=12, family=MONO, fontweight='bold', va='center')
    fig.text(0.03, fy(1.0), S.get('headline') or S['title'], color=INK, fontsize=27, family=SANS, fontweight=600, va='center')
    sub = S['title'] if S.get('headline') else ''
    fig.text(0.03, fy(1.5), sub, color=MUTED, fontsize=14.5, family=SANS, va='center')
    if S.get('tag'): fig.text(0.97, fy(0.42), S['tag'], color=MUTED, fontsize=12.5, family=MONO, fontweight='bold', ha='right', va='center')
    fig.add_artist(plt.Line2D([0.03, 0.97], [fy(1.9), fy(1.9)], color=GRID, lw=1.2))
    y = 2.05
    # hero-number tiles
    if kp:
        n = min(4, len(kp)); gap = 0.012; w = (0.94 - gap * (n - 1)) / n
        for i, k in enumerate(kp[:4]):
            x0 = 0.03 + i * (w + gap)
            fig.add_artist(plt.Rectangle((x0, fy(y + 1.7)), w, 1.6 / H, transform=fig.transFigure, color=PANEL, zorder=0))
            fig.add_artist(plt.Rectangle((x0, fy(y + 1.7)), 0.004, 1.6 / H, transform=fig.transFigure, color=BLUE if i == 0 else GRAY, zorder=1))
            fig.text(x0 + 0.014, fy(y + 0.38), str(k[0]).upper(), color=DIM, fontsize=12, family=MONO, fontweight='bold', va='center')
            fig.text(x0 + 0.014, fy(y + 0.9), str(k[1]), color=BLUE if i == 0 else INK, fontsize=33, family=SANS, fontweight=600, va='center')
            if len(k) > 2 and k[2]: fig.text(x0 + 0.014, fy(y + 1.42), str(k[2]), color=MUTED, fontsize=13, family=SANS, va='center')
        y += 1.9
    # photo
    if img is not None:
        ax = fig.add_axes([0.03, fy(y + img_h), 0.94, img_h / H]); ax.imshow(img); ax.set_axis_off()
        o = [pe.withStroke(linewidth=3.5, foreground='#000000b0')]
        L = list(S.get('image_labels', [])) + [''] * 4
        for (x_, y_, ha, va), s in zip(((0.012, 0.975, 'left', 'top'), (0.988, 0.975, 'right', 'top'), (0.012, 0.025, 'left', 'bottom'), (0.988, 0.025, 'right', 'bottom')), L[:4]):
            if s: ax.text(x_, y_, s, transform=ax.transAxes, color=INK, fontsize=14, family=MONO, fontweight='bold', ha=ha, va=va, path_effects=o)
        k = 0.025; ky = k * 0.94 * W / img_h
        for (x0, y0, dx, dy) in ((0, 1, 1, -1), (1, 1, -1, -1), (0, 0, 1, 1), (1, 0, -1, 1)):
            ax.plot([x0, x0 + dx * k], [y0, y0], transform=ax.transAxes, color=INK, lw=1.8, clip_on=False)
            ax.plot([x0, x0], [y0, y0 + dy * ky], transform=ax.transAxes, color=INK, lw=1.8, clip_on=False)
        y += img_h + 0.55
    # content block
    if b:
        if b.get('title'): fig.text(0.03, fy(y + 0.15), b['title'], color=INK, fontsize=16, family=SANS, fontweight=600, va='center')
        if b.get('subtitle'): fig.text(0.03, fy(y + 0.52), b['subtitle'], color=MUTED, fontsize=13, family=SANS, va='center')
        y += 0.7
        if b['type'] == 'bars':
            rows = b['rows']; base = b.get('pct_of'); unit = b.get('unit', '')
            cx = fig.add_axes([0.28, fy(y + bh - 0.8), 0.62, (bh - 1.2) / H]); cx.set_facecolor(BG)
            yy = list(range(len(rows)))[::-1]
            cx.barh(yy, [r[1] for r in rows], height=0.62, color=[BLUE if (len(r) > 2 and r[2]) else GRAY for r in rows], zorder=3)
            xmax = b.get('xmax') or max(r[1] for r in rows) * 1.18
            for yi, r in zip(yy, rows):
                hl = len(r) > 2 and r[2]
                t = ('%.2f %s' % (r[1], unit)).strip() + ('   %d%%' % round(r[1] / base * 100) if base else '')
                cx.text(r[1] + xmax * 0.01, yi, t, va='center', color=BLUE if hl else INK, fontsize=17, family=MONO, fontweight='bold')
            cx.set_yticks(yy); cx.set_yticklabels([r[0] for r in rows], fontsize=15.5, family=SANS)
            for lbl, r in zip(cx.get_yticklabels(), rows):
                lbl.set_color(INK if (len(r) > 2 and r[2]) else MUTED); lbl.set_fontweight(600 if (len(r) > 2 and r[2]) else 400)
            cx.set_xlim(0, xmax); cx.tick_params(axis='x', colors=DIM, labelsize=13); cx.tick_params(axis='y', length=0, pad=10)
            for t_ in cx.get_xticklabels(): t_.set_family(MONO)
            cx.grid(axis='x', color=GRID, lw=1, zorder=0); [s_.set_visible(False) for s_ in cx.spines.values()]
            cx.axvline(0, color=MUTED, lw=1.2, zorder=4)
            if b.get('axis'): cx.set_xlabel(b['axis'], color=DIM, fontsize=13.5, family=SANS, labelpad=10)
        elif b['type'] == 'table':
            cols = b['columns']; rows = b['rows']; hl = set(b.get('highlight_rows', [])); n = len(cols)
            xs = [0.03 + 0.94 * i / n for i in range(n)]
            for i, c in enumerate(cols): fig.text(xs[i], fy(y + 0.12), str(c).upper(), color=DIM, fontsize=12.5, family=MONO, fontweight='bold', va='center')
            fig.add_artist(plt.Line2D([0.03, 0.97], [fy(y + 0.42), fy(y + 0.42)], color=MUTED, lw=1))
            for r_i, r in enumerate(rows):
                yy = y + 0.78 + 0.52 * r_i
                if r_i in hl: fig.add_artist(plt.Rectangle((0.03, fy(yy + 0.24)), 0.94, 0.48 / H, transform=fig.transFigure, color=PANEL, zorder=0))
                for i, v in enumerate(r):
                    fig.text(xs[i] + (0.006 if r_i in hl else 0), fy(yy), str(v), color=BLUE if r_i in hl else INK, fontsize=16,
                             family=SANS if i == 0 else MONO, fontweight=600 if (r_i in hl or i == 0) else 'normal', va='center')
                fig.add_artist(plt.Line2D([0.03, 0.97], [fy(yy + 0.26), fy(yy + 0.26)], color=GRID, lw=0.8))
        elif b['type'] == 'kv':
            for i, (k_, v_) in enumerate(b['items']):
                yy = y + 0.12 + 0.48 * i
                fig.text(0.03, fy(yy), str(k_).upper(), color=DIM, fontsize=11.5, family=MONO, fontweight='bold', va='center')
                fig.text(0.30, fy(yy), str(v_), color=INK, fontsize=15.5, family=SANS, va='center')
        y += bh
    # spec strip
    if S.get('specs'):
        fig.add_artist(plt.Line2D([0.03, 0.97], [fy(y + 0.05), fy(y + 0.05)], color=GRID, lw=1.2))
        for i, (k_, v_) in enumerate(S['specs'][:4]):
            x_ = 0.03 + i * 0.2375
            fig.text(x_, fy(y + 0.45), str(k_).upper(), color=DIM, fontsize=12, family=MONO, fontweight='bold', va='center')
            fig.text(x_, fy(y + 0.9), str(v_), color=INK, fontsize=15.5, family=SANS, fontweight=500, va='center')
        y += 1.45
    # source + credit
    fig.add_artist(plt.Line2D([0.03, 0.97], [fy(y + 0.05), fy(y + 0.05)], color=GRID, lw=1.2))
    if note: fig.text(0.03, fy(y + 0.3), 'SOURCE / METHOD:  ' + note, color=DIM, fontsize=11.5, family=SANS, va='top', linespacing=1.6)
    fig.text(0.97, fy(H - 0.4), S.get('credit', 'EXPERIMENTAL BUILD BY NAVY'), color=BLUE, fontsize=12, family=MONO, fontweight='bold', ha='right', va='center')
    fig.savefig(S['out'], facecolor=BG); plt.close(fig)
    return S['out']


if __name__ == '__main__':
    print(make_sheet(json.load(open(sys.argv[1], encoding='utf-8'))))
