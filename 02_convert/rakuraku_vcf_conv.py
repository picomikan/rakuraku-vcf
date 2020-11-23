#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ドコモのらくらくスマートフォン3（F-06F）のアドレス帳データ(VCF)を
# グループ単位にソート＆分割＆変換
#   20200621 　初版
#   20200920 　コメント追加。引数見直し。
#   20200921 　convVCF()の復帰値に、出力ファイル名一覧を追加
#              グループ名の一行出力を標準出力時だけに変更
#   20201124   NからFNを求める論理が動いてなかった問題を修正

import sys
import codecs
import os
import re
import jaconv
import datetime

# デフォルト値
# 入力ファイルのエンコード: Windows版シフトJIS
ENCODE_DEFAULT = 'cp932'

# 半角カナを半角のままとするかのフラグ(デフォルトは変換)
HAN2HAN_DEFAULT = False

# グループ毎のファイルに分割出力するかどうか
DIVFILE_DEFAULT = False

# 無視する文字列一覧
ignore_strs = [';CHARSET=SHIFT_JIS']

# 処理するタグ一覧
#   key     :変換後のタグ(一部仮称)
#   value   :現状のタグ一覧の配列
docomo_tags = {
    'BEGIN'         :['BEGIN'],
    'VERSION'       :['VERSION'],
    'END'           :['END'],
    'CATEGORIES'    :['X-GN', 'X-DCM-GN-ORIGINAL'],
    'FN'            :['FN'],            # Formatted name
    'N'             :['N'],
    '_SOUND'        :['SOUND', 'X-DCM-SOUND-ORIGINAL', 'SORT-STRING'],
    'X-MAIDENNAME'  :['X-MAIDENNAME'],   # 旧姓
    'X-GENDER'      :['X-GENDER', 'X-WAB-GENDER'],
    'TEL'           :['TEL', 'X-DCM-TEL-ORIGINAL'],
    'EMAIL'         :['EMAIL', 'X-DCM-EMAIL-ORIGINAL'],
    'ADR'           :['ADR', 'X-DCM-ADR'],
    '_POSTAL'       :['X-DCM-POSTALCODE-ORIGINAL'],
    'ORG'           :['ORG'],
    'TITLE'         :['TITLE'],
    'NOTE'          :['NOTE', 'X-DCM-NOTE'],
    'NICKNAME'      :['NICKNAME'],
    'PHOTO'         :['PHOTO'],
    'URL'           :['URL', 'X-DCM-URL', 'X-DCM-URL-ORIGINAL'],
    'ANNIVERSARY'   :['ANNIVERSARY', 'X-DCM-CONTACTS_EVENT'],
    'BDAY'          :['BDAY'],
}

# Usage
def usage(argv0):
    '''
    Usage表示

    Args:
        argv0: コマンドラインのプログラム名

    '''

    print('Usage: ' + argv0 + ' {filename | -} [-u][-h][-O][--encoding=XXX][--help]', file=sys.stderr)
    print("""\
\t-  : standard input file
\t-u : Use utf-8 instead of cp932
\t-h : Never convert hankaku kana to zenkakku kana
\t-O : Output files per group
\t--encoding=XXX : Specify encode
\t--help : print usage
""", file=sys.stderr)
    return

# グループ名ごとのデータ
#   key: グループ名
#   value: personの配列
group_list = {}

