import json
import datetime
import logging
import amqp
from amqp.exceptions import AMQPError
from flask import request, current_app

from Config.Config import G_CONFIG
from lib.flask_jwt import current_identity

logger = logging.getLogger(__name__)

class _AuditLogPublisher:
    def __init__(self):
        self.connection = None

    def connect(self):
        if not self.connection or not self.connection.connected:
            logger.info("AuditLogClient: Connecting to AMQP")
            self.connection = amqp.Connection(
                host=G_CONFIG.config['rabbitmq']['host'] + ':' + G_CONFIG.config['rabbitmq']['port'],
                userid=G_CONFIG.config['rabbitmq']['user'],
                password=G_CONFIG.config['rabbitmq']['password'],
                exchange='audit-log-events',
                confirm_publish=True)
            self.connection.connect()
            logger.info("AuditLogClient: AMQP connection successful")

    def close(self):
        self.connection.close()

    def publish_message(self, audit_log_message, retry=2):
        if retry == -1:
            return

        # Ensure connection is open
        self.connect()

        try:
            channel = self.connection.channel()
            message = amqp.Message(
                body=json.dumps(audit_log_message),
                application_headers={
                    'jwt': current_app.keycloak.get_service_account_jwt(),
                })
            channel.basic_publish(message, routing_key='audit-log-events')
        except (OSError, AMQPError) as e:
            logger.info("AuditLogClient: Lost connection to AMQP")

            self.publish_message(audit_log_message, retry=retry - 1)


class AuditLogMessage:
    def __init__(self, event_type=None, failure_type=None, event_parameters=None):
        self._failure_type = None
        self.failure_type(failure_type)
        self._event_parameters = None
        self.event_parameters(event_parameters)
        self._event_type = None
        self.event_type(event_type)

    def failure_type(self, value):
        if value not in (None, 'UNPROCESSABLE_ENTITY', 'FORBIDDEN'):
            raise Exception("Invalid failure type")
        self._failure_type = value
        return self

    def event_parameters(self, value):
        self._event_parameters = value
        return self

    def event_type(self, value):
        if not value:
            raise Exception("Event type is required")
        self._event_type = value
        return self

    def build(self):
        return {
            "happened_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "trace_id": request.headers.get('x-request-id'),
            "event_type": self._event_type,
            "failure_type": self._failure_type,
            "context_institution_id": current_identity.institution_id,
            "acting_institution_user_id": current_identity.institution_user_id,
            "context_department_id": current_identity.department_id,
            "acting_user_pic": current_identity.institution_user_pic,
            "acting_user_forename": current_identity.institution_user_forename,
            "acting_user_surname": current_identity.institution_user_surname,
            "event_parameters": self._event_parameters
        }


_audit_log_publisher = _AuditLogPublisher()


def send_audit_log(message):
    if isinstance(message, AuditLogMessage):
        _audit_log_publisher.publish_message(message.build())
    else:
        _audit_log_publisher.publish_message(message)
