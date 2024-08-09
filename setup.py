from setuptools import setup


with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='stealth-requests',
    description='Make HTTP requests exactly like a browser.',
    version='0.1',
    packages=['stealth_requests'],
    install_requires=['curl_cffi'],
    extras_require={
        'parsers': [
            'lxml',
            'html2text',
            'beautifulsoup4'
        ]
    },
    author = 'Jacob Padilla',
    author_email = 'jp@jacobpadilla.com',
    url='https://github.com/jpjacobpadilla/Stealth-Requests',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=''
)