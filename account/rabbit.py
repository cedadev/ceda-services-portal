import logging
import json
import pika

from django.conf import settings


log = logging.getLogger(__name__)


class RabbitConnection():

    @property
    def channel(self):
        return self._channel

    def __init__(self):

        self._connection = None
        self._channel = None

        server = settings.RABBIT_SERVER
        credentials = pika.PlainCredentials(
            server.get("USER"), server.get("PASSWORD")
        )
        self._connection_parameters = pika.ConnectionParameters(
            host=server.get("HOST"),
            virtual_host=server.get("VHOST"),
            credentials=credentials
        )
        self._queue = server.get("QUEUE")

    def __enter__(self):

        self.connect()
        return self

    def __exit__(self, *args, **kwargs):

        self.close()

    def connect(self):

        log.debug("Initialising new RabbitMQ connection.")
        self._connection = pika.BlockingConnection(
            self._connection_parameters
        )

        self._channel = self._connection.channel()

    def close(self):

        log.debug("Closing RabbitMQ connection.")
        self._connection.close()
        self._channel = None

    def publish(self, body):

        log.debug("Publishing message")
        self._channel.queue_declare(self._queue, durable=True, passive=True)
        self._channel.basic_publish(
            exchange='',
            routing_key=self._queue,
            body=json.dumps(body)
        )
