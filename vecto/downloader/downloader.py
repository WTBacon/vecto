from zipfile import ZipFile
from requests import get
from os import path, walk, sep, mkdir, getcwd, makedirs
from git import Git
from git.exc import GitCommandError, GitCommandNotFound
from vecto.utils.metadata import WithMetaData
from functools import reduce
from vecto.downloader.resources import Resources
from vecto.utils.filesystem import rmtree
from json import load


class Downloader:
    def __init__(self, storage_dir=path.join(getcwd(), 'data', 'download')):
        self.path_to_repo = 'https://github.com/vecto-ai/vecto-resources.git'
        self.storage_dir = storage_dir
        self.resources = None
        self.full_resource_path = path.join('vecto-resources', 'resources')
        self.git_repo = Git(self.storage_dir)
        self.last_downloaded = None

    def log(self, stage, verbose=True):
        if not verbose:
            return
        if stage == 'fetch':
            print('Successfully fetched metadata to {}'.format(self.storage_dir))
        elif stage == 'replace':
            print('Removed previously fetched metdata.')
        elif stage == 'download':
            print('Successfully downloaded {}'.format(self.last_downloaded))

    def fetch_metadata(self, replace=False, verbose=True):
        while True:
            try:
                self.git_repo.clone(self.path_to_repo)
                self.log('fetch', verbose)
                break
            except GitCommandNotFound:
                makedirs(self.storage_dir)
            except GitCommandError:
                if replace:
                    rmtree(self.storage_dir)
                    mkdir(self.storage_dir)
                    self.log('replace', verbose)
                else:
                    break

    def unarchive(self, input_dir, archive_type='.zip'):
        if archive_type == '.zip':
            with ZipFile(input_dir, '') as z:
                z.extractall(self.storage_dir)

    def download_resource(self, resource_name, verbose=True):
        resource_metadata = WithMetaData()
        resource_metadata.load_metadata(path.join(self.storage_dir, 'vecto-resources', *resource_name, 'metadata.json'))
        path_dir = path.join(self.storage_dir, 'vecto-resources', *resource_name)
        with open(path.join(path_dir, 'metadata.json')) as f:
            q = load(f)
        output_file = q['url'].split('/')[~0]
        self.fetch_file(q['url'], path_dir, output_file)
        self.last_downloaded = path.join(*resource_name, output_file)
        self.log('download', verbose)

    @classmethod
    def fetch_file(self, url, path_dir, output_file, chunk_size=512):
        response = get(url, stream=True)
        handle = open(path.join(path_dir, output_file), 'wb')
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                handle.write(chunk)
        handle.close()

    def update_directory_structure(self):
        dir_struct = {}
        repo_storage_dir = path.join(self.storage_dir, self.full_resource_path)
        rootdir = repo_storage_dir.rstrip(sep)
        start = rootdir.rfind(sep) + 1
        for filepath, dirs, files in walk(rootdir):
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']
            folders = filepath[start:].split(sep)
            subdir = dict.fromkeys(files)
            parent = reduce(dict.get, folders[:-1], dir_struct)
            if None in subdir.values():
                parent[folders[-1]] = folders
            else:
                parent[folders[-1]] = subdir
        self.resources = Resources.wrap(dir_struct)

    def get_resources(self):
        return self.resources
