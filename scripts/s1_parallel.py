# -*- coding: utf-8 -*-
"""
S1 并行分片启动器：把剩余页范围分给 N 个 s1_ocr_bingyuan.py 子进程并行跑。
脚本可续跑（跳过已存在页），故安全。
用法：python scripts/s1_parallel.py            # 默认覆盖 0-1178 分 4 片
      python scripts/s1_parallel.py 564 1178 4 # 起始 结束 片数
"""
import os, sys, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = os.path.join(ROOT, 'scripts', 's1_ocr_bingyuan.py')
LOGD = os.path.join(ROOT, 'logs')
os.makedirs(LOGD, exist_ok=True)


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 1178
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    total = hi - lo + 1
    per = total // n
    ranges = []
    for i in range(n):
        a = lo + i * per
        b = (lo + (i + 1) * per - 1) if i < n - 1 else hi
        ranges.append((a, b))
    print('分片:', ranges, flush=True)

    procs = []
    env = {**os.environ, 'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
           'OMP_WAIT_POLICY': 'PASSIVE'}
    for idx, (a, b) in enumerate(ranges):
        log = open(os.path.join(LOGD, f'ocr_w{idx}_{a}_{b}.log'), 'w', encoding='utf-8')
        p = subprocess.Popen([sys.executable, '-X', 'utf8', OCR, '--pages', f'{a}-{b}'],
                             stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, env=env)
        procs.append((idx, a, b, p, log))
        print(f'启动 worker{idx} 页 {a}-{b} pid={p.pid} threads=2', flush=True)

    t0 = time.time()
    while True:
        alive = [x for x in procs if x[3].poll() is None]
        od = os.path.join(ROOT, 'data', 'bingyuan_ocr')
        done = len([f for f in os.listdir(od) if f.startswith('page_')]) if os.path.isdir(od) else 0
        print(f'[{time.time()-t0:.0f}s] 存活 {len(alive)}/{len(procs)} | OCR已完成页 {done}', flush=True)
        if not alive:
            break
        time.sleep(60)
    for idx, a, b, p, log in procs:
        log.close()
        print(f'worker{idx} ({a}-{b}) exit={p.returncode}', flush=True)
    print('ALL WORKERS DONE', flush=True)


if __name__ == '__main__':
    main()
