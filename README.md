# Search fuzzer
## Simple S3 bucket searcher

This is a very simple script that takes a base bucket name and will prefix and suffix the "fuzz words" using the allowed separators.


## Usage is simple
The simplest working command is

    python s3_seeker.py -b test
 
The main part of the bucket name you are searching for (e.g. CompanyName)

    -b, --base

File that contains terms to add to the main name above.

Default: fuzz.txt

    -f, --fuzzer

File that contains various separators to use.

Default: separators.txt

    -s, --separator

Write output to console and log file

Default: True

    -w, --write
