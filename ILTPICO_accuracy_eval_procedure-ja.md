# ILT-Pico 距離精度 評価手順書（初回オペレーター向け）

CalibratorV2 リグを使って ILT-Pico センサーの **距離 accuracy / precision** を
複数距離で評価する手順を、初めて行う人でも実行できるように順を追って説明します。

関連ツール: `wall_align.py`（→ `README_wall_align.md`）、
`script/slider_sweep_pointcloud.txt`、MkECTL GUI（→ `README.md`）。

---

## 0. この手順でやること（概要）

大きく平らな壁にセンサーを **正対** させ、スライダーで **距離を変えながら** 各距離で
点群を多数枚撮影します。壁に当たった点群の Z（奥行き）から、各距離での
センサー–壁間距離を求めます。

- **accuracy（正確さ・偏り）** = （測定距離の平均）−（指令スライダー距離）
  - 真値は「指令スライダー距離」。壁が平らで、スライダー軸が壁に垂直である前提。
- **precision（精度・ばらつき）** = 測定距離の標準偏差（同一距離・フレーム間）

```
            真値(指令距離)
                |
  precision →  |←→|   (フレーム間のばらつき)
        ●●●●●●●|●●●●●
        └──────┘
       accuracy = 平均のズレ
```

### 全体の流れ

| 手順 | 内容 | 使うもの |
| --- | --- | --- |
| 前提 | センサーのキャリブデータ（`out/`）を生成（初回・機種ごと、本書 4 章） | mkestudio / pc_calibration |
| A | 壁にセンサーを正対させる | `wall_align.py` |
| B | 取付オフセットを確定しスクリプトへ反映 | 距離計 + スクリプト編集 |
| C | スライダースイープを実行し点群を収集 | MkECTL GUI |
| D | 点群から accuracy / precision を算出 | `analyze-sweep` ツール（本書 8 章） |

> **重要な前提（最初に確認）**
> - 壁は **平らで大きく**、最短〜最長距離でセンサー視野を十分に埋めること。
> - **スライダーの移動方向が壁に垂直** であること（accuracy の真値がこれに依存）。
> - Keigan モーターのシリアルポートは **1 つのプロセスしか掴めない**。
>   `wall_align.py` と MkECTL を **同時に起動しない**（A を終えてから C）。

---

## 1. 必要なもの

**ハードウェア**
- CalibratorV2 リグ（3 軸 Keigan モーター: slide / pan / tilt、IR ライト、ILT-Pico USB センサー）
- 平らで大きい壁
- 距離計（メジャー or レーザー距離計）— 手順 B のオフセット較正用

**ソフトウェア / データ**（[[pyiltrs2-env-split]] 参照）
- **MkECTL Python 環境**（`PyQt5` / `qtutils` / `matplotlib` / `timeout_decorator` /
  `pyserial` を持つ venv）。ここに点群エンジンを入れる:
  ```bash
  pip install ./pyiltrs2-0.1.0-py3-none-any.whl
  ```
  pyusb は pyiltrs2 の optional-dependencies に含まれるため、ライブ USB
  (`--input usb`) を使うなら extra 付きで入れれば別途インストールは不要:
  ```bash
  pip install "./pyiltrs2-0.1.0-py3-none-any.whl[usb]"   # [usb] は extra 名（whl の定義に合わせる）
  ```
- センサーのキャリブデータ: `trajectory_data.bin` を含む `out/` ディレクトリ。
  例: `~/iltpico/pc_calibration/calib/ILT001/209/out`。**未生成なら 4 章** で作る。
- `reconstruct.py` の場所。例: `~/iltpico/pc_reconstruction/reconstruct.py`

---

## 2. 物理セットアップ

1. ILT-Pico センサーをリグに取り付ける。
2. リグを壁の正面に設置し、**スライダー移動方向が壁に垂直** になるよう合わせる。
3. 最短距離（後述 200mm）と最長距離（1000mm）の両方で、壁がセンサー視野を
   十分に埋めることを確認する。

---

## 3. ソフト準備（初回のみ）

`movslide` / `exec` コマンドや本手順用のスクリプトは MkECTL リポジトリの
**`feat/iltpico-eval` ブランチ** にあります。まずこのブランチをチェックアウトします。

```bash
cd <MkECTL>
git checkout feat/iltpico-eval
```

