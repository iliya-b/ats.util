
import logging
import logging.config
import pkg_resources

import structlog
import yaml


def setup_logging(config):
    if config['log']['jsonformat']:
        template = 'logging-json.yaml'
    else:
        template = 'logging.yaml'

    global_defaults = pkg_resources.resource_stream('ats.util.logging', template)
    logging.config.dictConfig(yaml.load(global_defaults))


async def structlog_middleware(app, handler):
    async def middleware_handler(request):
        request['slog'] = structlog.get_logger()
        return await handler(request)
    return middleware_handler


def setup_structlog(config, key_order=None):
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        # structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config['log']['jsonformat']:
        processors.extend([
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(indent=0, sort_keys=True),
        ])
    else:
        if key_order is None:
            key_order = []
        else:
            key_order = ['delivery_tag', 'task', 'uid', 'project', 'project_id', 'avm']
        processors.append(
            # structlog.dev.ConsoleRenderer(pad_event=30)
            structlog.processors.KeyValueRenderer(sort_keys=False,
                                                  key_order=key_order,
                                                  drop_missing=True)
        )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
