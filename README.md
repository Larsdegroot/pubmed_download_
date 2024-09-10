This is a clone of the original repository from the ONTOX GitHub page, created for portfolio visibility. Find the orginal GitHub page [here](https://github.com/ontox-hu/pubmed_download) 
---
# pubmed_download
Pubmed makes its [entire database publicly availible](https://pubmed.ncbi.nlm.nih.gov/download/). This data can be downloaded using the FTP protocol. The data is availible as a set of files that updates [annualy](https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/) or [daily](https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/). This repository holds a script to download this data dump quickly by making use of parallel downloading.

## Usage
The script [pubmed_downloader_ftp.py](https://github.com/ontox-hu/pubmed_download/blob/main/pubmed_downloader_ftp.py) is the code for a Command Line Interface (CLI). Find out how to use it by adding a `--help` flag:
```
python pubmed_downloader_ftp.py --help
```
Which will output the following:
![output of the --help flag](/img/cli_help.png)

In short the script visits the host that is supplied in the `host` argument, and moves into the directory specified in the 'host_wd' argument. Then it filters the files found there with a reg_ex supplied in the `reg_ex` argument. The script then begins downloading the filterd files in paralel. The `threads` argument indicates how many paralel downloads the script uses. WARNING too many paralel downloads might result in your IP adres being blocked by the National Center for Biotechnology Information. Please check out the [terms and conditions](https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/README.txt)

An example of the CLI being used can be found in [run_ftp.sh](https://github.com/ontox-hu/pubmed_download/blob/main/run_ftp.sh).
```
python pubmed_downloader_ftp.py 'tmp' 'ftp.ncbi.nlm.nih.gov' '/pubmed/baseline/' 'pubmed23n\d{4}\.xml\.gz$' 4
```

## Problems
- [pubmed_downloader.py](https://github.com/ontox-hu/pubmed_download/blob/main/pubmed_downloader.py) Is a implementation of the pubmed downloader that doesn't make use of FTP. For some reason this implementation would skip some files.

