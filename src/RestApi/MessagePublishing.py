from Config.Config import G_CONFIG

from rabbitmq_client import RMQProducer, ExchangeParams
from pika.exchange_type import ExchangeType
from pika.defs import PublishParams
from pika.spec import BasicProperties
from Config.Config import rabbitmq_connection
from datetime import datetime

import json
from pika import PlainCredentials, ConnectionParameters



from typing import Dict, AnyStr


def publish_audit_log_message(event_type, event_parameters):
    metadata = parse_message_metadata_from_request()

    publish_rabbitmq_message({
        'trace_id': metadata['trace_id'],
        'context_institution_id': metadata['context_institution_id'],
        'acting_institution_user_id': metadata['acting_institution_user_id'],
        'context_department_id': metadata['context_department_id'],
        'acting_user_pic': metadata['acting_user_pic'],
        'acting_user_forename': metadata['acting_user_forename'],
        'acting_user_surname': metadata['acting_user_surname'],
        'happened_at': datetime.now(),
        'event_type': event_type,
        'event_parameters': event_parameters,
        'failure_type': None,
    })

def parse_message_metadata_from_request() -> Dict:
    return {}

def obtain_service_account_jwt() -> AnyStr:
    return '{}'

def publish_rabbitmq_message(body):
    audit_logs_config = G_CONFIG['audit_logs']
    credentials = PlainCredentials(audit_logs_config['username'], audit_logs_config['password'])
    jwt = obtain_service_account_jwt()

    producer = RMQProducer(
        ConnectionParameters(
            host=audit_logs_config['host'],
            port=audit_logs_config['port'],
            credentials=credentials
        )
    )

    producer.start()

    producer.publish(
        json.dumps(body).encode('UTF-8'),
        publish_params=PublishParams(BasicProperties(headers={'jwt': jwt})),
        exchange_params=ExchangeParams(audit_logs_config['exchange'], ExchangeType.topic)
    )

