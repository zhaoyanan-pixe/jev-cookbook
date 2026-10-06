#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jev_smoke.py — 验证 Jev 判定器的连通与返回格式。

用法：
    export TYPESAFE_API_KEY=...     # 或 OPENROUTER_API_KEY
    python scripts/jev_smoke.py

特性：
- 纯标准库（无需安装依赖）；
- 只从环境变量读 key，**从不打印 key**；
- 失败时给出人话提示，安全退出（fail-open 精神）。

三种问法（本脚本各演示一个）：
- noul   → 是/否，返回 0-1 概率
- choice → 从给定选项里选一个（criteria 是「选项 → 说明」的字典）
- score  → 按有序档位打分（criteria 是「从低到高」的档位数组）
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

# 让 Windows 控制台也能稳定输出中文
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def build_questions() -> dict:
    """三个题型各一例。问题本身无所谓，目的是验证格式通。"""
    return {
        "smoke_bool": {
            "type": "noul",
            "instructions": "请判断『这次冒烟测试请求已被正确接收』这件事成立的概率。",
        },
        "smoke_choice": {
            "type": "choice",
            "instructions": "这个判定请求本身的格式，属于以下哪种情况？",
            "criteria": {
                "格式正常": "三题齐备、字段完整，可以正常作答",
                "格式有问题": "存在缺字段或类型不符",
                "无法判断": "信息不足，无法判断",
            },
        },
        "smoke_score": {
            "type": "score",
            "instructions": "这次冒烟请求的完整程度如何？",
            "criteria": ["很不完整", "一般", "比较完整"],
        },
    }


def main() -> int:
    ts_key = os.environ.get("TYPESAFE_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")
    if not ts_key and not or_key:
        print("[x] 没找到环境变量 TYPESAFE_API_KEY 或 OPENROUTER_API_KEY。")
        print("    先设置一个（不要把 key 写进任何文件/脚本！）：")
        print("    bash:  export TYPESAFE_API_KEY=...")
        print("    PowerShell:  $env:TYPESAFE_API_KEY='...'")
        return 2

    if ts_key:
        backend = "TypeSafe"
        url = "https://api.typesafe.ai/v1/systemone"
        key = ts_key
        payload = {
            "state": "你是一个运行在用户电脑上的 AI 助手，正在做一次连通性冒烟测试。",
            "model": "jev-latest",
            "questions": build_questions(),
        }
    else:
        backend = "OpenRouter"
        url = "https://openrouter.ai/api/alpha/decisions"
        key = or_key
        payload = {
            "model": "~typesafe/jev-latest",
            "state": "你是一个运行在用户电脑上的 AI 助手，正在做一次连通性冒烟测试。",
            "questions": build_questions(),
        }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
    )

    print(f"→ 后端: {backend} | 端点: {url}")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        print(f"[x] HTTP {e.code}：{e.reason}")
        if detail:
            print(f"    响应体: {detail}")
        print("    排查提示：见 docs/05-踩坑集.md「钥匙与连通」一节。")
        return 1
    except Exception as e:
        print(f"[x] 请求失败（{type(e).__name__}）: {e}")
        print("    排查提示：检查网络/代理；见 docs/05-踩坑集.md「钥匙与连通」。")
        return 1

    latency_ms = round((time.time() - started) * 1000)
    answers = body.get("answers", {})
    if not isinstance(answers, dict) or not answers:
        print("[x] 响应里没有 answers 字段——格式和预期不符。")
        print("    原始响应（截断）:", json.dumps(body, ensure_ascii=False)[:400])
        return 1

    print(f"[√] 连通正常（{latency_ms} ms）")
    print(f"    answers 数量: {len(answers)}")
    for qid, ans in answers.items():
        print(f"    - {qid}: {json.dumps(ans, ensure_ascii=False)[:240]}")
    usage = body.get("usage")
    if usage:
        print(f"    usage: {json.dumps(usage, ensure_ascii=False)[:200]}")
    print()
    print("下一步：打开 docs/02-接入指南.md，把第一个判定点接到你的助手上（建议先跑影子模式）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
