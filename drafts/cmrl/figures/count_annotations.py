# -*- coding: utf-8 -*-
"""运行时统计 gen_ch0N_figures_feynman.py 每幅图的标注数与最小字号（monkey-patch Axes.text/annotate）"""
import sys, os, io, contextlib, importlib.util

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, BASE)

def run_and_count(ch):
    path = os.path.join(BASE, 'figures', f'gen_{ch}_figures_feynman.py')
    spec = importlib.util.spec_from_file_location(f'gen_{ch}_cnt', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f'gen_{ch}_cnt'] = mod
    spec.loader.exec_module(mod)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    stats = {}
    orig_text = plt.Axes.text
    orig_annotate = plt.Axes.annotate
    cur_func = [None]

    def count(fn, name):
        def wrapper(self, *args, **kwargs):
            key = cur_func[0]
            if key is None:
                return fn(self, *args, **kwargs)
            if name == 'annotate' and args and isinstance(args[0], str) and args[0].strip() == '':
                return fn(self, *args, **kwargs)
            st = stats.setdefault(key, {'n': 0, 'min_fs': 99})
            st['n'] += 1
            fs = kwargs.get('fontsize')
            if fs is not None:
                if isinstance(fs, str):
                    fs = {'FS_NODE': 10, 'FS_KEY': 11, 'FS_MAIN': 12}.get(fs, 99)
                if st['min_fs'] > fs:
                    st['min_fs'] = fs
            return fn(self, *args, **kwargs)
        return wrapper

    plt.Axes.text = count(orig_text, 'text')
    plt.Axes.annotate = count(orig_annotate, 'annotate')

    fig_funcs = sorted(n for n in dir(mod) if n.startswith('fig') and callable(getattr(mod, n)))
    for fname in fig_funcs:
        cur_func[0] = fname
        fn = getattr(mod, fname)
        with contextlib.redirect_stdout(io.StringIO()):
            fn()
        cur_func[0] = None
    plt.Axes.text = orig_text
    plt.Axes.annotate = orig_annotate
    return stats

if __name__ == '__main__':
    all_ok = True
    for ch in ['ch01', 'ch02', 'ch03']:
        stats = run_and_count(ch)
        print(f"===== {ch}（运行时统计：标注数 / 最小字号）=====")
        for name in sorted(stats):
            st = stats[name]
            ok_n = st['n'] <= 10
            ok_fs = st['min_fs'] >= 9
            if not (ok_n and ok_fs):
                all_ok = False
            print(f"  {name}: 标注数={st['n']} ({'OK' if ok_n else '超限!'}), 最小字号={st['min_fs']}pt ({'OK' if ok_fs else '过小!'})")
    print('ALL PASS' if all_ok else 'HAS FAILURES')
