from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'api', 'core.urls_api', name='api'),
    host(r'admin', 'core.urls_admin', name='admin'),
    host(r'isletme', 'isletme_app.urls', name='isletme'),
    host(r'ip', 'core.urls_ip', name='ip'),
    host(r'demo', 'demo_app.urls', name='demo'),
    host(r'', 'core.urls', name='www'),
)

