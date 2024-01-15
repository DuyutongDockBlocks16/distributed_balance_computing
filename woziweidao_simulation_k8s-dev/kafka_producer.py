import kafka_setting
from kafka import KafkaProducer
# from confluent_kafka import Producer
from queue import Queue

from stats.base_stat import BaseStat


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


@singleton
class Kafka_Producer:

    def __init__(self):
        self.conf = kafka_setting.producer_setting
        self.producer = KafkaProducer(bootstrap_servers=self.conf['bootstrap_servers'],
                                      sasl_mechanism='PLAIN',
                                      security_protocol='SASL_PLAINTEXT',
                                      api_version=(0, 11),
                                      linger_ms=5000,
                                      # acks=-1,
                                      # value_serializer='org.apache.kafka.common.serialization.StringSerializer',
                                      sasl_plain_username=self.conf['sasl_plain_username'],
                                      sasl_plain_password=self.conf['sasl_plain_password'],
                                      # batch_size=24576,
                                      compression_type='gzip'
                                      )
        self.producer_closed_q = Queue(maxsize=5)

    def send(self, topic, key, value):
        self.producer.send(topic=topic, key=key, value=value).add_callback(self.on_send_success, value).add_errback(
            self.on_send_error, value)
        # # if '10000029' in str(value):
        # # if '"source_card_pos": 1' in str(value):
        #     if topic=='HB2198_wzwd_nm_battlelog_Battle':
        #         print(value)

    def send_get(self, topic, key, value):
        return self.producer.send(topic=topic, key=key, value=value).get()
        # print(f'topic: {topic}, value: {value}')

    def on_send_success(self, value, record_metadata):
        pass

    # TODO 立即关闭producer，线程安全，只关闭一次
    def on_send_error(self, value, excp):
        if (self.producer_closed_q.empty()):
            a_index = str(value, encoding='ascii').split('\001')[0]
            b_index = str(value, encoding='ascii').split('\001')[1]
            random_seed = str(value, encoding='ascii').split('\001')[2]
            battle_info = BaseStat.FIELDS_TERMINATED.join([a_index, b_index, random_seed])
            print(f'---- kafka_send_response_error occur! battle_info: {battle_info}, Exception: {repr(excp)}')
            self.producer.close(0)
            self.producer_closed_q.put(1)

    def flush(self):
        self.producer.flush()