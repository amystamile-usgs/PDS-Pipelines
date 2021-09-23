import os
from pathlib import Path

# Database credentials
credentials = {'upc_test': {'user': 'postgres',
                            'pass': '',
                            'host': 'localhost',
                            'port': '5432',
                            'db': 'upc_test'},
               'di_test': {'user': 'postgres',
                           'pass': '',
                           'host': 'localhost',
                           'port': '5432',
                           'db': 'di_test'},
               'clusterjob_test': {'user': 'postgres',
                                   'pass': '',
                                   'host': 'localhost',
                                   'port': '5432',
                                   'db': 'clusterjobs_test'}
              }

# The key for the database credentials used for the pds database
pds_db = 'di_test'
# The key for the database credentials used for the upc database
upc_db = 'upc_test'
# The key for the database credentials used for the cluster jobs database
cluster_db = 'clusterjob_test'


# Redis server info
redis_info = {'host': 'localhost', 'port': '6379', 'db': '0'}


# POW / MAP2 base path
pow_map2_base = '/pds_san/PDS_Services/'
# The base URL at which processed images will be hosted
web_base = 'https://pdsimage.wr.usgs.gov/Missions/'
# The local network location in which unprocessed products are located
archive_base = '/pds_san/PDS_Archive/'
# The local network location in which derived (POW/MAP) products will be stored
derived_base = '/pds_san/PDS_Derived/UPC/images/'
# The URL at which derived (POW/MAP) products will be hosted
derived_url = 'https://upcimages.wr.usgs.gov/'
# The location in which links generated by link_artifacts.py will be stored
link_dest = '/pds_san/PDS_Archive_Links/'


# The project root.  The 'main' folder containing source, log, and output subdirectories.
#  e.g. '/home/some_user/pds_pipelines' will lead to logs stored in '/home/some_user/pds_pipelines/logs'
root = Path(__file__).parent.parent


##
# These paths should only be changed by users who desire non-standard functionality.
#  By default, they depend on the root defined above, and will result in the
#  "standard" directory structure in which all subdirectories are children of root.
##

# The location in which processing recipes are stored
recipe_base = os.path.join(root, 'recipe/')
# The location of the PDSinfo.json file
pds_info = os.path.join(root, 'pds_pipelines/PDSinfo.json')
# The directory in which logs will be written.
pds_log = os.path.join(root, 'logs/')
# The directory in which slurm output will be written
slurm_log = os.path.join(root, 'output/')
# The directory containing python source files
cmd_dir = os.path.join(root, 'pds_pipelines/')


# The location to which temporary / working files will be written or copied
scratch = '/scratch/pds_services/'
workarea = os.path.join(scratch, 'workarea/')


# The namespace of redis queues.  Namespace, in this context, is a prefix used
#  to identify a queue (namespace:queue_name)
default_namespace = 'adampaquette_queue'


# The name of the redis queue used to store process lock information
lock_obj = 'processes'


# The name of the queue to which error information will be written
upc_error_queue = 'UPC_ErrorQueue'


# The allowable ratio of used:total disk space for processes that copy files.
#  If copying a file / set of files into 'dest' would use more than the specified
#  disk usage ratio, the script will notify the user and exit without copying.
disk_usage_ratio = 0.4


# Path to which JSON summary views are written
summaries_path = '/pds_san/PDS_Derived/UPC/images/summaries/'
