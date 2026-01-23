#
#   ___                  __                __ 
# .'  _|.--------.--.--.|  |_.-----.-----.|  |
# |   _||        |  |  ||   _|  _  |  _  ||  |
# |__|  |__|__|__|_____||____|_____|_____||__|
# 
#
 
 import sys
import os


directory = os.path.dirname(__file__)
with open(os.path.join(directory, "types.txt")) as file:
    types = {}
    for line in file.readlines():
        if line[-1] == '\n':
            line = line[:-1]
        print(line)
        (t, size) = line.split(',')

        types[t] = size


with open(os.path.join(directory, "test_sizeof.c"), "wt") as sys.stdout:
    print("""
#include <stdio.h>
#include <stdlib.h>
#include <fmi2Functions.h>
#include "remote.h"

int main(void) {
    int error = 0;
    """)

    for t in types.keys():
        print(f'''
    if (sizeof({t})  != {types[t]}) {{
        printf("%20s: %zd | ERROR: expected %d\\n", "{t}", sizeof({t}), {types[t]});
        error += 1;
    }} else {{
        printf("%20s: %zd | OK\\n", "{t}", sizeof({t}));
    }}
''')
    print("""
    return error;
}
    """)
