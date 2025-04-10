#!/bin/bash
set -e

# Load variables from .env
set -a
source .env
set +a

echo "🌍 Setting environment and Kafka cluster..."
confluent environment use "$ENV_ID"
confluent kafka cluster use "$CLUSTER_ID"

# ----------------------------------------------------------------
# 1) CREATE TOPIC
# ----------------------------------------------------------------
echo
echo "📜 Creating Kafka topic: $CC_TOPIC_NAME..."
confluent kafka topic create "$CC_TOPIC_NAME" --if-not-exists

# ----------------------------------------------------------------
# 2) REGISTER SCHEMA
# ----------------------------------------------------------------
echo
echo "📄 Registering Avro schema under the subject '$CC_TOPIC_NAME-value'..."
# You can either inline the schema, or keep it in a separate file. 
# Below we create a temp file with 'cat <<EOF'.
cat <<EOF > iot_schema.avsc
{
  "type": "record",
  "namespace": "com.example",
  "name": "DeviceEvent",
  "fields": [
    {
      "name": "device_id",
      "type": "string"
    },
    {
      "name": "device_type",
      "type": "string"
    },
    {
      "name": "timestamp",
      "type": "string"
    },
    {
      "name": "sensor_readings",
      "type": {
        "type": "record",
        "name": "SensorReadings",
        "fields": [
          {
            "name": "temperature",
            "type": "float"
          },
          {
            "name": "error_flag",
            "type": "boolean"
          }
        ]
      }
    }
  ]
}
EOF

# Register the schema with the Schema Registry
confluent schema-registry schema create \
  --subject "$CC_TOPIC_NAME-value" \
  --schema iot_schema.avsc \
  --type avro