import unittest,tempfile,time,tkinter as tk,importlib.util,importlib.machinery
from pathlib import Path
from unittest.mock import patch
class AutoRemoveTests(unittest.TestCase):
    def test_mixed_batch_preview_cancel_success_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);loader=importlib.machinery.SourceFileLoader('remove_gui',str(Path(__file__).parent/'word_clean_gui.pyw'));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m);m.BASE=base
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy);app=m.App(root)
            mapping=base/'mapping.csv';mapping.write_text('旧字型,新字形\n吿,告\n',encoding='utf-8-sig');app.map_path.set(str(mapping));app.out_path.set(str(base/'out'))
            files=[base/'first.txt',base/'failure.txt',base/'last.txt']
            for p in files:p.write_text('吿',encoding='utf-8')
            before={p:p.read_bytes() for p in files};app.add(files)
            def wait():
                until=time.monotonic()+10
                while app.busy and time.monotonic()<until:root.update();time.sleep(.01)
                self.assertFalse(app.busy)
            app.run(False);wait();self.assertEqual(app.files,files);self.assertFalse((base/'history.jsonl').exists())
            with patch.object(m.messagebox,'askyesno',return_value=False):app.run(True)
            self.assertEqual(app.files,files);self.assertFalse((base/'out').exists())
            real=m.process_file
            def convert(source,mapping,destination=None,encoding_choice='auto'):
                if destination and source==files[1]:raise OSError('synthetic failure')
                return real(source,mapping,destination,encoding_choice)
            with patch.object(m,'process_file',side_effect=convert),patch.object(m.messagebox,'askyesno',return_value=True):app.run(True);wait()
            self.assertEqual(app.files,[files[1]]);self.assertEqual(app.tree.get_children(),('0',));self.assertIn('失败',app.tree.set('0','result'));self.assertIsNone(app.ready)
            self.assertEqual(len(m.read_history(base/'history.jsonl')[0]),2);self.assertEqual(len(list(app.last_output.glob('*_字形已转换.txt'))),2)
            self.assertTrue((app.last_output/'字形统计.csv').exists());self.assertIn('2 个成功',app.log.get('1.0','end'))
            self.assertEqual(len(list(app.last_output.iterdir())),3)
            self.assertEqual({p.name for p in app.last_output.glob('*.csv')},{'字形统计.csv'})
            app.run(False);wait()
            with patch.object(m.messagebox,'askyesno',return_value=True):app.run(True);wait()
            self.assertEqual(app.files,[]);self.assertEqual(len(m.read_history(base/'history.jsonl')[0]),3)
            self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
if __name__=='__main__':unittest.main(verbosity=2)