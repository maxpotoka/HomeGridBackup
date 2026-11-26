# patch-id: stats-short-x-os-3.54
# [\u0424\u0410\u0419\u041b: gui/stats_view.py (v2.17 | 26.11.2026 10:33)
# patch-id: stats-cols-widen-3.53
# [\u0424\u0410\u0419\u041b: gui/stats_view.py (v2.16 | 26.11.2026 10:28)
# patch-id: ubuntu-stats-repaint-3.61
import threading, tkinter as tk
from tkinter import ttk

def show_three_tab_stats(dlg, root, engine, p, k, fs, fam, lang, _w, _p):
    sec_var = tk.StringVar(value='server')
    who_var = tk.StringVar(value='ALL')
    pc_var = tk.StringVar(value='ALL')
    net_var = tk.StringVar(value='ALL')
    srv_var = tk.StringVar(value='ALL')
    os_var = tk.StringVar(value='ALL')
    state_data = {'server': [], 'network': [], 'hardware': []}
    tab_btns, who_btns = {}, {}

    bf = tk.Frame(dlg, bg=p['bg'])
    bf.pack(side='bottom', fill='x', padx=14, pady=(4, 10))
    tk.Button(bf, text=_w if lang == 'uk' else 'Close', command=dlg.destroy, bg=p['panel'], fg=p['text'], font=(fam, fs, 'bold'), padx=18, pady=5, cursor='hand2').pack(side='right')
    leg = tk.Frame(bf, bg=p['bg'])
    leg.pack(side='left')
    for ltxt, lcol in (('\u041c\u043e\u0457 (\u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else 'Mine (median)', '#38bdf8'), ('\u0427\u0443\u0436\u0456 D1 (\u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else 'Others D1 (median)', '#f59e0b')):
        tk.Label(leg, text='\u25a0', bg=p['bg'], fg=lcol, font=(fam, fs, 'bold')).pack(side='left', padx=(0, 3))
        tk.Label(leg, text=ltxt, bg=p['bg'], fg=p['muted'], font=(fam, max(8, fs - 1))).pack(side='left', padx=(0, 14))

    top_bar = tk.Frame(dlg, bg=p['bg'])
    top_bar.pack(fill='x', padx=14, pady=(8, 4))
    act_bar = tk.Frame(dlg, bg=p['bg'])
    act_bar.pack(fill='x', padx=14, pady=(0, 4))
    lbl_st = tk.Label(act_bar, text='', bg=p['bg'], fg=p['muted'], font=(fam, max(8, fs - 1)))
    lbl_st.pack(side='right')
    flt_bar = tk.Frame(dlg, bg=p['bg'])
    flt_bar.pack(fill='x', padx=14, pady=(0, 4))

    chart_f = tk.Frame(dlg, bg=p['panel'], bd=1, relief='solid', padx=10, pady=6)
    chart_f.pack(fill='x', padx=14, pady=(2, 6))
    lbl_desc = tk.Label(chart_f, text='', bg=p['panel'], fg=p['cyan'], font=(fam, max(8, fs - 1), 'bold'))
    lbl_desc.pack(anchor='w', pady=(0, 4))
    cv = tk.Canvas(chart_f, height=int(195 * k), bg=p['log_bg'], highlightthickness=1, highlightbackground='#1e293b')
    cv.pack(fill='x')

    tbl_f = tk.Frame(dlg, bg=p['panel'], bd=1, relief='solid', padx=10, pady=6)
    tbl_f.pack(fill='both', expand=True, padx=14, pady=(0, 4))
    st_tv = ttk.Style()
    try: st_tv.theme_use('clam')
    except Exception: pass
    st_tv.configure('HGB3.Treeview', background=p['log_bg'], foreground=p['text'], fieldbackground=p['log_bg'], rowheight=max(26, int((fs + 16) * k)), font=(fam, fs))
    st_tv.configure('HGB3.Treeview.Heading', background=p['panel'], foreground=p['cyan'], font=(fam, max(8, fs - 1), 'bold'))
    tv = ttk.Treeview(tbl_f, columns=('c1', 'my', 'd1', 'n'), show='headings', height=6, style='HGB3.Treeview')
    for cid, ht, wc, anc in (('c1', '\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440', 460, 'w'), ('my', '\u041c\u043e\u0457 (\u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else 'Mine (median)', 165, 'center'), ('d1', '\u0427\u0443\u0436\u0456 D1 (\u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else 'Others D1 (median)', 165, 'center'), ('n', 'n (\u043c\u043e\u0457 / D1)' if lang == 'uk' else 'n (mine / D1)', 95, 'center')):
        tv.heading(cid, text=ht)
        tv.column(cid, width=int(wc * k), minwidth=80, anchor=anc, stretch=(cid == 'c1'))
    tv.tag_configure('own', background='#132a3a', foreground='#38bdf8')
    tv.pack(fill='both', expand=True)

    def _short_x(raw):
        parts = [x.strip() for x in str(raw or '').split(chr(8226))]
        if len(parts) >= 2:
            p0 = parts[0].split(':')[0].split('(')[0].strip()
            if len(p0) > 24:
                p0 = p0[:23] + chr(8230)
            mid = ' '.join(parts[1:-1])
            net_t = 'WAN' if 'Internet' in mid else ('Wi-Fi' if 'Wi-Fi' in mid else ('Eth 1G' if '1 Gbps' in mid else ('Ethernet' if 'Ethernet' in mid else '')))
            p1 = parts[-1].replace('buf ', '').strip()[:12]
            os_raw = parts[1].split('(')[0].strip()
            os_s = os_raw.replace('Windows ', 'W').replace('Linux', 'Lin').replace('macOS', 'Mac').split()[0][:10] if os_raw else ''
            if net_t:
                top = f"{net_t} {p1} ({os_s})" if os_s else f"{net_t} \u2022 {p1}"
            else:
                top = os_raw[:16] or p1
            return f"{top}\n({p0})"
        t = str(raw or '')
        return (t[:24] + chr(8230)) if len(t) > 25 else t

    def _fmt_v(val, n):
        u = '\u041c\u0411/\u0441' if lang == 'uk' else 'MB/s'
        low = '\u043c\u0430\u043b\u043e \u0434\u0430\u043d\u0438\u0445' if lang == 'uk' else 'low data'
        if n <= 0 or float(val or 0) <= 0: return '\u2014'
        return f"{val} {u}" + (f" ({low})" if n < 3 else "")
    def _draw_vbars(rows, lkey):
        cv.delete('all')
        w, h = max(420, cv.winfo_width() or int(880 * k)), max(150, cv.winfo_height() or int(195 * k))
        if not rows:
            cv.create_text(w // 2, h // 2, text='\u041d\u0435\u043c\u0430\u0454 \u0434\u0430\u043d\u0438\u0445' if lang == 'uk' else 'No data', fill=p['muted'], font=(fam, fs))
            return
        who = who_var.get()
        series = (('my', '#38bdf8', '#7dd3fc'),) if who == 'MY' else ((('d1', '#f59e0b', '#fbbf24'),) if who == 'D1' else (('my', '#38bdf8', '#7dd3fc'), ('d1', '#f59e0b', '#fbbf24')))
        vals = [float(r.get(vk) or 0) for r in rows for vk, _, _ in series]
        mx = max(vals + [1.0])
        pad_l, pad_r, pad_t, pad_b = int(32 * k), int(20 * k), int(24 * k), int(38 * k)
        y1 = h - pad_b
        ch = max(50, y1 - pad_t)
        for gi in range(4):
            gy = int(y1 - ch * gi / 3.0)
            cv.create_line(pad_l, gy, w - pad_r, gy, fill='#1e293b', dash=(2, 3))
        vis = rows[:6]
        slot = (w - pad_l - pad_r) / max(1, len(vis))
        bw = max(14, min(int(38 * k), int(slot * (0.45 if len(series) == 1 else 0.27))))
        for idx_r, r in enumerate(vis):
            cx = int(pad_l + slot * idx_r + slot / 2)
            for idx_b, (vk, c1, c2) in enumerate(series):
                val = float(r.get(vk) or 0)
                bx = (cx - bw // 2) if len(series) == 1 else (cx - bw - 3 if idx_b == 0 else cx + 3)
                dy = max(4, int((val / mx) * ch)) if val > 0 else 2
                cv.create_rectangle(bx, y1 - dy, bx + bw, y1, fill=c1 if val > 0 else '#334155', outline='')
                if val > 0:
                    cv.create_text(bx + bw // 2, y1 - dy - int(9 * k), text=f"{val}", fill=c2, font=(fam, max(7, fs - 2), 'bold'))
            cv.create_text(cx, y1 + int(17 * k), text=_short_x(r.get(lkey)), justify='center', fill=p['text'], font=(fam, max(7, fs - 2)))
    def _draw_hw_cards(rows):
        cv.delete('all')
        w, h = max(420, cv.winfo_width() or int(880 * k)), max(150, cv.winfo_height() or int(195 * k))
        if not rows:
            cv.create_text(w // 2, h // 2, text='Немає даних' if lang == 'uk' else 'No data', fill=p['muted'], font=(fam, fs))
            return
        who = who_var.get()
        u = 'МБ/с' if lang == 'uk' else 'MB/s'
        vis = rows[:4]
        pad = int(10 * k)
        cw = (w - pad * (len(vis) + 1)) // max(1, len(vis))
        for idx_c, r in enumerate(vis):
            x0 = pad + idx_c * (cw + pad)
            x1 = x0 + cw
            cv.create_rectangle(x0, pad, x1, h - pad, fill='#0b1220', outline='#1e293b')
            pts = [x.strip() for x in str(r.get('metric') or '').split(chr(8226))]
            m_name = pts.pop()[:22] if pts else ''
            pc_short = pts.pop(0).split('(').pop(0).strip()[:20] if pts else ''
            cv.create_text((x0 + x1) // 2, pad + int(14 * k), text=m_name, fill='#f8fafc', font=(fam, max(8, fs - 1), 'bold'))
            cv.create_text((x0 + x1) // 2, pad + int(30 * k), text=pc_short, fill=p['muted'], font=(fam, max(7, fs - 2)))
            v_my, v_d1 = float(r.get('my') or 0), float(r.get('d1') or 0)
            mx = max(v_my, v_d1, 1.0)
            y_bot = h - pad - int(22 * k)
            ch = max(40, y_bot - (pad + int(52 * k)))
            bw = max(18, min(int(36 * k), cw // 4))
            cx = (x0 + x1) // 2
            bars = [('my', v_my, '#38bdf8', '#7dd3fc', 'Мої' if lang == 'uk' else 'Mine')] if who == 'MY' else ([('d1', v_d1, '#f59e0b', '#fbbf24', 'D1')] if who == 'D1' else [('my', v_my, '#38bdf8', '#7dd3fc', 'Мої' if lang == 'uk' else 'Mine'), ('d1', v_d1, '#f59e0b', '#fbbf24', 'D1')])
            for bi, (_, val, c1, c2, blbl) in enumerate(bars):
                bx = (cx - bw // 2) if len(bars) == 1 else (cx - bw - 4 if bi == 0 else cx + 4)
                dy = max(4, int((val / mx) * ch)) if val > 0 else 2
                cv.create_rectangle(bx, y_bot - dy, bx + bw, y_bot, fill=c1 if val > 0 else '#334155', outline='')
                if val > 0:
                    cv.create_text(bx + bw // 2, y_bot - dy - int(9 * k), text=f"{val}", fill=c2, font=(fam, max(7, fs - 2), 'bold'))
                cv.create_text(bx + bw // 2, y_bot + int(10 * k), text=blbl, fill=p['muted'], font=(fam, max(7, fs - 2)))

    def _render_sec():
        sk, who = sec_var.get(), who_var.get()
        meta = {
            'server': ('name', '1. \u0421\u0415\u0420\u0412\u0415\u0420: \u0448\u0432\u0438\u0434\u043a\u0456\u0441\u0442\u044c \u0437\u0431\u0456\u0440\u043a\u0438 \u043d\u0430 HGM \u043f\u043e \u041e\u0421 \u043a\u043b\u0456\u0454\u043d\u0442\u0430 (\u041c\u0411/\u0441, \u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else '1. SERVER: HGM build speed by client OS (MB/s, median)', '\u0421\u0435\u0440\u0432\u0435\u0440 / \u041e\u0421 \u043a\u043b\u0456\u0454\u043d\u0442\u0430' if lang == 'uk' else 'Server / Client OS'),
            'network': ('group', '2. \u041c\u0415\u0420\u0415\u0416\u0410: \u0447\u0438\u0441\u0442\u0435 \u0441\u043a\u0430\u0447\u0443\u0432\u0430\u043d\u043d\u044f, \u0442\u0430 \u0441\u0430\u043c\u0430 \u041e\u0421/\u0431\u0443\u0444\u0435\u0440 \u0456 \u00b120% \u0440\u043e\u0437\u043c\u0456\u0440 (\u041c\u0411/\u0441)' if lang == 'uk' else '2. NETWORK: pure download, same OS/buffer & \u00b120% size (MB/s)', '\u041f\u0430\u0440\u0430 \u0441\u0435\u0440\u0432\u0435\u0440 / \u041e\u0421 / \u043b\u0456\u043d\u043a' if lang == 'uk' else 'Server / OS / Link'),
            'hardware': ('metric', '3. \u0417\u0410\u041b\u0406\u0417\u041e: \u0435\u0442\u0430\u043b\u043e\u043d\u043d\u0438\u0439 \u0442\u0435\u0441\u0442 \u041f\u041a \u0442\u0430 \u0434\u0438\u0441\u043a\u0430 (\u041c\u0411/\u0441, \u043c\u0435\u0434\u0456\u0430\u043d\u0430)' if lang == 'uk' else '3. HARDWARE: PC & disk benchmark (MB/s, median)', '\u041c\u0435\u0442\u0440\u0438\u043a\u0430' if lang == 'uk' else 'Metric')
        }
        lkey, d_txt, h1 = meta[sk]
        lbl_desc.configure(text=d_txt)
        tv.heading('c1', text=h1)
        for rid in tv.get_children(): tv.delete(rid)
        all_r = state_data.get(sk, [])
        sf = srv_var.get()
        if sf and sf != 'ALL' and sk in ('server', 'network'):
            all_r = [r for r in all_r if str(r.get(lkey) or '').startswith(sf)]
        nf = net_var.get()
        if nf and nf != 'ALL' and sk == 'network':
            all_r = [r for r in all_r if nf in str(r.get('group') or '')]
        pf = pc_var.get()
        if pf and pf != 'ALL' and sk == 'hardware':
            all_r = [r for r in all_r if str(r.get('pc') or '') == pf]
        osf = os_var.get()
        if osf and osf != 'ALL':
            all_r = [r for r in all_r if osf.lower() in str(r.get('os') or r.get(lkey) or '').lower()]
        rows = [r for r in all_r if r.get('n_my', 0) > 0] if who == 'MY' else ([r for r in all_r if r.get('n_d1', 0) > 0] if who == 'D1' else all_r)
        for r in rows:
            tv.insert('', 'end', values=(r[lkey], _fmt_v(r['my'], r['n_my']), _fmt_v(r['d1'], r['n_d1']), f"{r['n_my']} / {r['n_d1']}"), tags=(('own',) if r.get('n_my', 0) > 0 else ()))
        _draw_hw_cards(rows) if sk == 'hardware' else _draw_vbars(rows, lkey)

    def _sync_filters():
        nf, sf, sk = net_var.get(), srv_var.get(), sec_var.get()
        if sk == 'network' and nf and nf != 'ALL':
            srvs = sorted({next(iter(str(r.get('group') or '').split('\u2022'))).strip() for r in state_data.get('network', []) if nf in str(r.get('group') or '') and r.get('group')})
        else:
            srvs = sorted({str(r.get('name') or '').split('\u2022')[0].strip() for r in state_data.get('server', []) if r.get('name')} | {str(r.get('group') or '').split('\u2022')[0].strip() for r in state_data.get('network', []) if r.get('group')})
        cb_srv.configure(values=[all_lbl] + srvs, width=max(26, min(44, max((len(x) for x in [all_lbl] + srvs), default=26) + 2)))
        if sf != 'ALL' and sf not in srvs:
            srv_var.set('ALL'); cb_srv.set(all_lbl); sf = 'ALL'
        if sk == 'network':
            avail_nets = [v_o for _, v_o in n_opts]
            cb_net.configure(values=avail_nets)
            if cb_net.get() not in avail_nets:
                net_var.set('ALL'); cb_net.set(next(v for _, v in n_opts))
        all_os = sorted({str(r.get('os') or '').strip() for sec_k in ('server', 'network', 'hardware') for r in state_data.get(sec_k, []) if r.get('os')})
        os_vals = [os_all_lbl] + all_os
        cb_os.configure(values=os_vals)
        if cb_os.get() not in os_vals:
            os_var.set('ALL'); cb_os.set(os_all_lbl)

    def _set_sec(sk):
        sec_var.set(sk)
        for key_b, b_w in tab_btns.items():
            b_w.configure(bg=p['cyan'] if key_b == sk else p['panel'], fg='#0f172a' if key_b == sk else p['text'])
        cb_srv.pack_forget(); cb_net.pack_forget(); cb_pc.pack_forget(); cb_os.pack_forget()
        if sk == 'server':
            _sync_filters(); cb_srv.pack(side='left', padx=(8, 4)); cb_os.pack(side='left', padx=(4, 4))
        elif sk == 'network':
            _sync_filters(); cb_srv.pack(side='left', padx=(8, 4)); cb_net.pack(side='left', padx=(4, 4)); cb_os.pack(side='left', padx=(4, 4))
        elif sk == 'hardware':
            _sync_filters(); cb_pc.pack(side='left', padx=(8, 4)); cb_os.pack(side='left', padx=(4, 4))
        _render_sec()

    def _set_who(wk):
        who_var.set(wk)
        for key_w, b_w in who_btns.items():
            b_w.configure(bg=p['green'] if key_w == wk else p['panel'], fg='#0f172a' if key_w == wk else p['text'])
        _render_sec()
    for sk, suk, sen in (('server', '\U0001f5a5 1. \u0421\u0435\u0440\u0432\u0435\u0440', '\U0001f5a5 1. Server'), ('network', '\U0001f310 2. \u041c\u0435\u0440\u0435\u0436\u0430', '\U0001f310 2. Network'), ('hardware', '\u26a1 3. \u0417\u0430\u043b\u0456\u0437\u043e', '\u26a1 3. Hardware')):
        b_t = tk.Button(top_bar, text=suk if lang == 'uk' else sen, command=lambda m=sk: _set_sec(m), bg=p['cyan'] if sk == 'server' else p['panel'], fg='#0f172a' if sk == 'server' else p['text'], font=(fam, fs, 'bold'), padx=10, pady=3, cursor='hand2')
        b_t.pack(side='left', padx=(0, 6))
        tab_btns[sk] = b_t

    cv.bind('<Configure>', lambda e: _render_sec())

    def _load(refresh=True):
        lbl_st.configure(text='\u041e\u043d\u043e\u0432\u043b\u0435\u043d\u043d\u044f...' if lang == 'uk' else 'Refreshing...', fg=p['cyan'])
        def _w_fn():
            try:
                from core.cloud import build_three_section_stats
                res, err = build_three_section_stats(engine, refresh=refresh), ''
            except Exception as ex:
                res, err = None, str(ex)
            def _u():
                if not dlg.winfo_exists(): return
                if err:
                    lbl_st.configure(text=err, fg=p['red'])
                    return
                state_data.update(res)
                pcs = sorted({str(r.get('pc') or '') for r in res.get('hardware', []) if r.get('pc')})
                cb_pc.configure(values=[pc_all_lbl] + pcs)
                _sync_filters()
                _render_sec()
                _d1_e = getattr(__import__('core.speed_bench', fromlist=['_LAST_D1_ERR']), '_LAST_D1_ERR', '')
                lbl_st.configure(text=f"D1: {_d1_e}" if _d1_e else ('\u041e\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u2714' if lang == 'uk' else 'Updated \u2714'), fg=p['red'] if _d1_e else p['green'])
            root.after(0, _u)
        threading.Thread(target=_w_fn, daemon=True).start()

    tk.Button(act_bar, text='\U0001f504 \u041e\u043d\u043e\u0432\u0438\u0442\u0438' if lang == 'uk' else '\U0001f504 Refresh', command=lambda: _load(True), bg=p['panel'], fg=p['cyan'], font=(fam, fs), padx=10, pady=2, cursor='hand2').pack(side='left', padx=(0, 8))
    tk.Button(act_bar, text='\u26a1 \u0422\u0435\u0441\u0442 \u041f\u041a/\u0414\u0438\u0441\u043a\u0430' if lang == 'uk' else '\u26a1 PC/Disk Test', command=lambda: __import__('core.speed_bench', fromlist=['open_compact_bench_popup']).open_compact_bench_popup(dlg, engine.state, p, fs, fam, lambda: engine.state.get(_p, ''), on_done=lambda: _load(True)), bg=p['panel'], fg=p['green'], font=(fam, fs, 'bold'), padx=10, pady=2, cursor='hand2').pack(side='left', padx=(0, 8))
    tk.Button(act_bar, text='\U0001f9ea \u0411\u0443\u0444\u0435\u0440 16 vs 256 \u041a\u0411' if lang == 'uk' else '\U0001f9ea Buffer 16 vs 256 KB', command=lambda: __import__('core.speed_bench', fromlist=['open_buffer_ab_popup']).open_buffer_ab_popup(dlg, engine.state, p, fs, fam), bg=p['panel'], fg=p['cyan'], font=(fam, fs), padx=10, pady=2, cursor='hand2').pack(side='left', padx=(0, 16))
    for wk, wuk, wen in (('ALL', '\u0423\u0441\u0456', 'All'), ('MY', '\u041c\u043e\u0457', 'Mine'), ('D1', '\u0427\u0443\u0436\u0456 D1', 'Others D1')):
        bw_btn = tk.Button(act_bar, text=wuk if lang == 'uk' else wen, command=lambda m=wk: _set_who(m), bg=p['green'] if wk == 'ALL' else p['panel'], fg='#0f172a' if wk == 'ALL' else p['text'], font=(fam, max(8, fs - 1), 'bold'), padx=9, pady=2, cursor='hand2')
        bw_btn.pack(side='left', padx=(0, 4))
        who_btns[wk] = bw_btn

    all_lbl = '\u0423\u0441\u0456 \u0441\u0435\u0440\u0432\u0435\u0440\u0438' if lang == 'uk' else 'All servers'
    cb_srv = ttk.Combobox(flt_bar, state='readonly', width=36, font=(fam, max(8, fs - 1)), values=[all_lbl])
    cb_srv.set(all_lbl)
    cb_srv.pack(side='left', padx=(8, 4))
    def _on_srv(e=None):
        v = cb_srv.get()
        srv_var.set('ALL' if (not v or v == all_lbl) else v)
        _sync_filters(); _render_sec()
    cb_srv.bind('<<ComboboxSelected>>', _on_srv)

    n_opts = [
        ('ALL', '\u0423\u0441\u0456 \u043a\u0430\u043d\u0430\u043b\u0438 (Wi-Fi / LAN / Gbps)' if lang == 'uk' else 'All channels (Wi-Fi / LAN / Gbps)'),
        ('Wi-Fi', 'LAN \u2022 Wi-Fi'),
        ('1 Gbps', 'LAN \u2022 \u0413\u0456\u0433\u0430\u0431\u0456\u0442 (1 Gbps)' if lang == 'uk' else 'LAN \u2022 Gigabit (1 Gbps)'),
        ('LAN \u2022 Ethernet', 'LAN \u2022 \u041f\u0440\u043e\u0432\u0456\u0434 (Ethernet)' if lang == 'uk' else 'LAN \u2022 Ethernet'),
        ('Internet', '\u0406\u043d\u0442\u0435\u0440\u043d\u0435\u0442 (WAN)' if lang == 'uk' else 'Internet (WAN)')
    ]
    cb_net = ttk.Combobox(flt_bar, state='readonly', width=28, font=(fam, max(8, fs - 1)), values=[v for _, v in n_opts])
    cb_net.set(next(v for _, v in n_opts))
    def _on_net(e=None):
        sel = cb_net.get()
        net_var.set(next((k_o for k_o, v_o in n_opts if v_o == sel), 'ALL'))
        _sync_filters(); _render_sec()
    cb_net.bind('<<ComboboxSelected>>', _on_net)

    pc_all_lbl = '\u0423\u0441\u0456 \u041f\u041a' if lang == 'uk' else 'All PCs'
    cb_pc = ttk.Combobox(flt_bar, state='readonly', width=28, font=(fam, max(8, fs - 1)), values=[pc_all_lbl])
    cb_pc.set(pc_all_lbl)
    def _on_pc(e=None):
        v = cb_pc.get()
        pc_var.set('ALL' if (not v or v == pc_all_lbl) else v)
        _render_sec()
    cb_pc.bind('<<ComboboxSelected>>', _on_pc)

    os_all_lbl = '\u0423\u0441\u0456 \u041e\u0421 \u043a\u043b\u0456\u0454\u043d\u0442\u0430' if lang == 'uk' else 'All client OS'
    cb_os = ttk.Combobox(flt_bar, state='readonly', width=26, font=(fam, max(8, fs - 1)), values=[os_all_lbl])
    cb_os.set(os_all_lbl)
    def _on_os(e=None):
        v = cb_os.get()
        os_var.set('ALL' if (not v or v == os_all_lbl) else v)
        _render_sec()
    cb_os.bind('<<ComboboxSelected>>', _on_os)
    cb_os.pack(side='left', padx=(4, 4))

    _load(False)
    try:
        dlg.update_idletasks()
        dlg.lift()
        root.after(80, lambda: dlg.winfo_exists() and (dlg.update_idletasks(), dlg.lift(), _render_sec()))
    except Exception:
        pass
    dlg.after(120, lambda: dlg.winfo_exists() and _load(True))