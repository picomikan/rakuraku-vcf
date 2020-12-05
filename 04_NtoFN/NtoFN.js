//初期値
var text = document.getElementById('inputText');
text.value = 'BEGIN:VCARD\nVERSION:3.0\nN:山田;太郎;(旧姓田中);Mr.;さん\nX-PHONETIC-LAST-NAME:ﾔﾏﾀﾞﾀﾛｳ\nitem1.EMAIL;type=INTERNET:xxxx@ezweb.ne.jp\nitem1.X-ABLabel:_$!!$_\nTITLE:\nURL;type=HOME:\nPHOTO:\nitem3.X-ABDATE:\nitem3.X-ABLabel:_$!!$_\nitem4.X-ABDATE:\nitem4.X-ABLabel:_$!!$_\nBDAY;value=date:\nNICKNAME:\nTEL;type=OTHER;type=VOICE:09012345678\nitem2.ADR;type=OTHER:;;;;;;\nORG:\nEND:VCARD';
//HTMLエスケープ
function htmlEscape(str) {
    if (!str) return;
    return str.replace(/[<>&"'`]/g, function(match) {
      const escape = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#39;',
        '`': '&#x60;'
      };
      return escape[match];
    });
}
//変換処理
function convert() {
  text = document.getElementById("inputText").value;
  //前後の空白を削除
  text = text.replace(/^\s+/, '').replace(/\s+$/, '');
  //改行コードを統一
  text = text.replace(/\r\n|\r/g, '\n');
  //HTMLエスケープ
  text = htmlEscape(text);
  //一行毎のデータに分割
  var lines = text.split('\n');
  //行数MAX
  const maxLine = 100000;
  if (lines.length >= maxLine){
    alert("" + maxLine + "行を超過した分をカットしました");
    lines = lines.slice(0, maxLine-1);
  }
  let fn_found = false; //元からFNがあるかどうか
  let new_fn = ''; //Nから生成するFN
  let phase = 0;   //0:BEGINを探す 1:N,FN,ENDを探す
  let n_name = 0;  //Nの行番号
  for (let n in lines) {
    const line = lines[n];
    if (phase == 0){
      //BEGINチェック
      if (null != line.match(/^BEGIN:VCARD/)) {
        phase = 1;
        fn_found = false;
        new_fn = '';
        n_name = 0;
      }
    }
    else{//phase==1
      //N,FN,ENDを探す
      if (null != line.match(/^FN:.*$/)) {
        //もとからFNが存在
        fn_found = true;
      }
      else if (null != line.match(/^N:.*$/)) {
        //NからFNを作る
        n_name = n;
        if (new_fn != ''){
          //既にFN生成済み ->NOP
        }
        else if (null != line.match(/^N:[^;]*;[^;]*;[^;]*;[^;]*;.*$/)){
          //;が4個(以上)ある場合
          new_fn = line.replace(/N:([^;]*);([^;]*);([^;]*);([^;]*);(.*)/g, "FN:$4$2$3$1$5");
        }
        else if (null != line.match(/^N:[^;]*;[^;]*;[^;]*;[^;]*$/)){
          //;が3個ある場合
          new_fn = line.replace(/N:([^;]*);([^;]*);([^;]*);([^;]*)/g, "FN:$4$2$3$1");
        }
        else if (null != line.match(/^N:[^;]*;[^;]*;[^;]*$/)){
          //;が2個ある場合
          new_fn = line.replace(/N:([^;]*);([^;]*);([^;]*)/g, "FN:$2$3$1");
        }
        else if (null != line.match(/^N:[^;]*;[^;]*$/)){
          //;が1個ある場合
          new_fn = line.replace(/N:([^;]*);([^;]*)/g, "FN:$2$1");
        }
        else if (null != line.match(/^N:[^;]*$/)){
          //;がない場合
          new_fn = line.replace(/N:([^;]*)/g, "FN:$1");
        }
      }
      else if (null != line.match(/^END:VCARD/)) {
        phase = 0;
        //元からFNがないケースだけ生成する
        if (!fn_found){
          if (n_name > 0){
            lines[n_name] = lines[n_name] + "<br><span style='color:red;'>" + new_fn + "</span>";
          }
        }
      }
    }//if(phase)
  }//for
  text = lines.join('<br>');
  document.getElementById("outputText").innerHTML = text;
}
//リセット処理
function reset() {
  document.getElementById("inputText").value = '';
  document.getElementById("outputText").innerHTML = '';
}
