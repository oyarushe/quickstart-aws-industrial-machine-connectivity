import logging

from createSitewiseResources import CreateSitewiseResources

log = logging.getLogger('assetModelConverter')
log.setLevel(logging.DEBUG)


def handler(event, context):
    log.info('Processing Event {}'.format(event))
    CreateSitewiseResources().processEvent(event)
