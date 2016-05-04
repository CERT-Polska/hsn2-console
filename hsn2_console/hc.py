#!/usr/bin/python

# Copyright (c) NASK, NCSC
# 
# This file is part of HoneySpider Network 2.1.
# 
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import logging
import sys

from aliases import Aliases
from hsn2_commons import argparsealiases as argparse
from hsn2_commons.hsn2bus import Bus
from hsn2_commons.hsn2bus import BusException
from hsn2_commons.hsn2bus import BusTimeoutException
from hsn2_commons.hsn2cmd import CommandDispatcher


# ------------------------------
# Setup logging
#
def init_logger(cliargs):
    logger = logging.getLogger("HC")
    hdlr = logging.StreamHandler()
    hdlr.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
    logger.addHandler(hdlr)
    logger.setLevel(logging.getLevelName(cliargs.log_level.upper()))
    return logger

# ------------------------------
# Reading command line arguments
#
def cliparse(aliases):
    parser = argparse.ArgumentParser(
                description = 'HSN2 Command Line Interface.',
                formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                epilog = '''Each subcommand has it's own help message.'''
            )
    parser.add_argument('--log-level', '-ll', action = 'store', help = 'logging level (default: WARN)',
        choices = 'DEBUG INFO WARN ERROR'.split(), default = "WARN")
    parser.add_argument('--config', '-c', action = 'store', help = 'config file', default = "/etc/hsn2/console.conf", dest = 'configuration')
    parser.add_argument('--version', '-v', action = 'version', version = '== HSN2 Command Line Interface v0.1')
    cmd_parsers = parser.add_subparsers(dest = 'command', title = 'subcommands')

    # job command tree
    parser_job = cmd_parsers.add_parser('job', help = 'Send a command regarding jobs', aliases = aliases.getAliases('job'))
    job_parsers = parser_job.add_subparsers(dest = 'job', title = 'subcommands')
    parser_job_list = job_parsers.add_parser('list', help = 'send a get jobs query', aliases = aliases.getAliases('list', 'job'))
    parser_job_details = job_parsers.add_parser('details', help = 'send a get job details query', aliases = aliases.getAliases('details', 'job'))
    parser_job_details.add_argument('gjd_id', help = 'job id')
    parser_job_submit = job_parsers.add_parser('submit', help = 'send a job descriptor', aliases = aliases.getAliases('submit', 'job'))
    parser_job_submit.add_argument('jd_workflow', help = 'workflow id')
    parser_job_submit.add_argument('--jd_workflow', '-jw', help = 'workflow id')
    parser_job_submit.add_argument('param', action = 'append', help = 'service_label.key=value job descriptor parameters', nargs = '*')
    parser_job_submit.add_argument('--param', '-p', action = 'append', help = 'service_label.key=value job descriptor parameters', nargs = '*')

    # workflow command tree
    parser_workflow = cmd_parsers.add_parser('workflow', help = 'Send a command regarding workflows', aliases = aliases.getAliases('workflow'))
    workflow_parsers = parser_workflow.add_subparsers(dest = 'workflow', title = 'subcommands')
    parser_workflow_list = workflow_parsers.add_parser('list', help = 'send a get worflows query', aliases = aliases.getAliases('list', 'workflow'))
    parser_workflow_list.add_argument('--enabled', '-e', action = 'store_true', help = 'request only enabled workflows', default = False)
    parser_workflow_get = workflow_parsers.add_parser('get', help = 'send a get worflow query', aliases = aliases.getAliases('get', 'workflow'))
    parser_workflow_get.add_argument('jd_workflow', help = 'workflow id')
    parser_workflow_get.add_argument('--file', '-f', type = argparse.FileType('w'), help = 'file containing the workflow', required = False, default = None)
    parser_workflow_get.add_argument('revision', help = 'workflow revision', default = None, nargs = '?')
    parser_workflow_upload = workflow_parsers.add_parser('upload', help = 'upload a workflow', aliases = aliases.getAliases('upload', 'workflow'))
    parser_workflow_upload.add_argument('name', help = 'name for the workflow')
    parser_workflow_upload.add_argument('--no-overwrite', action = 'store_false', help = 'overwrite workflow', default = True, dest = "overwrite")
    parser_workflow_upload.add_argument('--file', '-f', type = argparse.FileType('r'), help = 'file containing the workflow', required = False, default = None)
    parser_workflow_disable = workflow_parsers.add_parser('disable', help = 'send a disable worflow query', aliases = aliases.getAliases('disable', 'workflow'))
    parser_workflow_disable.add_argument('jd_workflow', help = 'workflow id')
    parser_workflow_enable = workflow_parsers.add_parser('enable', help = 'send an enable worflow query', aliases = aliases.getAliases('enable', 'workflow'))
    parser_workflow_enable.add_argument('jd_workflow', help = 'workflow id')
    parser_workflow_history = workflow_parsers.add_parser('history', help = 'send a workflow history query', aliases = aliases.getAliases('history', 'workflow'))
    parser_workflow_history.add_argument('jd_workflow', help = 'workflow id')
    parser_workflow_status = workflow_parsers.add_parser('status', help = 'send a workflow status query', aliases = aliases.getAliases('status', 'workflow'))
    parser_workflow_status.add_argument('jd_workflow', help = 'workflow id')
    parser_workflow_status.add_argument('revision', help = 'workflow revision', default = None, nargs = '?')

    # config command tree
    parser_config = cmd_parsers.add_parser('config', help = 'Send a command regarding the configuration', aliases = aliases.getAliases('config'))
    config_parsers = parser_config.add_subparsers(dest = 'config', title = 'subcommands')
    parser_config_get = config_parsers.add_parser('get', help = 'send a get configuration query', aliases = aliases.getAliases('get', 'config'))
    parser_config_set = config_parsers.add_parser('set', help = 'send a set configuration query', aliases = aliases.getAliases('set', 'config'))
    parser_config_set.add_argument('--replace', '-r', action = 'store_true', help = 'if replace is set then the old config will be removed', default = False)
    parser_config_set.add_argument('--param', '-p', action = 'append', help = 'configuration_key=configuration_value', nargs = '*')
    parser_config_set.add_argument('param', action = 'append', help = 'configuration_key=configuration_value', nargs = '*')

    parser_ping = cmd_parsers.add_parser('ping', help = 'to send ping query', aliases = aliases.getAliases('ping'))

    return parser.parse_args()

