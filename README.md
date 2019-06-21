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
There is a set of required steps that needs to be done, before you could actually start streaming.

 * Kafka broker address:
   * A valid and existing host name where a Kafka service is running.
 * Kafka topic name:
   * An existing topic on the Kafka broker.
 * Kafka announce topic name:
   * If your topic name is 'test_topic', then you must have a 'test_topic_announce' as well.
 * Kafka consumer group:
   * A unique group name for your consumers within the same logical group.
 * Dependency service URI:
   * Dependency service is used to store/provide dependencies, such as configuration details, data format information etc.
 * Dependency client:
   * Dependency client is used to connect to the dependency service, using the provided dependency service URI and group name.
 * Dataformat client:
   * Dataformat client is used to put/get data formats of your streamed data. For quicker access it is cacheing data formats.
 * Kafka stream client is used to connect to a Kafka service, using the provided Kafka borker address and consumer group.

#### Definitions:
##### Data Format:
Describes data feeds in terms of their parameters, frequency, and stream encoding. A Data format can contain multiple feeds, each with different name.
##### Feed:
A Feed must have a unique name and it also contains a list of parameters and a given frequency for all of them. By default it is 100hz. These are set/bind when producing the messages, and as a consumer you can bind your input message handler for a feed by its name. This could be useful if you are interested in only specific data, within a topic/stream/session.
##### Atlas Configuration:
A tree-like structure that defines the display structure of your data, using the following levels in the tree:

```python
AtlasConfiguration({"config_name":
        ApplicationGroup(groups={"group_name":
            ParameterGroup(parameters={"parameter_name":
                AtlasParameter(name="parameter_display_name")})})})
```
Of course there can be multiple of each, hence the dictionary based tree-like structure.
Atlas configuration needs to be set and put to the dependency service only if you want to display your data in Atlas10.
##### Buffer:
Telemetry Data type messages are stored in a buffer and can be accessed immediately or later, by accessing the buffer.
#### Concept of consuming streams:
There can be multiple streams simultenaously in a Kafka topic, but they can be handled separately by their stream id.
The concept is to stream a topic into a stream input handler, that receives the uniqie stream id as an input parameter.
This stream input handler is invoked when a new stream is identified in the Kafka topic and it is responsible to handle the input messages.
AAS stream messages are logically coupled within a session and you can access them by creating a SessionTelemetryDataInput object, prodiving the stream id and the DataFormat client for data parsing.
There are different messages types, and they have their own way to handle them. They can be accessed through the SessionTelemetryDataInput object.
The general concept behind accessing different type of messages is similar to C# event subscriptions. Based on the message types, they can be stored in a buffer and accessed through it, or accessed directly, but some messages types (Session, Lap, Event) are not accessible directly, but they fire specific events that can be handled.
All these message related events can be subscribed with the "+=" operator, and they pass 2 parameters to the handler method: the sender object and an event_args object, that is specific to the message type.

#### Methods and subscriptable events for accessing input messages by their types:

##### Session:
 * state_changed: Fired when the session state changed, compare to the previous state of the session.
 * dependencies_changed: Fired when the session dependencies changed, compare to the previous dependencies of the session.
 * label_changed: Fired when the session label changed, compare to the previous label of the session.
 * details_changed: Fired when the session details changed, compare to the previous details of the session.
 * identifier_changed: Fired when the session identifier changed, compare to the previous identifier of the session.
 * sources_changed: Fired when the session sources changed, compare to the previous sources of the session.
 
##### Telemetry Samples:
 * autobind_feeds:
Telemtry Samples (samples_input) input messages are neither separated by feeds nor stored in a buffer, so you can access them by subscribing to the autobind_feeds event

##### Telemetry Data:
 * autobind_feeds:
Telemtry Data (data_input) input messages are separated by feeds and also stored in a buffer, but you can access all of the messages for every feed immediately by subscribing to the autobind_feeds event.
 * bind_default_feed: The default feed is the feed with name "" (empty string) and feed input of default stream can be accessed by invoking the bind_default_feed method.
 * bind_feed: You can access messages through feed input only for a specific feed name as well by invoking the bind_feed(feed_name="specific feed name") method.
 * data_buffered: It is possible to access the input messages immediately when they were put into the buffer by subscribing to the data_buffered event. It can be chained with both the bind_default_feed and the bind_feed methods:
    * bind_default_feed().data_buffered
    * bind_feed("test_feed").data_buffered
 * buffer: The buffer can directly be accessed through the feed input object too:
```python
feed_input: TelemetryDataFeedInput = telemetry_input.data_input.bind_default_feed()
feed_input_buffer = feed_input.buffer
```
Buffer has a set of method to access its content with or without removing it from the buffer: get_first(), get_last(), read_first(), read_last()
Buffer content can be accessed also for only a given timeframe by invoking the get_within(start, end) or the read_within(start, end) methods.
Triggers can be defined for a buffer, which are used to monitor incoming messages and act based on their specified condition: buffer.add_trigger(condition_func, tigger, trigger_once)
The input messages is tested against the triggers condition function, and if it is true, the tigger will be executed with the input message as its parameter. If trigger once is set to true, the trigger will be executed only for the first time when its condition will be true.
The input messages are being put in the buffer regardless of the triggers.
An example for a trigger that invokes the get_buffer() method, passing the whole buffer object to it only when the current input data's time reached a threshold:
```python
feed_input: TelemetryDataFeedInput = telemetry_input.data_input.bind_feed()
feed_input.buffer.add_trigger(lambda d: any(d.epoch + t > 1555372800000000000 + 38813465000000 for t in d.time), lambda: get_buffer(feed_input.buffer))
```
This could be handy if we want to process the buffer content only if the input reached a given time on the clock when it was recorded.

