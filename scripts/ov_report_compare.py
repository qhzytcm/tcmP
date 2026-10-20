import openpyxl, os, hashlib

files = [
    ("dev 192.168.0.105",       r"C:\Users\DELL\Desktop\OV-test.xlsx"),
    ("浪潮 192.168.0.102",       r"C:\Users\DELL\Desktop\OV-test-langchao.xlsx"),
    ("华为云 114.115.211.254",   r"C:\Users\DELL\Desktop\OV-test-huaweicloud.xlsx"),
    ("华为硬 192.168.1.12",      r"C:\Users\DELL\Desktop\OV-test-huaweihw.xlsx"),
    ("工作站 192.168.0.110",     r"C:\Users\DELL\Desktop\OV-test-desktop.xlsx"),
]

def load(p):
    wb = openpyxl.load_workbook(p)
    d = {}
    for row in wb["摘要"].iter_rows(min_row=2, values_only=True):
        if row and row[0]:
            d[str(row[0]).strip()] = row[1]
    env = {}
    for row in wb["环境信息"].iter_rows(values_only=True):
        if row and row[0]:
            env[str(row[0]).strip()] = row[1]
    cases = []
    for row in wb["测试用例"].iter_rows(min_row=2, values_only=True):
        if row and row[0]:
            cases.append((str(row[0]).strip(), str(row[1]).strip(), str(row[5]).strip()))
    return d, env, cases

data = []
for label, p in files:
    if not os.path.exists(p):
        print("MISSING:", p); continue
    d, env, cases = load(p)
    data.append((label, p, d, env, cases))

print("=" * 100)
print("表1  %d 台机器总览" % len(data))
print("=" * 100)
hdr = "%-24s %-6s %-6s %-6s %-6s %-9s %-22s" % ("主机", "用例", "PASS", "FAIL", "INFO", "通过率", "运行主机名")
print(hdr); print("-" * 100)
for label, p, d, env, cases in data:
    print("%-24s %-6s %-6s %-6s %-6s %-9s %-22s" % (
        label, d.get("用例总数"), d.get("通过(PASS)"), d.get("失败(FAIL)"),
        d.get("提示(INFO)"), d.get("通过率"), env.get("运行主机")))

print()
print("=" * 100)
print("表2  用例清单一致性（以 dev 为基准）")
print("=" * 100)
base = [c[1] for c in data[0][4]]
print("dev 用例数:", len(base))
for label, p, d, env, cases in data[1:]:
    names = [c[1] for c in cases]
    same = (names == base)
    print("%-24s 用例数=%-4d 与dev完全一致=%s" % (label, len(names), "YES" if same else "NO"))
    if not same:
        only_here = [n for n in names if n not in base]
        only_base = [n for n in base if n not in names]
        if only_here: print("      仅本机有:", only_here[:5])
        if only_base: print("      本机缺:", only_base[:5])

print()
print("=" * 100)
print("表3  分组通过情况（PASS/总）")
print("=" * 100)
groups = []
for _, _, _, _, cases in data:
    g = {}
    for cat, name, st in cases:
        g.setdefault(cat, [0, 0])
        g[cat][1] += 1
        if st == "PASS":
            g[cat][0] += 1
    groups.append(g)
allcats = []
for g in groups:
    for c in g:
        if c not in allcats: allcats.append(c)
print("%-20s" % "分组" + "".join("%-16s" % ("[" + str(i+1) + "]") for i in range(len(data))))
for c in allcats:
    row = "%-20s" % c
    for g in groups:
        if c in g: row += "%-16s" % ("%d/%d" % (g[c][0], g[c][1]))
        else: row += "%-16s" % "-"
    print(row)
print()
for i, (label, *_rest) in enumerate(data, 1):
    print("  [%d] %s" % (i, label))

print()
print("=" * 100)
print("表4  每台独有的 INFO/FAIL 明细")
print("=" * 100)
for label, p, d, env, cases in data:
    nf = [(c[1], c[2]) for c in cases if c[2] in ("INFO", "FAIL")]
    print("%s: %d 条" % (label, len(nf)))
    for name, st in nf:
        print("    %-6s %s" % (st, name))
