###################################################################
# Script : data_sync.py
# Author : Nicolas Emiliani @ US Media Consulting
# Email  : nicolas.emiliani@usmediaconsulting.com
#
# This script backs up rtbkit's data logs in a remote host.
# It uses rsync through ssh and it expects that you have
# access to the remote host using a preconfigured ssh key
# with no passphrase.
#
# The app looks for all the files that have been rotated (closed)
# using fuser and pushes them into the remote endpoint afterwards
# it cleans up the synched files.
#
# The remote endoint is the endpoint where the logs are pushed to.
# So you need to set the following parameters: 
# REMOTE_USER = 'user'
# REMOTE_HOST = 'remote_host'
# REMOTE_DIR  = '/tmp/backup'
# REMOTE_SSH_PORT = 40022
#
# This will end up doing an rsync to user@remote_host:/tmp/backup 
# on port 40022
# You will also have to the local dir to be pushed into the remote 
# using the LOCAL_DIR parameter, ie :
# LOCAL_DIR = '/home/rtbkit/logs/data'
# 
# For every run you'll get 4 log files wich names start with the run 
# date_time :
# - date_exclude.list : is the list with the files that are not going 
#   to be synched since they were open when we checked. This file is 
#   passed to rsync later
# - date_push_rsync.err : is stderr of the rsync execution
# - date_push_rsync.out : is stdout of the rsync execution
# - date_traffic_sync.log : is the app log


import sys
import shutil
import os
import logging
import subprocess
import datetime

# path of the application
BASE_PATH   = os.getcwd()

# directory for the logs and exclude lists
LOG_DIR     = os.path.join(BASE_PATH, 'logs')
# directory to be synched
LOCAL_DIR   = '/home/rtbkit/logs/data'

# remote endoint data
REMOTE_USER = 'user'
REMOTE_HOST = 'remote_host'
REMOTE_DIR  = '/tmp/backup'
REMOTE_SSH_PORT = 40022

if __name__ == '__main__' :
    now = datetime.datetime.now()
    dstr = now.strftime('%Y-%m-%d_%H:%M:%S')
    # set up logging
    logging.basicConfig(
            filename=os.path.join(LOG_DIR, '%s_traffic_sync.log' % dstr),
            format='%(asctime)-15s %(levelname)s %(message)s', 
            level=logging.DEBUG)
    logger = logging.getLogger('data_sync')
    logger.warning('running data_sync')

    # first we need to check wich files are not being written to
    # so we need to walk through the directory tree and run fuser
    # on each file
    excludes = open(os.path.join(LOG_DIR, '%s_exclude.list' % dstr), 'w')
    for root, subs, files in os.walk(LOCAL_DIR):
        for f in files :
            fuser = ['fuser', os.path.join(root, f)]        
            try :
                logging.info('cheking file %s' % ' '.join(fuser))     
                proc = subprocess.Popen(
                    ' '.join(fuser), 
                    shell=True, 
                    close_fds=True,
                    stdout=subprocess.PIPE,                    
                    stderr=subprocess.PIPE)
                stderr = proc.communicate()[1]
                if stderr.find(f) != -1 :
                    logging.warning('file is being used')
                    excludes.write('%s\n' % f)
                else :
                    logging.info('file is free')
            except :
                logging.error('unable to execute : %s' % ' '.join(fuser))
    excludes.close()
    
    # we now have the list with the files that are currently being used
    # so lets push the rotated logs into our backup storage
    command = [ 'rsync', 
                '-vcrt', 
                '-e \"ssh -p %d\"' % REMOTE_SSH_PORT,
                '--exclude-from=%s' % os.path.join(
                                        LOG_DIR, '%s_exclude.list' % dstr),
                '--remove-source-files',
                os.path.join(LOCAL_DIR, '*'),
                '%s@%s:%s' % (REMOTE_USER, REMOTE_HOST, REMOTE_DIR)]
    try :
        log_file_out = open(os.path.join(LOG_DIR, 
                        '%s_push_rsync.out' % dstr), 'w')
        log_file_err = open(os.path.join(LOG_DIR, 
                        '%s_push_rsync.err' % dstr), 'w')
        logging.info('executing push : %s', ' '.join(command))     
        proc = subprocess.Popen(
            ' '.join(command),
            shell=True, 
            close_fds=True,
            stderr=log_file_err,
            stdout=log_file_out)
        proc.wait()
        logging.info('return code : %d', proc.returncode)
        log_file_out.close()
        log_file_err.close()
    except :
        logging.critical('unable to push to remote end')
        sys.exit(1)
