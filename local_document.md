```shell
# ZooKeeper
$ docker run -it --rm --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 quay.io/debezium/zookeeper:1.9
# Kafka
$ docker run -it --rm --name kafka -p 9092:9092 --link zookeeper:zookeeper quay.io/debezium/kafka:1.9
# MySQL(debezium用にカスタマイズされたコンテナイメージ。debeziumユーザーが最初から存在している)
$ docker run -it --rm --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=debezium -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw quay.io/debezium/example-mysql:1.9
# MySQLコマンドラインクライアント
$ docker run -it --rm --name mysqlterm --link mysql --rm mysql:8.0 sh -c 'exec mysql -h"$MYSQL_PORT_3306_TCP_ADDR" -P"$MYSQL_PORT_3306_TCP_PORT" -uroot -p"$MYSQL_ENV_MYSQL_ROOT_PASSWORD"'
# Kafka Connect service
$ docker run -it --rm --name connect -p 8083:8083 -e GROUP_ID=1 -e CONFIG_STORAGE_TOPIC=my_connect_configs -e OFFSET_STORAGE_TOPIC=my_connect_offsets -e STATUS_STORAGE_TOPIC=my_connect_statuses --link kafka:kafka --link mysql:mysql quay.io/debezium/connect:1.9


# 8083(Kafka Connect)に対して、curlでリクエスト送信
$ curl -H "Accept: application/json" localhost:8083
# > {"version":"3.2.0","commit":"38103ffaa962ef50","kafka_cluster_id":"VEWzk4F7Tce8mCFhnaNZig"}
# 8083(Kafka Connect)に対して、コネクターのステータスを取得。connectors
$ curl -H "Accept: application/json" localhost:8083/connectors/

# MySQL Connectorのデプロイ
# MySQL Connectorは、MySQLのbinlogを参照する
# binlog - すべてのデータベーストランザクション（個々の行への変更やスキーマへの変更）が記録される
# Debeziumは変更イベントを生成する

$ curl -L -X POST 'http://localhost:8083/connectors/' \
-H 'Accept: application/json' \
-H 'Content-Type: application/json' \
--data-raw '{
  "name": "inventory-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "database.server.name": "dbserver1",
    "database.include.list": "inventory",
    "database.history.kafka.bootstrap.servers": "kafka:9092",
    "database.history.kafka.topic": "schema-changes.inventory"
  }
}'

$ curl -i -X GET -H "Accept: application/json" localhost:8083/connectors/inventory-connector


#HTTP/1.1 200 OK
#Date: Tue, 20 Sep 2022 05:52:43 GMT
#Content-Type: application/json
#Content-Length: 539
#Server: Jetty(9.4.44.v20210927)
{"name":"inventory-connector","config":{"connector.class":"io.debezium.connector.mysql.MySqlConnector","database.user":"debezium","database.server.id":"184054","tasks.max":"1","database.hostname":"mysql","database.password":"dbz","database.history.kafka.bootstrap.servers":"kafka:9092","database.history.kafka.topic":"schema-changes.inventory","name":"inventory-connector","database.server.name":"dbserver1","database.port":"3306","database.include.list":"inventory"},"tasks":[{"connector":"inventory-connector","task":0}],"type":"source"}
```

- コネクタが作成されて、開始されたことがログに出力されている
- Debezium ログ出力は、マップされた診断コンテキスト（MDC）を使用して、ログ出力にスレッド固有の情報を提供し、
  マルチスレッドで Kafka Connect サービスで何が発生しているかを理解しやすくする
- コネクタタイプ（MySQL）、コネクタ論理名（config.database.server.name）、コネクタのアクティビティ（タスク、スナップショット、binlog）が含まれる

