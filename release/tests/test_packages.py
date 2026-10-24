import copy
import io
from pathlib import Path
import stat
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from reproduction import safe_members,compare_measurements

class PackageTests(unittest.TestCase):
    def archive(self,names):
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w') as archive:
            for name in names:archive.writestr(name,b'x')
        memory.seek(0);return zipfile.ZipFile(memory)

    def test_unsafe_and_duplicate_names_fail_before_extraction(self):
        for names in (['../owner.token'],['/owner.token'],['raw/../../owner.token'],['a\\b'],['a','a']):
            with self.archive(names) as archive,self.assertRaises(ValueError):safe_members(archive)
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w') as archive:
            entry=zipfile.ZipInfo('link');entry.external_attr=(stat.S_IFLNK|0o777)<<16;archive.writestr(entry,'/home/private')
        memory.seek(0)
        with zipfile.ZipFile(memory) as archive,self.assertRaises(ValueError):safe_members(archive)

    def source(self,value=2.5):
        return {'observations.json':[{'id':'one','sha256':'a'*64}],
                'measurements.json':[{'observation_id':'one','role':'search','name':'period','unit':'d','value':value,
                                     'uncertainty':{'kind':'unavailable','reason':'Not estimated.'},'quality_flags':[]}]}

    def test_numerical_tolerance_does_not_hide_unit_or_input_changes(self):
        original=self.source();near=self.source(2.5+1e-11);limits={'absolute':1e-12,'relative':1e-10}
        count,differences=compare_measurements(original,near,limits);self.assertEqual(count,1);self.assertEqual(differences,[])
        changed=self.source(2.6);self.assertTrue(compare_measurements(original,changed,limits)[1])
        changed=self.source();changed['measurements.json'][0]['unit']='s';self.assertTrue(compare_measurements(original,changed,limits)[1])
        changed=self.source();changed['observations.json'][0]['sha256']='b'*64;self.assertEqual(compare_measurements(original,changed,limits)[0],0)
        self.assertTrue(compare_measurements(self.source(0),self.source(False),limits)[1])

    def test_duplicate_measurements_cannot_hide_a_difference(self):
        source=self.source();source['measurements.json']+=copy.deepcopy(source['measurements.json'])
        with self.assertRaises(ValueError):compare_measurements(source,self.source(),{'absolute':1e-12,'relative':1e-10})
