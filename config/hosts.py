from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'api', 'config.urls_api', name='api'),
    host(r'admin', 'config.urls_admin', name='admin'),
    host(r'', 'config.urls', name='www'),
)
