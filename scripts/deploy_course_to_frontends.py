# -*- coding: utf-8 -*-
"""deploy_course_to_frontends.py — 把教材视频课程上传到主/从前端浏览器站点

主前端 = 华为云 114.115.211.254  → /var/www/tcmai/books/<slug>/  （nginx root /var/www/tcmai，try_files 直出）
从前端 = 华为硬服务器 192.168.0.106 → IIS:80  （实测无 SSH/SMB 凭据 → 报告阻塞，不静默失败）

用法：
  python scripts/deploy_course_to_frontends.py --slug zhongji-jichu \
      --local "docs/教材视频/zhongji-jichu"
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path

CLOUD = dict(host="114.115.211.254", user="root", key=os.path.expanduser("~/.ssh/id_rsa"))
CLOUD_ROOT = "/var/www/tcmai/books"
SECONDARY_HOST = "192.168.0.106"


def upload_cloud(slug: str, local: Path) -> bool:
    import paramiko
    files = [p for p in sorted(local.iterdir())
             if p.is_file() and (p.name.endswith("-视频课程.html") or p.name.endswith(".mp4")
                                 or p.name == "index.html" or p.name.endswith("-course.json"))]
    if not files:
        print("[x] 无可上传文件"); return False
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CLOUD["host"], username=CLOUD["user"], key_filename=CLOUD["key"],
                look_for_keys=True, timeout=20)
    rdir = f"{CLOUD_ROOT}/{slug}"
    ssh.exec_command(f"mkdir -p {rdir} && chown -R www:www {CLOUD_ROOT}")[1].read()
    sftp = ssh.open_sftp()
    ok = 0
    for p in files:
        rp = f"{rdir}/{p.name}"
        sftp.put(str(p), rp)
        sz = sftp.stat(rp).st_size
        flag = "OK" if sz == p.stat().st_size else "MISMATCH"
        print(f"  [{flag}] {p.name}  {sz} bytes")
        ok += (flag == "OK")
    sftp.close()
    ssh.exec_command(f"chown -R www:www {rdir}")[1].read()
    ssh.close()
    print(f"[主前端·华为云] 上传 {ok}/{len(files)} → {rdir}")
    return ok == len(files)


def try_secondary(slug: str, local: Path) -> str:
    """从前端（华为硬服务器）—— 无 SSH(22 关)/SMB(Access denied)。探测后如实报告。"""
    import socket
    reach = {}
    for port in (22, 80, 443, 445):
        s = socket.socket(); s.settimeout(4)
        reach[port] = s.connect_ex((SECONDARY_HOST, port)) == 0
        s.close()
    if not reach.get(22):
        return (f"[从前端·华为硬服务器 {SECONDARY_HOST}] ⚠️ 阻塞：22(SSH) 未开放、"
                f"445(SMB) 需凭据、仅 80(IIS) 可达 → 无法自动上传。"
                f"需项目方提供 SSH/SMB 凭据或 IIS 部署路径后重跑。")
    return "[从前端] 22 已开放，可尝试上传（本函数未实现）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--skip-secondary", action="store_true")
    args = ap.parse_args()
    local = Path(args.local)
    if not local.is_dir():
        print(f"[x] 本地目录不存在: {local}"); sys.exit(1)
    cloud_ok = upload_cloud(args.slug, local)
    if not args.skip_secondary:
        print(try_secondary(args.slug, local))
    print("DEPLOY_RESULT cloud=" + ("OK" if cloud_ok else "FAIL"))


if __name__ == "__main__":
    main()
