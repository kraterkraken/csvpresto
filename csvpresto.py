#!/usr/bin/env python3

from argparse import ArgumentParser
from argparse import FileType
from statistics import mean
import csv
import sys
import signal

########## UTILITY FUNCTIONS ###################################################

def safe_float(s, err_msg):
    try:
        return float(s)
    except ValueError:
        sys.exit(err_msg)

def upper_string(s):
    return s.upper()

def pad_left(s, n):
    # return s left-padded with spaces so that it is at least n characters long
    padding = " " * (n - len(s)) # this automatically does the right thing if len >= n
    return padding + s

def data_sort(data, sort_cols, reverse=False):
    sort_cols.reverse() # reverse the order so the sorting works
    for col in sort_cols:
        data.sort(key=lambda x: x[col], reverse=reverse)
    sort_cols.reverse() # put the order back again

def signal_handler(sig, frame):
    sys.exit(0)

########## UTILITY CLASSES #####################################################

class ArgRetriever:
    def __init__(self):
        parser = ArgumentParser(
            usage="%(prog)s operation [filename] [options]",
            add_help=False,
            description="Program to read in a CSV file and perform statistical operations on various columns.")

        arg_group = parser.add_argument_group(title="Arguments")
        arg_group.add_argument("operation", type=upper_string, metavar="operation",
            choices=["SUM", "COUNT", "AVG", "MIN", "MAX", "HEADERS"],
            help="The operation to perform.  "
                "Valid choices are: SUM, AVG, MIN, MAX, COUNT, and HEADERS.  "
                "SUM, AVG, MIN, and MAX calculate the relevant stat in the "
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
                "set of stats for the entire file.  Output is sorted by these "
                "columns by default.  Ex: -g 1 2 3 4")
        opt_group.add_argument("-s", dest="stat_cols", nargs='+', type=int, metavar="col",
            help="The list of columns to perform stats on.  "
                "Required for SUM and AVG.  Ex: -s 5 6 7")
        opt_group.add_argument("-c", dest="csv_output", action="store_true",
            help="Causes the output to be in CSV format.  Useful for piping to "
                "other commands or redirecting to a file.")
        opt_group.add_argument("-a", dest="ascend_cols", nargs='+', type=int, metavar="col",
            help="The list of columns to sort by (ascending).")
        opt_group.add_argument("-d", dest="descend_cols", nargs='+', type=int, metavar="col",
            help="The list of columns to sort by (descending).")
        opt_group.add_argument("-r", dest="rows", type=int, metavar="N",
            help="Display at most N rows of results.  Can be used in conjunction "
            "with the -d/-a sorting options to show the top/bottom N rows.")

        args = parser.parse_args()

        self.group_cols = args.group_cols
        self.stat_cols = args.stat_cols
        self.combined_cols = self.group_cols + self.stat_cols
        self.infile = args.infile
        self.operation = args.operation
        self.csv_output = args.csv_output
        self.ascend_cols = args.ascend_cols
        self.descend_cols = args.descend_cols
        self.rows = args.rows

        if self.operation in ["AVG","SUM", "MIN", "MAX"] and None == self.stat_cols:
            sys.exit(f"Error: -s must be supplied for the {self.operation} operation.")

        if self.sort_cols_bad(self.ascend_cols) or self.sort_cols_bad(self.descend_cols):
            sys.exit("Error: you must choose columns from -g or -s to sort by.")

    def sort_cols_bad(self, sort_cols):
        if sort_cols == None: return False
        intersec = set(sort_cols).intersection(self.combined_cols)
        return len(intersec) != len(sort_cols)

class DataFormatter:
    def __init__(self):
        self.headers = []
        self.data_grid = []
        self.col_widths = None
        self.max_col_width = 15
        self.col_spacing = 3

    def add_data_row(self, r):
        self.data_grid.append(r)

    def set_headers(self, alist):
        self.headers = alist

    def display_as_csv(self, rows=None):
        if rows==None: rows=len(self.data_grid)
        csv_w = csv.writer(sys.stdout)
        csv_w.writerow(self.headers)
        csv_w.writerows(self.data_grid[:rows])

    def display(self, rows=None):
        self.calculate_col_widths()

        # display the headers
        print()
        print(self.list_to_colstring(
            self.headers,
            self.col_widths,
            self.col_spacing,
            self.max_col_width)
        )
        print('-' * 70)

        # display the data
        if rows==None: rows=len(self.data_grid)
        for row in self.data_grid[:rows]:
            print(self.list_to_colstring(
                row,
                self.col_widths,
                self.col_spacing,
                self.max_col_width)
            )

    def sort_ascend(self, cols):
        data_sort(data=self.data_grid, sort_cols=cols)

    def sort_descend(self,cols):
        data_sort(data=self.data_grid, sort_cols=cols, reverse=True)

    def calculate_col_widths(self):
        widths = [len(str(a)) for a in self.headers]
        for i, row in enumerate(self.data_grid):
            for j, result in enumerate(row):
                widths[j] = max(widths[j], len(str(result)))
        self.col_widths = widths

    def list_to_colstring(self,l, widths, spacing, max_width):
        s = ""
        for i, item in enumerate(l):
            s += pad_left(str(item)[:max_width], min(max_width,widths[i])+spacing)
        return(s)

