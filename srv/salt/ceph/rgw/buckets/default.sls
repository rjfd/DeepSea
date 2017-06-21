
install rgw:
  pkg.installed:
    - pkgs:
      - python-boto

{% for user in salt['rgw.users']('rgw') %}
{% set host = salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw', host=True)[0] %}
create demo bucket:
  module.run:
    - name: rgw.create_bucket
    - kwargs:
        'bucket_name': demo
        'host': {{ host }}
        'access_key': {{ salt['rgw.access_key'](user) }}
        'secret_key': {{ salt['rgw.secret_key'](user) }}
{% endfor %}