##### BackFill Data:
 * autobind_feeds:
BackFill Data (backfill_input) input messages are separated by feeds but not stored in a buffer. You can access all of the messages for every feed immediately by subscribing to the autobind_feeds event.
 * bind_default_feed: The default feed is the feed with name "" (empty string) and feed input of default stream can be accessed by invoking the bind_default_feed method.
 * bind_feed: You can access messages through feed input only for a specific feed name as well by invoking the bind_feed(feed_name="specific feed name") method.
 * data_received: It is possible to access the input messages immediately when they are streamed by subscribing to the data_received event. It can be chained with both the bind_default_feed and the bind_feed methods:
    * bind_default_feed().data_received
    * bind_feed("test_feed").data_received

##### Lap:
 * lap_started: Fired when a new lap started.
 * lap_completed: Fired when a lap completed
 * new_fastest_lap

#### Concept of producing streams:

Before starting to upstream data, you need to specify its data format and upload to to the dependency server through the data format client. This is essential for the consumers to be able to parse and understand your data by its structure and format. The data_format_client is used to put_and_identify_data_format the data format and generate a data_format_id for it.

In case the data need to be consumed and displayed by Atlas10, the atlas_configuration of the data structure must be uploaded to to the dependency server through the atlas_configuration_client, using the put_and_identify_atlas_configuration. A unique atlas_configuration_id will be generated by this method.

A Kafka stream client object is used to access/open an output topic by its topic name. 
AAS stream messages are logically coupled within a session and you can upstream them by creating a SessionTelemetryDataOutput object, prodiving the stream id and the output topic object that you have opened and have access to, plus the data_format_id and the data_format_client that is used to parse the output data.
There can be different dependencies for the session_output which need to be set first, just as other properties of the session, like its state, start time, identifier and other session details.
Make sure to send the session message before sending any telemetry data. This will also start a session heartbeat, which sends session message in every 10 seconds.

##### Telemetry Samples:
Telemetry samples messages can be sent using the initally created SessionTelemetryDataOutput object and its samples_output member, by binding to either the default feed or a specific feed. Once bound to a feed simply invoke the send() method, passing your TelemetrySamples object to it.

##### Telemetry Data:
Telemetry data messages can be sent using the initally created SessionTelemetryDataOutput object and its data_output member, by binding to either the default feed or a specific feed. Once bound to a feed simply invoke the send() method, passing your TelemetryData object to it.

##### BackFill Data:
BackFill data messages can be sent using the initally created SessionTelemetryDataOutput object and its backfill_data_output member, by binding to either the default feed or a specific feed. Once bound to a feed simply invoke the send() method, passing your BackFillData object to it.

Make sure to close the streaming session after sending the data.

#### Session linking:
In case you want to process input messages and upstream them, but also would like to forward the session messages, you can easily link them to the upstream topic with the SessionLinker.
Beside your SessionTelemetryDataInput object that is used to stream input messages a SessionTelemetryDataOutput object is also required for the upstream. Simply invoke the link_to_output() method on the telemetry input object, passign your telemetry output object's session_output member to it, and a session identifier transformer method.
```python
telemetry_input.link_to_output(
    session_output=output.session_output,
    identifier_transform=lambda identifier: identifier + "_changed")
```

#### Modelling messages:
If you want to process input messages, applying your business logic models to it and upstream them, you can do it easily. 
Beside your SessionTelemetryDataInput object that is used to stream input messages a SessionTelemetryDataOutput object is also required for the upstream. Bind to an upstream feed. Subscribe your data modelling method to the data_buffered event, process the data by accessing to it through the event_args.buffer.get_last() method and upstream it using the output feed object's send() method.


## Knowledgebase
Be sure to look at our support knowledgebase on Zendesk: https://mclarenappliedtechnologies.zendesk.com/

## Scope
This pre-release version of the API demonstrates the event-based messaging approach, for sessions and simple telemetry data. 

Future versions will model all ATLAS entities, and likely offer better support for aggregates and predictive models. 

## Requirements
You need to install the following PIP packages from [MAT source](https://artifactory-elb.core.mat.production.matsw.com/artifactory/pypi-local/mat.ocs.streaming/)

* MAT.OCS.Streaming==1.5.3.11rc0

pip install --index-url https://artifactory-elb.core.mat.production.matsw.com/artifactory/api/pypi/pypi-virtual/simple/ mat.ocs.streaming==1.5.3.11rc0

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
    tdata: TelemetryData = event_args.buffer.get_first()
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
