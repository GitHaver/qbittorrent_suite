from classes.torrent import Torrent


class Torrents:
    def __init__(self, qbit_client, config):
        self.qbit_client = qbit_client
        self.raw_torrents = qbit_client.torrents_info()

        self.torrents_by_tracker = {}
        for raw_torrent in self.raw_torrents:
            torrent = Torrent(raw_torrent['hash'], qbit_client, config)
            if torrent.private_tracker:
                if torrent.private_tracker not in self.torrents_by_tracker:
                    self.torrents_by_tracker[torrent.private_tracker] = [torrent]
                else:
                    self.torrents_by_tracker[torrent.private_tracker].append(torrent)
            else:
                if 'non-private' not in self.torrents_by_tracker:
                    self.torrents_by_tracker['non-private'] = [torrent]
                else:
                    self.torrents_by_tracker['non-private'].append(torrent)


if __name__ == '__main__':
    from classes.config import Config
    _config = Config()
    from lib.lib import connect_to_qbittorrent
    _qbit_client = connect_to_qbittorrent(**_config.connection_info)
    _torrents = Torrents(_qbit_client, _config)
    print(_torrents.torrents_by_tracker)