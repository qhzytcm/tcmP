# -*- coding: utf-8 -*-
"""deploy_course_to_frontends.py — 把教材视频课程上传到主/从前端浏览器站点

主前端 = 华为云 114.115.211.254  → /var/www/tcmai/books/<slug>/  （nginx root /var/www/tcmai，try_files 直出）
从前端 = 华为硬服务器 192.168.0.106 （Windows + IIS）

从前端部署（SSH，22）——需在 0.106 上开启 sshd 并提供站点根路径：
  python scripts/deploy_course_to_frontends.py --slug zhongji-jichu \
      --local "docs/教材视频/zhongji-jichu" \
      --secondary-user Administrator --secondary-pass '******' \
      --secondary-root 'C:\\inetpub\\wwwroot\\books'
  凭据也可走环境变量 TCM_SECONDARY_USER / TCM_SECONDARY_PASS / TCM_SECONDARY_ROOT。
  未提供凭据或路径时 → 只探测并如实报告阻塞（不静默失败）。

用法（仅主前端）：
  python scripts/deploy_course_to_frontends.py --slug <slug> --local <dir> --skip-secondary
"""
from __future__ import annotations
import argparse
import os
import socket
import sys
from pathlib import Path

CLOUD = dict(host="114.115.211.254", user="root", key=os.path.expanduser("~/.ssh/id_rsa"))
CLOUD_ROOT = "/var/www/tcmai/books"
SECONDARY_HOST = "192.168.0.106"

EXCLUDE_DIRS = {"__pycache__"}


def _course_files(local: Path):
    return [p for p in sorted(local.rglob("*"))
            if p.is_file() and p.suffix.lower() in (".html", ".mp4", ".json")
            and not any(part in EXCLUDE_DIRS for part in p.parts)
            and not any(part.startswith("ch") and part[2:].isdigit() for part in p.parts)]


# ── 主前端：华为云 ──────────────────────────────────────────────
def upload_cloud(slug: str, local: Path) -> bool:
    import paramiko
    files = _course_files(local)
    if not files:
        print("[x] 无可上传文件")
        return False
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


# ── 从前端：华为硬服务器 (Windows/IIS) ──────────────────────────
def _ssh_reachable(host: str, port: int = 22, t: int = 4) -> bool:
    s = socket.socket()
    s.settimeout(t)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def _secondary_blocked_msg() -> str:
    return (f"[从前端·华为硬服务器 {SECONDARY_HOST}] ⚠️ 不可达：22(SSH) 拒绝连接"
            f"（已从本机与 192.168.0.102 双向验证；ping OK、IIS:80 OK）。"
            f"请在 0.106 上确认 OpenSSH Server 已启动并放行 22：\n"
            f"    Get-Service sshd      # 应 Running；否则 Start-Service sshd; Set-Service sshd -StartupType Automatic\n"
            f"    Get-NetTCPConnection -LocalPort 22 -State Listen   # 应有监听\n"
            f"    New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22\n"
            f"  或改为提供 445(SMB) 凭据 / IIS 站点实际绝对路径。")


def deploy_secondary(slug: str, local: Path, user: str, password: str, root: str,
                     key: str = "") -> bool | None:
    """返回 True=成功 / False=失败 / None=阻塞（不可达或缺凭据）。支持密钥或口令认证。"""
    if not _ssh_reachable(SECONDARY_HOST):
        print(_secondary_blocked_msg())
        return None
    user = user or os.environ.get("TCM_SECONDARY_USER", "Administrator")
    password = password or os.environ.get("TCM_SECONDARY_PASS", "")
    root = root or os.environ.get("TCM_SECONDARY_ROOT", "")
    key = key or os.environ.get("TCM_SECONDARY_KEY", "")
    if (not password and not key) or not root:
        print(f"[从前端 {SECONDARY_HOST}] SSH 可达，但缺 认证方式(password 或 key) / 站点根路径 → "
              f"请传 --secondary-pass 或 --secondary-key 与 --secondary-root"
              f"（或 env TCM_SECONDARY_PASS/KEY/ROOT）")
        return None
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SECONDARY_HOST, username=user, password=(password or None),
                key_filename=(key or None), look_for_keys=False, timeout=20)
    rdir = f"{root.rstrip(chr(92))}\\{slug}"
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir(rdir)
    except OSError:
        pass
    files = _course_files(local)
    ok = 0
    for p in files:
        rp = f"{rdir}\\{p.name}"
        sftp.put(str(p), rp)
        sz = sftp.stat(rp).st_size
        flag = "OK" if sz == p.stat().st_size else "MISMATCH"
        print(f"  [{flag}] {p.name}  {sz} bytes")
        ok += (flag == "OK")
    sftp.close()
    ssh.close()
    print(f"[从前端·华为硬服务器] 上传 {ok}/{len(files)} → {rdir}")
    return ok == len(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--skip-secondary", action="store_true")
    ap.add_argument("--secondary-user", default="")
    ap.add_argument("--secondary-pass", default="")
    ap.add_argument("--secondary-key", default="")
    ap.add_argument("--secondary-root", default="")
    args = ap.parse_args()
    local = Path(args.local)
    if not local.is_dir():
        print(f"[x] 本地目录不存在: {local}")
        sys.exit(1)
    cloud_ok = upload_cloud(args.slug, local)
    sec = None
    if not args.skip_secondary:
        sec = deploy_secondary(args.slug, local, args.secondary_user,
                               args.secondary_pass, args.secondary_root, args.secondary_key)
    print("DEPLOY_RESULT cloud=" + ("OK" if cloud_ok else "FAIL")
          + " secondary=" + ("OK" if sec else ("BLOCKED" if sec is None else "FAIL")))


if __name__ == "__main__":
    main()
