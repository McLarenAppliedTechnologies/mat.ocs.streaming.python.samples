# ATLAS Advanced Streaming Samples

Table of Contents
=================
<!--ts-->
* [Introduction - MAT.OCS.Streaming library](/README.md)
* [Python Samples](/README.md)
* [Model sample](/src/Models/README.md)

<!--te-->

# Introduction - MAT.OCS.Streaming Library

This API provides infrastructure for streaming data around the ATLAS technology platform. 

Using this API, you can: 
* Subscribe to streams of engineering values - no ATLAS recorder required 
* Inject parameters and aggregates back into the ATLAS ecosystem 
* Build up complex processing pipelines that automatically process new sessions as they are generated 

With support for Apache Kafka, the streaming API also offers: 
* Late-join capability - clients can stream from the start of a live session 
* Replay of historic streams 
* Fault-tolerant, scalable broker architecture 

## API Documentation
See [v1.8 documentation](https://mclarenappliedtechnologies.github.io/mat.atlas.advancedstreams-docs/1.8/)

## Knowledgebase
Be sure to look at our support knowledgebase on Zendesk: https://mclarenappliedtechnologies.zendesk.com/

## Scope
This pre-release version of the API demonstrates the event-based messaging approach, for sessions and simple telemetry data. 

Future versions will model all ATLAS entities, and likely offer better support for aggregates and predictive models. 

## Requirements
You need to install the following PIP packages from [MAT source](https://artifactory-elb.core.mat.production.matsw.com/artifactory/pypi-local/mat.ocs.streaming/)

* MAT.OCS.Streaming==1.5.3.7rc0

pip install --index-url https://artifactory-elb.core.mat.production.matsw.com/artifactory/api/pypi/pypi-virtual/simple/ mat.ocs.streaming==1.5.3.7rc0 

# Python Samples
## Basic samples
Basic samples demonstrate the simple usage of Advanced Streams, covering all the bare-minimum steps to implement Telematry Data and Telemetry Samples read and write to and from Kafka or Mqtt streams.

## Read
First of all you need to configure the [dependencies]
(https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L11-L20)
```python
DEPENDENCY_SERVER_URI = 'http://10.228.4.9:8180/api/dependencies'
DEPENDENCY_GROUP = 'dev'
KAFKA_IP = '10.228.4.22:9092'
TOPIC_NAME = 'samples_test_topic'

dependency_client = HttpDependencyClient(DEPENDENCY_SERVER_URI, DEPENDENCY_GROUP)
data_format_client = DataFormatClient(dependency_client)
kafka_client = KafkaStreamClient(kafka_address=KAFKA_IP,
                                    consumer_group=DEPENDENCY_GROUP)
```

The dependency_client is used to handle requests for AtlasConfigurations and DataFormats. You must provide an URI for this service. 
The data_format_client handles the data formats through the dependency_client for the given group name.

Create a stream pipeline using the kafka_client and the TOPIC_NAME. Stream the messages [.Into your handler method](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L36)
```python
pipeline: StreamPipeline = kafka_client.stream_topic(TOPIC_NAME).into(stream_input_handler)
```

Within your [stream_input_handler method](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L29)
```python
def stream_input_handler(stream_id: str) -> StreamInput:
    print("Streaming session: " + stream_id)
```
Create a [SessionTelemetryDataInput](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L31-L32) with the actual stream id and the dataFormatClient 
```python
telemetry_input = SessionTelemetryDataInput(stream_id=stream_id, data_format_client=data_format_client)
```

### Read Telemetry Data
In this example we [bind the **data_input** to the handler method](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L33) using the default feed and simply [print out some details](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataRead.py#L22-L27) about the incoming data.

```python
def print_data(sender, event_args: TelemetryDataFeedEventArgs):
    tdata: TelemetryData = event_args.buffer.get()
    print(len(tdata.parameters))
    print('tdata for {0} with length {1} received'.format(
        str(event_args.message_origin.stream_id),
        str(len(tdata.time))))

telemetry_input.data_input.bind_default_feed("").data_buffered += print_data

```

### Read Telemetry Samples
In this example we [bind the **samples_input** to the handler method](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TSamplesRead.py#L34) and simply [print out some details](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TSamplesRead.py#L23-L27) 
```python
def print_samples(sender, event_args: TelemetryEventArgs):
    s: TelemetrySamples = event_args.data
    print('tsamples for {0} with {1} parameters received'.format(
        str(event_args.message_origin.stream_id),
        str(len(s.parameters.keys()))))

telemetry_input.samples_input.autobind_feeds += print_samples
```

You can optionally handle the stream_finished event.
```python
telemetry_input.stream_finished += lambda x, y: print('Stream finished')
```


## Write
First of all you need to configure the [dependencies](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L33-L66)
```python
"""Setup details"""
# Populate these constants with the correct values for your project.
DEPENDENCY_SERVER_URI = 'http://10.228.4.9:8180/api/dependencies'
DEPENDENCY_GROUP = 'dev'
KAFKA_IP = '10.228.4.22:9092'
TOPIC_NAME = 'samples_test_topic'

frequency = 100
"""Create a dependency client"""
dependency_client = HttpDependencyClient(DEPENDENCY_SERVER_URI, DEPENDENCY_GROUP)

"""Create Atlas configurations"""
atlas_configuration_client = AtlasConfigurationClient(dependency_client)
atlas_configuration = AtlasConfiguration({"Chassis":
    ApplicationGroup(groups={"State":
        ParameterGroup(parameters={"vCar:Chassis":
            AtlasParameter(name="vCar")})})})

atlas_configuration_id = atlas_configuration_client.put_and_identify_atlas_configuration(atlas_configuration)

"""Create Dataformat"""
parameter: DataFeedParameter = DataFeedParameter(identifier="vCar:Chassis", aggregates_enum=[Aggregates.avg])
parameters: List[DataFeedParameter] = [parameter]
feed = DataFeedDescriptor(frequency=frequency, parameters=parameters)

feed_name = ""
data_format = DataFormat({feed_name: feed})

data_format_client = DataFormatClient(dependency_client)
data_format_id = data_format_client.put_and_identify_data_format(data_format)

"""Create a Kafka client"""
client = KafkaStreamClient(kafka_address=KAFKA_IP,
                            consumer_group=DEPENDENCY_GROUP)
```

The dependency_client is used to handle requests for AtlasConfigurations and DataFormats. You must provide an URI for this service. 
The data_format_client handles the data formats through the dependency_client for the given group name.
DataFormat is required when writing to stream, as it is used to define the structre of the data and data_format_id is used to retrieve dataformat from the dataFormatClient.

AtlasConfigurationId is needed only if you want to display your data in Atlas10.

[Open the output topic](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L68-L69) using the preferred client (KafkaStreamClient or MqttStreamClient) and the topicName.
```python
output: SessionTelemetryDataOutput = None
with client.open_output_topic(TOPIC_NAME) as output_topic:
	...
```

[Create a SessionTelemetryDataOutput](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L71-L73) and configure session output [properties](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L75-L84).
```python
try:
    output = SessionTelemetryDataOutput(output_topic=output_topic,
                                        data_format_id=data_format_id,
                                        data_format_client=data_format_client)

    output.session_output.add_session_dependency(
        DependencyTypes.atlas_configuration, atlas_configuration_id)
    output.session_output.add_session_dependency(
        DependencyTypes.data_format, data_format_id)

    output.session_output.session_state = StreamSessionState.Open
    output.session_output.session_start = datetime.utcnow()
    output.session_output.session_identifier = "test_" + str(datetime.utcnow())
    output.session_output.session_details = {"test_session": "sample test session details"}
    output.session_output.send_session()

	....


except Exception as e:
    print(e)
    if output is not None:
        output.session_output.session_state = StreamSessionState.Truncated
finally:
    if output is not None:
        output.session_output.send_session()
```

Open the session within a Try Except block and handle sesseion status sending as shown above.
You must add data_format_id and atlas_configuration_id to session dependencies to be able to use them during the streaming session.


### Write Telemetry Data

[Bind the feed to **output.data_output**](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L86) by its name. You can use the default feedname or use a custom one.
```python
output_feed: TelemetryDataFeedOutput = output.data_output.bind_default_feed()
```

You will need **TelemetryData** to write to the output. In this example we [generate some random TelemetryData](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L88-L915) for the purpose of demonstration.
```python
data: TelemetryData = output_feed.make_telemetry_data(samples=10, epoch=to_telemetry_time(datetime.utcnow()))
data = generate_data(data, frequency)
```

[send](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L94) the telemetry data.
```python
output_feed.send(data)
```

### Write Telemetry Samples
You will need **TelemetrySamples** to write to the output. In this example we [generate some random telemetrySamples](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.samples/blob/f9f66fa96aaa51a4ec24bf921461918b3771d929/src/MAT.OCS.Streaming.Samples/Samples/Basic/TSamples.cs#L123) for the purpose of demonstration.
```python
telemetry_samples = generate_samples(sample_count=10, session_start=datetime.utcnow(), parameter_id="vCar:Chassis", frequency=frequency)
```

[Bind the feed to **output.samples_output**](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TSamplesWrite.py#L98-L99) by its name. You can use the default feedname or use a custom one.
```python
output_feed: TelemetrySamplesFeedOutput = output.samples_output.bind_feed(feed_name="")
```

[Send Samples](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TSamplesWrite.py#L101).
```python
output_feed.send(telemetry_samples)
```


Once you sent all your data, don't forget to [set the session state to closed](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L95) 
```python
output.session_output.session_state = StreamSessionState.Closed
```

and [send the session details](https://github.com/McLarenAppliedTechnologies/mat.ocs.streaming.python.samples/blob/develop/src/TDataWrite.py#L100-L102) or do it in the finally block as recommended above.
```python
output.SessionOutput.SendSession(); // send session
```
