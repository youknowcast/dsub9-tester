# dsub9-tester

秋月電子 AE-3069-LAN-BOARD-C (H8/3069F, 20MHz) の D-SUB9 シリアルを対象としたテストプログラムを管理するリポジトリです。

モード5 (実行モード) で動作中の h8mon-1.12 (38400bps 8N1) 経由で、プログラムを RAM (0xffbf20) にロードして実行します。フラッシュを書き換えないため、反復テストに安全です。

## 構成

| ファイル | 内容 |
|---|---|
| `test_serial.S` | テストプログラム (H8/300H アセンブリ) |
| `linker.ld` | RAM 配置用リンカスクリプト (0xffbf20) |
| `Makefile` | ビルド → S-record 生成 |
| `load.py` | h8mon ドライバ (`ld` → `go` → 受信表示) |

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

## ビルド

```sh
make
```

`test_serial.mot` (S-record) が生成されます。

## 実行

```sh
python3 load.py test_serial.mot ffbf20
```

`ld` で RAM にロードし、`go ffbf20` で実行、シリアル受信を表示します。

## 動作

`test_serial.S` は SCI1 を 38400bps 8N1 に初期化し、以下の動作を繰り返します:

- `DSUB9 TEST OK` + CRLF を約0.5秒間隔で送信
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

### ボーレート

38400bps 相当の BRR=15 (20MHz) は実際には 39062.5bps となり、±1.7% のずれがあります。実用上問題ありませんが、厳密なボーレートが必要な場合は BRR 値を調整してください。

## ライセンス

MIT License (LICENSE 参照)。h8mon (TOPPERS 簡易モニタ, GPLv2) および binutils (GPL) は本リポジトリに含まれません。