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

# if temp/requirements.txt is different, set a var to update the venv later
if ! cmp -s setup/requirements.txt "$clone_dir"/setup/requirements.txt; then
    echo "requirements.txt is different."
    update_venv=true
fi

echo "Updating files..."
rsync -av --delete \
  --exclude "config.yaml" \
  --exclude "setup/pat.txt" \
  --exclude "$clone_dir" \
  --exclude "venv" \
  "$clone_dir/"

# delete the temp folder
rm -rf "$clone_dir"

# if update_venv is true, activate and update the venv
if [ "$update_venv" = true ]; then
    echo "Updating venv..."
    source venv/bin/activate
    pip install -r setup/requirements.txt
fi


