import pytest
import salt.client
import os
from pyfakefs import fake_filesystem, fake_filesystem_glob

from mock import patch, MagicMock
import mock
from srv.modules.runners import ui_rgw

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class TestRadosgw():

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': '12345', 
                  'secret_key': 'abcdef',
                  'user_id': 'admin',
                  'success': True}

        fs.CreateFile('cache/user.admin.json',
              contents='''{\n"keys": [\n{\n"user": "admin",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.admin.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': '12345', 
                  'secret_key': 'abcdef',
                  'user_id': 'jdoe',
                  'success': True}

        fs.CreateFile('cache/user.jdoe.json',
            contents='''{\n"system": "true",\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_no_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        fs.CreateFile('cache/user.jdoe.json',
            contents='''{\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_admin_disabled_system_user(self, masterpillarutil, localclient):
        result = {'urls': [],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        fs.CreateFile('cache/user.jdoe.json',
            contents='''{\n"system": "false",\n"keys": [\n{\n"user": "jdoe",\n"access_key": "12345",\n"secret_key": "abcdef"\n}\n]\n}''')
        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/user.jdoe.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_dedicated_node(self, masterpillarutil, config, localclient):
        result = {'urls': ["http://rgw1:7480"],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw1'
            }
        }

        fs.CreateFile('cache/client.rgw.rgw1.json',
            contents='''[client.rgw.rgw1]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/client.rgw.rgw1.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_dedicated_node_with_ssl(self, masterpillarutil, config, localclient):
        result = {'urls': ["https://rgw1:443"],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw1'
            }
        }

        fs.CreateFile('cache/client.rgw.rgw1.json')
        fs.CreateFile('/srv/salt/ceph/configuration/files/ceph.conf.rgw',
            contents='''[client.rgw.rgw1]\nrgw_frontends = civetweb port=443s ssl_certificate=/etc/ceph/private/keyandcert.pem\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/client.rgw.rgw1.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/ceph.conf.rgw')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_shared_node(self, masterpillarutil, config, localclient):
        result = {'urls': ["http://rgw:7480"],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw'
            }
        }

        fs.CreateFile('cache/client.rgw.json',
            contents='''[client.rgw]\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/client.rgw.json')
        
        assert result == rg.credentials

    @patch('salt.client.LocalClient', autospec=True)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_shared_node_with_ssl(self, masterpillarutil, config, localclient):
        result = {'urls': ["https://rgw:443"],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        localclient().cmd.return_value = {
            'rgw1': {
                'fqdn': 'rgw'
            }
        }

        fs.CreateFile('cache/client.rgw.json')
        fs.CreateFile('/srv/salt/ceph/configuration/files/ceph.conf.rgw',
            contents='''[client.rgw.rgw1]\nrgw_frontends = civetweb port=443s ssl_certificate=/etc/ceph/private/keyandcert.pem\nkey = 12345\ncaps mon = "allow rwx"\ncaps osd = "allow rwx"\n''')

        rg = ui_rgw.Radosgw(pathname="cache")
        fs.RemoveFile('cache/client.rgw.json')
        fs.RemoveFile('/srv/salt/ceph/configuration/files/ceph.conf.rgw')
        
        assert result == rg.credentials


    @patch('salt.client.LocalClient', autospec=True)
    @patch('salt.config.client_config', autospec=True)
    @patch('salt.utils.master.MasterPillarUtil', autospec=True)
    @patch('__builtin__.open', new=f_open)
    @patch('glob.glob', new=f_glob.glob)
    def test_urls_endpoint_defined(self, masterpillarutil, config, localclient):
        result = {'urls': ["http://abc.def"],
                  'access_key': None, 
                  'secret_key': None,
                  'user_id': None,
                  'success': False}

        mpu = masterpillarutil.return_value 
        mpu.get_minion_pillar.return_value = { "minionA": { "rgw_endpoint": "http://abc.def" }}
        rg = ui_rgw.Radosgw(pathname="cache")
        
        assert result == rg.credentials

