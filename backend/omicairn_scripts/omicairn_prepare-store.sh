# create store folder
store_folder="$HOME/omicairn-store"

if [ ! -d $store_folder ]; then
    mkdir $store_folder
fi

# create data folder and example data backup folder
data_folder="$store_folder/adata"

data_backup_folder="$store_folder/data-backup"

if [ ! -d "$data_folder" ]; then
    mkdir $data_folder
fi

attached_data_folder="$store_folder/attached_data"

if [ ! -d $attached_data_folder ]; then
    mkdir $attached_data_folder
fi

if [ ! -d $attached_data_folder/genesets ]; then
    mkdir $attached_data_folder/genesets
fi

if [ ! -d $attached_data_folder/cellsets ]; then
    mkdir $attached_data_folder/cellsets
fi

if [ ! -d $attached_data_folder/compution_params ]; then
    mkdir $attached_data_folder/compution_params
fi

if [ ! -d $attached_data_folder/dependencies_versions ]; then
    mkdir $attached_data_folder/dependencies_versions
fi

if [ ! -d $attached_data_folder/graph_snapshot ]; then
    mkdir $attached_data_folder/graph_snapshot
fi

# create temp file folder
temp_file_folder="$store_folder/temps"
if [ ! -d $temp_file_folder ]; then
    # $temp_file_folder does not exist, create it .
    mkdir $temp_file_folder
fi

# create graph_snapshot folder
graph_snapshot_folder="$store_folder/graph_snapshot"
if [ ! -d $graph_snapshot_folder ]; then
    mkdir $graph_snapshot_folder
fi

if [ ! -d "$graph_snapshot_folder/image" ]; then
    mkdir "$graph_snapshot_folder/image"
fi

if [ ! -d "$graph_snapshot_folder/scene-environment" ]; then
    mkdir "$graph_snapshot_folder/scene-environment"
fi
