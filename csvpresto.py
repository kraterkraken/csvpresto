from argparse import ArgumentParser
import sys

if sys.version_info.major < 3 or sys.version_info.minor < 2:
    sys.exit("Error: csvpresto requires Python 3.2 or higher")

def validate_number(s, row, col):
    try:
        float(s)
    except ValueError:
        sys.exit("Error: found non-numeric data '{}' in row {}, column {}".format(s, row, col))

def list_to_string(l):
    return ", ".join([str(a) for a in l])

class ArgRetriever:
    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument("-g", dest="group_cols", nargs='+', type=int, required=True,
            help="The list of columns to group by.  Ex: 1 2 3 4")
        parser.add_argument("-s", dest="stat_cols", nargs='+', type=int, required=True,
            help="The list of columns to gather stats on.  Ex: 5 6 7")
        parser.add_argument("-f", dest="file_name", required=True,
            help="The CSV file to use as input")
        parser.add_argument("-o", dest="operation", required=True,
            choices=["SUM", "COUNT", "AVG"], default="SUM",
            help="The statistical operation to perform")
        args = parser.parse_args()

        #print(args)
        self.group_cols = args.group_cols
        self.stat_cols = args.stat_cols
        self.file_name = args.file_name
        self.operation = args.operation


# ------------------- MAIN PROGRAM --------------------------------------------
arg_retriever = ArgRetriever()
group_list = [int(a) for a in arg_retriever.group_cols]
stat_list = [int(a) for a in arg_retriever.stat_cols]

# read the data from the file into a 2D list
data = []
with open(arg_retriever.file_name) as file:
    data = [line.split(",") for line in file]
headers = data[:1][0]
data = data[1:]

# validate that the data makes sense with the given group and stat columns
if len(data) == 0:
    sys.exit("No data in file.")
if max(group_list) >= len(headers):
    sys.exit("Error: a specified group column is greater than the number of columns.")
if max(stat_list) >= len(headers):
    sys.exit("Error: a specified stat column is greater than the number of columns.")

###############################################################################
##### TODO - Handle data cells that are QUOTED strings with embedded commas
##### TODO - Verify that all rows have the same number of columns
###############################################################################

# sort the data by the grouping columns
group_list.reverse() # reverse the order so the sorting works
for col in group_list:
    data.sort(key=lambda x: x[col])
group_list.reverse() # put the order back again

# print the headers that we need
print()
print("{} ... {}".format(
    list_to_string([headers[i] for i in group_list]),
    list_to_string([headers[i] for i in stat_list]))
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
        if arg_retriever.operation == "SUM":
            result = sum
        elif arg_retriever.operation == "COUNT":
            result = count
        elif arg_retriever.operation == "AVG":
            result = [float(s)/float(c) for s,c in zip(sum,count)]

        print("{} ... {}".format(list_to_string(prev_group), list_to_string(result)))

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
        validate_number(row[row_index], ctr, row_index)
        sum[result_index] += float(row[row_index])
        count[result_index] += 1

    prev_group = curr_group