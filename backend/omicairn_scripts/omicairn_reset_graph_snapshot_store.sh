# create store folder
store_folder="$HOME/omicairn-store"

# create graph snapshot folder
graph_snapshot_folder="$store_folder/graph_snapshot"

if [ -d $graph_snapshot_folder ]; then
    rm -r $graph_snapshot_folder
fi

mkdir $graph_snapshot_folder
mkdir "$graph_snapshot_folder/image"
mkdir "$graph_snapshot_folder/scene-environment"
