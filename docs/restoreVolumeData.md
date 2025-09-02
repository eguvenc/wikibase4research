Whenever you run `./wiki.sh <projectPath> remove`, all docker containers and volumes are deleted (`docker compose down -v`).
In case you used the docker compose down command to remove the wiki containers but kept the docker volumes, you can restore that data to your wiki after rebuild it using the `setup` action.
To copy data from one volume to another, execute the following steps:

# show all docker volumes
`docker volume ls`

# inspect all volumes to find the volume id that you want to use as a data source
`docker volume inspect <volume_id>`

# optional: check the db data files to ensure, your data is there
`cd /var/lib/docker/volume/<volume_id>/_data`
`ls -al`
`less wiki/<db_table>.idb`

# show container to identify database container_id
`docker ps `

# identify volume id, currently used by the database container (here named current_volume_id)
`docker inspect <database_container_id>`

# stop the wiki
`cd /home/gitlab/wikibase4research`
`./wiki.sh <project_folder> stop`

# backup data
`mkdir volumebackup`
`cp /var/lib/docker/volumes/<current_volume_id> /home/gitlab/volumebackup/ -r`

# copy old volume data to new volume data
# !!! this will replace the whole volume data, make sure you want this !!!
`cp /var/lib/docker/volumes/<old_volume_id>/_data/* /var/lib/docker/volumes/<current_volume_id>/_data -r`
OR
`cp /var/lib/docker/volumes/<old_volume_id>/_data /var/lib/docker/volumes/<current_volume_id> -r`

#start the wiki
`./wiki.sh <project_folder> start`