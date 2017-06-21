# -*- coding: utf-8 -*-

"""
Consolidate any user interface rgw calls for Wolffish and openATTIC.

All operations will happen using the rest-api of RadosGW.  The one execption
is getting the credentials for an administrative user which is implemented
here.
"""

import logging
import os
import json
import re
import glob
import salt.client
import salt.utils.minions

log = logging.getLogger(__name__)


class Radosgw(object):
    """
    Return a structure containing S3 keys and urls
    """

    def __init__(self, canned=None, cluster='ceph', pathname='/srv/salt/ceph/rgw/cache'):
        """
        Initialize and call routines
        """
        if canned:
            self._canned(int(canned))
        else:
            self.cluster = cluster
            self.credentials = {'access_key': None,
                                'secret_key': None,
                                'user_id': None,
                                'urls': [],
                                'success': False}

            self.pathname = pathname
            self._admin()
            self._urls()

    def _canned(self, canned):
        """
        Return examples for debugging without a working Ceph cluster
        """
        if canned == 1:
            self.credentials = {'access_key': "ABCDEFGHIJKLMNOPQRST",
                                'secret_key': "0123456789012345678901234567890123456789",
                                'urls': ["http://rgw1"]}
        elif canned == 2:
            self.credentials = {'access_key': "ABCDEFGHIJKLMNOPQRST",
                                'secret_key': "0123456789012345678901234567890123456789",
                                'urls': ["http://red1",
                                         "http://red2",
                                         "http://blue1:8000",
                                         "http://blue2:8000"]}

    def _admin(self, filename="user.admin.json"):
        """
        Expect admin user file; otherwise, search for first system user.
        Update access_key, secret_key
        """
        filepath = "{}/{}".format(self.pathname, filename)
        if os.path.exists(filepath):
            user = json.loads(open(filepath).read())
        else:
            user = None
            for user_file in glob.glob("{}/user.*".format(self.pathname)):
                user = json.loads(open(user_file).read())
                if 'system' in user and user['system'] == "true":
                    break
                user = None
            if not user:
                # No system user
                log.error("No system user for radosgw found")
                return
        self.credentials['access_key'] = user['keys'][0]['access_key']
        self.credentials['secret_key'] = user['keys'][0]['secret_key']
        self.credentials['user_id'] = user['keys'][0]['user']
        self.credentials['success'] = True

    def _urls(self):
        """
        Check for user defined endpoint; otherwise, return list of gateways as
        urls.
        """
        search = "I@cluster:{}".format(self.cluster)
        __opts__ = salt.config.client_config('/etc/salt/master')
        pillar_util = salt.utils.master.MasterPillarUtil(search, "compound",
                                                         use_cached_grains=True,
                                                         grains_fallback=False,
                                                         opts=__opts__)
        cached = pillar_util.get_minion_pillar()
        for minion in cached:
            if 'rgw_endpoint' in cached[minion]:
                self.credentials['urls'].append(cached[minion]['rgw_endpoint'])
                return

        port = '7480'  # civetweb default port
        ssl = ''
        found = False
        for rgw_conf_file_path in glob.glob("/srv/salt/ceph/configuration/files/ceph.conf.*"):
            if os.path.exists(rgw_conf_file_path) and os.path.isfile(rgw_conf_file_path):
                with open(rgw_conf_file_path) as rgw_conf_file:
                    for line in rgw_conf_file:
                        if line:
                            match = re.search(r'rgw.*frontends.*=.*port=(\d+)(s?)', line)
                            if match:
                                port = match.group(1)
                                ssl = match.group(2)
                                found = True
            if found:
                break

        local = salt.client.LocalClient()
        result = local.cmd('I@roles:rgw', 'grains.item', ['fqdn'], expr_form="compound")
        for _, grains in result.items():
            self.credentials['urls'].append("http{}://{}:{}".format(ssl, grains['fqdn'], port))


def credentials(canned=None, **kwargs):
    """
    Return the administrative credentials for the RadosGW
    """
    radosgw = Radosgw(canned)
    return radosgw.credentials
