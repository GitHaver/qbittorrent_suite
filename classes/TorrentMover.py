class TorrentMover:
    def __init__(self, torrent):
        self.config = torrent.config
        self.client = torrent.client
        self.torrent = torrent

        self.torrent_files = []
        self.files = []
        self.get_torrent_files()

    def get_torrent_files(self):
        self.torrent_files = self.client.torrents_files(hash=self.torrent.hash)
        for file in self.torrent_files:
            t_file = TorrentFile(file, self.torrent.content_path)
            self.files.append(t_file)

    def determine_file_type(self):
        # check all file types and set a flag for each type present
        # if more than one type is present, set a flag for 'mixed'
        # if no type is present, set a flag for 'other'
        video_files = [file for file in self.files if file.type == 'video']
        subtitle_files = [file for file in self.files if file.type == 'subtitle']
        audio_files = [file for file in self.files if file.type == 'audio']
        archive_files = [file for file in self.files if file.type == 'archive']
        other_files = [file for file in self.files if file.type == 'other']

        if len(video_files) > 0:
            self.video = True
        if len(subtitle_files) > 0:
            self.subtitle = True
        if len(audio_files) > 0:
            self.audio = True
        if len(archive_files) > 0:
            self.archive = True
        if len(other_files) > 0:
            self.other = True

class TorrentFile:
    def __init__(self, file, content_path):
        self.file = file['name']
        self.size = file['size']
        torrent_paths = self.file.split('/')
        self.file_name = torrent_paths[-1]
        self.file_path = content_path + '/'
        self.file_path += '/'.join(torrent_paths[:-1])
        print(self.file_path)
        if self.file_name.endswith('.mkv', '.mp4', '.avi'):
            self.file.type = 'video'
        elif self.file_name.endswith('.srt'):
            self.file.type = 'subtitle'
        elif self.file_name.endswith('.mp3', '.flac'):
            self.file.type = 'audio'
        elif self.file_name.endswith('.rar', '.zip'):
            self.file.type = 'archive'
        else:
            self.file.type = 'other'