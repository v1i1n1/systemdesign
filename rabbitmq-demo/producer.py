
import pika
import json
import time
import random
from datetime import datetime

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="localhost",
        credentials=pika.PlainCredentials(
            "admin", "admin123"
        )
    )
)

channel = connection.channel()

# Create Fanout Exchange
channel.exchange_declare(
    exchange="sensor_exchange",
    exchange_type="fanout",
    durable=True
)

print("Sensor producer started...")

try:
    while True:

        sensor_data = {
            "sensor_id": "SENSOR_001",
            "temperature": round(random.uniform(25, 40), 2),
            "humidity": round(random.uniform(40, 80), 2),
            "vibration": round(random.uniform(0.1, 5.0), 2),
            "timestamp": datetime.now().isoformat()
        }

        channel.basic_publish(
            exchange="sensor_exchange",
            routing_key="",
            body=json.dumps(sensor_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json"
            )
        )

        print("Published:", sensor_data)

        time.sleep(1)

except KeyboardInterrupt:
    print("Producer stopped")

finally:
    connection.close()
