from pds_pipelines.config import pds_log, slurm_log, cmd_dir

log_format = '%(asctime)s - %(name)s - %(levelname)s, %(message)s'

jobconfig = {'di': {'logger': 'di_process_hpc_job',
                    'handle': pds_log + 'DI.log',
                    'info': 'Starting DI Process HPC Job Submission',
                    'name': 'pds_di_process',
                    'stdout': slurm_log + 'di_process_%A_%a.out',
                    'stderr': slurm_log + 'di_process_%A_%a.err',
                    'memory': '4096',
                    'wallclock': '365-00:00:00',
                    'partition': 'pds',
                    'cmd': cmd_dir + 'di_process.py',
                    'SBfile': slurm_log + 'di_hpc_@date@.sbatch'},
             'upc': {'logger': 'upc_process_hpc_job',
                    'handle': pds_log + 'UPC.log',
                    'info': 'Starting UPC Process HPC Job Submission',
                    'name': 'pds_upc_process',
                    'stdout': slurm_log + 'upc_process_%A_%a.out',
                    'stderr': slurm_log + 'upc_process_%A_%a.err',
                    'memory': '4096',
                    'wallclock': '365-00:00:00',
                    'partition': 'pds',
                    'cmd': cmd_dir + 'upc_process.py',
                    'SBfile': slurm_log + 'upc_hpc_@date@.sbatch'},
             'ingest': {'logger': 'ingest_process_hpc_job',
                        'handle': pds_log + 'Ingest.log',
                        'info': 'Starting Ingest Process HPC Job Submission',
                        'name': 'pds_ingest_process',
                        'stdout': slurm_log + 'ingest_process_%A_%a.out',
                        'stderr': slurm_log + 'ingest_process_%A_%a.err',
                        'memory': '4096',
                        'wallclock': '365-00:00:00',
                        'partition': 'pds',
                        'cmd': cmd_dir + 'ingest_process.py',
                        'SBfile': slurm_log + 'ingest_hpc_@date@.sbatch'},
             'derived': {'logger': 'derived_process_hpc_job',
                        'handle': pds_log + 'Process.log',
                        'info': 'Starting Derived Process HPC Job Submission',
                        'name': 'pds_derived_process',
                        'stdout': slurm_log + 'derived_process_%A_%a.out',
                        'stderr': slurm_log + 'derived_process_%A_%a.err',
                        'memory': '4096',
                        'wallclock': '365-00:00:00',
                        'partition': 'pds',
                        'cmd': cmd_dir + 'derived_process.py',
                        'SBfile': slurm_log + 'derived_hpc_@date@.sbatch'}
             }
