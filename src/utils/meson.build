pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
utilsdir = join_paths(pkgdatadir, 'bottles/utils')

bottles_sources = [
  '__init__.py',
  'connection.py',
  'gtk.py',
  'threading.py',
  'common.py',
]

install_data(bottles_sources, install_dir: utilsdir)
