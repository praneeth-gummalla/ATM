from __future__ import print_function
import argparse
import os
import random
from os.path import join

from atm.config import *
from atm.database import Database
from atm.enter_data import enter_datarun

from utilities import *


CONF_DIR = 'config/test/btb/'
RUN_CONFIG = join(CONF_DIR, 'run.yaml')
SQL_CONFIG = join(CONF_DIR, 'sql.yaml')

DATASETS_MAX_FIRST = [
    'collins_1.csv',
    'cpu_1.csv',
    'vowel_1.csv',
    'car_2.csv',
    'hill-valley_2.csv',
    'rabe_97_1.csv',
    'monks-problems-2_1.csv',
    # these datasets do not have baseline numbers
    #'wine_1.csv',
    #'balance-scale_1.csv',
    #'seeds_1.csv',
]


def btb_test(dataruns=None, datasets=None, processes=1, graph=False, **kwargs):
    """
    Run a test datarun using the chosen tuner and selector, and compare it to
    the baseline performance.

    Tuner and selector will be specified in **kwargs, along with the rest of the
    standard datarun arguments.
    """
    sql_conf, run_conf, _ = load_config(sql_path=SQL_CONFIG,
                                        run_path=RUN_CONFIG,
                                        **kwargs)

    db = Database(**vars(sql_conf))
    datarun_ids = dataruns or []
    datasets = datasets or DATASETS_MAX_FIRST

    # if necessary, generate datasets and dataruns
    if not datarun_ids:
        for ds in datasets:
            run_conf.train_path = DATA_URL + ds
            run_conf.dataset_id = None
            print('Creating datarun for', run_conf.train_path)
            datarun_ids.append(enter_datarun(sql_conf, run_conf))

    # work on the dataruns til they're done
    print('Working on %d dataruns' % len(datarun_ids))
    work_parallel(db=db, datarun_ids=datarun_ids, n_procs=processes)
    print('Finished!')

    results = {}

    # compute and maybe graph the results
    for rid in datarun_ids:
        res = report_auc_vs_baseline(db, rid, graph=graph)
        results[rid] = {'test': res[0], 'baseline': res[1]}

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
    Test the performance of an AutoML method and compare it to the baseline
    performance curve.
    ''')
    parser.add_argument('--processes', help='number of processes to run concurrently',
                        type=int, default=1)
    parser.add_argument('--graph', action='store_true', default=False,
                        help='if this flag is inculded, graph the best-so-far '
                        'results of each datarun against the baseline.')
    parser.add_argument('--dataruns', nargs='+', type=int,
                        help='(optional) IDs of previously-created dataruns to '
                        'graph. If this option is included, no new dataruns '
                        'will be created, but any of the specified dataruns '
                        'will be finished if they are not already.')
    parser.add_argument('--datasets', nargs='+',
                        help='(optional) file names of training data to use. '
                        'Each should be a csv file present in the downloaded/ '
                        'folder of the HDI project S3 bucket '
                        '(https://s3.amazonaws.com/mit-dai-delphi-datastore/downloaded/).'
                        'The default is to use the files in DATASETS_MAX_FIRST.')
    add_arguments_datarun(parser)
    args = parser.parse_args()

    btb_test(**vars(args))