```log
# 2022-09-20 05:50:21,297 INFO   ||  Successfully tested connection for jdbc:mysql://mysql:3306/?useInformationSchema=true&nullCatalogMeansCurrent=false&useUnicode=true&characterEncoding=UTF-8&characterSetResults=UTF-8&zeroDateTimeBehavior=CONVERT_TO_NULL&connectTimeout=30000 with user 'debezium'   [io.debezium.connector.mysql.MySqlConnector]
# 2022-09-20 05:50:21,299 INFO   ||  Connection gracefully closed   [io.debezium.jdbc.JdbcConnection]
# 2022-09-20 05:50:21,300 INFO   ||  AbstractConfig values:
#   [org.apache.kafka.common.config.AbstractConfig]
# 2022-09-20 05:50:21,302 INFO   ||  [Producer clientId=producer-3] Resetting the last seen epoch of partition my_connect_configs-0 to 0 since the associated topicId changed from null to QXU9PidOSimhRVOTTZuLhw   [org.apache.kafka.clients.Metadata]
# 2022-09-20 05:50:21,309 INFO   ||  [Worker clientId=connect-1, groupId=1] Connector inventory-connector config updated   [org.apache.kafka.connect.runtime.distributed.DistributedHerder]
# 2022-09-20 05:50:21,310 INFO   ||  [Worker clientId=connect-1, groupId=1] Rebalance started   [org.apache.kafka.connect.runtime.distributed.WorkerCoordinator]
# 2022-09-20 05:50:21,310 INFO   ||  [Worker clientId=connect-1, groupId=1] (Re-)joining group   [org.apache.kafka.connect.runtime.distributed.WorkerCoordinator]
# 2022-09-20 05:50:21,314 INFO   ||  [Worker clientId=connect-1, groupId=1] Successfully joined group with generation Generation{generationId=2, memberId='connect-1-efb74def-10ea-43e3-a057-52b838a9b306', protocol='sessioned'}   [org.apache.kafka.connect.runtime.distributed.WorkerCoordinator]
# 2022-09-20 05:50:21,320 INFO   ||  [Worker clientId=connect-1, groupId=1] Successfully synced group in generation Generation{generationId=2, memberId='connect-1-efb74def-10ea-43e3-a057-52b838a9b306', protocol='sessioned'}   [org.apache.kafka.connect.runtime.distributed.WorkerCoordinator]
# 2022-09-20 05:50:21,320 INFO   ||  [Worker clientId=connect-1, groupId=1] Joined group at generation 2 with protocol version 2 and got assignment: Assignment{error=0, leader='connect-1-efb74def-10ea-43e3-a057-52b838a9b306', leaderUrl='http://172.17.0.6:8083/', offset=2, connectorIds=[inventory-connector], taskIds=[], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0   [org.apache.kafka.connect.runtime.distributed.DistributedHerder]
# 2022-09-20 05:50:21,321 INFO   ||  [Worker clientId=connect-1, groupId=1] Starting connectors and tasks using config offset 2   [org.apache.kafka.connect.runtime.distributed.DistributedHerder]
# 2022-09-20 05:50:21,322 INFO   ||  [Worker clientId=connect-1, groupId=1] Starting connector inventory-connector   [org.apache.kafka.connect.runtime.distributed.DistributedHerder]


# 2022-09-20 05:50:21,560 INFO   MySQL|dbserver1|snapshot  Metrics registered   [io.debezium.pipeline.ChangeEventSourceCoordinator]
# 2022-09-20 05:50:21,560 INFO   MySQL|dbserver1|snapshot  Context created   [io.debezium.pipeline.ChangeEventSourceCoordinator]
# 2022-09-20 05:50:21,564 INFO   MySQL|dbserver1|snapshot  No previous offset has been found   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,564 INFO   MySQL|dbserver1|snapshot  According to the connector configuration both schema and data will be snapshotted   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,565 INFO   MySQL|dbserver1|snapshot  Snapshot step 1 - Preparing   [io.debezium.relational.RelationalSnapshotChangeEventSource]
# 2022-09-20 05:50:21,566 INFO   MySQL|dbserver1|snapshot  Snapshot step 2 - Determining captured tables   [io.debezium.relational.RelationalSnapshotChangeEventSource]
# 2022-09-20 05:50:21,566 INFO   MySQL|dbserver1|snapshot  Read list of available databases   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,568 INFO   MySQL|dbserver1|snapshot          list of available databases is: [information_schema, inventory, mysql, performance_schema, sys]   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,568 INFO   MySQL|dbserver1|snapshot  Read list of available tables in each database   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,575 INFO   MySQL|dbserver1|snapshot         snapshot continuing with database(s): [inventory]   [io.debezium.connector.mysql.MySqlSnapshotChangeEventSource]
# 2022-09-20 05:50:21,575 INFO   MySQL|dbserver1|snapshot  Adding table inventory.addresses to the list of capture schema tables   [io.debezium.relational.RelationalSnapshotChangeEventSource]
# 2022-09-20 05:50:21,575 INFO   MySQL|dbserver1|snapshot  Adding table inventory.customers to the list of capture schema tables   [io.debezium.relational.RelationalSnapshotChangeEventSource]
# 2022-09-20 05:50:21,575 INFO   MySQL|dbserver1|snapshot  Adding table inventory.orders to the list of capture schema tables   [io.debezium.relational.RelationalSnapshotChangeEventSource]
# 2022-09-20 05:50:21,575 INFO   MySQL|dbserver1|snapshot  Adding table inventory.geom to the list of capture schema tables   [io.debezium.relational.RelationalSnapshotChangeEventSource]
```

