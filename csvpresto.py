#!/usr/bin/env python3

from argparse import ArgumentParser
from argparse import FileType
import csv
import sys
import signal

if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
    sys.exit("Error: csvpresto requires Python 3.2 or higher")

def validate_number(s, row, col):
    try:
        float(s)
    except ValueError:
        sys.exit(f"Error: found non-numeric data '{s}' in row {row}, column {col}")

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

        args = parser.parse_args()

        self.group_cols = args.group_cols
        self.stat_cols = args.stat_cols
        self.infile = args.infile
        self.operation = args.operation
        self.csv_output = args.csv_output
        self.ascend_cols = args.ascend_cols
        self.descend_cols = args.descend_cols

        if self.operation in ["AVG","SUM"] and None == self.stat_cols:
            sys.exit(f"Error: -s must be supplied for the {self.operation} operation.")

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

    def display_as_csv(self):
        csv_w = csv.writer(sys.stdout)
        csv_w.writerow(self.headers)
        csv_w.writerows(self.data_grid)

    def display(self):
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
        for row in self.data_grid:
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
        else:
            return Accumulator()

class Accumulator:
    def __init__(self):
        self.reset()

    def reset(self):
        self._value = None
        self._count = 0

    def accumulate(self, value):
        self._count += 1
        if self._value == None:
            self._value = value
        else:
            self._sub_accumulate(value)

    def _sub_accumulate(self, value):
        self._value = self._count

    def get_value(self):
        return self._value

class SumAccumulator(Accumulator):
    def _sub_accumulate(self, value):
        self._value += value

class AverageAccumulator(SumAccumulator):
    def get_value(self):
        return float(self._value) / float(self._count)

class MaxAccumulator(Accumulator):
    def _sub_accumulate(self, value):
        self._value = max(value, self._value)

class MinAccumulator(Accumulator):
    def _sub_accumulate(self, value):
        self._value = min(value, self._value)

# ------------------- MAIN PROGRAM --------------------------------------------

signal.signal(signal.SIGINT, signal_handler)

args = ArgRetriever()

# -- OUTLINE TO REFACTOR THE CODE --
# INITIALIZE
    # CHECK PYTHON VERSION
    # HANDLE SIGINT
    # GET COMMAND LINE ARGS
# READ IN DATA
# PERFORM OPERATION
    # HEADERS OPERATION: DISPLAY HEADERS
    # MATH OPERATIONS:
        # VALIDATE DATA
        # CALCULATE RESULTS
        # DISPLAY RESULTS
            # DISPLAY HEADER LINE (AND SEPARATOR)
            # DISPLAY RESULT ROWS

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

# put the string arguments into a list as integers
group_list = [int(a) for a in args.group_cols]
stat_list = [int(a) for a in args.stat_cols]
combined_cols = group_list + stat_list

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

# now iterate over the data, performing the desired operation for each group
# and printing the results
data_sort(data, group_list)
data.append([None for a in data[0]]) # add a a dummy row as the last row ... see below for why
prev_group = [val for col, val in enumerate(data[0]) if col in group_list]

accumulators = [AccumulatorFactory.new_accumulator(args.operation) for a in stat_list]

formatter = DataFormatter()
formatter.set_headers(
    [headers[i] for i in group_list] +
    [args.operation + ' ' + headers[i] for i in stat_list]
)

for ctr, row in enumerate(data):

    curr_group = [val for col, val in enumerate(row) if col in group_list]

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
    for result_index, row_index in enumerate(stat_list):
        if args.operation != "COUNT":
            validate_number(row[row_index], ctr, row_index)

        accumulators[result_index].accumulate(float(row[row_index]))

    prev_group = curr_group

# print out the whole thing!
if args.ascend_cols != None:
    formatter.sort_ascend([combined_cols.index(a) for a in args.ascend_cols])
elif args.descend_cols != None:
    formatter.sort_descend([combined_cols.index(a) for a in args.descend_cols])

if args.csv_output:
    formatter.display_as_csv()
else:
    formatter.display()
