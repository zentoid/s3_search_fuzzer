#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Created by zentoid

import os
import random
from argparse import ArgumentParser
from time import sleep

import requests

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
args = parser.parse_args()

main_bucket_part = args.main_bucket_name_part


def _get_back_off_time():
    sleep_time = min(MAX_SLEEP_TIME, random.randint(BASE_SLEEP_TIME, start_sleep_time * 3))

    if sleep_time > MAX_SLEEP_TIME:
        sleep_time = BASE_SLEEP_TIME

    return sleep_time


def _do_sleep():
    sleeper = _get_back_off_time()
    print('Sleeping for {} seconds'.format(sleeper))
    sleep(sleeper)


def _check_file_exists(source_file: str):
    if '/' in source_file:
        return os.path.isfile(source_file)
    else:
        return os.path.isfile(os.path.join(os.getcwd(), source_file))


if not _check_file_exists(args.source_fuzzer_file):
    print('No fuzzer file found')
    exit(-1)

if not _check_file_exists(args.source_separators_file):
    print('No separators file found')
    exit(-1)

with open(args.source_fuzzer_file, 'r') as f:
    fuzzers = [line.strip() for line in f]
    fuzzers_count = len(fuzzers)

with open(args.source_separators_file, 'r') as s:
    separators = [line.strip() for line in s]
    separators_count = len(separators)

print(
    f'Starting checks on target \'{main_bucket_part}\', loaded {fuzzers_count} fuzzer words from from {args.source_fuzzer_file} and loaded {separators_count} separators from {args.source_separators_file}.')


def _print_public_bucket_info(check_name):
    print('\tPublic bucket, try listing its contents: aws s3 ls s3://{} --no-sign-request'.format(check_name))


for separator in separators:
    for fuzz in fuzzers:
        check_name = "{}{}{}".format(main_bucket_part, separator, fuzz)
        if len(check_name) > 63:
            print('Bucket name ({}) is to long {}'.format(check_name, len(check_name)))
            continue

        r = requests.head("http://{}.s3.amazonaws.com".format(check_name))

        if r.status_code != 404:
            print('Success: {} --> {}'.format(check_name, r.status_code))

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
            print('Success: {} --> {}'.format(reversed_check_name, r.status_code))

            if r.status_code == 200:
                _print_public_bucket_info(check_name)
        else:
            # not a viable candidate
            pass

        if ENABLE_SLEEP_TIMER:
            _do_sleep()

print(f'All checks from \'{args.source_fuzzer_file}\' have completed.')
