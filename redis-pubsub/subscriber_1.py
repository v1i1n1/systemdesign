
import redis
import json

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

pubsub = r.pubsub()

pubsub.subscribe("sensor_updates")

print("Subscriber 1 listening...")

for message in pubsub.listen():

    if message["type"] == "message":

        data = json.loads(message["data"])

        print("\n[SERVER A] Received sensor data")
        print("Temperature:", data["temperature"])
        print("Humidity:", data["humidity"])
        print("Vibration:", data["vibration"])
