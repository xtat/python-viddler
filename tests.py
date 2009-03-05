#!/usr/bin/python
# cheap viddler API tests
# Todd Troxell <todd@viddler.com>
#
# Copyright 2008 Todd Troxell
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

APIKEY = "000000000000000000000000"
USER = "user"
PASSWORD = "pass"
from viddler import Viddler

if __name__ == '__main__':
  v = Viddler(APIKEY, USER, PASSWORD)
  
  print v.getProfile("todd")
  print v.getByTag("funny")
  print v.getByUser("todd")
  print v.getDetails("1f27204")
  print v.getDetailsByUrl("http://www.viddler.com/explore/todd/videos/20/")
  print v.getFeatured()
  print v.getProfile("todd")
  print v.getRecordToken()
  print v.getStatus("1f27204")
  #print v.setProfile({'first_name':'fblehfo'})
  #print v.register()
  #print v.upload("rb_05_dec_28.mov", "test", "test", "test")
  #print v.setDetails()
  #print v.setOptions()
  #print v.setProfile()
