#!/usr/bin/env python
import netaddr
import argparse


parser = argparse.ArgumentParser(description='generate ASA nats for pre and post 8.4 ASA Code')


parser.add_argument("-p", "--public", dest="public",
                    metavar="1.1.1.0/24", help="CIDR range of PUBLIC addrs. ex: 1.1.1.0/24 or 1.1.1.3/32, etc")

parser.add_argument("-P", "--private", dest="private",
                    metavar="172.16.1.0/27", help="CIDR range of PRIVATE addrs to NAT to. ex: 172.16.1.0/27, 10.10.10.10/32, etc")

parser.add_argument("-s" "--sequence", dest="sequence",
                    metavar="5056", help="If this option is selected this will trigger build of pre 8.4 NATs, with this value being\
                    next number in the sequence, NOT using this arg will result in 8.4+ rules being built")

parser.add_argument("-o", "--outside", dest="outside_iface",
                    metavar="outside_iface", help="name of the outside interface")

parser.add_argument("-i", "--inside", dest="inside_iface",
                    metavar="inside_iface", help="name of the inside interface")

args = parser.parse_args()



def buildConfig(sequence=None, public=None, private=None,
                in_iface=None, out_iface=None):

    """ 
        Build NAT rules 
        Pre 8.4 style reference:

          nat (inside) 22 172.17.103.192 255.255.255.224
          global (outside) 22 1.2.3.4  netmask 255.255.255.255

        8.4 and current style reference:

           object network obj-1.2.3.4
           subnet 172.17.103.92 255.255.255.224
           nat (inside,outside) dynamic 1.2.3.4
    """

    public = netaddr.IPNetwork(public)
    privates = netaddr.IPNetwork(private)

    # If sequence number exists, build in the pre 8.4 styling
    if sequence:
        nats = []
        globals = []
        set_privates = privates
        for ip in public.iter_hosts():
  
            getmask = netaddr.IPNetwork(ip)
            nats.append("nat (%s) %d %s %s" % (in_iface, sequence, set_privates.cidr.ip.format(),
                                               set_privates.cidr.netmask.format()))

            globals.append("global (%s) %d %s netmask %s" % (out_iface, sequence,
                                                             ip, getmask.netmask))
         
            # Get the next private network...
            set_privates = set_privates.next()
            # Bump the sequence
            sequence += 1

        for x in nats:
            print x
        for x in globals:
           print x


    # Else build post 8.4 style
    else:
        set_privates = privates
        for ip in public.iter_hosts():
            getmask = netaddr.IPNetwork(ip)
            print "object network obj-%s" % ip
            print "subnet %s %s" % (set_privates.cidr.ip.format(), 
                                    set_privates.cidr.netmask.format())
            print "nat (%s,%s) dynamic %s\n" % (in_iface, out_iface, ip)

            set_privates = set_privates.next()


if __name__ == "__main__":
    if args.sequence:
        buildConfig(sequence=int(args.sequence), public=args.public,
                    private=args.private, in_iface=args.inside_iface,
                    out_iface=args.outside_iface)

    else:

        buildConfig(public=args.public, private=args.private, 
                    in_iface=args.inside_iface, 
                    out_iface=args.outside_iface)
