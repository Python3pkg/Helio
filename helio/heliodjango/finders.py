import re
from os import walk
from os.path import join, exists, basename, splitext
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.finders import BaseFinder
from django.template.loaders.filesystem import Loader
from helio.settings import COMPONENT_BASE_DIRECTORIES


def walk_component_base_dir(component_base_dir):
    for (dir_root, dir_list, file_list) in walk(component_base_dir):
        if basename(dir_root) == 'static':
            yield dir_root, dir_list, file_list


def should_ignore_file(static_file, ignore_patterns):
    for pattern in ignore_patterns:
        if pattern.match(static_file):
            return True

    return False


class ComponentStaticFinder(BaseFinder):
    def __init__(self,):
        self.component_base_directories = COMPONENT_BASE_DIRECTORIES

    def find(self, path, all=False):
        split_path = path.split('/')

        if len(split_path) < 2:
            return

        component_dir = '/'.join(split_path[:-1])

        all_components = []

        for component_base_dir in self.component_base_directories:
            full_path = join(component_base_dir, component_dir, 'static', split_path[-1])
            if exists(full_path):
                if all:
                    all_components.append(full_path)
                else:
                    return full_path

        return all_components or ()

    def list(self, ignore_patterns):
        re_patterns = []

        for pattern in ignore_patterns:
            if pattern.startswith('*'):
                re_pattern = re.compile(pattern[1:].replace('.', '\\.') + '$')
            elif pattern.endswith('*'):
                re_pattern = re.compile('^' + pattern[:-1].replace('.', '\\.'))
            else:
                re_pattern = re.compile(pattern)

            if re_pattern is not None:
                re_patterns.append(re_pattern)

        for component_base_dir in self.component_base_directories:
            for (dir_root, dir_list, file_list) in walk_component_base_dir(component_base_dir):
                for static_file in file_list:
                    if should_ignore_file(static_file, re_patterns):
                        continue

                    full_static_path = join(dir_root, static_file)

                    res = re.search(r'/(.*)/static', full_static_path)
                    if res is None:
                        continue

                    storage = FileSystemStorage(location=dir_root)
                    storage.prefix = res.group(1)
                    yield (static_file, storage)


class ComponentTemplateLoader(Loader):
    is_usable = True

    def __init__(self):
        self.component_base_directories = COMPONENT_BASE_DIRECTORIES

    def get_template_sources(self, template_name, template_dirs=None):
        split_template_name = template_name.split('/')

        if len(split_template_name) == 1:
            component_name, ext = splitext(split_template_name[-1])
            final_template_name = component_name.split('.')[-1] + ext
        else:
            component_name = split_template_name[0]
            final_template_name = '/'.join(split_template_name[1:])

        component_dir = component_name.replace('.', '/')

        for component_base_dir in self.component_base_directories:
            yield join(component_base_dir, component_dir, final_template_name)