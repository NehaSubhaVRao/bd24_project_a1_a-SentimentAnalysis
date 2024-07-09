package Serializer;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;
import Dto.Sentiment;

public class SentimentSerializationSchema implements SerializationSchema<Sentiment> {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public byte[] serialize(Sentiment sentiment) {
        try {
            return objectMapper.writeValueAsBytes(sentiment);
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize sentiment", e);
        }
    }
}