# watch-topic -a -k でトピックを監視する

# -> データベース名.テーブル名の指定が可能

```shell
$ docker run -it --rm --name watcher --link zookeeper:zookeeper --link kafka:kafka quay.io/debezium/kafka:1.9 watch-topic -a -k dbserver1.inventory.customers
```

- 主キー：1004 に対する操作をしたことを示すログ

```json
{
  "schema": {
    "type": "struct",
    "fields": [{ "type": "int32", "optional": false, "field": "id" }],
    "optional": false,
    "name": "dbserver1.inventory.customers.Key"
  },
  "payload": { "id": 1004 }
}
```

- Schema: Kafka Connect スキーマ(dbserver1.inventry.customers.Envelope)
  - op: 操作タイプを説明する文字列を含むフィールド。MySQL においては、作成・挿入の c, 更新の u, 削除の d, 読み取り(スナップショット)の r を表すものが指定される
  - before: イベントが発生する前の状態を含むオプションフィールド。
  - after: イベント発生後の行の状態を含むオプションフィールド
  - source: イベントのソースメタデータを記述する構造を含む必須フィールド。
    イベントが記録された binlog ファイルの名前、binlog ファイル内のイベント位置、影響を受けたデータベースとテーブル名、変更を行った MySQL スレッド ID、このイベントがスナップショットの一部であったかどうか
  - ts_ms

```json
{
  "schema": {
    "type": "struct",
    "fields": [
      {
        "type": "struct",
        "fields": [
          {
            "type": "int32",
            "optional": false,
            "field": "id"
          },
          {
            "type": "string",
            "optional": false,
            "field": "first_name"
          },
          {
            "type": "string",
            "optional": false,
            "field": "last_name"
          },
          {
            "type": "string",
            "optional": false,
            "field": "email"
          }
        ],
        "optional": true,
        "name": "dbserver1.inventory.customers.Value",
        "field": "before"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "int32",
            "optional": false,
            "field": "id"
          },
          {
            "type": "string",
            "optional": false,
            "field": "first_name"
          },
          {
            "type": "string",
            "optional": false,
            "field": "last_name"
          },
          {
            "type": "string",
            "optional": false,
            "field": "email"
          }
        ],
        "optional": true,
        "name": "dbserver1.inventory.customers.Value",
        "field": "after"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "string",
            "optional": false,
            "field": "version"
          },
          {
            "type": "string",
            "optional": false,
            "field": "connector"
          },
          {
            "type": "string",
            "optional": false,
            "field": "name"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "ts_ms"
          },
          {
            "type": "string",
            "optional": true,
            "name": "io.debezium.data.Enum",
            "version": 1,
            "parameters": {
              "allowed": "true,last,false,incremental"
            },
            "default": "false",
            "field": "snapshot"
          },
          {
            "type": "string",
            "optional": false,
            "field": "db"
          },
          {
            "type": "string",
            "optional": true,
            "field": "sequence"
          },
          {
            "type": "string",
            "optional": true,
            "field": "table"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "server_id"
          },
          {
            "type": "string",
            "optional": true,
            "field": "gtid"
          },
          {
            "type": "string",
            "optional": false,
            "field": "file"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "pos"
          },
          {
            "type": "int32",
            "optional": false,
            "field": "row"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "thread"
          },
          {
            "type": "string",
            "optional": true,
            "field": "query"
          }
        ],
        "optional": false,
        "name": "io.debezium.connector.mysql.Source",
        "field": "source"
      },
      {
        "type": "string",
        "optional": false,
        "field": "op"
      },
      {
        "type": "int64",
        "optional": true,
        "field": "ts_ms"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "string",
            "optional": false,
            "field": "id"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "total_order"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "data_collection_order"
          }
        ],
        "optional": true,
        "field": "transaction"
      }
    ],
    "optional": false,
    "name": "dbserver1.inventory.customers.Envelope"
  },
  "payload": {
    "before": null,
    "after": {
      "id": 1004,
      "first_name": "Anne",
      "last_name": "Kretchmar",
      "email": "annek@noanswer.org"
    },
    "source": {
      "version": "1.9.5.Final",
      "connector": "mysql",
      "name": "dbserver1",
      "ts_ms": 1663653022001,
      "snapshot": "true",
      "db": "inventory",
      "sequence": null,
      "table": "customers",
      "server_id": 0,
      "gtid": null,
      "file": "mysql-bin.000003",
      "pos": 157,
      "row": 0,
      "thread": null,
      "query": null
    },
    "op": "r",
    "ts_ms": 1663653022001,
    "transaction": null
  }
}
```

