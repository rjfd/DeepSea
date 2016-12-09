

{% set kernel = grains['kernelrelease'] | replace('-default', '')  %}
{% set installed = salt['cmd.run']('rpm -q --last kernel-default-base | head -1 | cut -f1 -d\  ') | replace('kernel-default-base', '') %}


warning:
  module.run:
    - name: advise.reboot
    - running: {{ kernel }}
    - installed: {{ installed }}
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"


reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"
    - failhard: True
    - fire_event: True



