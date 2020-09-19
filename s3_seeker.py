#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Created by zentoid
import logging
import os
import random
from argparse import ArgumentParser
from datetime import datetime
from time import sleep

import boto3
import botocore.exceptions
import coloredlogs
import requests
from botocore import UNSIGNED
from botocore.config import Config

ENABLE_SLEEP_TIMER = False
BASE_SLEEP_TIME = 1
MAX_SLEEP_TIME = 3

fuzzers_count = 0
separators_count = 0
start_sleep_time = BASE_SLEEP_TIME

parser = ArgumentParser()
parser.add_argument("-b", "--base", dest="main_bucket_name_part", help="The main part of the bucket name you are searching for (e.g. CompanyName)", required=True)
parser.add_argument("-f", "--fuzzer", dest="source_fuzzer_file", help="File tht contains terms to add to the main name above", default="fuzz.txt")
parser.add_argument("-s", "--separator", dest="source_separators_file", help="File tht contains various separators to use", default="separators.txt")
parser.add_argument("-w", "--write", dest="write", help="Write output to console and log file", default=True)
args = parser.parse_args()

log_file_name = str(datetime.strftime(datetime.now(), '%d-%m-%Y_%H-%M-%S.%f'))
write_to_file = args.write

# Create file logger
flog = logging.getLogger('s3seeker_file_log')
flog.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler('{}.log'.format(log_file_name))
fh.setLevel(logging.DEBUG)

# Add the handler to logger
flog.addHandler(fh)

# Create secondary logger for logging to console
stdoutlog = logging.getLogger('s3seeker_file_log_std_out')
stdoutlog.setLevel(logging.INFO)

# The levels here are used to set the console output color
levelStyles = {
    'debug': {'color': 'orange'},
    'info': {'color': 'white'},
    'warning': {'color': 'yellow'},
    'error': {'color': 'red'}
}

# This is nice if you want the time in a static color - not using at the moment
fieldStyles = {
    'asctime': {'color': 'white'}
}

# Not using time in the output messages
# coloredlogs.install(level='DEBUG', logger=stdoutlog, fmt='%(asctime)s - %(message)s', level_styles=levelStyles, field_styles=fieldStyles)
coloredlogs.install(level='DEBUG', logger=stdoutlog, fmt='%(message)s', level_styles=levelStyles, field_styles=fieldStyles)

main_bucket_part = args.main_bucket_name_part

# Setup the s3 client with no request signing (no credentials used)
s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
pager = s3_client.get_paginator('list_objects_v2')


def _output_message(message, level):
    if write_to_file:
        flog.log(level=level, msg=message, )

    stdoutlog.log(level=level, msg=message)


def _get_back_off_time():
    sleep_time = min(MAX_SLEEP_TIME, random.randint(BASE_SLEEP_TIME, start_sleep_time * 3))

    if sleep_time > MAX_SLEEP_TIME:
        sleep_time = BASE_SLEEP_TIME

    return sleep_time


def _do_sleep():
    sleeper = _get_back_off_time()
    _output_message('Sleeping for {} seconds'.format(sleeper), logging.DEBUG)
    sleep(sleeper)


def _check_file_exists(source_file: str):
    if '/' in source_file:
        return os.path.isfile(source_file)
    else:
        return os.path.isfile(os.path.join(os.getcwd(), source_file))


def _list_bucket_contents(bucket_name):
    try:
        for data in pager.paginate(
                Bucket=bucket_name,
                FetchOwner=True,
        ):
            for keys in data["Contents"]:
                _output_message(f'\t\t{keys["Key"]}', logging.INFO)
    except botocore.exceptions.ClientError as ex:
        if ex.response["Error"]["Code"] == "AccessDenied":
            _output_message('\t\tList access denied', logging.WARN)


def _print_public_bucket_info(bucket_name):
    _output_message('\tPublic bucket, try listing its contents: aws s3 ls s3://{} --no-sign-request'.format(bucket_name), logging.INFO)
    _list_bucket_contents(bucket_name=bucket_name)


if __name__ == '__main__':
    try:
        _output_message("Run started @ {}".format(str(datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S.%f'))), logging.INFO)
        if not _check_file_exists(args.source_fuzzer_file):
            _output_message('No fuzzer file found', logging.ERROR)
            exit(-1)

        if not _check_file_exists(args.source_separators_file):
            _output_message('No separators file found', logging.ERROR)
            exit(-1)

        with open(args.source_fuzzer_file, 'r') as f:
            fuzzers = [line.strip() for line in f]
            fuzzers_count = len(fuzzers)

        with open(args.source_separators_file, 'r') as s:
            separators = [line.strip() for line in s]
            separators_count = len(separators)

        _output_message(f'Starting checks on target \'{main_bucket_part}\', '
                        f'loaded {fuzzers_count} fuzzer words from {args.source_fuzzer_file} '
                        f'and loaded {separators_count} separators from {args.source_separators_file}.', logging.INFO)

        _output_message('THis may take a little while. Pleas wait...', logging.WARN)

        # check the base bucket
        if len(main_bucket_part) > 63:
            _output_message('Bucket name ({}) is to long {}'.format(main_bucket_part, len(main_bucket_part)), logging.ERROR)
        else:
            r = requests.head("http://{}.s3.amazonaws.com".format(main_bucket_part))

            if r.status_code != 404:
                _output_message('Found: {} --> {}'.format(main_bucket_part, r.status_code), logging.INFO)

                if r.status_code == 200:
                    _print_public_bucket_info(main_bucket_part)

            else:
                # not a viable candidate
                pass

        for separator in separators:
            for fuzz in fuzzers:
                check_name = "{}{}{}".format(main_bucket_part, separator, fuzz)
                if len(check_name) > 63:
                    _output_message('Bucket name ({}) is to long {}'.format(check_name, len(check_name)), logging.INFO)
                    continue

                r = requests.head("http://{}.s3.amazonaws.com".format(check_name))

                if r.status_code != 404:
                    _output_message('Exists: {} --> {}'.format(check_name, r.status_code), logging.INFO)

                    if r.status_code == 200:
                        _print_public_bucket_info(check_name)

                else:
                    # not a viable candidate
                    pass

                if ENABLE_SLEEP_TIMER:
                    _do_sleep()

                # swap bucket part and fuzz
                reversed_check_name = '{}{}{}'.format(fuzz, separator, main_bucket_part)

                r = requests.head('http://{}.s3.amazonaws.com'.format(reversed_check_name))

                if r.status_code != 404:
                    _output_message('Exists: {} --> {}'.format(reversed_check_name, r.status_code), logging.INFO)

                    if r.status_code == 200:
                        _print_public_bucket_info(check_name)
                else:
                    # not a viable candidate
                    pass

                if ENABLE_SLEEP_TIMER:
                    _do_sleep()

        _output_message(f'All checks from \'{args.source_fuzzer_file}\' have completed.', logging.INFO)
    finally:
        _output_message("Run ended @ {}".format(str(datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S.%f'))), logging.INFO)