- 仮に、1004 の行の first_name を rinne_grid に変更した場合、下記 2 つのトピックが発生する

```json
{
  "schema": {
    "type": "struct",
    "fields": [{ "type": "int32", "optional": false, "field": "id" }],
    "optional": false,
    "name": "dbserver1.inventory.customers.Key"
  },
  "payload": { "id": 1004 }
}
```

```json
{
  "schema": {
    "type": "struct",
    "fields": [
      {
        "type": "struct",
        "fields": [
          { "type": "int32", "optional": false, "field": "id" },
          { "type": "string", "optional": false, "field": "first_name" },
          { "type": "string", "optional": false, "field": "last_name" },
          { "type": "string", "optional": false, "field": "email" }
        ],
        "optional": true,
        "name": "dbserver1.inventory.customers.Value",
        "field": "before"
      },
      {
        "type": "struct",
        "fields": [
          { "type": "int32", "optional": false, "field": "id" },
          { "type": "string", "optional": false, "field": "first_name" },
          { "type": "string", "optional": false, "field": "last_name" },
          { "type": "string", "optional": false, "field": "email" }
        ],
        "optional": true,
        "name": "dbserver1.inventory.customers.Value",
        "field": "after"
      },
      {
        "type": "struct",
        "fields": [
          { "type": "string", "optional": false, "field": "version" },
          { "type": "string", "optional": false, "field": "connector" },
          { "type": "string", "optional": false, "field": "name" },
          { "type": "int64", "optional": false, "field": "ts_ms" },
          {
            "type": "string",
            "optional": true,
            "name": "io.debezium.data.Enum",
            "version": 1,
            "parameters": { "allowed": "true,last,false,incremental" },
            "default": "false",
            "field": "snapshot"
          },
          { "type": "string", "optional": false, "field": "db" },
          { "type": "string", "optional": true, "field": "sequence" },
          { "type": "string", "optional": true, "field": "table" },
          { "type": "int64", "optional": false, "field": "server_id" },
          { "type": "string", "optional": true, "field": "gtid" },
          { "type": "string", "optional": false, "field": "file" },
          { "type": "int64", "optional": false, "field": "pos" },
          { "type": "int32", "optional": false, "field": "row" },
          { "type": "int64", "optional": true, "field": "thread" },
          { "type": "string", "optional": true, "field": "query" }
        ],
        "optional": false,
        "name": "io.debezium.connector.mysql.Source",
        "field": "source"
      },
      { "type": "string", "optional": false, "field": "op" },
      { "type": "int64", "optional": true, "field": "ts_ms" },
      {
        "type": "struct",
        "fields": [
          { "type": "string", "optional": false, "field": "id" },
          { "type": "int64", "optional": false, "field": "total_order" },
          {
            "type": "int64",
            "optional": false,
            "field": "data_collection_order"
          }
        ],
        "optional": true,
        "field": "transaction"
      }
    ],
    "optional": false,
    "name": "dbserver1.inventory.customers.Envelope"
  },
  "payload": {
    "before": {
      "id": 1004,
      "first_name": "Anne",
      "last_name": "Kretchmar",
      "email": "annek@noanswer.org"
    },
    "after": {
      "id": 1004,
      "first_name": "rinne_grid",
      "last_name": "Kretchmar",
      "email": "annek@noanswer.org"
    },
    "source": {
      "version": "1.9.5.Final",
      "connector": "mysql",
      "name": "dbserver1",
      "ts_ms": 1663656135000,
      "snapshot": "false",
      "db": "inventory",
      "sequence": null,
      "table": "customers",
      "server_id": 223344,
      "gtid": null,
      "file": "mysql-bin.000003",
      "pos": 401,
      "row": 0,
      "thread": 8,
      "query": null
    },
    "op": "u",
    "ts_ms": 1663656135956,
    "transaction": null
  }
}
```

- コミットログなので当然か・・・。トランザクションがロールバックされた場合は binlog に載らない(?)ため、トピックは作成されない
