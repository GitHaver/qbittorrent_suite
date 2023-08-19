from classes.Torrent import Torrent


class Torrents:
    def __init__(self, qbit_client, config):
        self.qbit_client = qbit_client
        self.raw_torrents = qbit_client.torrents_info()

        self.torrents_by_tracker = {}
        for raw_torrent in self.raw_torrents:
            torrent = Torrent(raw_torrent, qbit_client, config)
            if torrent.tracker not in self.torrents_by_tracker:
                self.torrents_by_tracker[torrent.tracker] = [torrent]
            else:
                self.torrents_by_tracker[torrent.tracker].append(torrent)



if __name__ == '__main__':
    from classes.Config import Config
    _config = Config()
    from lib.lib import connect_to_qbittorrent
    _qbit_client = connect_to_qbittorrent(**_config.connection_info)
    _torrents = Torrents(_qbit_client, _config)
    for _tracker in _torrents.torrents_by_tracker:
        print(_tracker)
        for _torrent in _torrents.torrents_by_tracker[_tracker]:
            print(f"\t{_torrent.name}")
