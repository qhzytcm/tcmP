# -*- coding: utf-8 -*-
"""
ICD-11 查询工具 — tcmP 病证图谱 ICD-11 编码桥接
=================================================
数据源双通道：
  1) 内网 ICD-11 API（192.168.0.111:8080，WHO whoicd/icd-api 容器，release 2026-01）
     -> 中文搜索：病证名 -> Foundation 实体 ID + 中文标题/定义
  2) 本地 icd11_mms.db（31,838 实体，release 2026-01 与内网同版本）
     -> 编码出口：Foundation ID -> MMS 标准编码（如 BA00、SF57）

桥接：中文病证名 -> (API) ID -> (db) 标准编码，用于病历/医保对接。

用法：
  python icd11_client.py 高血压            # 中文搜索+编码（需内网 API）
  python icd11_client.py --code BA00       # 编码反查
  python icd11_client.py --en hypertension # 英文搜索（纯 db，无内网依赖）
"""
from __future__ import annotations
import argparse, json, os, re, sqlite3, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Optional

# ── 配置 ──
ICD_API_BASE = os.environ.get("ICD_API_BASE", "http://192.168.0.111:8080")
ICD_API_HEADERS = {"Accept": "application/json", "Accept-Language": "zh", "API-Version": "v2"}
DB_PATH = Path(__file__).parent.parent / "data" / "icd11_mms.db"

# 避免 Anaconda/部分环境 sqlite3 段错误的兼容提示
try:
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.close()
except Exception:
    pass


class ICD11Client:
    def __init__(self, api_base: str = ICD_API_BASE, db_path=None):
        self.api_base = api_base
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn = None

    # ── db 通道 ──
    @property
    def conn(self):
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"icd11_mms.db 不存在: {self.db_path}")
            self._conn = sqlite3.connect(str(self.db_path))
        return self._conn

    def code_by_id(self, foundation_id) -> Optional[dict]:
        """Foundation ID -> MMS 标准编码"""
        r = self.conn.execute(
            "SELECT id, code, title, class_kind, browser_url FROM entities WHERE id=?",
            (str(foundation_id),)).fetchone()
        if not r:
            return None
        return {"foundation_id": r[0], "code": r[1], "title_en": r[2],
                "class_kind": r[3], "browser_url": r[4]}

    def search_en(self, query: str, limit: int = 10) -> list:
        """英文搜索（纯 db）"""
        rows = self.conn.execute(
            "SELECT id, code, title, fully_specified_name FROM entities "
            "WHERE title LIKE ? OR fully_specified_name LIKE ? OR code LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query.upper()}%", limit)).fetchall()
        return [{"foundation_id": r[0], "code": r[1], "title_en": r[2],
                 "fully_specified_name": r[3]} for r in rows]

    def code_lookup(self, code: str) -> Optional[dict]:
        """编码反查"""
        r = self.conn.execute(
            "SELECT id, code, title FROM entities WHERE code=?", (code.upper(),)).fetchone()
        return {"foundation_id": r[0], "code": r[1], "title_en": r[2]} if r else None

    # ── API 通道（中文）──
    def search_cn(self, query: str, limit: int = 5) -> list:
        """内网 API 中文搜索 -> [{foundation_id, title_cn, chapter}]"""
        url = f"{self.api_base}/icd/entity/search?q={urllib.parse.quote(query)}" \
              f"&releaseId=2026-01&linearizationName=mms&limit={limit}"
        req = urllib.request.Request(url, headers=ICD_API_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                d = json.loads(resp.read())
        except Exception as e:
            return [{"error": f"API不可达({self.api_base}): {e}"}]
        out = []
        for de in d.get("destinationEntities", []):
            title = re.sub(r"</?em[^>]*>", "", de.get("title", ""))
            out.append({"foundation_id": de.get("id", "").rsplit("/", 1)[-1],
                        "title_cn": title, "chapter": de.get("chapter"),
                        "stem_id": de.get("stemId", "").rsplit("/", 1)[-1]})
        return out

    def lookup(self, query: str, limit: int = 5) -> list:
        """桥接：中文病证名 -> 标准编码（API 不可达时降级英文搜索）
        长短语自适应：全名无结果时滑动窗口取子串再搜（WHO 中文索引对长词支持差）"""
        results = self._lookup_once(query, limit)
        if results and "error" not in results[0]:
            return results
        # 滑动窗口降级
        best = None
        q = query
        for win in range(min(6, len(q)), 1, -1):
            for i in range(0, len(q) - win + 1):
                sub = q[i:i + win]
                r = self._lookup_once(sub, limit)
                if r and "error" not in r[0]:
                    best = r
                    return best
        return results

    def _lookup_once(self, query: str, limit: int = 5) -> list:
        """单次桥接查询"""
        results = []
        cn = self.search_cn(query, limit)
        cn_ok = [i for i in cn if "error" not in i]
        if not cn_ok:  # API 不可达 → 降级纯 db 英文搜索
            return [{"error": f"ICD-11 API 不可达，降级英文搜索", "fallback": self.search_en(query, limit)}]
        for item in cn_ok:
            code = self.code_by_id(item["foundation_id"])
            results.append({**item, **(code or {"code": None, "title_en": None})})
        return results


def main():
    ap = argparse.ArgumentParser(description="ICD-11 查询工具（tcmP）")
    ap.add_argument("query", nargs="?", help="查询词（默认走中文搜索+编码桥接）")
    ap.add_argument("--code", help="编码反查，如 BA00")
    ap.add_argument("--en", help="英文搜索（纯 db，无内网依赖）")
    ap.add_argument("--db", default=None, help="icd11_mms.db 路径")
    ap.add_argument("--api", default=ICD_API_BASE, help="内网 ICD API 地址")
    args = ap.parse_args()

    c = ICD11Client(api_base=args.api, db_path=args.db)

    if args.code:
        r = c.code_lookup(args.code)
        print(json.dumps(r, ensure_ascii=False, indent=2) if r else f"编码 {args.code} 未找到")
    elif args.en:
        for r in c.search_en(args.en):
            print(f"  {r['code'] or '--':8s} {r['foundation_id']:12s} {r['title_en'][:60]}")
    elif args.query:
        print(f"═══ 「{args.query}」 ICD-11 查询 ═══")
        for r in c.lookup(args.query):
            if "error" in r:
                print(f"  ⚠️ {r['error']}")
                continue
            print(f"  {r.get('code') or '--':8s} {r['foundation_id']:12s} "
                  f"{(r.get('title_cn') or '')[:30]} | {(r.get('title_en') or '')[:40]}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