1. MkECTL 環境を有効化（例 `source venv/bin/activate`）。
2. 上記 wheel と `pyusb` をインストール済みか確認。
3. `--calib-dir` のパスを確認。
4. `script/slider_sweep_pointcloud.txt` を開き、自分の環境に合わせて以下が
   正しいか確認する（パスに空白を含めないこと）:
   - `reconstruct.py` の絶対パス
   - `--calib-dir` のパス
   - 先頭の `python3`（pyusb/iltrecon が別 venv なら、そのインタプリタ絶対パスに置換）

---

## 4. キャリブデータの用意（初回 / センサー機種ごと）

`wall_align.py` も `reconstruct.py` も、センサーのキャリブデータ
（`out/` ディレクトリ内の `trajectory_data.bin` ほか）を必要とします。まだ無い場合は
本章で生成します。**一度作れば同じセンサー機種では使い回せます**ので、既に `out/` が
ある場合はこの章を飛ばして手順 A へ進んでください。

生成は 2 段階です。

1. **near / far 画像を作る**（DOE ドットパターンの合成画像）— `make_doe_image.py`
2. **その 2 枚からキャリブデータを生成する** — `pc_calibration`（`calibrate.py`）

> どちらも **mkestudio が動く Python 仮想環境**（`pymkeds` が入っている環境）で実行できます。
> `pyiltpicocalib`（`calibrate.py`）の wheel もこの mkestudio venv にインストールすればよく、
> 専用 venv を別に作る必要はありません。MkECTL 環境とは分けてください。

### 4-1. near / far 画像を生成する

`make_doe_image.py` は、mkecc セッション
（`.msf`）の DOE ドットパターンを、指定距離に置いた billboard 上にレンダリングして PNG
として保存します。

**必ず mkestudio が実行できる Python 仮想環境**（`pymkeds` をインポートできる環境）で
実行してください。

near=190mm, far=715mm の 2 枚を生成する例:

```bash
# mkestudio の venv を有効化してから実行する
# near: 190mm
python make_doe_image.py <session.msf> -z 190 -o MkeccCamera0_000_slide=190.png

# far: 715mm
python make_doe_image.py <session.msf> -z 715 -o MkeccCamera0_001_slide=715.png
```

- `<session.msf>` は対象センサーの mkecc セッションファイル。
- `-z` が billboard 距離 [mm]、`-o` が出力 PNG パス。
- ファイル名は後段の `config.json`（4-3）で参照するので、距離が分かる名前にしておくと
  管理しやすい（例にならい `..._slide=190.png` / `..._slide=715.png`）。

### 4-2. pc_calibration ツールのセットアップ（mkestudio venv に wheel を入れる）

キャリブデータ生成ツールは、`usb-rp2040-spi` リポジトリの `feat/pc_calibration`
ブランチで `tools/pc_calibration` にあります。**4-1 と同じ mkestudio venv** に
wheel を作ってインストールします（専用 venv は不要）。

```bash
# mkestudio の venv を有効化した状態で
cd <usb-rp2040-spi>/tools/pc_calibration   # feat/pc_calibration ブランチ

# wheel をビルドしてインストール
pip install build
python -m build --wheel            # -> dist/pyiltpicocalib-<version>-py3-none-any.whl
pip install dist/pyiltpicocalib-*.whl
```

インストールすると `pyiltpicocalib` コンソールコマンドが使えます
（あるいはソースツリーから直接 `python calibrate.py` でも実行可）。

> ソースのまま動かすだけなら wheel を作らず `pip install -r requirements.txt`
> （numpy / scipy / Pillow）でも可。配布・再現性のためには wheel 化を推奨します。

### 4-3. config.json を書く

4-1 で作った 2 枚と、その距離を JSON で指定します。雛形は同ツールの
`sample_config.json`、実例は `calib/ILT001/064/config.json` を参照してください。

先頭の 4 つが本手順で差し替える項目です:

```json
{
  "near_image": "MkeccCamera0_000_slide=190.png",
  "far_image":  "MkeccCamera0_001_slide=715.png",
  "z_near": 190.0,
  "z_far":  715.0,

  "camera":    { "...": "sample_config.json の値（センサー機種の build-time 定数）" },
  "lens":      { "...": "レンズ係数" },
  "projector": { "...": "プロジェクタ原点" },
  "meta":      { "...": "h_total / exposure / gain / laser など" }
}
```

- **`near_image` / `far_image`**: 4-1 で生成した PNG のパス（`config.json` からの相対 or 絶対）。
- **`z_near` / `z_far`**: それぞれの画像を生成したときの距離 [mm]。**4-1 の `-z` と一致させる**
  （この例では 190.0 / 715.0）。
- `camera` / `lens` / `projector` / `meta` ブロックは、センサー機種ごとの定数・レンズ係数・
  撮影メタ情報。`sample_config.json` と既存の `calib/ILT001/064/config.json` を雛形に、対象
  センサーに合わせて埋める（ここはキャリブ担当に確認）。

