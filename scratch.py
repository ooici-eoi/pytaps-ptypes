#import argparse
#
#parser = argparse.ArgumentParser(description='This command line application does something cool')
#parser.add_argument('--c', dest='is_ncom', action='store_true', help="use this if you want ncom")
#parser.add_argument('--a', dest='this_is_a', action='store_true', help='use this if you want a you silly')
#args = parser.parse_args()
#
#
#if args.is_ncom:
#    print "you want ncom"
#
#if args.this_is_a:
#    print "you want a"

import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('integers', metavar='N', type=int, nargs='+',
    help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
    const=sum, default=max,
    help='sum the integers (default: find the max)')

args = parser.parse_args()
print args.accumulate(args.integers)