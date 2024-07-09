package Deserializer;

import Dto.Sentiment;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;


import java.io.IOException;

public class JSONValueDeserializationSchema implements DeserializationSchema<Sentiment> {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public Sentiment deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, Sentiment.class);
    }


    @Override
    public boolean isEndOfStream(Sentiment sentiment) {
        return false;
    }

    @Override
    public TypeInformation<Sentiment> getProducedType() {
        return TypeInformation.of(Sentiment.class);
    }
}
