#!/bin/bash

python pubmed_downloader_ftp.py 'tmp' 'ftp.ncbi.nlm.nih.gov' '/pubmed/baseline/' 'pubmed23n\d{4}\.xml\.gz$' 4