# VCFファイルを読み込んで変換
def convVCF(in_path, han2han=False, encode='cp932', divfile=False, stdout=True):
    '''
    指定したVCFファイルを変換

    変換結果は標準出力 or 単一ファイル or 複数ファイルに出力。

    Args:
        in_path: 入力VCFファイルのパス
        han2han: 半角カナをそのままにするフラグ
        encode : 入力ファイルのエンコード。デフォルトは cp932(Windows版シフトJIS)
        divfile: グループ毎の複数のファイルに分割出力するかのフラグ
        stdout : 変換結果を標準出力するかファイル出力するかのフラグ

    Returns:
        out_files: 出力ファイル名の一覧(標準出力の場合は空っぽ)

    '''

    # ファイル読み込み
    lines = read_file(in_path, han2han, encode)

    # 入力データの各行を処理
    next_person = True
    for line in lines:

        if next_person:
            next_person = False

            # 一人分のアドレス情報(ハッシュ)を初期化
            #   key     :変換後のタグ(一部仮称)
            #   value   :subtag, valueのペア(*)の配列
            #       *: item = {'subtags':subtags, 'value':value}
            person = {}

            # 一人分のアドレスが属するグループ名一覧を初期化
            g_names = []

        # 一行のデータをアイテムに変換 
        tag, subtags, value = get_item(line)

        # グループ名と END をチェック
        if tag in docomo_tags['CATEGORIES']:
            # グループ名

            if value == '':
                # valueが空っぽならスキップ
                continue

            if value in g_names:
                # グループ名が既出ならスキップ
                continue

            # 新規のグループ名なら追加
            g_names.append(value)

        elif tag in docomo_tags['END']:
            # 一人分のアドレス情報終了

            # 次のループで一人分のアドレス情報を初期化
            next_person = True

        # valueが空っぽかチェック
        # ( ; を無視)
        tmp_str = re.sub(';', '', value)
        if tmp_str == '':
            # valueが空っぽなら次へ
            continue

        # 一人分のアドレス情報にアイテムを追加
        add_item(person, tag, subtags, value)

        if next_person:
            # グループ単位の配列に一人のアドレス情報を追加
            add_person(group_list, g_names, person)

        # end of for()
     
    # 最後の目印なしで抜けた?
    if next_person != True:
        # グループ単位の配列に追加
        add_person(group_list, g_names, person)

    # 以上で読み込んだデータの整理完了

    # 現在時刻
    dt_now = datetime.datetime.now()
    dt_str = dt_now.strftime('%Y%m%d%H%M%S')

    # 出力ファイル名一覧
    out_files = []

    # VCARD 3.0に変換
    for g_name in group_list.keys():
        if divfile:
            # 複数ファイルに分割出力
            out_file = dt_str + g_name + '.VCF'
            f = open(out_file, mode='w')

            # 出力ファイル名を追加
            out_files.append(out_file)

        elif stdout:
            # 標準出力
            f = sys.stdout
            print('### Group Name:[' + g_name + ']')

        else:
            # 単一ファイルに出力
            out_file = dt_str + '_converted' + '.VCF'
            f = open(out_file, mode='a')

            # 出力ファイル名を追加
            if out_file not in out_files:
                out_files.append(out_file)

        for person in group_list[g_name]:

            # 変換
            # (複数のグループに属する場合で変換２回目はNOP)
            conv_person(person)

            items = person['BEGIN']
            put_item(f, 'BEGIN', items[0])

            items_end = person['END']

            # BEGIN, END, _CONVERTED 以外の残りを順に出力
            for tag in person.keys():
                if tag in ['BEGIN', 'END', '_CONVERTED']:
                    continue

                items = person[tag]
                for item in items:
                    put_item(f, tag, item)

            put_item(f, 'END', items_end[0])

        if f != sys.stdout:
            f.close()

    return out_files

