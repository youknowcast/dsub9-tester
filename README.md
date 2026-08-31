# dsub9-tester

秋月電子 AE-3069-LAN-BOARD-C (H8/3069F, 20MHz) の D-SUB9 シリアルを対象とした、パターン送信フレームワークです。

モード5 (実行モード) で動作中の h8mon-1.12 (38400bps 8N1) 経由で、プログラムを RAM (0xffbf20) にロードして実行します。フラッシュを書き換えないため、反復テストに安全です。

特定のバイト列を定間隔で繰り返し送信するエンジン (`sender.S`) と、送信パターン・ボーレート・間隔をビルド時に埋め込むホストツール (`gen_mot.py`) で構成されます。台貫 (トラックスケール) 等のシリアル機器エミュレーションの土台として使えます。ベンダ固有のフォーマットはパターンファイルとして後から追加できます。

## 構成

| ファイル | 内容 |
|---|---|
| `sender.S` | 送信エンジン (H8/300H アセンブリ) + パラメータブロック (RAM 0xffc000) |
| `linker.ld` | RAM 配置用リンカスクリプト (コード 0xffbf20, パラメータ 0xffc000) |
| `Makefile` | エンジンのビルド → S-record 生成 |
| `gen_mot.py` | パラメータブロックにパターン・ボーレート・間隔をパッチするツール |
| `patterns/` | 送信パターンファイル (詳細は「パターンの作成」) |
| `load.py` | h8mon ドライバ (`ld` → `go` → 受信表示) |

## パラメータブロック

`sender.S` のエンジンは RAM 0xffc000 のパラメータブロックを参照して送信します。

| オフセット | サイズ | 内容 |
|---|---|---|
| 0x00 | 1B | BRR (ボーレート除数, 15 = 38400bps @ 20MHz) |
| 0x02 | 4B | 送信間隔 (delay カウント, 2000000 ≈ 0.55秒 実測) |
| 0x06 | 1B | パターン長 |
| 0x08 | 最大56B | パターン (デフォルト "DSUB9 TEST OK\r\n") |

エンジンはループで LED (PA0) トグル → パターン送信 → 間隔待ちを繰り返します。

## 前提条件

- ボード: AE-3069-LAN-BOARD-C (H8/3069F, 水晶 20MHz)
  - モード5 (実行モード) に DIP-SW を設定
  - フラッシュに h8mon-1.12 を書き込み済み (SCI1 → CN4 D-SUB9, 38400bps 8N1)
- USB-シリアル変換ケーブル (PL2303 等) が `/dev/ttyUSB0` として認識されている
- Python 3
- h8300-elf クロスツールチェイン (binutils)

### h8300-elf binutils のビルド

GCC は h8300 ターゲットを GCC 11 で削除済みですが、binutils は現行バージョンでも対応しています。アセンブラ+リンカのみで十分です。

```sh
curl -sSL -o binutils-2.47.tar.xz https://ftp.jaist.ac.jp/pub/GNU/binutils/binutils-2.47.tar.xz
tar xf binutils-2.47.tar.xz
mkdir binutils-build && cd binutils-build
../binutils-2.47/configure --target=h8300-elf --prefix=$HOME/tools/h8300-elf \
  --disable-nls --disable-werror --disable-gdb --disable-gprofng --disable-gdbserver
make -j$(nproc) && make install
export PATH=$HOME/tools/h8300-elf/bin:$PATH
```

インストール先を変える場合は `Makefile` の `PREFIX` を上書きします (`make PREFIX=/path/to/bin`)。

## ビルドと実行

デフォルト (38400bps, "DSUB9 TEST OK", 約0.55秒間隔) の場合:

```sh
make
python3 load.py sender.mot ffbf20
```

パターン・ボーレート・間隔を変更する場合:

```sh
python3 gen_mot.py --pattern patterns/custom.txt --baud 19200 --interval 500000 -o sender_custom.mot
python3 load.py sender_custom.mot ffbf20 6 19200
```

`load.py` の引数: モトファイル, アドレス, 受信時間 (秒), 受信ボーレート (省略時 38400)。モニタとのやり取りは常に 38400 で行い、`go` 後に受信ボーレートへ切り替えます。

## パターンの作成

送信するバイト列は `patterns/` 配下のテキストファイルに 1 行で書きます。

```
DSUB9 TEST OK
```

