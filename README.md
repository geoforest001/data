# data

現場調査アプリ用の配布データ置き場。

```
catalog.json                調査の一覧（make_catalog.py が自動で作る）
make_catalog.py             目録を作るスクリプト
surveys/<調査フォルダ>/
  *.pmtiles                 その調査のPMTiles（林班・小班・施業班など）
  survey.json               任意。表示名や説明 {"name": "...", "note": "..."}
```

更新手順: `surveys/` にPMTilesを置いたら `python3 make_catalog.py` を実行して、`catalog.json` ごとコミットする。