# 引数を解析して、入力ファイル名を取得
def ana_arg(*argv):
    '''
    コマンドライン引数を解析

    Args:
        *argv: コマンドライン引数(可変長)

    Returns:
        rc        : 復帰値
        file_name : 入力ファイルのパス
        han2han   : 半角カナをそのままにするフラグ
        encode    : 入力ファイルのエンコード。デフォルトは cp932(Windows版シフトJIS)
        divfile   : グループ毎の複数のファイルに分割出力するかのフラグ
    '''

    global ENCODE_DEFAULT
    global HAN2HAN_DEFAULT
    global DIVFILE_DEFAULT

    encode = ENCODE_DEFAULT
    han2han = HAN2HAN_DEFAULT
    divfile = DIVFILE_DEFAULT

    OPT_ENCODE = '--encoding='

    rc = 0
    file_name = ''

    loop = True
    while loop:
        loop = False    # 実際にはループしない。returnを一箇所にまとめたいだけ。

        if len(argv) < 2:
            usage(argv[0])
            rc = -1
            break

        if argv[1] == '-':
            # 標準入力
            file_name = sys.stdin.fileno()
        
        elif argv[1][:1] == '-':
            usage(argv[0])
            rc = -1
            break

        else:
            file_name = sys.argv[1]

            if not os.path.isfile(file_name):
                print('File not found.', file=sys.stderr)
                rc = -2
                break
        
        if len(sys.argv) >= 3:
            i = 2
            while i < len(argv):

                if argv[i] == '-u':
                    encode = 'utf-8'

                elif argv[i][:len(OPT_ENCODE)] == OPT_ENCODE:
                    encode = argv[i][len(OPT_ENCODE):]

                elif argv[i] == '-h':
                    han2han = True

                elif argv[i] == '-O':
                    divfile = True

                elif argv[i] == '--help':
                    usage(argv[0])
                    rc = -1
                    break

                i += 1
            
        # end of while loop

    return rc, file_name, han2han, encode, divfile

# データ読み込み
def read_file(in_path, han2han=False, encode='cp932'):
    '''
    データを読み込む

    Args:
        in_path: 入力ファイルのパス
        han2han: 半角カナをそのままにするフラグ
        encode : 入力ファイルのエンコード。デフォルトは cp932(Windows版シフトJIS)

    Returns:
        lines: ファイルを読んだ結果。各要素が一行分の文字列の配列  
    '''

    lines = []

    with codecs.open(in_path, 'r', encode) as f:
 
        # 一行単位で標準入力
        for line in f:
            str = line.rstrip()

            # 空行は無視
            if len(str) == 0:
                continue

            if not han2han:
                # 半角カナ -> 全角
                str = jaconv.h2z(str)

            # 要素を追加
            lines.append(str)

    return lines

# 一行のデータをアイテムに変換
def get_item(line):
    '''
    一行のデータをアイテムに変換

    Args:
        line: 1行分のデータ(1個の文字列)
                例: "TEL;VOICE;09012345678"

    Returns:
        tag     : タグ。例だと"TEL"
        subtags : サブタグ。複数でも可能。例だと"VOICE"
        value   : 値。例だと"09012345678"
    '''

    # 無視する文字列を除外
    for ignore_str in ignore_strs:
        line = re.sub(ignore_str, '', line)

    # タグと値に分離
    tags, value = re.split(':', line, 1)

    # タグからサブタグ(複数可)を分離
    tag, *subtags = re.split(';', tags)

    ## 値を分離
    #values = re.split(';', value)

    return tag, subtags, value

# アイテムをアドレス情報に追加
def add_item(person, old_tag, subtags, value):
    '''
    アイテムをアドレス帳に追加

    タグを変換したものをキーとする辞書に、サブタグと値を追加する。
    追加する時重複排除。

    Args:
        person  : 一人分のアドレス情報。タグをキーにした辞書。
        old_tag : 変換前のタグ
        subtags : サブタグ
        value   : 値

    Returns:
        -
    '''

    # タグを変換
    tag = ''
    for key in docomo_tags.keys():
        # 引数の old_tagが docomo_tags[key]一覧に一致するか？
        if old_tag in docomo_tags[key]:
            # 一致する場合、keyに変換
            tag = key
            break
    if tag == '':
        # タグを変換できず -> NOP
        return

    # (重複排除の前に) X-IRMC-N の subtagsを無視
    subtags = [x for x in subtags if not x == 'X-IRMC-N']

    # subtag, valueをアイテムとしてまとめる
    item = {'subtags':subtags, 'value':value}

    # 既に変換後のタグがアドレス情報にあるか?
    if tag in person.keys():
        # 既にある

        # 重複排除
        isHit = False
        # 変換後のタグに対応するアイテム一覧をなめる
        for tmp_item in person[tag]:
            if tmp_item == item:
                # 同じアイテムが既に存在
                isHit = True
                break
        if isHit:
            return
    else:
        # 新規タグ
        person[tag] = []

    # アドレス情報として追加
    person[tag].append(item)

    return

