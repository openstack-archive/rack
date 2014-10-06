# 分散シェルライクアプリケーション

ここではRACKを活用した分散アプリケーションプログラムの例の一つを紹介します。
本アプリケーションは、シェルのワンライナーを、分散クラスター上で実行します。
RACKの思想を取り入れた、ユニークなアプリケーションです。


## シェルの実行フロー

通常、シェルワンライナーというと、

```
$ cat /input/file.txt | grep -i "foo" | sed -e "s/bar/hoge/g"
```

というようなものを想像するでしょう。
このコマンドの実行フローを詳述すると、
まず`bash`プロセスから`cat`プロセス、`grep`プロセス、`sed`プロセスが`fork`され、それぞれのプロセスの標準入力と標準出力がパイプで繋がれます。
そして、`cat`プロセスから出力された文字列がパイプを伝って`grep`プロセスに渡され、`grep`による検索処理が行われます。
さらに、`grep`プロセスの出力はまたパイプを伝って`sed`プロセスに渡され、`sed`による置換処理が行われたあと標準出力に出力されます。
当然ですが、この一連の処理は**1台のコンピュータ上で行われます**。


## RACKを活用したシェルワンライナーの分散実行

今回我々が作成したアプリケーションは、シェルワンライナーを複数のVMで分散実行させるというものです。
RACKを使ってこれを実現すると、例えば以下のようになります。

まず、入力となるファイルは、あらかじめRACKが提供するファイルシステムに保存しておきます。
そして、`bash`の役割を担う親プロセス(VM)を起動します。
このとき、ファイルが保存されているディレクトリ(例えば`/input`)と出力先のディレクトリ(例えば`/output`)、コマンド(例えば`grep -i "foo" | sed -e "s/bar/hoge/g"`)をオプションとして与えます。
次に、起動した親プロセスは、コマンドを実行する役割を担う子プロセス(VM)を`fork`します。
ここでは`grep -i "foo"`というコマンドを実行する子プロセス(VM)と、`sed -e "s/bar/hoge/g"`というコマンドを実行する子プロセス(VM)を起動します。
子プロセス(VM)間の処理結果の受け渡しは、RACKが提供するパイプによって行います。
最後に、`sed`コマンドを実行した子プロセス(VM)は、処理結果をファイルシステムに保存します。

親プロセスには、複数の入力ファイルを並列に処理するために、起動するクラスタ数をオプションとして指定することができます。
例えば、クラスタ数を2とした場合、`grep`コマンドを実行するプロセスと`sed`コマンドを実行するプロセスの組(クラスタ)が2つ起動されます。
入力ディレクトリに4つのファイルがある場合、各クラスタは2ファイルずつ処理することになります。
クラスタ数を増やせば増やすほど、全体の処理速度が向上します。


## 新しいアプリケーションの可能性

RACKを使えば、1台のVMでは処理するデータ量が多すぎて時間がかかってしまう処理も、上記の例のように複数のVMに処理を分散してあげれば、高速に処理することが可能です。
また、あるVMで処理した結果を別のVMに渡して別の処理をさせるといったことも、RACKが提供するパイプを利用すれば、IPアドレスを調べたり、渡す相手が起動しているか確認するなどの煩わしい処理をすることなしに実現可能です。

RACKは、既存の枠にとらわれない新しいアプリケーションを開発できる可能性を秘めているのです。


![shell](shell.png "shell")


## アプリケーションの実行準備

### 1. Glanceイメージの作成

親プロセス、子プロセスは共に同じGlanceイメージから起動します。
起動時に自身に親プロセスが存在するかどうかを確認することにより、振る舞いを変えるようにしています。

まずは、HorizonもしくはNova CLIからVMを起動してください。
`CentOS-6.5`ベースのGlanceイメージを使用し、VMがDNSサーバにて名前解決できる必要があります。

VMが起動したらrootユーザでログインし、以下のコマンドを順に実行してください。
`imagebuild.sh`スクリプトは、動作に必要なパッケージのインストール、設定等を一括で行います。

```
# git clone https://github.com/stackforge/rack
# cd rack/tools/sample-apps/shell-vm
# ./imagebuild.sh
Start image building...
...

****************************************
Finish image building.
Shutdown and save snapshot of this instance via Horizon or glance command.
****************************************
```

上記のメッセージが表示されたら完了です。
VMをシャットダウンし、HorizonもしくはGlance CLIで**スナップショットを作成してください**。

下記のようなメッセージが出ていたら、スクリプトは処理を完了していません。
問題を解決し、再度`imagebuild.sh`を実行してください。

```
****************************************
Error occurred. Execution aborted.
Error: Installing the required packages
****************************************
```


### 2. プロセスグループの初期化

