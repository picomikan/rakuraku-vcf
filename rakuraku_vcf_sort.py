#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import codecs
import os
import re

START_MARK = "BEGIN:VCARD"
END_MARK = "END:VCARD"
GRP_MARK = "X-DCM-GN-ORIGINAL;CHARSET=SHIFT_JIS:"
NAME_MARK = "N;CHARSET=SHIFT_JIS:"

# グループ名ごとのデータ
group = {}

def main():
    if len(sys.argv) < 2:
        usage()
        return -1

    if not os.path.isfile(sys.argv[1]):
        print("File not found.")
        return -2

    top_of_person = True

    # 入力データの各行を処理
    for line in read_file(sys.argv[1]):
        if top_of_person:
            top_of_person = False

            # 一人分のアドレス情報(ハッシュ)を初期化
            person = {'name':"", 'group':"", 'data':[]}

        # 一人分のアドレス情報に追加
        person['data'].append(line)

#        if line == START_MARK:
            # NOP

        #if line.find(END_MARK) != -1:
        if line == END_MARK:
            # 一人分のアドレス情報終了

            # グループ単位の配列に追加
            add_person(person['group'], person)

            # 次のループで一人分のアドレス情報を初期化
            top_of_person = True

        elif line[:len(GRP_MARK)] == GRP_MARK:
            # グループ名を取り出す
            person['group'] = line[len(GRP_MARK):]

        elif line[:len(NAME_MARK)] == NAME_MARK:
            # 名前を取り出す
            str = line[len(NAME_MARK):]
            # 末尾の複数のセミコロンを無視
            str = re.sub(';+$', '', str)
            # 途中のセミコロンを空白に置換
            str = re.sub(';', ' ', str)

            person['name'] = str;

    # 最後の目印なしで抜けた?
    if not top_of_person:
        # グループ単位の配列に追加
        add_person(person['group'], person)

    # 出力
    for g_name in group.keys():
        print("### Group Name:[" + g_name + "]")
        for person in group[g_name]:
            print("# Name:[" + person['name'] + "]")
            for line in person['data']:
                print(line)

    return 0

# Usage
def usage():
    print("Usage: " + sys.argv[0] + " filename")

# データ読み込み
def read_file(in_path):
    lines = []

#    with codecs.open(in_path, 'r', 'shift-jis') as f:
    with codecs.open(in_path, 'r', 'cp932') as f:
 
        # 一行単位で標準入力
    #    for line in sys.stdin.readlines():
        for line in f:
            str = line.rstrip()

#            print("@@@" + str + "@@@")

            # 空行は無視
            if len(str) == 0:
                continue

            # 要素を追加
            lines.append(str)

    return lines

# グループ毎の配列に要素追加
def add_person(g_name, person):
    # グループ名のハッシュを追加(存在しなければ)
    group.setdefault(g_name, [])

    # 要素を追加
    group[g_name].append(person)

# main
if __name__ == "__main__":
    rc = main()
    sys.exit(rc)

