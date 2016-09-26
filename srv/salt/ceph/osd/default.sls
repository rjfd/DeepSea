
include:
  - .keyring

{% set base_cmd = "ceph-disk -v prepare " %}
{% set cluster_ident = " --cluster " + salt['pillar.get']('cluster') %}
{% set cluster_uuid = " --cluster-uuid " +  salt['pillar.get']('fsid') %}
{% set data_and_journal = " --data-dev --journal-dev" %}
{% set fstype = "xfs" %}

{% for device in salt['pillar.get']('storage:osds') %}
{% set dev = salt['cmd.run']('readlink -f ' + device.dev ) %}

{% if device.dmcrypt %}
   {% set cmd = base_cmd + " --dmcrypt "%}
{% else %}
    {% set cmd = base_cmd %}
{% endif %}

{% if device.bluestore %}
   {% set cmd = cmd + " --bluestore " + data_and_journal + cluster_ident + cluster_uuid + " " %}

set experimental flag {{ device.dev }}:
  cmd.run:
    - name: "echo 'enable experimental unrecoverable data corrupting features = *' >> /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"
    - unless: "grep 'enable experimental unrecoverable data corrupting features = *' /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"

{% else %}
   {% set cmd = cmd + " --fs-type " + fstype + data_and_journal + cluster_ident + cluster_uuid + " " %}
{% endif %}

set journal size {{ device.dev }}:
  cmd.run:
    - name: "sed -i 's/^osd_journal_size =.*/osd_journal_size = {{ device.journal_size }}/g' /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"

prepare {{ device.dev }}:
  cmd.run:
    - name: "{{ cmd }} {{ dev }}"
    - unless: "fsck {{ dev }}1"
    - fire_event: True

{% if not device.dmcrypt %}

activate {{ device.dev }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ dev }}1"
    - unless: "grep -q ^{{ dev }}1 /proc/mounts"
    - fire_event: True

{% endif %}

{% endfor %}

{% for entry in salt['pillar.get']('storage:data+journals') %}

{% if entry.dmcrypt %}
   {% set cmd = base_cmd + " --dmcrypt "%}
{% else %}
    {% set cmd = base_cmd %}
{% endif %}

{% if entry.bluestore %}
   {% set cmd = cmd + " --bluestore " + data_and_journal + cluster_ident + cluster_uuid + " " %}

set experimental flag2 {{ device.dev }}:
  cmd.run:
    - name: "echo 'enable experimental unrecoverable data corrupting features = *' >> /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"
    - unless: "grep 'enable experimental unrecoverable data corrupting features = *' /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"

{% else %}
   {% set cmd = cmd + " --fs-type " + fstype + data_and_journal + cluster_ident + cluster_uuid + " " %}
{% endif %}

set journal size2 {{ entry.data }}:
  cmd.run:
    - name: "sed -i 's/^osd_journal_size =.*/osd_journal_size = {{ entry.journal_size }}/g' /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"

prepare2 {{ entry.data }}:
  cmd.run:
    - name: "{{ cmd }} {{ entry.data }} {{ entry.journal }}"
    - unless: "fsck {{ entry.data }}1"
    - fire_event: True

{% if not entry.dmcrypt %}

activate2 {{ entry.data }}:
  cmd.run:
    - name: "ceph-disk -v activate --mark-init systemd --mount {{ entry.data }}1"
    - unless: "grep -q ^{{ entry.data }} /proc/mounts"
    - fire_event: True

{% endif %}

{% endfor %}

set journal size to none:
  cmd.run:
    - name: "sed -i 's/^osd_journal_size =.*/osd_journal_size =/g' /etc/ceph/{{ salt['pillar.get']('cluster') }}.conf"

