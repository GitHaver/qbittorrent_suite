cd ..

username="GitHaver"
pat=$(cat pat.txt)
repo="github.com/GitHaver/qbittorrent_suite.git"

# Clone the repo with an echo statement, to a temp folder
echo "Cloning repo..."
git clone https://"$username":"$pat"@"$repo" temp

# if any errors, exit
if [ $? -ne 0 ]; then
    echo "Error cloning repo. Exiting..."
    exit 1
fi

clone_dir="temp"

echo "Updating files..."
rsync -av --delete --exclude "config.yaml" --exclude "setup/pat.txt" --exclude "$clone_dir" "$clone_dir/"

# delete the temp folder
rm -rf "$clone_dir"


