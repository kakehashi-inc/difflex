# difflex

3-way比較、類似度検出、外部ツール連携機能を備えたスマートなファイル・ディレクトリ比較ツール

## 開発者向け

### 依存関係のインストール

仮想環境を作成してアクティベートします：

```bash
python -m venv venv

# Windows の場合
.\venv\Scripts\Activate.ps1

# Linux/macOS の場合
source venv/bin/activate

pip install -e ".[dev]"
```

### Windows アイコンの作成

```exec
magick assets/app.png -define icon:auto-resize=256,128,96,64,48,32,24,16 assets/app.ico
```
