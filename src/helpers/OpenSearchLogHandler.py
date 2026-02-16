import logging
import datetime
import uuid
from helpers.OpenSearchHelper import OpenSearchHelper


class IndexNameFrequency:
    """Enum for index name frequency"""
    DAILY = 'daily'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'


class OpenSearchLogHandler(logging.Handler):
    """
    A logging handler that sends log records to OpenSearch.
    This replaces the outdated cmreslogging handler.
    """

    FILTER_FIELDS = ['args', 'exc_info', 'exc_text', 'filename', 'funcName',
                     'levelname', 'lineno', 'module', 'pathname', 'process',
                     'processName', 'stack_info', 'thread', 'threadName',
                     'msg', 'message']
    
    def __init__(self, es_index_name='python_log', index_name_frequency=IndexNameFrequency.MONTHLY):
        """
        Initialize the OpenSearch log handler.
        
        Args:
            es_index_name: Base name for the index (e.g., 'query_log')
            index_name_frequency: Frequency for index rotation (DAILY, MONTHLY, YEARLY)
        """
        super().__init__()
        self.es_index_name = es_index_name
        self.index_name_frequency = index_name_frequency
        try:
            self.es = OpenSearchHelper()
            self.es_client = self.es.es
        except Exception:
            self.es = None
            self.es_client = None
        
    def _get_index_name(self):
        """Generate index name based on frequency"""
        now = datetime.datetime.utcnow()
        
        if self.index_name_frequency == IndexNameFrequency.DAILY:
            return f"{self.es_index_name}-{now.strftime('%Y.%m.%d')}"
        elif self.index_name_frequency == IndexNameFrequency.MONTHLY:
            return f"{self.es_index_name}-{now.strftime('%Y.%m')}"
        elif self.index_name_frequency == IndexNameFrequency.YEARLY:
            return f"{self.es_index_name}-{now.strftime('%Y')}"
        else:
            return self.es_index_name
    
    def _format_record(self, record):
        """Format log record for OpenSearch, filtering out unwanted fields"""
        now = datetime.datetime.utcnow()
        log_data = {
            '@timestamp': now.isoformat(),
            'timestamp': now.isoformat(),
            'level': record.levelname,
            'logger': record.name,
        }
        

        for key, value in record.__dict__.items():
            if key not in self.FILTER_FIELDS:
                if isinstance(value, (datetime.datetime, datetime.date)):
                    log_data[key] = value.isoformat()
                elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    log_data[key] = str(value)
                else:
                    log_data[key] = value

        if hasattr(record, 'message') and record.message:
            log_data['message'] = record.message
        elif hasattr(record, 'msg') and record.msg:
            log_data['message'] = str(record.msg)
        
        return log_data
    
    def emit(self, record):
        """Emit a log record to OpenSearch"""
        if self.es is None:
            return
            
        try:
            log_data = self._format_record(record)
            index_name = self._get_index_name()

            log_id = str(uuid.uuid4())

            self.es.index(
                index=index_name,
                id=log_id,
                body=log_data,
                ignore=409
            )
        except Exception as e:
            import sys
            import traceback
            try:
                sys.stderr.write(f"[OpenSearchLogHandler] Error emitting record: {e}\n")
                sys.stderr.write(f"{traceback.format_exc()}\n")
            except:
                pass
            self.handleError(record)

