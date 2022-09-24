### Debezium + Kafka + Django

#### やりたいこと

* Debezium Connector経由で作成されたトピックやメッセージをKafka Topic UIで表示しつつ、検証を進めたい

#### 状況

* [x] Debezium Connector経由で作成されたトピックをKafka Topic UIで表示する
* [ ] Djangoアプリ、あるいは他のPythonアプリでkafkaトピックを元に処理する

#### 通信整理

```
[Django mysite:8000]
 |
[PostgreSQL 5432:5432]
 |
[Debezium connector for PostgreSQL 8083:8083]
 |
[Kafka 9092:9092] <- [Kafka REST 8086:8086] <- [Kafka Topic UI 8888:8000]
 |
[Zookeeper 2181:2181]
```

#### セットアップ手順

* Dockerコンテナ起動

```shell
$ docker-compose up -d
```

* Kafka Connect (Debezium)の設定追加

```shell
$ curl --location --request POST 'http://localhost:8083/connectors/' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "django-app-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.server.name": "mysite",
    "database.dbname" : "postgres", 
    "table.include.list": "public.polls_outbox",
    "transform": "outbox",
    "transform.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "value.converter": "io.debezium.converters.ByteBufferConverter",
    "value.converter.schemas.enable": "false",
    "value.converter.delegate.converter.type": "org.apache.kafka.connect.json.JsonConverter"
  }
}'
```

* Python3.10のインストール

* モジュールインストール

* protocのインストール

  * https://github.com/protocolbuffers/protobuf/releases/tag/v21.6

    * Windows: protoc-21.6-win64.zip
    * macOS: protoc-21.6-osx-x86_64.zip


[//]: # (```shell)
[//]: # ($ cd ./proto)
[//]: # ($ protoc ./question.proto --python_out=./output --descriptor_set_out=question.desc)
[//]: # ($ cp ./output/question_pb2.py ../mysite/proto)
[//]: # (```)

```shell
# 必要に応じて仮想環境作成
$ pip install -r requirements.txt
```

* Djangoのマイグレーションと起動

```shell
$ cd mysite
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py runserver
```

* 以下のURLにアクセス
  * Django Admin画面
    * http://localhost:8000/admin
  * Kafka Topic UI
    * http://localhost:8888

* Kafka Topic UIに、```mysite.public.polls_question```と```mysite.public.polls_choice```が表示されていればOK

#### Docker Composeで作成するサービス一覧

* Zookeeper
* Kafka
* PostgreSQL
* Kafka Connect
* Kafka Rest
* Kafka Topic UI
