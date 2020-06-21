# rakuraku-vcf-conv

ドコモのらくらくスマートフォン3（F-06F）のアドレス帳データ(VCF)をグループ単位にソート＆分割＆変換します。

## 使い方
$ python rakuraku_vcf_conv.py {filename | -} [-u][-h][-O][--encoding=XXX][--help]

* filename: アドレス帳データ(VCF形式)のファイル名
代わりに「-」を指定すると標準入力からアドレス帳データを読み込みます。

* -u: 入力データの日本語コードを UTF8として扱います。
* --encoding=XXX: 入力データの日本語コードを直接指定します。
デフォルトは Windows版シフトJIS(CP932)とです。

* -h: 半角カナをそのまま半角カナとして扱います。
デフォルトは 半角カナを全角カナに変換します。

* -O: グループ毎に別々のファイルに出力します。
デフォルトは 標準出力です。

## 説明
らくらくスマートフォン3 のアドレス帳データを iPhoneのV3.0形式に変換します。
（変換は実験結果に基づく、ベストエフォート型です。。）
また、グループ単位にソートします。
複数のグループに属しているアドレスは、両方のグループに追加されます。
逆に同一グループ内に全ての要素が同じアドレスが既に存在したら、無視されます(重複排除)。

## その他
rakuraku_vcf_sort をベースに拡張してみました。

pythonの作法などよくわかってないですが、ご了承願います。