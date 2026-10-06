#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jev_key_sweep.py — 密钥泄漏面扫描。

扫描一个目录里"看起来像密钥/令牌的长字符串"，只报告位置与掩码，
**从不打印完整值**。用途：
- 提交前自查（别把 key 提交进仓库）；
- 定期巡检工作目录、日志目录。

用法:
    python scripts/jev_key_sweep.py            # 扫当前目录
    python scripts/jev_key_sweep.py <目录>...  # 扫指定目录
    python scripts/jev_key_sweep.py --json     # 机器可读输出

退出码: 0=干净; 1=发现疑似泄漏; 2=参数/运行错误。

设计取舍：宁可多报（误报可人工忽略），不可漏报；但**永不输出完整值**。
"""
import argparse
import json
import os
import re
import sys

TEXT_EXT = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".env", ".sh", ".bat", ".ps1", ".js", ".ts", ".html", ".css", ".xml",
    ".csv", ".log",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode"}
MAX_SIZE = 5 * 1024 * 1024  # 跳过 >5MB 的文件

# 常见前缀模式（sk-/pk-/api-key/token/secret 等）+ 长随机串兜底
PREFIX_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?:sk|pk|api|key|token|secret|bearer)[-_]?[A-Za-z0-9_\-]{16,}"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
LONG_RE = re.compile(r"(?<![A-Za-z0-9_\-])[A-Za-z0-9_\-]{32,}(?![A-Za-z0-9_\-])")


def mask(token: str) -> str:
    digits = sum(1 for c in token if c.isdigit())
    return f"{token[:4]}…（共 {len(token)} 字符，{digits} 位数字）"


def entropy_like(token: str) -> bool:
    """粗判'像随机串'：字符种类 >= 3（大小写/数字/符号）。"""
    kinds = sum([
        any(c.islower() for c in token),
        any(c.isupper() for c in token),
        any(c.isdigit() for c in token),
        any(not c.isalnum() for c in token),
    ])
    return kinds >= 3


def scan_file(path: str):
    hits = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                for m in PREFIX_RE.finditer(line):
                    tok = m.group(0)
                    if len(tok) >= 24:
                        hits.append((lineno, mask(tok)))
                for m in LONG_RE.finditer(line):
                    tok = m.group(0)
                    if entropy_like(tok):
                        hits.append((lineno, mask(tok)))
    except OSError:
        pass
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="密钥泄漏面扫描（只报告掩码，不泄露值）")
    ap.add_argument("roots", nargs="*", default=["."], help="要扫描的目录（默认当前目录）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    findings = []
    for root in args.roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(fp) > MAX_SIZE:
                        continue
                except OSError:
                    continue
                for lineno, m in scan_file(fp):
                    findings.append({"file": fp, "line": lineno, "masked": m})

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=1))
    elif not findings:
        print("[√] 未发现疑似密钥。")
    else:
        print(f"[!] 发现 {len(findings)} 处疑似密钥片段：")
        for x in findings:
            print(f"  {x['file']}:{x['line']}  {x['masked']}")
        print("提示：确认后请移除并轮换；误报可忽略。")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
