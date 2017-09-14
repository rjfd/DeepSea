{% set kernel = grains['kernelrelease'] | replace('-default', '')  %}
{% set installed = salt['cmd.run']('rpm -q --last kernel-default | head -1 | cut -f1 -d\  ') | replace('kernel-default-', '') %}

{% if kernel not in installed %}
deepsea/packagemanager/reboot:
  event.send:
    - data:
      reason: "Reboot to upgrade from kernel {{ kernel }} to {{ installed }}."
{% endif %}

dry_reboot:
  cmd.run:
    - name: "echo fail | grep onpurpose"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"
    - failhard: True
