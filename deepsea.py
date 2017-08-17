# -*- coding: utf-8 -*-
import fnmatch
import sys

import salt.config
import salt.utils.event

opts = salt.config.client_config('/etc/salt/master')

event = salt.utils.event.get_event(
        'master',
        sock_dir=opts['sock_dir'],
        transport=opts['transport'],
        opts=opts)


# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar

    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\x1b[2K\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

stages = {
    'ceph.stage.radosgw': 8,
    'ceph.stage.0': 47,
    'ceph.stage.prep': 47,
    'ceph.stage.1': 6,
    'ceph.stage.discovery': 6,
    'ceph.stage.2': 25,
    'ceph.stage.configure': 25,
    'ceph.stage.3': 19,
    'ceph.stage.deploy': 19,
    'ceph.stage.4': 38,
    'ceph.stage.services': 38,
}


print("Started listening to DeepSea events")
num_events = 0
curr_stage = None
while True:
    ret = event.get_event(full=True)
    if ret is None:
        continue
    #print(ret)
    #print("EVENT: {}".format(ret))
    if fnmatch.fnmatch(ret['tag'], 'salt/job/*/new'):
        #print("Tag: {} -> {} -> {}".format(ret['tag'], ret['data']['tgt'], ret['data']['fun']))
        if ret['data']['fun'] == 'state.sls':
            #print("Running state '{}'".format(ret['data']['arg'][0]))
            num_events += 1
            print_progress(num_events, stages[curr_stage], prefix = '{}:'.format(curr_stage[5:]), suffix = 'Running {}'.format(ret['data']['arg'][0]), bar_length = 50)

    if fnmatch.fnmatch(ret['tag'], 'salt/run/*'):
        #print("Tag: {} -> {} -> {}".format(ret['tag'], ret['data']['fun'], ret['data']['fun_args']))
        if ret['data']['fun'] == 'runner.state.orch':
            if ret['data']['fun_args'][0].startswith('ceph.stage'):
                curr_stage = ret['data']['fun_args'][0]
                if fnmatch.fnmatch(ret['tag'], 'salt/run/*/new'):
                    #print("****** Started stage '{}' ******".format(ret['data']['fun_args'][0]))
                    print_progress(num_events, stages[curr_stage], prefix = '{}:'.format(curr_stage[5:]), suffix = 'Started {}'.format(curr_stage), bar_length = 50)
                elif fnmatch.fnmatch(ret['tag'], 'salt/run/*/ret'):
                    print_progress(num_events+1, stages[curr_stage], prefix = '{}:'.format(curr_stage[5:]), suffix = 'Finished {}'.format(curr_stage), bar_length = 50)
                    #print("****** Ended stage '{}' ****** {}".format(ret['data']['fun_args'][0], num_events))
                    num_events = 0
                    curr_stage = None
        else:
            if fnmatch.fnmatch(ret['tag'], 'salt/run/*/new'):
                #print("Running runner '{}'".format(ret['data']['fun']))
                num_events += 1
                print_progress(num_events, stages[curr_stage], prefix = '{}:'.format(curr_stage[5:]), suffix = 'Running {}'.format(ret['data']['fun']), bar_length = 50)

