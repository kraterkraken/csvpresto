#!/usr/bin/env python3

from argparse import ArgumentParser
from argparse import FileType
from csv import reader
import sys
import signal

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
    sys.exit("Error: csvpresto requires Python 3.2 or higher")

def validate_number(s, row, col):
    try:
        float(s)
    except ValueError:
        sys.exit(f"Error: found non-numeric data '{s}' in row {row}, column {col}")

def list_to_string(l):
    return ", ".join([str(a) for a in l])

def upper_string(s):
    return s.upper()

def pad_left(s, n):
    # return s left-padded with spaces so that it is at least n characters long
    padding = " " * (n - len(s)) # this automatically does the right thing if len >= n
    return padding + s

def signal_handler(sig, frame):
    sys.exit(0)

class ArgRetriever:
    def __init__(self):
        parser = ArgumentParser(
            usage="%(prog)s operation [filename] [options]",
            add_help=False,
            description="Program to read in a CSV file and perform statistical operations on various columns.")

        arg_group = parser.add_argument_group(title="Arguments")
        arg_group.add_argument("operation", type=upper_string, metavar="operation",
            choices=["SUM", "COUNT", "AVG", "HEADERS"],
            help="The operation to perform.  "
                "Valid choices are: SUM, AVG, COUNT, and HEADERS.  "
                "SUM and AVG calculate the sum and average of the data in the "
                "columns specified by -s, grouping by the columns specified by -g.  "
                "COUNT counts the number of records for each distinct group specified by -g.  "
                "HEADERS displays all of the headers and their column numbers as an "
                "aid in determining what values to use for the -g and -s arguments."
                )

        arg_group.add_argument("infile", metavar="filename",
            nargs='?', type=FileType('r'), default=sys.stdin,
            help="The CSV (comma-separated-value) file to use as input.  "
                "If omitted or '-', will read from standard input.")

        opt_group = parser.add_argument_group(title="Options")

        opt_group.add_argument("-h", action="help", help="Show this help message and exit.")
        opt_group.add_argument("-g", dest="group_cols", nargs='+', type=int, metavar="col",
            help="The list of columns to group by.  If omitted, will display one "
                "set of stats for the entire file.  Ex: -g 1 2 3 4")
        opt_group.add_argument("-s", dest="stat_cols", nargs='+', type=int, metavar="col",
            help="The list of columns to perform stats on.  "
                "Required for SUM and AVG.  Ex: -s 5 6 7")

        args = parser.parse_args()

        self.group_cols = args.group_cols
        self.stat_cols = args.stat_cols
        self.infile = args.infile
        self.operation = args.operation

        if self.operation in ["AVG","SUM"] and None == self.stat_cols:
            sys.exit(f"Error: -s must be supplied for the {self.operation} operation.")

# ------------------- MAIN PROGRAM --------------------------------------------

signal.signal(signal.SIGINT, signal_handler)

args = ArgRetriever()

# read the data from the file into a 2D list
# (note: I am using the csv module's reader object
# to automagically handle commas inside quoted strings)
data = [line + ["ALL ROWS"] for line in reader(args.infile)]
args.infile.close()

headers = data[:1][0]
data = data[1:]

# if the headers operation was specified, display the cols and headers, then exit
if args.operation == "HEADERS":
    print("Column\tHeader (Description)")
    print("------\t--------------------")
    for i, header in enumerate(headers):
        istr = pad_left(str(i), 6)
        print(f"{istr}\t{header}")
    sys.exit(0)

# if no grouping column was specified, use the "ALL ROWS" column as the group
# (this has the effect of printing just one set of stats for the entire file)
if args.group_cols == None:
    args.group_cols = [len(headers) - 1]

# if no stat column was specified (which is only valid for COUNT) then
# use the "ALL ROWS" column.
if args.stat_cols == None:
    args.stat_cols = [len(headers) - 1]

# put the string arguments into a list as integers
group_list = [int(a) for a in args.group_cols]
stat_list = [int(a) for a in args.stat_cols]

# validate the data
if len(data) == 0:
    sys.exit("No data in file.")
if max(group_list) >= len(headers):
    sys.exit("Error: a specified group column is greater than the number of columns.")
if max(stat_list) >= len(headers):
    sys.exit("Error: a specified stat column is greater than the number of columns.")

for i, row in enumerate(data):
    if len(row) != len(headers):
        sys,exit(f"Error: row {i} has the wrong number of columns.")

# sort the data by the grouping columns
group_list.reverse() # reverse the order so the sorting works
for col in group_list:
    data.sort(key=lambda x: x[col])
group_list.reverse() # put the order back again

# print the headers that we need
print()
print("{} ... {}".format(
    list_to_string([headers[i] for i in group_list]),
    list_to_string([args.operation + " " + headers[i] for i in stat_list]))
    )
print("-----------------------------------------------------------------------")

# now iterate over the data, performing the desired operation for each group
# and printing the results
data.append([None for a in data[0]]) # add a a dummy row as the last row ... see below for why
prev_group = [val for col, val in enumerate(data[0]) if col in group_list]

sum = [0 for a in stat_list]
count = [0 for a in stat_list]
avg = [0 for a in stat_list]
result = []

for ctr, row in enumerate(data):

    curr_group = [val for col, val in enumerate(row) if col in group_list]

    # if the group changed, print the results for the previous group
    # then reset the results for this new group
    if curr_group != prev_group:
        if args.operation == "SUM":
            result = sum
        elif args.operation == "COUNT":
            result = count
        elif args.operation == "AVG":
            result = [float(s)/float(c) for s,c in zip(sum,count)]

        print(f"{list_to_string(prev_group)} ... {list_to_string(result)}")

        sum = [0 for a in stat_list]
        count = [0 for a in stat_list]
        avg = [0 for a in stat_list]
        result = []

    # if we are on the last row (the dummy row ... see above),
    # then there are no results to tabulate, so just exit the loop (we are done)
    if ctr == len(data) - 1:
        break

    # tabulate the results for the current row
    for result_index, row_index in enumerate(stat_list):
        if args.operation != "COUNT":
            validate_number(row[row_index], ctr, row_index)
            sum[result_index] += float(row[row_index])
        count[result_index] += 1

    prev_group = curr_group
