#Implementation of 'Crack' problem set from CS50 in Python
#Author: Vinícius C. Silva

import sys, crypt, itertools
from string import ascii_lowercase
from string import ascii_uppercase


def main():
    if(len(sys.argv) != 2):
        print("Usage: python3 crack.py 'hash'")
        exit(1)

    HASH = sys.argv[1]
    salt = str(50)
    password = []

    for attempt in range(5):
        print("Cracking attempt {}...".format(attempt))
        if Crack(attempt, salt, HASH) == True:
            break

    print("Program terminated.")





def Crack(n, salt, HASH):
    alpha = ascii_uppercase + ascii_lowercase

    for x in itertools.permutations(alpha, n):
        s = ""
        password = s.join(x)
        if crypt.crypt(password, salt) == HASH:
            print("Password is '{}'".format(password))
            return True


if __name__ == "__main__":
    main()
