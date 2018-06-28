# This file contains the  that is used to run the framework
# based on user inputs from the command line.

from __future__ import print_function

import sys
import logging
import os
import time

from src.core.traffic_generator import Trex
if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    from src.core.traffic_generator.trex_client.stl.trex_automated import *
from src.env_conf import settings
from src.util import LogUtil, ParserUtil, DbUtil, HostSession
from src.usecases import host_optimizations
from src.usecases import vm_deploy, traffic_config
from src.usecases import vm_optimizations,monitoring
from src.usecases import tech_support, reporting
from src.core.traffic_generator import Trex, Spirent
from src.core.traffic_generator.trex_client.stl import trex_v3



def main():
    """
    Main Script that controls the framework execution; This is the starting point of the framework.
    """
    args = ParserUtil.Parser(__file__).parse_cmd_args()
    logger1 = logging.getLogger()

    # configure settings
    print("Loading configuration file values in current session...")
    settings.load_from_dir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src', 'env_conf'))
    print("Done.")

    # if required, handle list-* operations
    print("Scanning for command line arguments...")
    ParserUtil.Parser().process_cmd_switches(args)
    print("Done.")
    if args['generate_support_bundle']:
        print(args['generate_support_bundle'])
    if args['verbose']:
        LogUtil.LogUtil().configure_logging(logger1, 'debug')
    else:
        LogUtil.LogUtil().configure_logging(logger1, settings.getValue('VERBOSITY'))

    logger = LogUtil.LogUtil()
    # Check if there are any specific operations to perform, otherwise continue the normal framework execution.
    if args['generate_support_bundle']:
        tech_support.TechSupport().generate_tech_support('host', args['generate_support_bundle'])
    if args['perform']:
        # Apply host optimizations based on host.json file.
        if args['perform'] == 'host_optimization':
            logger.info('Initiating host optimizations.')
            splittx = False
            splitrx = False
            rss = False
            if args['host_optimization_type']:
                splittx = 'splittx' in args['host_optimization_type']
                splitrx = 'splitrx' in args['host_optimization_type']
                rss = 'rss' in args['host_optimization_type']
            if host_optimizations.host_config(splitrx = splitrx, splittx = splittx, rss = rss) == False:
                logger.error('Unable to configure host optimizations.')
                print('Unable to configure host optimizations. See logs for more details.')
            else:
                logger.info('Host optimizations successful.')
                print('Host optimizations successful.')
            sys.exit(0)

        # Deploy vnfs based on the vnf.json file.
        if args['perform'] == 'vm_deploy':
            logger.info('Initiating VM deployment on host')
            if vm_deploy.VMDeploy().deploy_vm() == False:
                logger.error('Unable to deploy VM.')
                print('Unable to deploy VM. See logs for more details.')
                sys.exit(0)
            else:
                logger.info('VM Deployment complete')
        
        # Apply VM optimizations based on vm.json file.
        if args['perform'] == 'vm_optimization':
            logger.info('Initiating VM optimization')
            vm_optimizations.vm_config()
            logger.info('VM optimization complete')

        # Run traffic from traffic generator based on traffic_config.json file.
        if 'traffic_run' in args['perform']:
            logger.info('Setting up DPDK application on VM(s)')
            logger.info('Setting up traffic profile and initiating traffic run.')
            print('Initiating traffic from spirent')
            traffic_config.test_run(testcase=args['perform'].split()[1], restart = True)
            """result = Spirent.spirent_util(tc=args['perform'].split()[1], rfc=True, restart = True)
            config = {}
            client = HostSession.HostSession().connect('192.168.11.4', 'root', 'ca$hc0w', False)
            config['host'] = host_optimizations.get_host_config(printdata=False)
            config['vm'] = vm_optimizations.get_env_data(client, settings.getValue('VM_TOPOLOGY')['VM_DETAILS'][0]['VM_NAME'])
            HostSession.HostSession().disconnect(client)
            print(DbUtil.db_util(result['data'], config))"""

        # Generate support bundle.
        if args['perform'] == 'generate_support_bundle':
            logger.info('Generating support bundle')
            tech_support.TechSupport().generate_tech_support('Host')
            sys.exit(0)

        # Perform Monitoring.
        if args['perform'] == 'monitoring':
            Trex.Trex().specify_dest_mac()
            sys.exit(0)

        # Perform Reporting.
        if args['perform'] == 'reporting':
            reporting.Report().get_excel()
            sys.exit(0)

    if args['testcase']:
        print(args['testcase'])
        tcase = settings.getValue('TRAFFIC_PROFILE')
        for tc in tcase:
            if args['testcase'] in tc['TESTCASE']:
                # Host Config
                logger.info('Initiating host optimizations.')
                splittx = False
                splitrx = False
                rss = False
                if args['host_optimization_type']:
                    splittx = 'splittx' in args['host_optimization_type']
                    splitrx = 'splitrx' in args['host_optimization_type']
                    rss = 'rss' in args['host_optimization_type']
                if host_optimizations.host_config(splitrx = splitrx, splittx = splittx, rss = rss) == False:
                    logger.error('Unable to configure host optimizations.')
                    print('Unable to configure host optimizations. See logs for more details.')
                    sys.exit(0)
                else:
                    logger.info('Host optimizations successful.')
                    print('Host optimizations successful.')
                # VM deploy
                logger.info('Initiating VM deployment on host')
                if vm_deploy.VMDeploy().deploy_vm() == False:
                    logger.error('Unable to deploy VM.')
                    print('Unable to deploy VM. See logs for more details.')
                    sys.exit(0)
                else:
                    logger.info('VM Deployment complete. Waiting for IP configurations to take place...')
                    time.sleep(60)
                logger.info('Initiating VM optimization')
                vm_optimizations.vm_config()
                logger.info('VM optimization complete')
                Spirent.stc_util()
                #trex = Trex.Trex()
                #trex.trafficGen()
                sys.exit(0)


#if __name__ == 'main':
main()
