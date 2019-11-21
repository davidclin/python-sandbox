#!/usr/bin/python3
"""
Print the information about IP address usage of EC2 account

Sorts by VPC id, the by account owner
"""
import boto3
import sys
import json
import collections
import re

def main():
    client = boto3.client('ec2')

    response = client.describe_network_interfaces()
    assert response.get('NextToken') is None, 'Pagination not supported'

    stats = collections.defaultdict(lambda: collections.defaultdict(int))
    info = collections.defaultdict(set)

    for ifrec in response['NetworkInterfaces']:
        descr = ','.join(g['GroupName'] for g in ifrec['Groups']) or 'no-groups'

        creator = 'unknown'
        for g in ifrec['TagSet']:
            if g['Key'] == 'AutoTag_Creator':
                creator = g['Value']
        creator = re.sub('^arn:aws:iam::929292782238:(user/)', r'\1', creator)
        creator = re.sub('^arn:aws:sts::929292782238:(assumed-role/)', r'\1', creator)
        creator = re.sub('^(assumed-role/[^/]+)/i-[0-9a-f]+$', r'\1', creator)
        creator = re.sub('^(assumed-role)/' + re.escape(descr) + '$', r'\1', creator)
        info[descr].add('by ' + creator)

        for k1 in ('~all-subnets', ifrec['SubnetId']):
            for k2 in ('~total', descr):
                stats[k1][k2] += len(ifrec['PrivateIpAddresses'])


    for k1, k1_vals in sorted(stats.items()):
        print('\n==== %s =====' % k1)
        small_num = small_count = 0
        small_limit = min(2, len(k1_vals) / 10)
        for k2, count in sorted(k1_vals.items(), key=lambda kv:-kv[1]):
            if count > small_limit:
                print(" %5d %s" % (count, '; '.join([k2] + sorted(info[k2]))))
            else:
                small_count += count
                small_num += 1
        if small_num:
            print(" %5d from %d items with %d IPs or less" % (small_count, small_num, small_limit))


if __name__ == '__main__':
    main()
