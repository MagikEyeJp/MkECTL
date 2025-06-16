# Pi Camera Capture Specification

このドキュメントでは、評価用画像を取得するためのスクリプト言語の仕様をまとめます。

## 新機能
- Lark を用いた構文解析による DSL インタープリタを追加しました。
- 変数、数式、ループ、ユーザー定義関数を利用できます。

## サンプル
```dsl
set x, 3
function demo(n){
    for i in range(0, n){
        mov 0, i*10, 0
    }
}
demo(x)
```
