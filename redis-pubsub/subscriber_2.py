
import redis
import json

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

pubsub = r.pubsub()

pubsub.subscribe("sensor_updates")

print("Subscriber 2 listening...")

for message in pubsub.listen():

    if message["type"] == "message":

        data = json.loads(message["data"])

        print("\n[SERVER B] Received sensor data")
        print("Sensor ID:", data["sensor_id"])
        print("Temperature:", data["temperature"])
        print("Timestamp:", data["timestamp"])
    