class AccumulatorFactory():
    @classmethod
    def new_accumulator(cls, type):
        if type == "MAX":
            return MaxAccumulator()
        elif type == "MIN":
            return MinAccumulator()
        elif type == "SUM":
            return SumAccumulator()
        elif type == "AVG":
            return AverageAccumulator()
        elif type == "COUNT":
            return Accumulator()
        else:
            raise ValueError(f"Bad Accumulator type: '{type}'")

class Accumulator:
    def __init__(self):
        self.reset()

    def reset(self):
        self._values = []

    def accumulate(self, value):
        self._values.append(value)

    def get_value(self):
        return len(self._values)

class SumAccumulator(Accumulator):
    def get_value(self):
        return sum(self._values)

class AverageAccumulator(Accumulator):
    def get_value(self):
        return mean(self._values)

class MaxAccumulator(Accumulator):
    def get_value(self):
        return max(self._values)

class MinAccumulator(Accumulator):
    def get_value(self):
        return min(self._values)

########## MAIN PROGRAM ########################################################
# -- OUTLINE --
# INITIALIZE
    # HANDLE SIGINT
    # GET COMMAND LINE ARGS
# READ IN DATA
# PERFORM OPERATION
    # HEADERS OPERATION: DISPLAY HEADERS AND EXIT
    # MATH OPERATIONS:
        # VALIDATE DATA
        # CALCULATE RESULTS
        # DISPLAY RESULTS
            # DISPLAY HEADERS AND RESULT ROWS

signal.signal(signal.SIGINT, signal_handler)
args = ArgRetriever()

# read the data from the file into a 2D list
# (note: I am using the csv module's reader object
# to automagically handle commas inside quoted strings)
data = [line + ["ALL ROWS"] for line in csv.reader(args.infile)]
args.infile.close()

headers = data[0]  # zeroth row is the headers
data = data[1:]    # all subsequent rows are data

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

# validate the data
if len(data) == 0:
    sys.exit("No data in file.")
if max(args.group_cols) >= len(headers):
    sys.exit("Error: a specified group column is greater than the number of columns.")
if max(args.stat_cols) >= len(headers):
    sys.exit("Error: a specified stat column is greater than the number of columns.")

for i, row in enumerate(data):
    if len(row) != len(headers):
        sys,exit(f"Error: row {i} has the wrong number of columns.")

# now iterate over the data, performing the desired operation for each group
# and printing the results
data_sort(data, args.group_cols)
data.append([None for a in data[0]]) # add a a dummy row as the last row ... see below for why
prev_group = [val for col, val in enumerate(data[0]) if col in args.group_cols]

accumulators = [AccumulatorFactory.new_accumulator(args.operation) for a in args.stat_cols]

formatter = DataFormatter()
formatter.set_headers(
    [headers[i] for i in args.group_cols] +
    [args.operation + ' ' + headers[i] for i in args.stat_cols]
)

for ctr, row in enumerate(data):

    curr_group = [val for col, val in enumerate(row) if col in args.group_cols]

    # if the group changed, store the results in the formatter for the
    # previous group then reset the results for this new group
    if curr_group != prev_group:
        values = [acc.get_value() for acc in accumulators]
        formatter.add_data_row(prev_group + values)
        for acc in accumulators: acc.reset()

    # if we are on the last row (the dummy row ... see above),
    # then there are no results to tabulate, so just exit the loop (we are done)
    if ctr == len(data) - 1:
        break

    # tabulate the results for the current row
    for result_index, row_index in enumerate(args.stat_cols):
        value = safe_float(row[row_index],
            f"Error: found non-numeric data '{row[row_index]}' in row {ctr}, column {row_index}")
        accumulators[result_index].accumulate(value)

    prev_group = curr_group

# print out the whole thing!
if args.ascend_cols != None:
    formatter.sort_ascend([args.combined_cols.index(a) for a in args.ascend_cols])
elif args.descend_cols != None:
    formatter.sort_descend([args.combined_cols.index(a) for a in args.descend_cols])

if args.csv_output:
    formatter.display_as_csv(args.rows)
else:
    formatter.display(args.rows)
