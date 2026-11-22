
import pika
import json
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="localhost",
        credentials=pika.PlainCredentials("admin", "admin123")
    )
)

channel = connection.channel()

channel.exchange_declare(
    exchange="sensor_exchange",
    exchange_type="fanout",
    durable=True
)

channel.queue_declare(
    queue="vibration_queue",
    durable=True
)

channel.queue_bind(
    exchange="sensor_exchange",
    queue="vibration_queue"
)

def callback(ch, method, properties, body):
    data = json.loads(body)

    print(
        "[Consumer 3] Vibration:",
        data["vibration"]
    )

    time.sleep(1)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue="vibration_queue",
    on_message_callback=callback
)

print("Consumer 3 waiting...")
channel.start_consuming()
