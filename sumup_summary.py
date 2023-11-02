#!/usr/bin/python

import argparse
import calendar
import csv
import json
import pandas as pd
from pathlib import Path
import toml
import re
import requests
from time import sleep
import os
import sys
import datetime

res_folder = "res_files"
default_cleaned_file = (
    res_folder
    + "/sumup_clean"
    + str(datetime.datetime.now().month)
    + "-"
    + str(datetime.datetime.now().year)
    + "-"
    + str(datetime.datetime.now().hour)
    + str(datetime.datetime.now().minute)
    + ".csv"
)


def get_sumup_sumary(priv_token, year, month):
    ## Get history from last month
    sumup_url = "https://api.sumup.com/v0.1/me/"

    financial_request = "financials/transactions"
    detail_request = "transactions"

    month = month.zfill(2)
    assert int(month) <= 12, "month is too high"
    assert (
        datetime.datetime(int(year), int(month), 1) < datetime.datetime.now()
    ), "This month is in future."

    last_day_month = str(calendar.monthrange(int(year), int(month))[1])

    period = (
        "start_date="
        + year
        + "-"
        + month
        + "-01&end_date="
        + year
        + "-"
        + month
        + "-"
        + last_day_month
    )
    header = {"Authorization": "Bearer " + priv_token}

    res = requests.get(sumup_url + financial_request + "?" + period, headers=header)

    transactions = json.loads(res.text)
    if not transactions:
        print("There is no result")
        return 1
    assert "error_code" not in transactions[0].keys(), (
        "There was an error in the request: "
        + transactions[0]["error_code"]
        + " --- "
        + transactions[0]["message"]
    )
    clean_sumary = []

    for trans in transactions:
        ## We extract the transaction to get transaction details
        trans_id = trans["transaction_code"]
        ## We need details to get the product description
        details = requests.get(
            sumup_url + detail_request,
            headers=header,
            params={"transaction_code": trans_id},
        )
        try:
            detail = json.loads(details.text)
        except Exception as e:
            print(details)
            raise e

        transactions = json.loads(res.text)
        for product in detail["products"]:
            sleep(1)
            ## Create a new dic with Date,Time,Description,Price,Transaction ID
            tmp_dic = dict()
            hour = int(trans["timestamp"][11:13]) + 2
            delta_day = 0
            if hour >= 24:
                delta_day = 1
                hour = hour % 24
            tmp_dic["Date"] = (
                datetime.datetime.strptime(trans["timestamp"][:10], "%Y-%m-%d")
                + datetime.timedelta(days=delta_day)
            ).strftime("%d/%m/%Y")

            tmp_dic["Time"] = str(hour) + trans["timestamp"][13:16]
            all_desc = product["name"]
            # if "description" in product.keys():
            #     all_desc += " " + product["description"]
            tmp_dic["Description"] = all_desc
            if "total_with_vat" not in product.keys():
                tmp_dic["Price"] = product["total_price"]
            else:
                tmp_dic["Price"] = product["total_with_vat"]
            tmp_dic["Transaction ID"] = trans_id
            clean_sumary.append(tmp_dic)
    ## For debug ================================================
    df = pd.DataFrame(clean_sumary)
    df.sort_values("Description").to_csv("test.csv", index=False)
    ## ==========================================================
    return clean_sumary


def send_to_MM(dict_to_send, server, token, channel_to_send):
    header = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    post_content = {"channel_id": channel_to_send, "message": ""}

    months_fr = {
        "January": "janvier",
        "February": "février",
        "March": "mars",
        "April": "avril",
        "May": "mai",
        "June": "juin",
        "July": "juillet",
        "August": "août",
        "September": "septembre",
        "October": "octobre",
        "November": "Novembre",
        "December": "décembre",
    }

    for month_report in dict_to_send.keys():
        message = (
            """Bonjour bonjour !
Voici le rapport Sumup du mois de """
            + months_fr[month_report]
        )
        for cat in dict_to_send[month_report].keys():
            message += (
                "\n- **" + cat + "** --> " + str(dict_to_send[month_report][cat]) + "€"
            )
        post_content["message"] = message
        res = requests.post(
            server + "api/v4/posts", headers=header, data=json.dumps(post_content)
        )
    print(res)
    return res


def extract_data(data_dict, toml_file):
    config_file = toml.loads(open(toml_file, "r").read())
    cat = config_file["categories"]
    sums = dict()

    for row in data_dict:
        desc = row["Description"]
        month = calendar.month_name[int(row["Date"][3:5])]
        if month not in sums.keys():
            sums[month] = dict.fromkeys(cat, 0)
            print("reset")
        found = False
        for category in cat:
            if re.match(category, desc):
                sums[month][category] += row["Price"]
                found = True
                break
        if not found:
            sums[month][desc] = row["Price"]
            cat.append(desc)
    ## For tests
    print(sums)

    return sums


def extract_data_from_file(cleaned_file, toml_file):
    df = pd.read_csv(cleaned_file)
    df.sort_values("Description").to_csv(cleaned_file, index=False)
    return extract_data(df.iterrows(), toml_file)


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

    last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    year_last_month = last_month.strftime("%Y")
    last_month = last_month.strftime("%m")

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--inputfile")
    parser.add_argument("-o", "--outputfile", default=default_cleaned_file)
    parser.add_argument("-cf", "--configFile", default="categories.toml")
    parser.add_argument("-mm", "--mattermostServer")
    parser.add_argument("-mmT", "--mattermostToken")
    parser.add_argument("-mmC", "--mattermostChannelID")
    parser.add_argument("-sT", "--SumupToken")
    parser.add_argument("-month", default=last_month)
    parser.add_argument("-year", default=year_last_month)

    args = parser.parse_args(cli_args)

    inputfile = args.inputfile
    cleaned_file = args.outputfile
    toml_file = args.configFile
    mmServer = args.mattermostServer
    mmToken = args.mattermostToken
    mmChannel = args.mattermostChannelID
    sumupToken = args.SumupToken
    month = args.month
    year = args.year

    if sumupToken:
        data = get_sumup_sumary(sumupToken, year, month)
        resume = extract_data(data, toml_file)
    elif inputfile:
        rm_csv_rows(inputfile, cleaned_file)
        resume = extract_data_from_file(cleaned_file, toml_file)
    else:
        print("Problem with arguments")
        return 1
    send_to_MM(resume, mmServer, mmToken, mmChannel)


if __name__ == "__main__":
    main(sys.argv[1:])
