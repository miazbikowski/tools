import httplib2
import os
import re
import threading
import urllib
from urlparse import urlparse, urljoin
from BeautifulSoup import BeautifulSoup

class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance

class ImageDownloaderThread(threading.Thread):
    """A thread for downloading images in parallel."""
    def __init__(self, thread_id, name, counter):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        print 'Starting thread ', self.name
        download_images(self.name)
        print 'Finished thread ', self.name

def traverse_site(max_links=10):
    link_parser_singleton = Singleton()

    # While we have pages to parse in queue
    while link_parser_singleton.queue_to_parse:
        # If collected enough links to download images, return
        if len(link_parser_singleton.to_visit) == max_links:
            "That's enough, piggy."
            return

        url = link_parser_singleton.queue_to_parse.pop()

        http = httplib2.Http()
        # Next Block Seems to Fail
        try:
            status, response = http.request(url)
            print status, response
        except Exception:
            "Something broke?"
            continue

        # Skip if not a webpage
        if status.get('content-type') != 'text/html':
            print "Not a webpage!"
            continue

        # Add the link to queue for downloading images
        link_parser_singleton.to_visit.add(url)
        print 'Added ', url, ' to queue'

        bs = BeautifulSoup(response)

        for link in BeautifulSoup.findAll(bs, 'a'):

            link_url = link.get('href')

            # <img> tag may not contain href attribute MZ: I think they meant <a>
            if not link_url:
                continue

            parsed = urlparse(link_url)

            # If link follows to external webpage, skip ImageDownloaderThread
            if parsed.netloc and parsed.netloc != parsed_root.netloc:
                continue

            # Construct a full url from a link which can be relative
            link_url = (parsed.scheme or parsed_root.scheme) + '://' + (parsed.netloc or parsed_root.netloc) + parsed.path or ''

            # If link was added previously, skip it 
            if link_url in link_parser_singleton.to_visit:
                continue

            # Add a link for further parsing
            link_parser_singleton.queue_to_parse = [link_url] + link_parser_singleton.queue_to_parse

def download_images(thread_name):
    singleton = Singleton()
    # While we have pages where we have not downloaded images
    while singleton.to_visit:
        url = singleton.to_visit.pop()

        http = httplib2.Http()
        print thread_name, 'Starting downloading images from ', url

        try:
            status, response = http.request(url)
        except Exception:
            continue

        bs = BeautifulSoup(response)

        # Find all the <img> tags
        images = BeautifulSoup.findAll(bs, 'img')

        for image in images:
            # Get image source url which can be absolute or relative
            src = image.get('src')
            # Construct a full url. If the image url is relative, 
            # it will be prepended to the webpage domain.
            # If the image url is absolute, it will remain as is
            src = urljoin(url, src)

            # Get a base name, for example, 'image.png' to name file locally
            basename = os.path.basename(src)

            if src not in singleton.downloaded:
                singleton.downloaded.add(src)
                print 'Downloading', src
                # Download image to local filesystem
                urllib.urlretrieve(src, os.path.join('images', basename))

        print thread_name, ' finished downloading images from ', url

if __name__ == '__main__':
    root = 'http://python.org'

    parse_root = urlparse(root)

    singleton = Singleton()
    singleton.queue_to_parse = [root]
    # a set of urls to download images from
    singleton.to_visit = set()
    # Downloaded images
    singleton.downloaded = set()

    traverse_site()

    # Create images directory if it does not exist
    if not os.path.exists('images'):
        os.makedirs('images')

    # Create new threads
    thread1 = ImageDownloaderThread(1, "Thread-1", 1)
    thread2 = ImageDownloaderThread(2, "Thread-2", 2)

    # Start threads
    thread1.start()
    thread2.start()

