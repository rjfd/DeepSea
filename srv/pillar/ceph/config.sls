cluster_config:
  name: ceph
  #include: [data1.ceph, data2.ceph]
  #exclude: [test*]

  osds:
    filter:
      n_disks_gt: 1 # only consider minions with more than 1 disk
      disk_size_gte: 2G # only consider disks with at least 2G

    global:
      allow_share_data_and_journal: true # default true
      allow_use_ssd_for_journal: true    # default true
      allow_use_nvme_for_journal: true   # default true

      dmcrypt: false                     # default false
      journal_size: 5G                   # default 5G

      # We compute automatically the journal size based on the
      # disk throughput as described in http://docs.ceph.com/docs/master/rados/configuration/osd-config-ref/#journal-settings
      # This option is disabled by default
      use_estimated_journal_size: false

    data1.ceph:
      journal_size: 512M
      max_journal_partitions_per_disk: 3
      vdb: { journal_only: true }  # /dev/vdb will be used only for journal partitions
      vdc: { data_only: true }

    data2.ceph:
      journal_size: 256M
      dmcrypt: true         # all osds will have dmcrypt enabled on this minion

    # data3.ceph:
    #  model:intel-xx-nn:    # specify a disk through the model
    #    journal_size: 10G   # all OSDs that use intel-xx-nn disks should have
                             # 10G journals

  mons:
    global:
      allow_osd_role_sharing: true  # allow osd to be also a mon


    include: [mon1.ceph, data1.ceph, data2.ceph]

  admins:
    include: [admin.ceph]


