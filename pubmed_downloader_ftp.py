from ftplib import FTP
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

class FTPDownloader:

    def __init__(self, host):
        '''
        Create an instance of a pubmed downloader. The pubmed downloader uses requests to download all urls that are in the starting url.
        
        '''
        self._host = host
        self.cwd = None
        self.all_fileNames = []
        self.filtered_fileNames = []
        self.download_dir = Path('')

    def get_logger(self):
        '''
        '''
        return logging.getLogger(__name__)

    def set_download_dir(self, path):
        if not os.path.isdir(path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
        else:
            self.download_dir = Path(path)

    def find_files(self, starting_dir: str):
        '''
        Find all files insinde of starting directory
        '''
        
        self.cwd = starting_dir
        
        # Get the start directory
        with FTP(self._host) as ftp_client:
            ftp_client.login()
            ftp_client.cwd(self.cwd)
    
            # Get all of the links on the starting url
            self.all_fileNames = sorted(ftp_client.nlst())
        
        logging.info(f'Found {len(self.all_fileNames)} files in {self._host}')
        logging.debug(f'All files:   {self.all_fileNames}')

    def filter_files(self, reg_ex: str):
        '''
        Collects all urls that match the regex pattern
        '''
        self.reg_ex = reg_ex

        # Filter links based on match with regex
        re_obj = re.compile(self.reg_ex)
        self.filtered_fileNames = [fileName for fileName in self.all_fileNames if re_obj.match(fileName)]
        logging.info(f'filtered {len(self.filtered_fileNames)} files on {self._host} using regular expression: {reg_ex}')
        logging.debug(f'filtered files:    {self.filtered_fileNames}')
    
    def download_file(self, filename: str):
        '''
        '''
        
        with FTP(self._host) as ftp_client:
            ftp_client.login()
            ftp_client.cwd(self.cwd)
    
            with open(self.download_dir.joinpath(filename), "wb") as file:
                logging.info(f'Downloading {filename} from {ftp_client.host+ftp_client.pwd()}')
                ftp_client.retrbinary(f"RETR {filename}", file.write)
                logging.info(f'Retrieved {filename} from {ftp_client.host+ftp_client.pwd()}')

        return #Exit function process
        
    def download_files(self, threads: int = 3, progressbar: bool = False):
        '''
        Download all urls using multithreading
        '''
        if not self.filtered_fileNames:
            logging.warning("No files to download")
            return None

        logging.info(f'Starting download of {len(self.filtered_fileNames)} files')
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            with Progress() as progress:
                if progressbar:
                    task = progress.add_task("[cyan]Downloading...", total=len(self.filtered_fileNames))

                futures = [executor.submit(self.download_file, fileName) for fileName in self.filtered_fileNames]

                for future in concurrent.futures.as_completed(futures):
                    if progressbar:
                        progress.update(task, advance=1)
        logging.info('Download finished')

def main(
    path: Annotated[str, typer.Argument(help='The directory where the downloaded files are stored.')],
    host: Annotated[str, typer.Argument(help='The FTP host to download files from.')]='ftp.ncbi.nlm.nih.gov',
    host_wd: Annotated[str, typer.Argument(help='The directory of the FTP host to find files in.')]='/pubmed/baseline/',
    reg_ex: Annotated[str, typer.Argument(help='A regular expression that is used to filter the urls found on the starting url.')]='pubmed23n\d{4}\.xml\.gz$',
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
    
    # initializing and find files
    downloader = FTPDownloader(host=host)
    downloader.set_download_dir(path)
    downloader.find_files(starting_dir=host_wd)
    
    # filtering files
    downloader.filter_files(reg_ex=reg_ex)
    msg.info(f'Found {len(downloader.all_fileNames)} files in current working directory, {len(downloader.filtered_fileNames)} left after filtering')
    
    # downloading filterd files
    start_time = time.time()
    downloader.download_files(threads=threads, progressbar=True)
    end_time = time.time()
    msg.good(f'Download finished in {str(timedelta(seconds=round(end_time-start_time,0)))}')

if __name__ == '__main__':
    typer.run(main)