# グループ毎の配列に要素追加
def add_person(group_list, g_names, person):
    '''
    グループ毎の配列に要素追加

    Args:
        group_list: グループ毎の属している人の配列
        g_names   : グループ名の配列。各グループに追加する。
        person    : 一人分のデータ

    Returns:
        -
    '''

    # グループ名の個数が 0ならデフォルト
    if len(g_names) == 0:
        g_names.append("default")
    
    # 各グループにpersonを追加
    for g_name in g_names:

        # 新規のグループ名なら、グループの配列を初期化
        if not g_name in group_list.keys():
            group_list[g_name] = []

        # 重複チェック
        isFound = False
        for person_wk in group_list[g_name]:

            if 0 == compare_persons(person_wk, person):
                # 重複
                isFound = True
                break
        
        if not isFound:
            # 要素を追加
            group_list[g_name].append(person)

    return

# 人(アイテム一覧)同士で比較
def compare_persons(person0, person1):
    '''
    辞書と辞書を比較して、不一致のものを抽出

    Args
    - person0, person1: それぞれ一人分のアドレス情報(タグをキーにした辞書)

    Returns:
    - 不一致の要素の数
    '''
    tags_unmatch = [tag for tag in person0 if tag not in person1 or person0[tag] != person1[tag]]

    return len(tags_unmatch)

