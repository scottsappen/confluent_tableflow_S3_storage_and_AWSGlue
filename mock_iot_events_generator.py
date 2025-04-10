import os
import time
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Load the .env file
load_dotenv()

# Access environment variables
CC_BOOTSTRAP_SERVER = os.getenv("CC_BOOTSTRAP_SERVER")
CC_CLUSTER_API_KEY = os.getenv("CC_CLUSTER_API_KEY")
CC_CLUSTER_API_SECRET = os.getenv("CC_CLUSTER_API_SECRET")
CC_SCHEMA_REGISTRY_URI = os.getenv("CC_SCHEMA_REGISTRY_URI")
CC_SCHEMA_REGISTRY_AUTH = os.getenv("CC_SCHEMA_REGISTRY_AUTH")
CC_TOPIC_NAME = os.getenv("CC_TOPIC_NAME")

# Define the Avro schema - must match your registered schema
user_query_schema_str = """
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
"""

DEVICES = [
    {"device_id": "MRI-01", "device_type": "MRI Model X"},
    {"device_id": "CT-01", "device_type": "CT Scanner Z"},
    {"device_id": "US-01", "device_type": "Ultrasound Device Y"},
    {"device_id": "XR-01", "device_type": "X-Ray 3000"},
    {"device_id": "VT-01", "device_type": "Ventilator Pro"},
    {"device_id": "ECG-01", "device_type": "ECG Monitor A"},
    {"device_id": "IP-01", "device_type": "Infusion Pump B"},
    {"device_id": "DF-01", "device_type": "Defibrillator D"},
    {"device_id": "PM-01", "device_type": "Patient Monitor P"},
    {"device_id": "AM-01", "device_type": "Anesthesia Machine AM"},
    {"device_id": "IP-02", "device_type": "Infusion Pump B2"},
    {"device_id": "XR-02", "device_type": "Portable X-Ray"},
    {"device_id": "US-02", "device_type": "Ultrasound Device Z"},
    {"device_id": "MRI-02", "device_type": "MRI Model Y"},
    {"device_id": "CT-02", "device_type": "CT Scanner Q"},
    {"device_id": "VT-02", "device_type": "Ventilator X"},
    {"device_id": "ECG-02", "device_type": "ECG Monitor B"},
    {"device_id": "DF-02", "device_type": "Defibrillator E"},
    {"device_id": "PM-02", "device_type": "Patient Monitor Q"},
    {"device_id": "AM-02", "device_type": "Anesthesia Machine X"}
]

# Confluent Cloud configuration
conf = {
    'bootstrap.servers': CC_BOOTSTRAP_SERVER,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': CC_CLUSTER_API_KEY,
    'sasl.password': CC_CLUSTER_API_SECRET,
}

# Schema Registry configuration
schema_registry_conf = {
    'url': CC_SCHEMA_REGISTRY_URI,
    'basic.auth.user.info': CC_SCHEMA_REGISTRY_AUTH
}

# Initialize Schema Registry client
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Initialize serializer
avro_serializer = AvroSerializer(
    schema_registry_client,
    user_query_schema_str
)

# Initialize Producer
producer = Producer(conf)

def delivery_report(err, msg):
    """Callback to report the result of the delivery attempt."""
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered message to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def generate_event():
    """Generate a random IoT device event."""
    device = random.choice(DEVICES)
    temperature = round(random.uniform(60, 115), 1)
    error_flag = temperature > 100 or (random.random() < 0.05)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    return {
        "device_id": device["device_id"],
        "device_type": device["device_type"],
        "timestamp": timestamp,
        "sensor_readings": {
            "temperature": temperature,
            "error_flag": error_flag
        }
    }

def main():
    print("Starting mock IoT event producer. Press Ctrl+C to stop.")
    try:
        while True:
            # Generate a new IoT event
            event = generate_event()
            print(f"Producing event: {event}")

            # Serialize event as Avro
            serialized_data = avro_serializer(
                event,
                SerializationContext(CC_TOPIC_NAME, MessageField.VALUE)
            )

            # Produce to Kafka
            producer.produce(
                topic=CC_TOPIC_NAME,
                value=serialized_data,
                on_delivery=delivery_report
            )
            # Let the producer handle any outstanding deliveries
            producer.poll(0)

            # Wait 2 seconds before producing the next message
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nShutting down mock event producer...")
    finally:
        # Wait for all messages to be delivered
        producer.flush()
        print("All messages flushed. Exiting.")

if __name__ == "__main__":
    main()
