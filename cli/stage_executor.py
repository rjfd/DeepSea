# -*- coding: utf-8 -*-
"""
DeepSea Stage executor module
This module is responsible for starting the execution of a DeepSea stage

The user can run a stage like this:
    $ deepsea stage run ceph.stage.0

which is equivalent to:
    $ salt-run state.orch ceph.stage.0
"""
from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import signal
import subprocess
import threading
import time
import sys

import salt.config
import salt.client

from .common import PrettyPrinter as PP
from .monitor import Monitor, MonitorListener
from .monitors.terminal_outputter import SimplePrinter, StepListPrinter
from .stage_parser import StateRenderingException, RenderingException


# pylint: disable=C0103
logger = logging.getLogger(__name__)


class StageExecutor(threading.Thread):
    """
    Executes a stage in its own process
    """
    def __init__(self, stage_name):
        super(StageExecutor, self).__init__()
        self.stage_name = stage_name
        self.proc = None
        self.retcode = None

    def run(self):
        """
        Runs the stage in a different process
        """
        # pylint: disable=W8470
        with open(os.devnull, "w") as fnull:
            exec_array = ["salt-run", "state.orch", self.stage_name]
            logger.info("Start salt command subprocess: %s", exec_array)
            self.proc = subprocess.Popen(exec_array, stdout=fnull, stderr=fnull)
            self.retcode = self.proc.wait()

    def interrupt(self):
        """
        Sends SIGINT signal to the salt-run process
        """
        if self.proc:
            self.proc.send_signal(signal.SIGINT)

    def is_running(self):
        """
        Checks if the salt-run process is running
        """
        return self.proc is not None and self.retcode is None


class RebootListener(MonitorListener):
    """
    Listener DeepSea reboot events
    """
    def __init__(self, monitor, executor):
        super(RebootListener, self).__init__()
        self.monitor = monitor
        self.executor = executor
        self.reboot = False
        self.minions = []

    def deepsea_event(self, event):
        self.reboot = True
        self.minions.append({
            'minion': event.minion,
            'reason': event.reason
        })

        if not self.monitor.is_interrupting():
            self.monitor.interrupt()


def _get_salt_master_id():
    """
    Returns the minion id of the salt master node
    """
    opts = salt.config.minion_config('/etc/salt/minion')
    opts['file_client'] = 'local'
    caller = salt.client.Caller(mopts=opts)
    result = caller.cmd('pillar.get', 'master_minion')
    return result


def _set_pillar_CLI_options(pillar):
    """
    This function sets the pillar keys required by the CLI
    to control the reboot of minions
    """
    opts = salt.config.minion_config('/etc/salt/minion')
    opts['file_client'] = 'local'
    caller = salt.client.Caller(mopts=opts)
    # pylint: disable=W8470
    with open("/srv/pillar/ceph/init.sls", "a") as pillar_file:
        pillar_file.write("\n")
        for key, val in pillar.items():
            res = caller.cmd('pillar.get', key)
            logger.debug("Pillar %s=%s type=%s", key, res, type(res))
            if res is not None and res != "":
                continue
            if isinstance(val, str):
                val = '"{}"'.format(val)
            pillar_file.write("{}: {}\n".format(key, val))

    __local__ = salt.client.LocalClient()
    __local__.cmd('*', 'saltutil.refresh_pillar', [])


def run_stage(stage_name, hide_state_steps, hide_dynamic_steps, simple_output):
    """
    Runs a stage
    Args:
        stage_name (str): the stage name
        hide_state_steps (bool): don't show state result steps
        hide_dynamic_steps (bool): don't show runtime generated steps
        simple_output (bool): use the minimal outputter
    """
    master_id = _get_salt_master_id()
    logger.info("Salt master ID is: %s", master_id)

    _set_pillar_CLI_options({'auto_reboot': False, 'updates_restart': 'default-cli'})

    if simple_output:
        PP.NO_FORMAT = True

    mon = Monitor(not hide_state_steps, not hide_dynamic_steps)
    printer = SimplePrinter() if simple_output else StepListPrinter(False)
    mon.add_listener(printer)
    executor = StageExecutor(stage_name)
    rebooter = RebootListener(mon, executor)
    mon.add_listener(rebooter)
    try:
        mon.parse_stage(stage_name)
    except RenderingException as ex:
        # pylint: disable=E1101
        if isinstance(ex, StateRenderingException):
            PP.println(PP.bold("An error occurred while rendering one of the following states:"))
            for state in ex.states:
                PP.print(PP.cyan("    - {}".format(state)))
                PP.println(" ({})".format("/srv/salt/{}".format(state.replace(".", "/"))))
        else:
            PP.println(PP.bold("An error occurred while rendering the stage file:"))
            PP.println(PP.cyan("    {}".format(ex.stage_file)))
        PP.println()
        PP.println(PP.bold("Error description:"))
        PP.println(PP.red(ex.pretty_error_desc_str()))
        return 2

    mon.start()

    # pylint: disable=W0613
    def sigint_handler(*args):
        """
        SIGINT signal handler
        """
        logger.debug("SIGINT, stopping stage executor")
        if executor.is_running():
            executor.interrupt()
        else:
            if mon.is_running():
                mon.stop(True)
            sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    executor.start()

    if sys.version_info > (3, 0):
        logger.debug("Python 3: blocking main thread on join()")
        executor.join()
    else:
        logger.debug("Python 2: polling for monitor.is_running() %s", mon.is_running())
        while executor.is_running():
            time.sleep(1)
        executor.join()

    if rebooter.reboot:
        logger.debug("Monitor was interrupted due to a deepsea reboot event")
        mon.wait_to_finish()

        PP.println()
        PP.println(PP.bold("The following minions installed some packages that require"
                           " a reboot of the system:"))
        for minion in rebooter.minions:
            PP.print(PP.cyan("    - {}".format(minion['minion'])))
            if minion['minion'] == master_id:
                PP.print(PP.purple(" (master)"))
            if minion['reason']:
                PP.print(PP.dark_yellow(": {}".format(minion['reason'])))
            PP.println()
        PP.println()
        PP.print(PP.bold("Please reboot the minions above, and re-run stage: "))
        PP.println(PP.magenta(stage_name))
        PP.println()
        return 100
    elif mon.is_running():
        time.sleep(1)
        mon.stop(True)
    return executor.retcode
