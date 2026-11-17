# NOTES

How to run: `python3 -m unittest -v` (tests) and `python3 dedup.py summary` (CLI). Python 3 standard library only, nothing to install.

## Duplicate groups found and what I decided

_(filled in as each step is built)_

## What I did not do, and why

- No external libraries: standard library only, so the tool runs with nothing to install.
- `phone_secondary` does not identify a company. The rule says "main phone number", so only `phone` is used.

## What I would do differently with more time

- Root domain is "the last two labels of the host" and a phone is "ten digits, US country code dropped". Both fit this dataset (US shops on .com/.net/.us). In production I would use the Public Suffix List and `phonenumbers` instead.

## Things in the data you should know about
