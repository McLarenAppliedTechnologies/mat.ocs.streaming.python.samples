from mat.ocs.streaming.IO.SessionTelemetryDataInput import SessionTelemetryDataInput
from mat.ocs.streaming.TelemetryDataFeedEventArgs import TelemetryDataFeedEventArgs
from mat.ocs.streaming.clients.DataFormatClient import DataFormatClient
from mat.ocs.streaming.clients.KafkaStreamClient import KafkaStreamClient
from mat.ocs.streaming import (HttpDependencyClient)
from mat.ocs.streaming.models import TelemetryData
from mat.ocs.streaming.clients.pipeline.stream_input import StreamInput
from mat.ocs.streaming.clients.pipeline.stream_pipeline import StreamPipeline

if __name__ == '__main__':
    """Setup details"""
    DEPENDENCY_SERVER_URI = 'http://localhost:8180/api/dependencies'
    DEPENDENCY_GROUP = 'dev'
    KAFKA_IP = 'localhost:9092'
    TOPIC_NAME = 'test_topic'

    dependency_client = HttpDependencyClient(DEPENDENCY_SERVER_URI, DEPENDENCY_GROUP)
    data_format_client = DataFormatClient(dependency_client)
    kafka_client = KafkaStreamClient(kafka_address=KAFKA_IP, consumer_group=DEPENDENCY_GROUP)

    def print_data(sender, event_args: TelemetryDataFeedEventArgs):
        tdata: TelemetryData = event_args.buffer.get()
        print(len(tdata.parameters))
        print('data for ' + str(event_args.message_origin.stream_id) + ' with length ' + str(len(tdata.time)))


    def stream_input_handler(stream_id: str) -> StreamInput:
        print("Streaming session: " + stream_id)
        telemetry_input = SessionTelemetryDataInput(stream_id=stream_id, data_format_client=data_format_client)
        telemetry_input.data_input.bind_default_feed("").data_buffered += print_data
        return telemetry_input

    pipeline: StreamPipeline = kafka_client.stream_topic(TOPIC_NAME).into(stream_input_handler)

