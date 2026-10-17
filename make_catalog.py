#!/usr/bin/env python3
"""surveys/ フォルダ以下の調査フォルダから catalog.json を作る。

フォルダ構成:
  catalog.json
  surveys/<調査フォルダ>/*.pmtiles   （ファイル名は自由）
  surveys/<調査フォルダ>/survey.json （任意: {"name": "表示名", "note": "説明", "sheet": {...}}）

使い方（リポジトリのフォルダで）:  python3 make_catalog.py
"""
import gzip
import json
import os
import struct
import sys
from datetime import date

LAYER_LABELS = {"rinpan": "林班", "shohan": "小班", "segyohan": "施業班", "rindou": "林道"}
LAYER_ORDER = ["rinpan", "shohan", "segyohan", "rindou"]


def read_pmtiles(path):
    with open(path, "rb") as f:
        head = f.read(127)
        if head[:7] != b"PMTiles" or head[7] != 3:
            raise ValueError("PMTiles v3 ではありません")
        meta_off, meta_len = struct.unpack("<2Q", head[24:40])
        internal_comp = head[97]
        min_zoom, max_zoom = head[100], head[101]
        w, s, e, n = [v / 1e7 for v in struct.unpack("<4i", head[102:118])]
        f.seek(meta_off)
        raw = f.read(meta_len)
    if internal_comp == 2:
        raw = gzip.decompress(raw)
    meta = json.loads(raw) if raw else {}
    layers = meta.get("vector_layers")
    if layers is None and "json" in meta:
        layers = json.loads(meta["json"]).get("vector_layers")
    layer_id = layers[0]["id"] if layers else None
    return {
        "layer": layer_id,
        "minzoom": min_zoom,
        "maxzoom": max_zoom,
        "bbox": [w, s, e, n],
    }


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    out = os.path.join(root, "catalog.json")
    surveys_dir = os.path.join(root, "surveys")
    if not os.path.isdir(surveys_dir):
        sys.exit(f"surveys フォルダが見つかりません: {surveys_dir}")

    surveys = []
    for folder in sorted(os.listdir(surveys_dir)):
        sdir = os.path.join(surveys_dir, folder)
        if not os.path.isdir(sdir):
            continue
        info = {}
        info_path = os.path.join(sdir, "survey.json")
        if os.path.exists(info_path):
            with open(info_path, encoding="utf-8") as f:
                info = json.load(f)

        layers, boxes = [], []
        for name in sorted(os.listdir(sdir)):
            if not name.endswith(".pmtiles"):
                continue
            path = os.path.join(sdir, name)
            try:
                p = read_pmtiles(path)
            except Exception as ex:
                print(f"  スキップ {folder}/{name}: {ex}")
                continue
            boxes.append(p["bbox"])
            layers.append({
                "type": p["layer"],
                "label": LAYER_LABELS.get(p["layer"], p["layer"]),
                "file": os.path.relpath(path, root).replace(os.sep, "/"),
                "size": os.path.getsize(path),
                "minzoom": p["minzoom"],
                "maxzoom": p["maxzoom"],
            })
        if not layers:
            continue
        layers.sort(key=lambda l: LAYER_ORDER.index(l["type"]) if l["type"] in LAYER_ORDER else 99)
        bbox = [
            min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes),
        ]
        surveys.append({
            "id": folder,
            "name": info.get("name", folder),
            "note": info.get("note", ""),
            "bbox": [round(v, 6) for v in bbox],
            "sheet": info.get("sheet"),
            "layers": layers,
        })
        print(f"  {folder}: {len(layers)}層, {sum(l['size'] for l in layers) / 1048576:.1f} MB")

    catalog = {"version": 2, "updated": date.today().isoformat(), "surveys": surveys}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{out}: 調査 {len(surveys)}件")


if __name__ == "__main__":
    main()
