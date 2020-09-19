# Search fuzzer
## Simple S3 bucket searcher

This is a very simple script that takes a base bucket name and will prefix and suffix the "fuzz words" using the allowed separators.

It has been written using Python 3.8.5

If it finds an open S3 bucket it will try to list the contents f that bucket.

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

---
If you dont want to spam requests to S3 you can set

    ENABLE_SLEEP_TIMER=True

in the s3_seeker.py file

---
Your use of this is at your own risk. If it breaks things our you get into trouble.

**That's on you not me!**
