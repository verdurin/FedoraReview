#!/usr/bin/python -tt
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# (C) 2011 - Tim Lauridsen <timlau@fedoraproject.org>
'''
Unit tests for bugzilla bug handling
'''


import sys
import os.path
import re
sys.path.insert(0,os.path.abspath('../'))

import os
import unittest
import glob
from reviewtools import Helpers, Source, SRPMFile, SpecFile
from base import *

class MiscTests(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.srpm_file = TEST_WORK_DIR + os.path.basename(TEST_SRPM)
        self.spec_file = TEST_WORK_DIR + os.path.basename(TEST_SPEC)
        self.source_file = TEST_WORK_DIR + os.path.basename(TEST_SRC)
        self.helper = Helpers()

    def setUp(self):
        if not os.path.exists(TEST_WORK_DIR):
            os.makedirs(TEST_WORK_DIR)
        self.helper.set_work_dir(TEST_WORK_DIR)
        self.helper._get_file(TEST_SRPM)
        #self.helper._get_file(TEST_SRC)
        self.helper._get_file(TEST_SPEC)


    def test_spec_file(self):
        ''' Test the SpecFile class'''
        spec = SpecFile(self.spec_file) 
        # Test misc rpm values (Macro resolved)
        self.assertEqual(spec.name,'python-test')
        self.assertEqual(spec.version,'1.0')
        # resolve the dist-tag
        dist = self.helper._run_cmd('rpm --eval %dist')[:-1]
        self.assertEqual(spec.release,'1'+dist)
        # test misc rpm values (without macro resolve)
        self.assertEqual(spec.find_tag('Release'),'1%{?dist}')
        self.assertEqual(spec.find_tag('License'),'GPLv2+')
        self.assertEqual(spec.find_tag('Group'),'Development/Languages')
        # Test rpm value not there
        self.assertEqual(spec.find_tag('PreReq'),None)
        # Test get sections
        expected = {'%clean': ['rm -rf $RPM_BUILD_ROOT']}
        self.assertEqual(spec.get_section('%clean'), expected)
        expected = {'%build': ['%{__python} setup.py build']}
        self.assertEqual(spec.get_section('%build'), expected)
        expected = {'%install': ['rm -rf $RPM_BUILD_ROOT', '%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT']}
        self.assertEqual(spec.get_section('%install'),expected)
        expected = {'%files': ['%defattr(-,root,root,-)', '%doc COPYING', '%{python_sitelib}/*']}
        self.assertEqual(spec.get_section('%files'),expected)
        # Test get_sources (return the Source/Patch lines with macros resolved)
        expected = {'Source0': 'http://timlau.fedorapeople.org/files/test/review-test/python-test-1.0.tar.gz'}
        self.assertEqual(spec.get_sources(), expected)
        # Test find
        regex = re.compile(r'^Release\s*:\s*(.*)')
        res = spec.find(regex)
        if res:
            self.assertEqual(res.groups(), ('1%{?dist}',))
        else:
            self.assertTrue(False)
            
        
        
    def test_source_file(self):
        """ Test the SourceFile class """
        source = Source()
        # set the work dir
        source.set_work_dir(TEST_WORK_DIR)
        # download the upstream source file
        source.get_source(TEST_SRC)
        # check that source exists and source.filename point to the right location
        self.assertEqual(source.filename, self.source_file)
        self.assertTrue(os.path.exists(self.source_file))
        self.assertEqual(source.check_source_md5(), "289cb714af3a85fe36a51fa3612b57ad")
        
    def test_srpm_file(self):
        """ Test the SRPMFile class """
        srpm = SRPMFile(self.srpm_file)
        # install the srpm
        srpm.install()
        self.assertTrue(srpm.is_installed)
        src_files = glob.glob(os.path.expanduser('~/rpmbuild/SOURCES/*'))
        expected = [os.path.expanduser('~/rpmbuild/SOURCES/python-test-1.0.tar.gz')]
        self.assertEqual(src_files, expected)
        srpm.build()
        self.assertTrue(srpm.is_build)
        rpm_files = glob.glob(os.path.expanduser('~/rpmbuild/RPMS/noarch/*'))
        dist = self.helper._run_cmd('rpm --eval %dist')[:-1]
        expected = [os.path.expanduser('~/rpmbuild/RPMS/noarch/python-test-1.0-1%(dist)s.noarch.rpm') % {'dist': dist}]
        self.assertEqual(rpm_files, expected)
        
        