# ------------------------------
# Reading command line arguments
#
def configparse(logger, cliargs):
    config = ConfigParser.ConfigParser()
    try:
        ret = config.readfp(open(cliargs.configuration))
    except IOError:
        logger.warn("Cannot open specified config file '%s'. Trying to read from '/etc/hsn2/console.conf'" % cliargs.configuration)
        try:
            ret = config.readfp(open("/etc/hsn2/console.conf"))
        except IOError:
            logger.warn("Cannot open '/etc/hsn2/console.conf'. Exiting...")
            sys.exit(2)

    return config

def main():
    # ------------------------------
    # Main
    #
    aliases = Aliases()
    # Parse command line arguments
    cliargs = cliparse(aliases)
    # Configure logging
    logger = init_logger(cliargs)

    # Parse config file
    config = configparse(logger, cliargs)

    # Configure Bus
    fwkBus = Bus.createConfigurableBus(logger, config, 'cli')

    # Main
    try:
        logger.debug("Connected to the bus.");
        disp = CommandDispatcher(fwkBus, logger, cliargs, config)
        disp.dispatch(cliargs.command, aliases)
    except BusException, e:
        logger.error("Cannot connect to HSN2 Bus because '%s'" % e)
        print "ERROR: Cannot connect to HSN2 Bus because '%s'" % e
    except BusTimeoutException, e:
        logger.error("Response timeout")
        print "ERROR: Response wait timeout"

    # Clean up
    fwkBus.close()
    logger.info("Finished")
    sys.exit(0)

if __name__ == '__main__':
    main()
