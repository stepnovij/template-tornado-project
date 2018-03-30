import os
import collections
import time

from concurrent.futures import ThreadPoolExecutor
from tornado import concurrent

from utils import generate_hash

DataSet = collections.namedtuple('DataSet', ['original', 'translation', 'lang_from', 'lang_to'])


class BaseStorage:

    def open(self, *args, **kwargs):
        raise NotImplemented

    def save(self, *args, **kwargs):
        raise NotImplemented


class DefaultStorage(BaseStorage):
    DATA_SET_BASE_PATH = os.path.join(os.getcwd(), 'data_set')
    RESULTS_BASE_PATH = os.path.join(os.getcwd(), 'results')

    def __init__(self, *args, **kwargs):
        self.data_set_base_path = kwargs.get('data_set_base_path', self.DATA_SET_BASE_PATH)
        self.results_base_path = kwargs.get('results_base_path', self.RESULTS_BASE_PATH)

    def _generate_name(self, name):
        return '{}.txt'.format(generate_hash(name))

    def _get_path(self, data_set_id):
        dat_set_dir = os.path.join(self.data_set_base_path, str(data_set_id))
        # currently only on file per folder is supported
        try:
            file_path = os.listdir(dat_set_dir)[0]
            full_path = os.path.join(dat_set_dir, file_path)
        except FileNotFoundError:
            full_path = None
        return full_path

    def get_file_name(self, data_set_id):
        file_name = os.path.basename(self._get_path(data_set_id))
        return file_name

    def _process_line(self, line):
        sentences = [sentence.strip() for sentence in line.decode().split('\t')]
        return sentences[0], sentences[1]

    def open(self, data_set_id, mode='rb'):
        file_path = self._get_path(data_set_id)
        if file_path is None:
            return
        #
        result = []
        with open(file_path, mode) as fd:
            for line in fd:
                result.append(self._process_line(line))
        return result

    def save(self, provider_id, data_set_id, data):

        current_time = str(int(time.time()))
        hashed_time = self._generate_name(current_time)
        full_path = os.path.join(
            *[self.results_base_path, provider_id, str(data_set_id), current_time, hashed_time]
        )
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        return self._save(full_path, data)

    def _save(self, full_path, data):
        with open(full_path, 'wb') as fd:
            fd.write('\n'.join(data).encode())
        return full_path


class Manager:
    def __init__(self, *args, **kwargs):
        self.storage = kwargs.get('storage', DefaultStorage())
        self.executor = ThreadPoolExecutor(max_workers=4)

    def get_from_to_languages(self, data_set_id):
        file_name, ext = os.path.splitext(self.storage.get_file_name(data_set_id))
        lang_from, lang_to = file_name.split('-')
        return lang_from, lang_to

    @concurrent.run_on_executor
    def get_data_set(self, data_set_id):
        result = self.storage.open(data_set_id)
        lang_from, lang_to = self.get_from_to_languages(data_set_id)
        original = []
        translation = []

        for line in result:
            orig, transl = line
            original.append(orig)
            translation.append(transl)

        return DataSet(original=original, translation=translation,
                       lang_from=lang_from, lang_to=lang_to)

    @concurrent.run_on_executor
    def save(self, data_set_id, response_data):
        if isinstance(response_data, list):
            saved_data = []
            for result in response_data:
                provider_id = result['service']['provider']
                saved_data.append(self.storage.save(provider_id, data_set_id, response_data))
            return saved_data
        return self.storage.save(response_data['service']['provider']['id'],
                                 data_set_id, response_data)