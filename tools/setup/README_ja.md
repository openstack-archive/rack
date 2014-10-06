# RACKのデプロイ方法

ここではRACKのデプロイ方法について説明します。

OpenStack環境が手元にない、あるいは手軽に試してみたいという場合は、[devstackを使ってRACKを試す](#procedure2)の手順をご覧ください。


## デプロイ手順

### 1. 前提事項

RACKを利用するに当たり、以下の各OpenStackサービスが起動している必要があります。
バージョンは`icehouse`を想定しています。
各サービスのバックエンドの構成については特に指定はなく、基本的には各サービスのAPIが提供されていれば動作可能です。

また、`CentOS-6.5`のGlanceイメージが登録されている必要があります。

| Service  | API version |
| -------- |:-----------:|
| Nova     | v2          |
| Neutron  | v2          |
| Glance   | v1          |
| Keystone | v2.0        |
| Swift    | v1          |


### 2. 構成

RACKは大きく２つの役割に別れており、`rack-api`と`rack-proxy`から構成されます。
`rack-proxy`はプロセスグループごとに起動され、中央の`rack-api`が持つデータベースを共有するという構成を取ります。
`rack-api`と`rack-proxy`はそれぞれVMとして起動されます。

![network-topology](network-topology.png "network-topology")


### 3. デプロイ手順

#### 3.1. Glanceイメージの作成

`rack-api`と`rack-proxy`は同じGlanceイメージから起動されます。
ただし、起動条件を変えることにより、どちらか一方のサービスを提供するVMとして起動します。

まずは、HorizonもしくはNova CLIからVMを起動してください。
`CentOS-6.5`ベースのGlanceイメージを使用し、VMがDNSサーバにて名前解決できる必要があります。

VMが起動したらrootユーザでログインし、以下のコマンドを順に実行してください。
`imagebuild.sh`スクリプトは、`rack-api`の動作に必要なパッケージのインストール、設定等を一括で行います。

```
# git clone https://github.com/stackforge/rack
# cd rack/tools/setup
# ./imagebuild.sh
Start RACK image building...
...

****************************************
Finish RACK image building.
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


#### 3.2. 仮想ネットワークの作成

`rack-api`VMが接続する仮想ネットワークを作成します。
HorizonもしくはNeutron CLIを利用し、以下の条件を満たす仮想ネットワークを作成してください。

* インターネットに接続可能な仮想ルータに接続されている
* DNSサーバが登録されている


#### 3.3. セキュリティグループの作成

`rack-api`VMは以下のポートを公開します。
HorizonもしくはNeutron CLIを利用し、外部からこれらのポートに接続可能となるように、セキュリティグループを作成してください。

| Port  | Service           |
|:-----:| ----------------- |
| 8088  | APIサービス        |
| 3306  | MySQLサービス      |


#### 3.4. rack-apiVMの起動

`rack-api`VMを起動します。
Nova CLIを利用し、以下のコマンドを実行してください。
なお、ここでメタデータとして指定しているOpenStackの認証情報は、rack-apiVMの設定ファイルに書き込まれます。

```
# nova boot \
  --flavor {2GB以上のメモリー推奨} \
  --image {手順3.1で作成したイメージ} \
  --nic net-id={手順3.2で作成したネットワーク} \
  --meta os_username={Keystone認証用のユーザ名} \
  --meta os_password={Keystone認証用のパスワード} \
  --meta os_tenant_name={Keystone認証用のテナント名} \
  --meta os_auth_url={Keystone APIのURL} \
  --meta os_region_name={リージョン名}
  rack-api
```

VMが起動したら、`rack-api`サービスが正常に動作しているかどうか確認します。
ここではRACK CLIを使用します。
RACK CLIの導入方法については[**こちら**](https://github.com/stackforge/python-rackclient)をご覧ください。

```
$ export RACK_URL=http://{rack-apiVMのIPアドレス}:8088/v1
$ rack group-list
+-----+------+-------------+--------+
| gid | name | description | status |
+-----+------+-------------+--------+
+-----+------+-------------+--------+
```



## <a name="procedure2">devstackを使ってRACKを試す</a>

**準備中**
