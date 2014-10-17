from setuptools import setup

setup(
    name='jsonecho',
    scripts=['jsonecho.py'],
    entry_points={'wex':['jsonecho = jsonecho:echo']},
)