本アプリケーションを動作させるための環境を用意します。
事前に`rack-api`が起動している必要があります。
`rack-api`の準備については[**こちら**](https://github.com/stackforge/rack/blob/master/tools/setup/README_ja.md)をご覧ください。

RACK CLIを導入したマシン上で、グループ初期化用の設定ファイルを作成します。
RACK CLIの導入方法については[**こちら**](https://github.com/stackforge/python-rackclient)をご覧ください。

以下の空欄になっている部分はご自身の環境に合わせて記載してください。

**group.conf**
```
[group]
name =

[keypair]
is_default = True

[network]
cidr =
ext_router_id =
dns_nameservers =

[securitygroup]
rules =
    protocol=tcp,port_range_max=8080,port_range_min=8080,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8088,port_range_min=8088,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8888,port_range_min=8888,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=6379,port_range_min=6379,remote_ip_prefix=0.0.0.0/0

is_default = True

[proxy]
nova_flavor_id =
glance_image_id =
```

以下のコマンドでプロセスグループを初期化します。

```
$ export RACK_URL=http://{rack-apiVMのIPアドレス}:8088/v1
$ rack group-init group.conf
...
+------------------+--------------------------------------+
| Property         | Value                                |
+------------------+--------------------------------------+
| gid              | d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d |
| keypair_id       | 4ae497df-4f41-4cc3-bb11-14f7d8fff0ef |
| network_id       | f1cff914-c9e8-4a8e-ba51-4f0481680c89 |
| proxy pid        | 8377f985-6b68-4eb5-a0c0-502cc06a4edd |
| securitygroup_id | 2e965967-2f43-4a1b-9aa2-1e9e321ecbd7 |
+------------------+--------------------------------------+
```

しばらくすると、`rack-proxy`VMが起動します。
`rack-proxy`の動作確認のため、以下のコマンドを実行してください。

```
$ rack --rack-url http://{rack-proxyVMのIPアドレス}:8088/v1 group-list
+--------------------------------------+---------+-------------+--------+
| gid                                  | name    | description | status |
+--------------------------------------+---------+-------------+--------+
| d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d | test    | None        | ACTIVE |
+--------------------------------------+---------+-------------+--------+
```

これでプロセスグループの初期化は完了です。


### 3. アプリケーションの実行

#### 3.1. 入力ファイルの準備

アプリケーションを実行する前に、入力ファイルを準備する必要があります。
テキストファイルであればどのような内容でも構いません。
ここでは4つのファイル `file1.txt`、`file2.txt`、`file3.txt`、`file4.txt`を用意することを想定します。
ファイルは`rack-proxy`VMが提供する`file system`に保存します。
以下のコマンドを実行し、用意したファイルを保存してください。

```
$ rack file-put --proxy_ip {rack-proxyVMのIPアドレス} /input/file1.txt file1.txt
$ rack file-put --proxy_ip {rack-proxyVMのIPアドレス} /input/file2.txt file2.txt
$ rack file-put --proxy_ip {rack-proxyVMのIPアドレス} /input/file3.txt file3.txt
$ rack file-put --proxy_ip {rack-proxyVMのIPアドレス} /input/file4.txt file4.txt
```

#### 3.2. アプリケーションの実行

アプリケーションの実行方法は非常にシンプルです。
手順1で作成したGlanceイメージに対してオプションを指定して起動するだけです。

RACK CLIでは`--args`というオプションによってアプリケーションに任意のパラメータを指定することができます。
ここではパラメータとして`command`と`stdin`、`stdout`、`cluster`を指定します。

`command`にはシェルのワンライナーを指定します。
手順1で作成したOSが備えているコマンドであれば何でも構いませんが、
ここではわかりやすい例として`grep -i "foo" | sed -e "s/bar/hoge/g"`を指定します(foo,bar,hogeは自由に変更してください)。
`stdin`には手順3.1で用意したファイルの保存先ディレクトリ(ここでは`/input`)を指定します。
`stdout`にはアプリケーションの実行結果の出力先ディレクトリを指定します。
`cluster`には起動するクラスタ数を指定します。

それでは以下のコマンドを実行し、アプリケーションを起動してください。
環境変数`RACK_GID`には先ほど作成したグループの`gid`を指定してください。

```
$ export RACK_GID=d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d
$ rack process-create \
  --nova_flavor_id {任意のフレーバーID} \
  --glance_image_id {手順1で作成したGlanceイメージのID} \
  --args command='grep -i "foo" | sed -e "s/bar/hoge/g"',stdin=/input,stdout=/output,cluster=2
```

正常に処理が完了すると、すべてのプロセスは削除されます。
処理の結果は`file system`に保存されているので、
以下のコマンドでファイルを取得してください。

```
$ rack file-get --proxy_ip {rack-proxyVMのIPアドレス} /input/file1.txt
$ rack file-get --proxy_ip {rack-proxyVMのIPアドレス} /input/file2.txt
$ rack file-get --proxy_ip {rack-proxyVMのIPアドレス} /input/file3.txt
$ rack file-get --proxy_ip {rack-proxyVMのIPアドレス} /input/file4.txt
```

