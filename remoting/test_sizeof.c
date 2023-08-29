/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#include <stdio.h>
#include <stdlib.h>
#include <fmi2Functions.h>
#include "remote.h"

int main(void) {
    int error = 0;
    

    if (sizeof(fmi2Boolean)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2Boolean", sizeof(fmi2Boolean), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2Boolean", sizeof(fmi2Boolean));
    }


    if (sizeof(fmi2Byte)  != 1) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2Byte", sizeof(fmi2Byte), 1);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2Byte", sizeof(fmi2Byte));
    }


    if (sizeof(fmi2Integer)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2Integer", sizeof(fmi2Integer), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2Integer", sizeof(fmi2Integer));
    }


    if (sizeof(fmi2Real)  != 8) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2Real", sizeof(fmi2Real), 8);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2Real", sizeof(fmi2Real));
    }


    if (sizeof(fmi2StatusKind)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2StatusKind", sizeof(fmi2StatusKind), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2StatusKind", sizeof(fmi2StatusKind));
    }


    if (sizeof(fmi2Type)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2Type", sizeof(fmi2Type), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2Type", sizeof(fmi2Type));
    }


    if (sizeof(fmi2ValueReference)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "fmi2ValueReference", sizeof(fmi2ValueReference), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "fmi2ValueReference", sizeof(fmi2ValueReference));
    }


    if (sizeof(portable_size_t)  != 4) {
        printf("%20s: %zd | ERROR: expected %d\n", "portable_size_t", sizeof(portable_size_t), 4);
        error += 1;
    } else {
        printf("%20s: %zd | OK\n", "portable_size_t", sizeof(portable_size_t));
    }


    return error;
}
    
