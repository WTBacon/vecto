import fnmatch
import os
import pathlib
import tarfile
from zipfile import ZipFile
import logging
import tempfile
# from vecto.config import load_config
from vecto.utils.metadata import WithMetaData
from vecto.utils.data import load_json
from .io import fetch_file

logger = logging.getLogger(__name__)
# TODO: make config module-global
# config = load_config()
# TODO: get dataset dir from config
dir_datasets = os.path.expanduser("~/.vecto/datasets")
dir_temp = os.path.join(tempfile.gettempdir(), "vecto", "tmp")
os.makedirs(dir_datasets, exist_ok=True)
os.makedirs(dir_temp, exist_ok=True)
resources = {}

class Dataset(WithMetaData):
    """
    Container class for stock datasets.
    Arguments:
        path (str): local path to place files
    """

    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError("test dataset dir does not exist:" + path)
        super().__init__(path)
        self.path = path

    def file_iterator(self):
        for root, _, filenames in os.walk(self.path):
            for filename in fnmatch.filter(sorted(filenames), '*'):
                if filename.endswith('json'):
                    continue
                yield(os.path.join(root, filename))


def download_index():
    logger.info("downloading index of resources")
    path_tar = os.path.join(dir_temp, "resources.tar")
    url_resources = "https://github.com/vecto-ai/vecto-resources/tarball/master/"
    fetch_file(url_resources, path_tar)
    with tarfile.open(path_tar) as tar:
        for member in tar.getmembers():
            parts = member.name.split("/")
            if len(parts) <= 1: 
                continue
            if parts[1] != "resources":
                continue
            member.path = os.path.join(*parts[1:])
            tar.extract(member, dir_datasets)


def gen_metadata_snippets(path):
#    for name in os.listdir(path):
    for sub in path.iterdir():
        if sub.name == "metadata.json":
            yield sub
        else:
            if os.path.isdir(sub):
                yield from gen_metadata_snippets(sub)

def load_dataset_infos():
    for f_meta in gen_metadata_snippets(pathlib.Path(dir_datasets)):
        # print("visiting", f_meta.parent)
        metadata = load_json(f_meta)
        if "name" in metadata:
            # print("name: ", metadata["name"])
            if "url" in metadata:
                # print("url: ", metadata["url"])
                # print("folder: ", f_meta.parent)
                metadata["local_path"] = f_meta.parent
                resources[metadata["name"]] = metadata
                # check if files are not there
                # fownload
        print()

def download_dataset_by_name(name):
    filename = resources[name]["url"].split("/")[-1]
    print("down", filename)
    path_download_archive = os.path.join(dir_temp,filename)
    # fetch_file(resources[name]["url"], path_download_archive)
    # TODO: unzip
    with ZipFile(path_download_archive) as z:
        z.extractall(os.path.join(dir_temp, name))

def is_dataset_downloaded(path_dataset):
    for f in path_dataset.iterdir():
        if f.name.endswith("metadata.json"):
            continue
        return True
    return False

def get_dataset_by_name(name):
    load_dataset_infos()
    if not resources:
        logger.info("index not found, forcing download")
        download_index()
        load_dataset_infos()
    # print(resources)
    if name in resources:
        path_dataset = resources[name]["local_path"]
    else:
        raise RuntimeError("Dataset %s not known" % name)
    # TODO: refactor this into intuitive method
    if not is_dataset_downloaded(path_dataset):
        logger.info("only metadata is present, need to download")
        download_dataset_by_name(name)
    dataset = Dataset(path_dataset)
    return dataset
