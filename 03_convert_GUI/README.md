# rakuraku-vcf-gui

ドコモのらくらくスマートフォン3（F-06F）のアドレス帳データ(VCF)をグループ単位にソート＆分割＆変換します。

## 説明
rakuraku_vcf_conv.py 用のGUIモジュールです。
機能詳細は rakuraku_vcf_conv.py を参照願います。

## 使い方 (rakuraku_vcf_gui.py)
rakuraku_vcf_gui.py と同じフォルダにrakuraku_vcf_conv.py を置いてください。

$ python rakuraku_vcf_gui.py

GUI画面から変換元のVCFファイルを選択して、変換を実行してください。
変換結果は、現在フォルダに新規ファイルとして作成します。

##オプション
- 1つのファイルに出力
デフォルトはグループ毎の複数ファイル

- 入力ファイルの文字コードがUTF-8
デフォルトはシフトJIS

- 半角カナを全角に変換しない (デフォルトは変換)

## その他
pyinstaller で Win/Macの実行形式ファイルも作ってみました。
