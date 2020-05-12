# rakuraku-vcf-sort

ドコモのらくらくスマートフォン3（F-06F）のアドレス帳データ(VCF)をグループ単位にソートします。

## 使い方
$ python rakuraku_vcf_sort.py XXXX.VCF

XXXX.VCF はアドレス帳データ。

日本語は Windows版シフトJIS(CP932)を想定。

## 説明
X-DCM-GN-ORIGINALではじまる行にグループ名があるという想定です。

とりあえずはソートのみします。

## その他
初めて Python 書いてみました。

作法などよくわかってないですが、ご了承願います。
