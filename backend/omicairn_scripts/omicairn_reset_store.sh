store_folder="$HOME/omicairn-store"

attached_data_folder="$store_folder/attached_data"

if [ -d "$attached_data_folder" ]; then
    rm -r $attached_data_folder
fi

mkdir $attached_data_folder

mkdir $attached_data_folder/genesets
mkdir $attached_data_folder/cellsets
mkdir $attached_data_folder/compution_params
mkdir $attached_data_folder/dependencies_versions
mkdir $attached_data_folder/graph_snap
