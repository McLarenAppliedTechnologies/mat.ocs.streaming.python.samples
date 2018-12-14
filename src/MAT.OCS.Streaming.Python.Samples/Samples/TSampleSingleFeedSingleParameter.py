import uuid
from mat.ocs.streaming import (AasSerializer, AasDeserializer, KafkaAasConsumer,
                               KafkaAasProducer, MessageInput, Key, KeyType,
                               DependencyServer, FormatState)
from mat.ocs.streaming.models import TSamples


class TSampleSingleFeedSingleParameter:
    """Receive a tsample message and publish it on a different topic."""

    def __init__(
            self,
            consumer: KafkaAasConsumer,
            producer: KafkaAasProducer,
            key_uid: uuid,
            formats: FormatState,
            subscribe_topic_name: str,
            send_topic_name: str
    ):

        """
        Init method.

        Args:
            consumer (KafkaAasConsumer):
                KafkaAasConsumer object to coordinate the receiving of Kafka
                messages.

            producer (KafkaAasProducer):
                KafkaAasProducer object to coordinate the producing of
                Kafka messages.

            key_uid (UUID):
                UUID for the key of the message that is send by this demo.

            formats (FormatState):
                FormatState object used to persist the hash values of the
                Atlas Configuration and Data Format, for reuse when sending
                other message types (e.g. session messages).

            subscribe_topic_name (str):
                Name of Kafka topic that this demo subscribes to.

            send_topic_name (str):
                Name of Kafka topic that this demo sends messages on.

        """
        self.consumer = consumer
        self.producer = producer
        self.key_uid = key_uid
        self.formats = formats
        self.send_topic_name = send_topic_name

        # Create message dispatcher and link to callback functions
        self.dispatcher = MessageInput()
        self.dispatcher.tsamples.on_new_message(self.process_tsample_message)

        # Subscribe to the topic.
        self.consumer.subscribe({subscribe_topic_name: self.dispatcher})

    def process_tsample_message(self, tsample):

        # Received Pandas DataFrames (one for each parameter) are in
        # tsample.dataframes
        # This is where you can insert your model to use the DataFrame.
        # Then use your model's output to create the tx_value (below).

        tx_value = TSamples(dataframes=tsample.dataframes)
        tx_value.populate_data_format(server)
        # tx_value.populate_atlas_config(server)  # Not supported yet

        tx_key = Key(KeyType.tsamples, key_uid)
        tx_key, tx_value = producer.serialize(key_value=(tx_key, tx_value))
        tx_key, tx_value = producer.encode(key_dict=(tx_key, tx_value))

        producer.send_message(key=tx_key, msg=tx_value, topic=self.send_topic_name)

    @staticmethod
    def run():
        for msg in consumer:
            rx_key, rx_value = consumer.decode(msg)
            rx_key, rx_value = consumer.deserialize(key_value=(rx_key, rx_value))
            consumer.callbacks[msg.topic]((rx_key, rx_value))
            print('.', end='')


if __name__ == '__main__':

    # Populate these constants with the correct values for your project.
    DEPENDENCY_SERVER_URI = 'http://10.228.4.9:8180/api/dependencies'
    DEPENDENCY_GROUP = 'dev'
    KAFKA_IP = '10.228.4.22:9092'
    SUBSCRIBE_TOPIC_NAME = 'MIST'
    SEND_TOPIC_NAME = 'jonathan_test_1'

    server = DependencyServer(DEPENDENCY_SERVER_URI, DEPENDENCY_GROUP)

    producer = KafkaAasProducer(
        bootstrap_servers=KAFKA_IP,
        serializer=AasSerializer(server),
    )

    consumer = KafkaAasConsumer(
        deserializer=AasDeserializer(dependency_server=server),
        bootstrap_servers=KAFKA_IP,
    )

    key_uid = uuid.uuid4()

    # Container to store Atlas configuration and data format hash values
    formats = FormatState()

    demo = TSampleSingleFeedSingleParameter(consumer, producer, key_uid, formats,
                                            SUBSCRIBE_TOPIC_NAME, SEND_TOPIC_NAME)

    demo.run()