ルール:

- **ファイル内容がそのまま送信バイト列**になります。改行 (`LF`) のみ CRLF (`\r\n`) に自動変換されます。`patterns/default.txt` の `DSUB9 TEST OK` + 改行は `DSUB9 TEST OK\r\n` として送信されます
- 複数行にすると各行の改行が CRLF になるため、複数レコードを連続送信するパターンも書けます
- **エスケープ処理はありません**。`\r` 等のエスケープ表記はそのままの文字として送信されます。STX/ETX などの制御文字を含めたい場合は `gen_mot.py` の拡張が必要です
- パターンは**最大 56 バイト** (CRLF 変換後)。超えると `gen_mot.py` がエラーを返します

作成したパターンファイルは `gen_mot.py` の `--pattern` で指定します。出力先 (`-o`) と `load.py` の引数は任意の名前で構いません。製品 (ベンダ仕様) ごとにパターンファイルを追加することで、エンジン本体を変えずに複数仕様へ対応できます。

## ターミナルでのシリアル出力の確認

ボードの送信内容は、ターミナルソフトでシリアルポートを直接覗いて確認できます。

`38400` はボーレート (通信速度, 1秒あたりのビット数) です。ボードの送信速度 (h8mon のコンソールおよび `sender.mot` のデフォルト) と受信側を合わせる必要があります。`gen_mot.py` の `--baud` でボーレートを変えた場合は、ここで指定する数値も同じ値に合わせてください。

### Linux

```sh
stty -F /dev/ttyUSB0 38400 raw -echo && cat /dev/ttyUSB0
```

Ctrl-C で停止します。ポート名は環境に応じて `ttyUSB0` 以外 (`ttyACM0` 等) の場合があります。`/dev/serial/by-id/` で確認できます。

### Windows

COM ポート番号はデバイスマネージャー (ポート (COM と LPT)) で確認してください。以下は COM3 の例です。

#### cmd (type コマンド)

```bat
mode COM3: 38400,n,8,1
type COM3:
```

Ctrl-C で停止します。

#### PowerShell

```powershell
$port = New-Object System.IO.Ports.SerialPort COM3,38400,None,8,One
$port.Open()
while ($true) { $s = $port.ReadExisting(); if ($s) { Write-Host -NoNewline $s } }
```

Ctrl-C で停止します。

#### Tera Term / PuTTY

新規接続で COM3 を選択し、38400bps / 8bit / parity none / stop 1bit / flow control none に設定します。Tera Term はシリアル接続の定番ソフトです。

## 動作

`sender.S` は SCI1 を指定ボーレート 8N1 に初期化し、以下の動作を繰り返します:

- パラメータブロックのパターンを指定間隔で送信
- PA0 (ポート A bit 0) をトグル

PA0 は拡張ヘッダに引き出されています。LED + 抵抗 (例: 1kΩ) を PA0-GND 間に接続すると点滅を確認できます。オンボードの LED1-3 は LAN コントローラ (RTL8019AS) 直結のため CPU からは制御できません。

プログラムは無限ループのため、モニタに戻すにはボードをリセットします。

## 注意点

### H8/3069 SCI の TDRE クリア

H8/3069 の SCI は TDR にデータを書き込んだだけでは送信を開始しません。SSR の TDRE フラグを 1 で読み出した後、**0 を書き込んでクリア**する必要があります。

```asm
	mov.b	r0l, @TDR1:24
	mov.b	@SSR1:24, r0l
	and.b	#0x7f, r0l
	mov.b	r0l, @SSR1:24
```

### ボーレート誤差

BRR は `20MHz / 32 / ボーレート - 1` で計算します。38400 の場合 BRR=15 で実効 39062.5bps (±1.7%)、19200 の場合 BRR=31 で実効 19531.25bps (±1.7%) です。実用上問題ありませんが、厳密なボーレートが必要な場合は BRR を直接指定してください。

### パターン長

パターンは最大 56 バイト (CRLF 変換後) です。超える場合は `gen_mot.py` がエラーを返します。上限を広げるには `sender.S` の `.space` と `gen_mot.py` の `MAX_PATTERN` を同時に変更します。

## ライセンス

MIT License (LICENSE 参照)。h8mon (TOPPERS 簡易モニタ, GPLv2) および binutils (GPL) は本リポジトリに含まれません。