from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'api', 'core.urls_api', name='api'),
    host(r'admin', 'core.urls_admin', name='admin'),
    host(r'(www)?', 'core.urls', name='www'),
)
