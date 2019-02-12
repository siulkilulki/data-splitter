#!/usr/bin/env python3

import hashlib
import argparse
import sys
import itertools
import bisect
import logging
logging.basicConfig(level=logging.INFO)
# MAX_NUM = 256**2 - 1  #255+255*256
# BYTES = 3
# MAX_NUM = 256**BYTES - 1  #255+255*256+255*256^2

BYTE_SIZE = 256


def get_args():
    parser = argparse.ArgumentParser(
        description='Splits data in reproducible fashion.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'first_fraction',
        metavar='fraction',
        type=float,
        help='Fraction or percentage of infile with will be in output file.')
    parser.add_argument(
        'rest_fractions', metavar='fraction', type=float, nargs='+')
    # help=argparse.SUPPRESS)
    parser.add_argument(
        '-i',
        '--input',
        dest='infile',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin)
    parser.add_argument(
        '-f',
        '--fields',
        help=
        'Fields from which to calculate hash in the same format as Linux `cut` command. e.g. -f 1,3-5 to select 1st, 3rd, 4th, 5th field.'
    )
    parser.add_argument(
        '--with-header',
        action='store_true',
        dest='is_header',
        help='Handles header. Add it into every splitted file.')
    parser.add_argument(
        '-hash',
        '--hash-function',
        default='md5',
        help='Hash function to be used')
    parser.add_argument(
        '-b',
        '--bytes-nr',
        default=4,
        type=int,
        help='number of last bytes of hash (e.g md5) to consider')
    parser.add_argument(
        '--endian',
        choices=['big', 'little'],
        default='big',
        help=
        'Choose order of bytes. With with big endian last X bytes are choosen, with little endian first X bytes are choosen.'
    )
    parser.set_defaults(is_header=False)
    namespace = parser.parse_args()
    namespace.fractions = [namespace.first_fraction] + namespace.rest_fractions
    return namespace


class RangeStruct:
    """Simple range dict with O(logn) search, O(n) insertions
    points      -> [0.2, 0.5,  1 ]
    items       -> ['a', 'b', 'c']
    (0 - 0.2]   -> 'a'
    (0.2 - 0.5] -> 'b'
    (0.5 - 1]   -> 'c'
    get(0.1) returns 'a'
    get(0.2) returns 'a'
    get(0.3) returns 'b'"""

    def __init__(self):
        self.points = []
        self.items = []

    def add(self, point, item):
        index = bisect.bisect_left(self.points, point)
        self.points.insert(index, point)
        self.items.insert(index, item)

    def get(self, value):
        index = bisect.bisect_left(self.points, value)
        return self.items[index]


def cumulative_normalized_fractions(fractions, bytes_nr):
    max_num = BYTE_SIZE**bytes_nr - 1
    fract_sum = sum(fractions)
    cum_fractions = itertools.accumulate(fractions)
    return map(lambda fract: max_num * fract / fract_sum, cum_fractions)


def get_range_struct(fractions, infile_name, bytes_nr):
    cum_fractions = cumulative_normalized_fractions(fractions, bytes_nr)
    range_dict = RangeStruct()
    for i, fract in enumerate(cum_fractions):
        fname = f'{infile_name}.part_{i}'
        range_dict.add(fract, open(fname, 'w'))
    return range_dict


def calc_hash(string, hash_function):
    # TODO: change to named constructor instead of new, for speed improvement
    hash_gen = hashlib.new(hash_function)
    hash_gen.update(string.encode())
    return hash_gen.digest()


def append_to_file(line, range_dict, fields, hash_function, bytes_nr, endian):
    if fields:
        row = line.rstrip('\n').split('\t')
        to_hash = ''.join([row[i] for i in fields])
    else:
        to_hash = line
    hash_ = calc_hash(to_hash, hash_function)
    value = int.from_bytes(hash_[-bytes_nr:], endian)
    file_ = range_dict.get(value)
    print(line, file=file_, end='')


def get_fields(fields_arg):
    if not fields_arg:
        return []
    fields = []
    for field in fields_arg.split(','):
        if not '-' in field:
            fields.append(int(field) - 1)
        else:
            start, end = map(int, field.split('-'))
            fields = fields + list(range(start - 1, end))
    return fields


def main():
    args = get_args()
    infile_name = args.infile.name.lstrip('<').rstrip('>')
    fractions = args.fractions
    fields = get_fields(args.fields)
    range_dict = get_range_struct(fractions, infile_name, args.bytes_nr)
    logging.info(f'''\nhash: {args.hash_function}
    bytes number: {args.bytes_nr}
    byte-order: {args.endian}''')
    if args.is_header:
        header = next(args.infile)
        for outfile in range_dict.items:
            print(header, file=outfile, end='')
    for line in args.infile:
        append_to_file(line, range_dict, fields, args.hash_function,
                       args.bytes_nr, args.endian)
    for outfile in range_dict.items:
        outfile.close()


if __name__ == '__main__':
    main()
