#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script chuan hoa dia chi cua hang bang mo hinh LLM (Qwen2.5-3B-Instruct GGUF).
Doc du lieu truc tiep tu PostgreSQL, chuan hoa dia chi, ghi de lai vao database.
"""
import sys
import os
import io

# Fix encoding cho Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Them thu muc goc du an vao sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import json
import psycopg2
from pathlib import Path
from utils.llm_normalizer import normalize_address

# ============================================================
# Cau hinh database (lay tu settings.py cua Django)
# ============================================================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "mydb",
    "user": "myuser",
    "password": "mypassword",
}

def main():
    # 1. Ket noi database
    print("Dang ket noi database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()

    # 2. Doc tat ca dia chi tu bang shops_store
    cur.execute("SELECT id, name, address FROM shops_store ORDER BY id;")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Tim thay {total} cua hang trong database.")
    print("=" * 70)

    # 3. Chuan hoa tung dia chi bang LLM
    results = []
    for i, (store_id, name, raw_addr) in enumerate(rows):
        print(f"  [{i+1}/{total}] ID={store_id} | {name}")
        print(f"    Dia chi goc : \"{raw_addr}\"")
        normalized = normalize_address(raw_addr)
        print(f"    Chuan hoa   : \"{normalized}\"")
        print()
        results.append((normalized, raw_addr, store_id))

    # 4. Luu ket qua vao file JSON (de backup truoc khi ghi de database)
    backup_data = []
    for norm, raw, sid in results:
        backup_data.append({
            "id": sid,
            "address_raw": raw,
            "address_normalized": norm,
        })
    backup_path = Path(PROJECT_ROOT) / "address_normalization_backup.json"
    backup_path.write_text(json.dumps(backup_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Da luu backup vao: {backup_path}")
    print("=" * 70)

    # 5. Hoi xac nhan truoc khi ghi de
    print(f"San sang ghi de {total} dia chi vao database.")
    print("Dang ghi de...")

    # 6. Ghi de dia chi trong database
    update_count = 0
    for normalized, raw, store_id in results:
        if normalized and normalized != raw:
            cur.execute(
                "UPDATE shops_store SET address = %s WHERE id = %s;",
                (normalized, store_id)
            )
            update_count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Hoan tat! Da cap nhat {update_count}/{total} dia chi trong database.")
    print(f"Backup file: {backup_path}")


if __name__ == "__main__":
    main()
