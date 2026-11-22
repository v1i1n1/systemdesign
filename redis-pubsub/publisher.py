
import redis
import json
import time
import random
from datetime import datetime

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

channel = "sensor_updates"

print("Sensor publisher started...")

try:
    while True:

        sensor_data = {
            "sensor_id": "SENSOR_001",
            "temperature": round(random.uniform(25, 40), 2),
            "humidity": round(random.uniform(40, 80), 2),
            "vibration": round(random.uniform(0.1, 5), 2),
            "timestamp": datetime.now().isoformat()
        }

        message = json.dumps(sensor_data)

        # Publish to Redis channel
        subscribers = r.publish(channel, message)

        print(
            f"Published: {message} | "
            f"Active subscribers: {subscribers}"
        )

        time.sleep(1)

except KeyboardInterrupt:
    print("Publisher stopped.")