### 4-4. キャリブデータ（`out/`）を生成する

config.json を入力に `calibrate.py` を実行します。`-o` で出力ディレクトリを指定します。

```bash
# mkestudio の venv を有効化した状態で
cd <usb-rp2040-spi>/tools/pc_calibration   # feat/pc_calibration ブランチ

python calibrate.py config.json -o out
#   または wheel 導入後のコンソールコマンドで:
# pyiltpicocalib config.json -o out
```

- 成功すると `out/` に `trajectory_data.bin`（+ 関連ファイル）が生成されます。
- 実行時に reproj 誤差などの metrics が表示されます。極端に大きい場合は画像 / config を見直す。
- この `out/` の **絶対パス** を、以降の手順の `--calib-dir` に渡します
  （例: `<usb-rp2040-spi>/tools/pc_calibration/out`）。

### 4-5. trajectory_data.bin をセンサーへ書き込む

**測定するセンサー自身にも、生成した `trajectory_data.bin` を書き込んでください。**
ファームウェアには trajectory をアップロードする USB コマンドが無いため、`.bin` を
フラッシュのキャリブ領域へ直接書き込みます。書き込み先は XIP アドレス
**`0x100c0000`**（オフセット `0x000C0000` = `FLASH_ADRS_TRAJECTORY_DATA`）です。
この領域のみが書き換わり、ファームや他データはそのまま残ります。

`picotool`（BOOTSEL モード）で書き込みます。次のどちらかを使います。

**方法A — UF2 に変換して書き込む**

```bash
# trajectory_data.bin のあるディレクトリで
picotool uf2 convert trajectory_data.bin traj.uf2 -o 0x100c0000
# （picotool が family id で文句を言う場合は --family rp2040 を付ける）
```

`-o` は **出力ファイルではなくオフセット**で、`<入力> <出力>` は位置引数です。続いて
**BOOTSEL を押しながら** Pico を接続し、`traj.uf2` を `RPI-RP2` ドライブにコピー
（または `picotool load traj.uf2`）します。

**方法B — picotool load で直接書き込む（UF2 不要）**

```bash
# BOOTSEL を押しながら接続した状態で
picotool load trajectory_data.bin -o 0x100c0000 -v
picotool reboot
```

> **meta フィールドを正しく**: 測定開始時にデバイスは `VERIFY` を実行し、
> `h_total / v_total / exposure / gain / blc_target`（署名・距離レンジに加えて）を
> 検証します。ゼロは拒否されます。4-3 の `config.json` の `meta` ブロックを、
> キャリブ画像を撮影したときの値に合わせてください（ファーム既定値は
> `1280 / 525 / 30 / 16 / 256`, `laser=1`）。書き込み後に測定モードへ入り、
> 3D 点群が出れば成功です。

> ここまでで `out/` の用意とセンサーへの書き込みが済んだら、手順 A へ進みます。
> 以降のコマンドは **MkECTL 環境** で実行します（mkestudio venv ではない）。

---

## 5. 手順A — 壁にセンサーを正対させる

`wall_align.py` で pan / tilt を駆動し、センサー光軸を壁に垂直にします。
**スライダーは動かしません。** 詳細は `README_wall_align.md`。

### A-1. まず符号を確認（実機では必須）

`--pan-sign` / `--tilt-sign` は取付依存で、机上では決められません。
最初に手動モードで「1 ステップで誤差が減るか」を確認します。

```bash
python3 wall_align.py --manual --calib-dir ~/iltpico/pc_calibration/calib/ILT001/209/out/
```

`CalibratorV2_REV` の既定は `--pan-sign -1 / --tilt-sign +1`。
誤差が増える軸があれば、その符号を反転して再確認します。

### A-2. 自動で正対させる

```bash
python3 wall_align.py --auto \
    --calib-dir ~/iltpico/pc_calibration/calib/ILT001/209/out/ \
    --frame 40 --threshold 0.3
```

- レポートの **`total tilt vs wall`** が `--threshold`（0.3°）以下になれば収束。
- `DIVERGING` で止まる / 収束しない場合は `README_wall_align.md` のトラブルシュート参照
  （`--frames` を増やす、`--threshold` を上げる、`--gain` を下げる）。
- 収束したら **`wall_align.py` を終了**（プロセス終了でモーター開放）。

> 正対した pan / tilt 姿勢は、この後 MkECTL を `Initialize` しても保持されます
> （`Initialize` はホーミングしない）[[keiganrobot-axis-and-init]]。
> 以降、**pan / tilt は触らない**（slider のみ動かす）。

