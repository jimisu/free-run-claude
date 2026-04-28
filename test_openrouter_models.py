#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch the list of models from OpenRouter, pick the best free model
based on performance (speed) and quality (logic), and run a tiny
chat‑completion test to verify that the model is usable.

Requirements:
    pip install httpx rich
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional, Tuple

import httpx
from rich import print
from rich.table import Table
from rich.console import Console

# ------------------------------------------------------------
# 設定 -------------------------------------------------------
# ------------------------------------------------------------
# 若想直接在程式碼內寫入 API 金鑰，請將下列變數改成你的金鑰
# 注意：將金鑰硬編碼在程式碼中可能會有安全風險，建議還是使用環境變數方式管理
API_KEY = os.getenv("OPENROUTER_API_KEY") or "sk-YOUR_KEY_HERE"
if not API_KEY:
    print("[bold red]❌ 請提供有效的 OPENROUTER_API_KEY！[/bold red]")
    sys.exit(1)

BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ------------------------------------------------------------
# 工具函式 ---------------------------------------------------
# ------------------------------------------------------------
def fetch_models() -> List[Dict[str, Any]]:
    """呼叫 OpenRouter 的 models endpoint，回傳完整模型清單。"""
    url = f"{BASE_URL}/models"
    resp = httpx.get(url, headers=HEADERS, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    models = data.get("data") or data.get("models") or []
    return models


def is_free(model: Dict[str, Any]) -> bool:
    """
    判斷模型是否「免費」。
    OpenRouter 的 `pricing` 可能提供以下欄位：
    - `price_per_input_token` / `price_per_output_token`
    - `prompt` / `completion`
    若任一對應費用為 0（或字串 "0"、"0.0"）就視為免費模型。
    """
    pricing = model.get("pricing", {})
    # 可能是數字、字串或缺少鍵
    def to_float(val: Any) -> float:
        try:
            return float(val)
        except Exception:
            return 1.0  # 非零視為付費

    # 檢查多種可能的鍵名
    input_price = pricing.get("price_per_input_token") or pricing.get("prompt")
    output_price = pricing.get("price_per_output_token") or pricing.get("completion")
    return to_float(input_price) == 0.0 and to_float(output_price) == 0.0


def score_model(model: Dict[str, Any], latency_ms: Optional[float] = None) -> float:
    """計算模型的綜合分數。

    現在同時考慮三個面向：
    1. **效能（performance）** – 從 API 回傳的文字標籤轉成 0~3 分。
    2. **品質（quality）** – `score`、`quality`、`reliability` 任一欄位，預設 0~10 分。
    3. **實測延遲** – 以毫秒為單位，延遲越低分數越高（以 0‑2000ms 為基礎做線性正規化）。

    `latency_ms` 參數為可選：如果提供，就把它納入計算；若未提供則只用前兩項。
    """
    # 1️⃣ 效能分數（0~3）
    performance = model.get("performance", "").lower()
    perf_score = {"fast": 3, "medium": 2, "slow": 1}.get(performance, 0)

    # 2️⃣ 品質分數（0~10）
    quality_score = (
        float(model.get("score", 0))
        or float(model.get("quality", 0))
        or float(model.get("reliability", 0))
        or 0
    )

    # 3️⃣ 延遲分數（0~1）
    latency_score = 0.0
    if latency_ms is not None:
        # 設定一個合理的上限（2000ms），超過則視為最差
        max_latency = 2000.0
        latency_score = max(0.0, (max_latency - latency_ms) / max_latency)
        # 轉成 0~3 的分數範圍，方便與 perf_score 加權
        latency_score = latency_score * 3

    # 加權合併（可自行調整比例）
    # 目前：效能 30%、品質 50%、實測延遲 20%
    total = (
        0.30 * perf_score
        + 0.50 * quality_score
        + 0.20 * latency_score
    )
    return total


def pick_best_free_model(models: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """從所有模型中挑出免費且分數最高的模型。

    現在會先對每個免費模型執行一次測試請求，以取得實測延遲（ms），
    再把延遲資訊帶入 `score_model` 計算最終分數。
    如果測試失敗，會給予一個非常低的分數，確保它不會被選為最佳模型。
    """
    free_models = [m for m in models if is_free(m)]
    if not free_models:
        return None

    for m in free_models:
        # 先測試模型，取得成功與延遲資訊
        success, latency_ms = test_model(m.get("id", ""))
        # 若測試失敗，給予極低分數（-1）以排除
        if not success:
            m["_score"] = -1.0
        else:
            m["_score"] = score_model(m, latency_ms=latency_ms)
    # 依分數遞減排序，排除分數為負的模型
    free_models = [m for m in free_models if m["_score"] >= 0]
    if not free_models:
        return None
    free_models.sort(key=lambda x: x["_score"], reverse=True)
    return free_models[0]


def test_model(model_name: str) -> Tuple[bool, Optional[float]]:
    """對模型發送測試請求，回傳 (成功與否, 延遲毫秒)。

    為了在選擇模型時納入實測延遲，我們同時量測呼叫耗時。
    若回傳內容存在則視為成功，否則視為失敗。
    """
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "請簡短說明什麼是『大模型』"}],
        "max_tokens": 64,
        "temperature": 0.3,
    }
    start = time.perf_counter()
    try:
        resp = httpx.post(url, headers=HEADERS, json=payload, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if content:
            print(f"[green]✅ 測試成功！模型回覆:[/green] {content}")
            return True, elapsed_ms
        else:
            print("[yellow]⚠️ 測試完成但沒有取得回覆內容[/yellow]")
            return False, elapsed_ms
    except httpx.HTTPStatusError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[red]❌ HTTP 錯誤 {exc.response.status_code}: {exc.response.text}[/red]")
        return False, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[red]❌ 其他例外: {e}[/red]")
        return False, elapsed_ms


def pretty_print_model(model: Dict[str, Any]) -> None:
    """使用 rich 把模型資訊表格化輸出。"""
    table = Table(title="最佳 Free 模型資訊")
    table.add_column("欄位", style="cyan", no_wrap=True)
    table.add_column("值", style="magenta")

    fields = {
        "id": model.get("id"),
        "name": model.get("name"),
        "description": model.get("description", "").replace("\n", " "),
        "performance": model.get("performance"),
        "score": str(model.get("score", "")),
        "pricing (input)": str(model.get("pricing", {}).get("price_per_input_token", "N/A")),
        "pricing (output)": str(model.get("pricing", {}).get("price_per_output_token", "N/A")),
        "url": model.get("url", "N/A"),
        "combined_score": f"{model.get('_score', 0):.2f}",
    }
    for k, v in fields.items():
        table.add_row(k, v or "-")
    console = Console()
    console.print(table)

# ------------------------------------------------------------
# 主流程 -------------------------------------------------------
# ------------------------------------------------------------
def main() -> None:
    console = Console()
    console.print("[bold blue]🔎 正在抓取 OpenRouter 模型清單…[/bold blue]")
    try:
        models = fetch_models()
    except Exception as e:
        console.print(f"[red]❌ 抓取模型列表失敗: {e}[/red]")
        sys.exit(1)
    console.print(f"[green]✅ 取得 {len(models)} 個模型[/green]")
    best = pick_best_free_model(models)
    if not best:
        console.print("[red]⚠️ 找不到任何 Free 模型[/red]")
        sys.exit(1)
    pretty_print_model(best)
    console.print("[bold blue]🚀 正在使用挑選出的模型進行測試…[/bold blue]")
    success, _ = test_model(best["id"])
    if success:
        console.print("[bold green]🎉 模型可用且測試成功！[/bold green]")
    else:
        console.print("[red]❌ 測試失敗，請檢查模型名稱或金鑰權限[/red]")

if __name__ == "__main__":
    main()
