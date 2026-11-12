# DICOM MPR Viewer

Python と PySide6 を使用して開発した、DICOM画像の多断面再構成（MPR: Multiplanar Reconstruction）表示アプリケーションです。

Axial・Coronal・Sagittal の3方向から医用画像を観察でき、各断面の位置を患者座標系（LPS）で管理することで、断面間のクロスヘア（位置情報）を同期します。

## 1. 主な機能

### 1.1 DICOM画像の読み込み
- ファイルメニューからDICOM画像を読み込み
- フォルダ内のDICOMファイルをSeries Instance UIDごとに分類
- シリーズ選択による表示画像の切り替え

### 1.2 MPR表示
以下の3方向の断面画像を表示します。

| 断面 | 説明 |
|---|---|
| Axial | 横断面 |
| Coronal | 冠状断面 |
| Sagittal | 矢状断面 |

- 選択した断面をメインビューとして大きく表示
- 残りの2断面をサブビューとして表示
- Image Orientation Patient、Image Position Patient、Pixel Spacingを利用した幾何学的な位置合わせ
- SciPyによる補間処理を用いたMPR画像の生成

### 1.3 クロスヘア同期
- 画像上のクリック位置にクロスヘアを表示
- 患者座標系（LPS: Left, Posterior, Superior）で位置を管理
- いずれかの断面で位置を変更すると、ほかの2断面にも反映
- 3断面間で同一の患者位置を確認可能

### 1.4 画像表示操作

| 操作 | 動作 |
|---|---|
| マウスホイール | スライス位置の変更 |
| Ctrl + マウスホイール | 拡大・縮小 |
| 右ドラッグ | Window Width / Window Level の調整 |
| 中ボタンドラッグ | 画像のパン |
| 左クリック | クロスヘア位置の変更 |

### 1.5 表示・保存機能
- スライス位置のスライダー操作
- Window Width（WW）・Window Level（WL）の調整
- DICOMタグ情報の表示
- メイン画像のPNG保存
- アプリケーション画面全体のスクリーンショット保存

## 2. 動作環境

- Python 3.10 以上を推奨
- Windows / Linux
- GUI表示が可能なデスクトップ環境

## 3. 使用ライブラリ

| ライブラリ | 用途 |
|---|---|
| PySide6 | GUIの構築 |
| pydicom | DICOMファイルの読み込み |
| NumPy | 画像データ・数値計算 |
| SciPy | MPR画像の補間・再サンプリング |
| Matplotlib | 画像表示・描画 |

## 4. インストール方法

### 4.1 プロジェクトの配置

プロジェクトのファイル構成は以下のとおりです。

```text
dicom_mpr_viewer/
├── main.py
├── requirements.txt
└── README.md
```

### 4.2 仮想環境の作成（推奨）

```bash
python -m venv .venv
```

Windowsの場合：

```bash
.venv\Scripts\activate
```

Linuxの場合：

```bash
source .venv/bin/activate
```

### 4.3 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

`requirements.txt` の内容：

```text
PySide6>=6.6
pydicom>=2.4
numpy>=1.24
scipy>=1.10
matplotlib>=3.7
```

## 5. 起動方法

プロジェクトのルートディレクトリで、以下を実行します。

```bash
python main.py
```

アプリケーションのメインウィンドウが表示されます。

## 6. 基本的な使用方法

### Step 1. DICOM画像の読み込み

1. アプリケーションを起動します。
2. FileメニューからDICOM画像が格納されたフォルダを選択します。
3. 読み込みが完了すると、画像シリーズが表示されます。

### Step 2. シリーズの選択

シリーズ選択欄から表示したいDICOMシリーズを選択します。

### Step 3. MPR断面の選択

Axial、Coronal、Sagittalのいずれかを選択します。

選択した断面がメインビューに表示され、ほかの2断面はサブビューに表示されます。

### Step 4. クロスヘアの操作

いずれかの断面画像上をクリックします。

クリックした位置に対応する患者座標が計算され、ほかの断面にもクロスヘアが反映されます。

### Step 5. スライス位置の変更

マウスホイールまたはスライダーを操作してスライス位置を変更します。

### Step 6. WW/WLの調整

WW（Window Width）とWL（Window Level）のスライダーを操作して、画像のコントラストと輝度を調整します。

### Step 7. 画像の保存

必要に応じて、メインビューのPNG画像またはアプリケーション画面全体を保存します。

## 7. MPR処理の概要

本プログラムでは、DICOM画像の画素配列だけでなく、患者座標系における画像の位置・方向情報を利用してMPRを実行します。

主に以下のDICOM属性を使用します。

| DICOM属性 | 内容 |
|---|---|
| ImageOrientationPatient (0020,0037) | 画像の行・列方向を示す方向余弦 |
| ImagePositionPatient (0020,0032) | 画像左上画素の患者座標 |
| PixelSpacing (0028,0030) | 画素間隔 |
| SeriesInstanceUID (0020,000E) | シリーズ識別子 |
| WindowWidth (0028,1051) | ウィンドウ幅 |
| WindowCenter (0028,1050) | ウィンドウ中心 |

画像の幾何学情報をもとに患者座標系（LPS）の3次元ボリュームを構成し、SciPyの補間処理を利用してAxial・Coronal・Sagittal各断面を生成します。

クロスヘアの位置もLPS座標で管理するため、各断面で同一の患者位置を参照できます。

## 8. 現在の対応範囲と制限事項

このプログラムはMPR処理の学習・研究・開発を目的とした試作版です。

現時点では、以下の制限があります。

- 通常の単一フレーム・モノクロDICOM画像を対象としています。
- Enhanced Multi-frame DICOMには対応していません。
- カラーDICOM画像には対応していません。
- PET画像のSUV変換など、モダリティ固有の定量補正には対応していません。
- スライス間隔が不規則なシリーズは正しく処理できない場合があります。
- DICOMのすべてのTransfer Syntaxや特殊な画像構造をサポートするものではありません。
- 補間処理によって元画像に存在しない画素値が生成される場合があります。

## 9. 注意事項

本プログラムは開発・検証用のソフトウェアであり、医療機器としての認証や診断用途での妥当性確認は行っていません。

診断、治療方針の決定、臨床上の計測などには使用しないでください。

## 10. 今後の拡張候補

今後、以下の機能を追加することで、より実用的なDICOMビューワへ発展させることができます。

- Enhanced Multi-frame DICOMへの対応
- CT・MRI・PETなどモダリティ別の画像処理
- DICOMシリーズの自動判定と並び替えの強化
- 不規則なスライス間隔への対応
- 任意断面（Oblique MPR）の表示
- 距離・角度・ROI計測
- DICOM画像の匿名化
- 3D Volume Rendering
- GPUを利用した高速な再構成処理
- DICOM形式での画像書き出し
