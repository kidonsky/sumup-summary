#!/usr/bin/python

import argparse
import csv
import pandas as pd
import toml
import re
import os
import sys
from datetime import datetime


default_cleaned_file = (
    "sumup_clean"
    + str(datetime.now().month)
    + "-"
    + str(datetime.now().year)
    + "-"
    + str(datetime.now().hour)
    + str(datetime.now().minute)
    + ".csv"
)


def play_with_file(cleaned_file, toml_file):
    df = pd.read_csv(cleaned_file)
    df.sort_values("Description").to_csv(cleaned_file)

    config_file = toml.loads(open(toml_file, "r").read())
    cat = config_file["categories"]
    sums = dict.fromkeys(cat, 0)

    for index, row in df.iterrows():
        desc = row["Description"]
        for category in cat:
            if re.match(category, desc):
                sums[category] += row["Price"]
    ## For tests
    print(sums)


def clean_file(inputfile, cleaned_file):
    with open(inputfile, newline="") as csvfile:
        read_file = csv.DictReader(csvfile)
        with open(cleaned_file, "w", newline="") as csvfile:
            filenames = [
                "Date",
                "Time",
                "Description",
                "Price",
                "Transaction ID",
            ]
            new_file = csv.DictWriter(csvfile, fieldnames=filenames)
            new_file.writeheader()
            for row in read_file:
                new_file.writerow(
                    {
                        "Date": row["Date"],
                        "Time": row["Time"],
                        "Description": row["Description"],
                        "Price": row["Price (Gross)"],
                        "Transaction ID": row["Transaction ID"],
                    }
                )
    return 0


def main(cli_args):
    try:
        os.remove(default_cleaned_file)
    except Exception as e:
        pass

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--inputfile", required=True)
    parser.add_argument("-o", "--outputfile", default=default_cleaned_file)
    parser.add_argument("-cf", "--configFile", default="categories.toml")
    parser.add_argument("-mm", "--mattermostServer")
    parser.add_argument("-mmT", "--mattermostToken")
    parser.add_argument("-sT", "--SumupToken")

    args = parser.parse_args(cli_args)

    inputfile = args.inputfile
    cleaned_file = args.outputfile
    toml_file = args.configFile
    mmServer = args.mattermostServer
    mmToken = args.mattermostToken
    sumupToken = args.SumupToken

    clean_file(inputfile, cleaned_file)
    play_with_file(cleaned_file, toml_file)


if __name__ == "__main__":
    main(sys.argv[1:])
