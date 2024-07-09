package flinkConnector;

import Deserializer.JSONValueDeserializationSchema;
import Dto.Sentiment;
import Serializer.SentimentSerializationSchema;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import java.util.Properties;
import java.sql.Timestamp;


public class DataStreamJob {
	public static void main(String[] args) throws Exception {
		// Sets up the execution environment, which is the main entry point
		// to building Flink applications.
		final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

		String inputTopic = "sender";

		KafkaSource<Sentiment> source = KafkaSource.<Sentiment>builder()
				.setBootstrapServers("localhost:9092")
				.setTopics(inputTopic)
				.setGroupId("flink-group")
				.setStartingOffsets(OffsetsInitializer.earliest())
				.setValueOnlyDeserializer(new JSONValueDeserializationSchema())
				.build();

		DataStream<Sentiment> sentimentStream = env.fromSource(source, WatermarkStrategy.noWatermarks(), "Kafka Source");

		// Process the data stream
		DataStream<Sentiment> processedStream = sentimentStream
				.map(sentiment -> {
					sentiment.transformLabel();
					return sentiment;
				})
				.map(sentiment -> {
					// Create a new Sentiment object with only the required fields
					Sentiment processedSentiment = new Sentiment();
					processedSentiment.setCreatedUtc(sentiment.getCreatedUtc());
					processedSentiment.setBody(sentiment.getBody());
					processedSentiment.setlabel(sentiment.getlabel());
					return processedSentiment;
				});

		// Set up Kafka properties
		Properties properties = new Properties();
		properties.setProperty("bootstrap.servers", "localhost:9092");

		// Create a Flink Kafka Producer
		FlinkKafkaProducer<Sentiment> myProducer = new FlinkKafkaProducer<>(
				"processed-sender",                  // target topic
				new SentimentSerializationSchema(),    // serialization schema
				properties          // producer config
		);

		// Add the Kafka sink to the Flink data stream
		processedStream.addSink(myProducer);

		// Execute program, beginning computation.
		env.execute("Flink Kafka Streaming Job");
	}
}



