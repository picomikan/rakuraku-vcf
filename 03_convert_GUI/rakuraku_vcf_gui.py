#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ドコモのらくらくスマートフォン3（F-06F）のアドレス帳データ(VCF)を
# グループ単位にソート＆分割＆変換 (GUI部のみ)
#   20200921 　初版
#
# 参考: 
# https://qiita.com/nnahito/items/ad1428a30738b3d93762
# https://qiita.com/studio_haneya/items/ddbaa76a6ee2c705ad5a

import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
try:
    import rakuraku_vcf_conv
except Exception as e:
    print(e)
    print("Please get rakuraku_vcf_conv.py from https://github.com/picomikan/rakuraku-vcf/")
    sys.exit(-1)

# 画面
class TkinterClass:
    def __init__(self):
        '''
        コンストラクタ
        '''
        self.root = tk.Tk()
        self.root.title('アドレス帳変換')
        self.root.geometry("700x500")

        ### 変数 ###
        # ファイル名
        self.file_name = tk.StringVar()
        self.file_name.set('(未選択)')

        # チェックボックスの各項目の初期値
        self.singlefile   = tk.BooleanVar(value=False)      # 単一ファイルに出力するかのフラグ
        self.encodeIsUtf8 = tk.BooleanVar(value=False)      # 入力ファイルがUTF-8かのフラグ
        self.han2han      = tk.BooleanVar(value=False)      # 半角カナをそのままとするかのフラグ


        ### 画面上の部品
        # 冒頭の文字
        label = tk.Label(self.root, text="ドコモらくらくスマートフォン3(F-06F)の", font=('', 18))
        label.pack(padx=10, pady=0, anchor=tk.W)
        label = tk.Label(self.root, text="アドレス帳データ(VCF)をiPhone用に変換します。", font=('', 18))
        label.pack(padx=10, pady=0, anchor=tk.W)
        label = tk.Label(self.root, text="変換するファイルを選択してください", font=('', 14))
        label.pack(padx=10, pady=10, anchor=tk.W)

        # ファイル選択ボタン
        button = tk.Button(self.root, text='ファイル選択', font=('', 14), height=2)
        button.bind('<ButtonPress>', self.file_dialog)
        button.pack(padx=20, anchor=tk.W)

        # ファイル名表示
        label = tk.Label(self.root, text="ファイル名：", font=('', 12))
        label.pack(padx=20, anchor=tk.W)
        label = tk.Label(textvariable=self.file_name, font=('', 12))
        label.pack(padx=20, pady=5, anchor=tk.W)

        # オプション指定のラベル
        label = tk.Label(self.root, text="オプション指定", font=('', 14))
        label.pack(padx=10, pady=10, anchor=tk.W)

        # オプション指定のチェックボックス
        checkbox = tk.Checkbutton(self.root, text="1つのファイルに出力 (デフォルトはグループ毎の複数ファイル)", font=('', 12), variable=self.singlefile)
        checkbox.pack(padx=20, pady=0, anchor=tk.W)
        checkbox = tk.Checkbutton(self.root, text="入力ファイルの文字コードがUTF-8 (デフォルトはシフトJIS)", font=('', 12), variable=self.encodeIsUtf8)
        checkbox.pack(padx=20, pady=0, anchor=tk.W)
        checkbox = tk.Checkbutton(self.root, text="半角カナを全角に変換しない (デフォルトは変換)", font=('', 12), variable=self.han2han)
        checkbox.pack(padx=20, pady=0, anchor=tk.W)

        # デフォルトに戻すボタン
        button = tk.Button(self.root, text='デフォルトに戻す', font=('', 12))
        button.bind("<Button-1>", self.checkBoxClear)
        button.pack(padx=20, pady=5, anchor=tk.W)

        # フレーム
        frame = tk.Frame(self.root, relief=tk.RIDGE, bd=0)
        # 変換実行ボタン
        self.buttonSubmit = tk.Button(frame, text='変換実行', font=('', 18), width=10, height=3)
        self.buttonSubmit['state'] = tk.DISABLED
        self.buttonSubmit.bind("<Button-1>", self.startConvert)
        self.buttonSubmit.pack(padx=5, pady=10, anchor=tk.W, side=tk.LEFT)
        # キャンセルボタン
        button = tk.Button(frame, text='キャンセル', font=('', 18), width=10, height=3)
        button.bind('<Button-1>', self.cancel)
        button.pack(padx=5, pady=10, anchor=tk.W, side=tk.LEFT)

        frame.pack(padx=30, pady=10, anchor=tk.W)

        self.root.mainloop()

    def file_dialog(self, event):
        '''
        ファイル選択のダイアログ
        '''
        fTyp = [("", "*")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        selected_filename = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
        if len(selected_filename) == 0:
            # ダイアログで何も選択せず
            pass
        else:
            # ダイアログで選択した場合、変数に反映する
            self.file_name.set(selected_filename)
        
        if self.file_name.get() == '(未選択)':
            # ファイル名未選択なら、変換実行ボタンは無効
            self.buttonSubmit['state'] = tk.DISABLED
        else:
            # ファイル名未選択なら、変換実行ボタンは有効
            self.buttonSubmit['state'] = tk.NORMAL

    def checkBoxClear(self, event):
        '''
        チェックボックスの値をデフォルトに戻す
        '''
        self.singlefile.set(False)
        self.encodeIsUtf8.set(False)
        self.han2han.set(False)
    
    def startConvert(self, event):
        '''
        変換実行
        '''
        if self.buttonSubmit['state'] == tk.DISABLED:
            # ボタンが無効なら、処理もNOP
            return

        # ボタン無効化
        self.buttonSubmit['state'] = tk.DISABLED

        try:
            encodeValue = 'utf-8' if self.encodeIsUtf8.get() else 'cp932'

            # 変換実行
            out_files = rakuraku_vcf_conv.convVCF(
                                                    self.file_name.get(),
                                                    han2han=self.han2han.get(),
                                                    encode=encodeValue,
                                                    divfile=(not self.singlefile.get()),
                                                    stdout=False
                                                )
            tk.messagebox.showinfo('','完了しました\n\n' + '出力ファイル名一覧:\n' + '\n'.join(out_files))

        except Exception as e:
            tk.messagebox.showwarning('エラー',e)

        # 画面終了
        self.quit()

    def cancel(self, event):
        '''
        キャンセルボタン押下
        '''
        # 画面終了
        self.quit()

    def getFileName(self):
        '''
        退避してあるファイル名を取り出す
        '''
        return self.file_name.get()

    def quit(self):
        '''
        画面終了
        '''
        self.root.destroy()

# main
if __name__ == "__main__":
    tk = TkinterClass()
    sys.exit(0)
