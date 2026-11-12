import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from word_clean_history import append_history,read_history

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'history.jsonl'
    def test_minimal_data_and_repeated_success(self):
        for _ in range(2):append_history(self.path,Path(self.tmp.name)/'private-folder'/'sample.txt',{'吿':'告'},{'吿':2})
        records,bad=read_history(self.path);self.assertEqual(bad,0);self.assertEqual(len(records),2)
        for r in records:
            self.assertEqual(set(r),{'file_name','processed_at','replacements'});self.assertEqual(r['file_name'],'sample.txt');self.assertEqual(r['replacements'],[{'old':'吿','new':'告','count':2}])
        self.assertNotIn('private-folder',self.path.read_text(encoding='utf-8'));self.assertNotIn(self.tmp.name,self.path.read_text(encoding='utf-8'))
    def test_empty_zero_and_corrupt_history(self):
        self.assertEqual(read_history(self.path),([],0));append_history(self.path,'zero.txt',{},{});before=self.path.read_bytes()
        with self.path.open('ab') as f:f.write(b'{broken\n')
        records,bad=read_history(self.path);self.assertEqual(len(records),1);self.assertEqual(records[0]['replacements'],[]);self.assertEqual(bad,1);self.assertEqual(self.path.read_bytes(),before+b'{broken\n')
    def test_read_rejects_extra_fields_or_paths(self):
        self.path.write_text(json.dumps({'file_name':'x/y.txt','processed_at':'now','replacements':[]})+'\n'+json.dumps({'file_name':'y.txt','processed_at':'now','replacements':[],'body':'private'}),encoding='utf-8');self.assertEqual(read_history(self.path),([],2))
    def test_write_failure_propagates(self):
        with patch('word_clean_history.os.open',side_effect=PermissionError('read only')):
            with self.assertRaises(PermissionError):append_history(self.path,'sample.txt',{}, {})

if __name__=='__main__':unittest.main(verbosity=2)