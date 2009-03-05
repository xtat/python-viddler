#!/usr/bin/python

import viddler
import sys

APIKEY = "0xdeadbeef"
USER = "user"
PASS = "password"

viddler_api = viddler.Viddler(APIKEY, USER, PASS)
print viddler_api.getProfile("todd")
