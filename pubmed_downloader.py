import requests
import logging
import re
import concurrent.futures
import errno
import os
import typer
import time
from datetime import timedelta
from typing_extensions import Annotated
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rich.progress import Progress
from pathlib import Path
from wasabi import Printer
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

class PubmedDownloader:

    def __init__(self):
        '''
        Create an instance of a pubmed downloader. The pubmed downloader uses requests to download all urls that are in the starting url.
        
        '''
        self._links = []
        self.all_urls = []
        self.filtered_urls = []
        self.failed_urls = []
        self.start_url = ''

    def get_logger(self):
        '''
        '''
        return logging.getLogger(__name__)

    def find_urls(self, starting_url: str):
        '''
        '''
        
        self.start_url = starting_url
        
        # Get the start url webpage and check if it got a response
        response = requests.get(self.start_url)
        if not response.status_code == 200:
            logging.error('')
            return None

        # Get all of the links on the starting url
        soup = BeautifulSoup(response.content, "html.parser")
        self._links = soup.find_all("a", href=True)
        self.all_urls = [urljoin(self.start_url, link["href"]) for link in self._links]

        logging.info(f'Found {len(self.all_urls)} urls on {self.start_url}')
        logging.debug(f'All urls:   {self.all_urls}')

    def filter_urls(self, reg_ex: str):
        '''
        Collects all urls that match the regex pattern
        '''
        self.reg_ex = reg_ex

        # Filter links based on match with regex
        re_obj = re.compile(self.reg_ex)
        self.filtered_urls = [urljoin(self.start_url, link["href"]) for link in self._links if re_obj.match(link["href"])]
        logging.info(f'filtered {len(self.filtered_urls)} urls on {self.start_url} using regular expression: {reg_ex}')
        logging.debug(f'filtered urls:    {self.filtered_urls}')
    
    def download_file(self, url: str, path: str):
        '''
        '''
        @retry(wait=wait_random_exponential(min=3, max=120), stop=stop_after_attempt(6))
        def requestGet_with_backoff(**kwargs):
            logging.debug(f'Trying to GET {kwargs["url"]}')
            return requests.get(**kwargs)

        # try to get file 
        try:
            response = requestGet_with_backoff(url=url, timeout=2)
            logging.debug(f'Response for {url} status code: {response.status_code}')
        except: # No response (within timeout window) for six times
            logging.warning(f'No response for {url} within timeout.')
            self.failed_urls.append(url)
            return #Exit function process

        # save file to disk  
        path = Path(path)
        filename = url.split("/")[-1]
        content = response.content
        logging.info(f'Downloaded: {url}')
        with open(path.joinpath(filename), "wb") as file:
            file.write(content)
        logging.info(f'Written {filename} to {path+"/"+filename}')
        return #Exit function process
        
    def download_urls(self, path: str, threads: int = 3, progressbar: bool = False):
        '''
        Download all urls using multithreading
        '''
        if not self.filtered_urls:
            logging.warning("No URLs to download")
            return None

        logging.info(f'Starting download of {len(self.filtered_urls)} urls')
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            with Progress() as progress:
                if progressbar:
                    task = progress.add_task("[cyan]Downloading...", total=len(self.filtered_urls))

                futures = [executor.submit(self.download_file, url, path) for url in self.filtered_urls]

                for future in concurrent.futures.as_completed(futures):
                    if progressbar:
                        progress.update(task, advance=1)
        logging.info('Download finished')

def main(
    path: Annotated[str, typer.Argument(help='The directory where the downloaded files are stored.')],
    url: Annotated[str, typer.Argument(help='The url to download files from.')],
    reg_ex: Annotated[str, typer.Argument(help='A regular expression that is used to filter the urls found on the starting url.')],
    threads: Annotated[int, typer.Argument(help='Number of threads used for downloading all the found urls on the starting url. ')]=3
):
    logging.basicConfig(
        filename='pubmed_downloader.log',
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    msg = Printer()
    
    # Check if path is a valid directory
    if not os.path.isdir(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    # Check if threads is a valid int
    if threads > 10:
        msg.warn(f'{threads} threads will be used for concurrent downloading. Using a high number of threads may get your ip blacklisted!')
    
    downloader = PubmedDownloader()
    downloader.find_urls(url)
    downloader.filter_urls(reg_ex)
    msg.info(f'Found {len(downloader.all_urls)} on starting url, {len(downloader.filtered_urls)} left after filtering')
    
    start_time = time.time()
    downloader.download_urls(path = path, threads=threads, progressbar=True)
    end_time = time.time()
    msg.good(f'Download finished in {str(timedelta(seconds=round(end_time-start_time,0)))}')

if __name__ == '__main__':
    typer.run(main)