---

## 6. 手順B — 取付オフセットを確定しスクリプトへ反映

センサーの取り付け位置はスライダーの z 指令値と一定量ずれています。これを
補正しないと「指令距離」と「真のセンサー–壁間距離」が食い違い、accuracy が
系統的にずれます。[[slider-sensor-mount-offset]]

### B-1. オフセットを 1 点測定で求める

1. MkECTL（手順 C で起動）または `wall_align.py` 実行中の任意の状態で、
   スライダーをある指令値 `z0`（例 500）に置く。
2. その状態でセンサーから壁までの **真の距離 `D0`** を距離計で測る。
3. オフセット = `z0 − D0`（加算オフセット前提）。
   - 例: 指令 500 のとき実測 615mm → offset = `500 − 615 = −115`。

### B-2. スクリプトへ反映

`script/slider_sweep_pointcloud.txt` 先頭の `offset` 行を更新します。
**引数は必ずカンマ区切り**（スペース区切りは連結され桁が化ける）[[dsl-args-comma-separated]]。

```text
offset -115, 0, 0
```

これで `movslide 200` 〜 `movslide 1000` の引数は「真のセンサー–壁間距離」を表し、
出力フォルダ名 `dist_0200` 〜 `dist_1000` がそのまま真値ラベルになります。

> **スライダー原点に注意**: オフセット値は「slide=0 をどこに取ったか」に依存します。
> 毎回同じ machineFile / 原点基準で測定し、取付やリグを変えたらオフセットを
> 再較正してください。物理位置は `真の距離 + offset` にシフトするので、
> 可動域（おおむね 0〜1000mm 相当）に収まるかも確認します（例 offset −115 なら
> 物理 85〜885mm）。

---

## 7. 手順C — スライダースイープを実行（MkECTL）

`reconstruct.py` が USB センサーを占有するため、**MkECTL 側ではセンサーを接続しません**
（ロボットにのみ接続する）。

1. MkECTL を起動:
   ```bash
   python3 MkECTL.py
   ```
2. **machineFile を選択**（例 `machineFiles/CalibratorV2_REV.json`）し、
   **`connect` ボタン** を押してロボットに接続する。pan / tilt は手順 A の姿勢のまま
   保持される（接続では原点へ動かさない）。
3. **センサーウィンドウは開かない / センサー接続しない**（USB 競合を避けるため）。
4. **`Select Script button`** → `script/slider_sweep_pointcloud.txt` を選択。
5. **`Execute Script button`** で先頭から実行。`Progress` ウィンドウに進捗が出る。
   - 各距離で `movslide`（slider のみ移動）→ 整定 → `exec` で `reconstruct.py` が走り、
     その距離の PLY フレーム群を書き出す。
   - 途中で止めたいときは `Progress` の **`Stop button`**。
6. 全 9 地点（200〜1000mm, 100mm 刻み）が終わると完了。

> **最初は 1 地点で動作確認**するのを推奨します。スクリプトを 1 ブロック
> （`movslide 200` + 続く `exec`）だけにしたコピーで試し、PLY が出力されることを
> 確認してから全 9 地点を回すと安全です。

### 出力データ構造

```
data/sweep/
  dist_0200/ frame0000.ply frame0001.ply ... frame0099.ply (+ depth npy)
  dist_0300/ ...
  ...
  dist_1000/ ...
```

- PLY 座標は **mm**。フォルダ名 = 真の距離ラベル（offset 補正済み）。
- 各距離 100 フレーム（`--max-frames 100` / `--frame all`）。precision を取るには
  全フレームが必要で、N=100 だと std の相対不確かさは約 7%
  （≈ `1/sqrt(2(N-1))`）。N を増やすほど安定。

---

## 8. 手順D — 解析（accuracy / precision を算出）

`analyze-sweep` ツールで、各 `dist_XXXX` フォルダの PLY から距離ごとの
**Accuracy / Precision** を算出し、コンソール表と PNG グラフ
（`accuracy_precision_plot.png`）を出力します。フォルダ名 `dist_XXXX` の
**末尾 4 桁が Ground Truth（真値, mm）** として扱われます。

### 8-1. インストール

wheel は本リポジトリの `analyze-sweep/` ディレクトリからビルドします。

```bash
cd analyze-sweep
pip install build
python -m build --wheel    # -> dist/analyze_sweep-1.0.0-py3-none-any.whl
```

任意の Python 環境（MkECTL 環境でも可）に analyze_sweep をインストールします。