# VCARD 3.0に変換
def conv_person(person):
    '''
    一人分のアドレス情報をVCARD 3.0に変換

    Args:
        person: 一人分のアドレス情報(タグをキーにした辞書)

    Returns:
        -
    '''

    if '_CONVERTED' in person:
        # 既に変換済み
        # -> NOP
        return

    # 各アイテムの subtags を無条件に変換
    for key in person.keys():
        items = person[key]
        for item in items:
            # subtag を置換
            item['subtags'] = ['TYPE=' + subtag if subtag in ['VOICE', 'CELL', 'HOME', 'WORK', 'IM', 'MAIN', 'INTERNET'] else subtag for subtag in item['subtags']]

    # VERSION差し替え
    if 'VERSION' in person:
        items = person['VERSION']
        item = items[0]
        item['value'] = '3.0'

    # _SOUND を変換
    if '_SOUND' in person:
        # _SOUND のアイテムを取り出して削除
        items = person.pop('_SOUND')
        for item in items:
            # 値を分離
            values = re.split(';', item['value'], 2)

            # 3つを別のアイテムとして詰め直す
            if values[0] != '':
                person['X-PHONETIC-LAST-NAME'] = [{'subtags':item['subtags'], 'value':values[0]}]
            if values[1] != '':
                person['X-PHONETIC-FIRST-NAME'] = [{'subtags':item['subtags'], 'value':values[1]}]
            if values[2] != '':
                person['X-PHONETIC-MIDDLE-NAME'] = [{'subtags':item['subtags'], 'value':values[2]}]
            
    # N を変換
    if 'N' in person:
        items = person['N']
        for item in items:
            # N の値を分離
            values = re.split(';', item['value'], 4)
            while len(values) < 5:
                values.append('')

            # Nを再結合
            item['value'] = ';'.join(values)

            # FN がなければ 'N'から作って追加
            if not 'FN' in person:
                person['FN'] = [{'subtags':[], 'value':values[3] + values[1] + values[2] + values[0] + values[4]}]

    # ADR変換の前に '_POSTAL'があれば退避
    postal_code = ''
    if '_POSTAL' in person:
        # _POSTAL のアイテムを取り出して削除
        items = person.pop('_POSTAL')
        item = items[0]
        postal_code = item['value']

    # ADR を変換
    if 'ADR' in person:
        for item in items:
            # ADR の値を分離
            values = re.split(';', item['value'], 6)
            while len(values) < 7:
                values.append('')

            postal_of_adr = values[5]

            # _POSTALの値と比較して更新
            if postal_code != '':
                if postal_of_adr == postal_code:
                    # _POSTAL と一致 -> NOP
                    postal_code = ''
                elif postal_of_adr == '':
                    # ADRに郵便番号がない -> 上書き
                    postal_of_adr = postal_code
                    postal_code = ''
            
            # ADRを再結合
            values[5] = postal_of_adr
            item['value'] = ';'.join(values)
        
    if postal_code != '':
        # ADRが無かった or _POSTALと不一致だった
        #  -> 新規でADRを追加
        person['ADR'].append({'subtags':[], 'value':';;;;;' + postal_code + ';'})

    # ANNIVERSARY変換の前に誕生日をがあれば退避
    birthday = ''
    if 'BDAY' in person:
        items = person['BDAY']
        item = items[0]
        birthday = item['value']
     
    # ANNYVERSARY のうち 誕生日は除外
    if 'ANNIVERSARY' in person:
        items = person['ANNIVERSARY']
        for item in items:
            if birthday != '':
                if 'BIRTHDAY' in item['subtags'] or len(item['subtags']) == 0:
                    # subtagsのいずれかが 'BIRTHDAY' または subtagsが空っぽ
                    birthday_of_anniv = re.sub('-', '', item['value'])
                    if birthday_of_anniv == birthday:
                        # _ANNIVERSARY が BDAYと一致するのでこのアイテムを削除
                        person['ANNIVERSARY'].remove(item)

    # NOTE はまとめたもので差し替え
    if 'NOTE' in person:
        note = ''
        items = person['NOTE']
        for item in items:
            if note == '':
                note += item['value']
            else:
                # NOTEが複数ある場合、まとめる
                note += '\\n' + item['value']

        person['NOTE'] = [{'subtags':[], 'value':note}]

    # CATEGORIES はまとめたもので差し替え
    if 'CATEGORIES' in person:
        categories = ''
        items = person['CATEGORIES']
        for item in items:
            if categories == '':
                categories += item['value']
            else:
                # CATEGORIESが複数ある場合、まとめる
                categories += ',' + item['value']

        person['CATEGORIES'] = [{'subtags':[], 'value':categories}]

    # 変換済みのマーク
    person['_CONVERTED'] = [{'subtags':[], 'value':''}]

    return

# アイテムを出力
def put_item(f, tag, item):
    '''
    アイテムを出力

    指定タグと対応するサブタグ、値を整形して出力

    Args:
        f    : 出力ファイルオブジェクト
        tag  : タグ
        item : アイテム(タグをキーにした一人分のアドレス情報)

    Returns:
        -
    '''

    str = ''

    # tag
    str += tag

    # subtags
    if 'subtags' in item:
        for subtag in item['subtags']:
            if subtag != '':
                str += ';' + subtag

    # value
    if 'value' in item:
        value = item['value']
    else:
        value =''
    str += ':' + value

#    print(str)
    f.write(str + '\n')

    return

# main
if __name__ == "__main__":
    rc = 0

    try:
        # 引数を解析して、入力ファイル名を取得
        rc, file_name, han2han, encode, divfile = ana_arg(*sys.argv)
        if rc < 0:
            sys.exit(rc)

        # 変換
        convVCF(file_name, han2han, encode, divfile)

    except Exception as e:
        print(e, file=sys.stderr)
        rc = -1

    sys.exit(rc)
