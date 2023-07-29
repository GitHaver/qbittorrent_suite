import sys
import qbittorrentapi
from classes.config import Config

is_iptorrents = False
try:
    torrent_file = sys.argv[1]
except IndexError: # use tkinter filedialog to select a file
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    torrent_file = filedialog.askopenfilename()



print("\n============================================================\n"
      "Torrent file: ", torrent_file, '\n')

torrent_name = torrent_file.split('\\')[-1].replace('.torrent', '')

config = Config()

if ' [IPT]' in torrent_name:
    torrent_name = torrent_name.replace(' [IPT]', '')
    is_iptorrents = True

qbit_client = qbittorrentapi.Client(**config.connection_info)

print(f"Connecting to qBittorrent...")

try:
    qbit_client.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    print("Unable to connect: \n", e)
    sys.exit()

print("Connected to qBittorrent\n")

print("Adding Torrent: ", torrent_name, "\n")

check = qbit_client.torrents_add(torrent_files=torrent_file)
if check != "Fails.":
    print("Torrent successfully added.\n")

else:
    print('Failed to add torrent - was it already added?\n')

while True:
    category = input("Enter a category: \n1. Movie\n2. TV\n3. Anime\n4. Music\n5. Other\n")
    if category == "1":
        category = "Movie"
        break
    elif category == "2":
        category = "TV"
        break
    elif category == "3":
        category = "Anime"
        break
    elif category == "4":
        category = "Music"
        break
    elif category == "5":
        category = "Other"
        break
    else:
        print("Invalid input, please try again.")

torrents = qbit_client.torrents_info()
added_torrent = sorted(torrents, key=lambda x: x.added_on)[-1]

print(f"\nAdding tag {category} to torrent {added_torrent['name']}")
qbit_client.torrents_add_tags(tags=category, torrent_hashes=added_torrent['hash'])
if is_iptorrents:
    qbit_client.torrents_add_tags(tags="IPT", torrent_hashes=added_torrent['hash'])

wait = input("Press enter to exit.")
