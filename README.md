data_sync
=========

 This script backs up rtbkit's data logs in a remote host.
 It uses rsync through ssh and it expects that you have
 access to the remote host using a preconfigured ssh key
 with no passphrase.

 The app looks for all the files that have been rotated (closed)
 using fuser and pushes them into the remote endpoint afterwards
 it cleans up the synched files.

 The remote endoint is the endpoint where the logs are pushed to.
 So you need to set the following parameters: 
 REMOTE_USER = 'user'
 REMOTE_HOST = 'remote_host'
 REMOTE_DIR  = '/tmp/backup'
 REMOTE_SSH_PORT = 40022

 This will end up doing an rsync to user@remote_host:/tmp/backup 
 on port 40022
 You will also have to the local dir to be pushed into the remote 
 using the LOCAL_DIR parameter, ie :
 LOCAL_DIR = '/home/rtbkit/logs/data'
 
 For every run you'll get 4 log files wich names start with the run 
 date_time :
 - date_exclude.list : is the list with the files that are not going 
   to be synched since they were open when we checked. This file is 
   passed to rsync later
 - date_push_rsync.err : is stderr of the rsync execution
 - date_push_rsync.out : is stdout of the rsync execution
 - date_traffic_sync.log : is the app log
