#!/usr/bin/python

import argparse
import calendar
import csv
import pandas as pd
from pathlib import Path
import toml
import re
import os
import sys
from datetime import datetime

res_folder = "res_files"
default_cleaned_file = (
    res_folder
    + "/sumup_clean"
    + str(datetime.now().month)
    + "-"
    + str(datetime.now().year)
    + "-"
    + str(datetime.now().hour)
    + str(datetime.now().minute)
    + ".csv"
)


def send_to_MM(dict_to_send, server, token):
    pass


def extract_data_from_file(cleaned_file, toml_file):
    df = pd.read_csv(cleaned_file)
    df.sort_values("Description").to_csv(cleaned_file, index=False)

    config_file = toml.loads(open(toml_file, "r").read())
    cat = config_file["categories"]
    sums = dict()

    for index, row in df.iterrows():
        desc = row["Description"]
        month = calendar.month_name[int(row["Date"][3:5])]
        if month not in sums.keys():
            sums[month] = dict.fromkeys(cat, 0)
        found = False
        for category in cat:
            if re.match(category, desc):
                sums[month][category] += row["Price"]
                found = True
                break
        if not found:
            sums[month][desc] = row["Price"]
    ## For tests
    print(sums)

    return sums


def rm_csv_rows(inputfile, cleaned_file):
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
    Path("./" + res_folder).mkdir(parents=True, exist_ok=True)
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

    rm_csv_rows(inputfile, cleaned_file)
    resume = extract_data_from_file(cleaned_file, toml_file)
    send_to_MM(resume, mmServer, mmToken)


if __name__ == "__main__":
    main(sys.argv[1:])