```bash
pip install dist/analyze_sweep-1.0.0-py3-none-any.whl
```

依存（numpy / matplotlib / plyfile）は自動で入ります。PLY 読み込みに open3d を
使いたい場合は `pip install "analyze-sweep[open3d]"`（無くても plyfile で動作）。

### 8-2. 実行

スイープ出力（`data/sweep/dist_XXXX`）を入力に実行します。

```bash
# data/sweep を解析し、accuracy_precision_plot.png を出力
analyze-sweep -s data/sweep -o accuracy_precision_plot.png

# 既定（./sweep を解析、./accuracy_precision_plot.png に出力）なら引数なしでも可
# analyze-sweep
# モジュールとしても実行可: python -m analyze_sweep --help
```

| オプション | 既定 | 説明 |
|---|---|---|
| `-s, --sweep-dir` | `./sweep` | `dist_XXXX` を含むディレクトリ |
| `-o, --output` | `./accuracy_precision_plot.png` | 出力 PNG パス |
| `-t, --threshold` | `50` | 外れ値フィルタのしきい値 [mm]（測定 Z の中央値 ± この値で壁を切り出す） |

### 8-3. 指標の定義と読み方

- **Accuracy** =（フィルタ後の Z 平均）−（Ground Truth）。正なら遠側、負なら近側へ偏り。
- **Accuracy (%)** = Accuracy / Ground Truth × 100。
- **Precision** = フィルタ後の Z の標準偏差（ばらつき。小さいほど安定。距離とともに増えるのが典型）。

外れ値フィルタは「測定 Z の中央値 ± `--threshold`」内の点を壁とみなして残します。
実データには Ground Truth に対する系統オフセットがあるため、GT 基準ではなく
中央値基準で壁を切り出し、そのオフセット自体を Accuracy として報告します。

コンソール表に加え、距離 vs Accuracy / Precision のグラフが
`accuracy_precision_plot.png` に出力されます。

---

## 9. 結果の解釈と合否判断

- **accuracy にほぼ一定のバイアス** が残る → オフセット較正（手順 B）の残差の可能性。
  全距離で同程度のズレなら offset を微調整して再評価。距離に比例して増えるズレは
  スケール誤差（センサー機差 or 較正）を示唆。
- **precision が距離とともに増える** のは ToF/三角測量の一般的傾向。仕様値と比較する。
- **precision がどの距離でも大きい / 値が不安定** → 正対不足 or 壁が平らでない可能性。
  手順 A をやり直す。必要なら `--threshold` を見直して壁の切り出しを確認する。
- 単一距離だけでなく、`accuracy_precision_plot.png`（距離 vs accuracy / precision）で
  傾向を確認する。

---

## 10. トラブルシュート

| 症状 | 対処 |
| --- | --- |
| `wall_align` が収束しない / `DIVERGING` | `README_wall_align.md` 参照（`--frames`↑ `--threshold`↑ `--gain`↓、符号確認） |
| スクリプトが slider 可動域外で失敗 | 手順 B の offset 書式（カンマ区切り）と原点を確認 [[dsl-args-comma-separated]] |
| `exec` で `reconstruct.py` が失敗 | スクリプト内のパス / `--calib-dir` / `python3` を確認。USB をセンサーウィンドウが掴んでいないか確認 |
| PLY が空 / 有効フレーム少 | 壁が視野を埋めているか、レーザー点灯、距離が近/遠すぎないか |
| モーターに接続できない | `wall_align` と MkECTL を同時起動していないか（ポート競合）。片方を終了 |

---

## 付録: 実行チェックリスト

- [ ] 壁が平ら・大きい・視野を埋める。スライダー軸が壁に垂直。
- [ ] MkECTL 環境に pyiltrs2 wheel + pyusb 済み。`--calib-dir` 確認。
- [ ] `wall_align.py --auto` で `total tilt` が閾値以下に収束。終了した。
- [ ] offset を 1 点測定で確定し、スクリプトへ **カンマ区切り** で反映。
- [ ] スクリプト内の reconstruct.py パス / `--calib-dir` / `python3` を確認。
- [ ] MkECTL: machineFile を選択 → `connect`（センサーは接続しない）。
- [ ] まず 1 地点で動作確認 → 全 9 地点を `Execute Script`。
- [ ] `analyze-sweep` で accuracy / precision を算出し、仕様と比較。

---

## 関連ドキュメント

- `README_wall_align.md` — 正対ツールの詳細
- `README.md` — MkECTL GUI とスクリプト文法
- `script/slider_sweep_pointcloud.txt` — スイープスクリプト本体
