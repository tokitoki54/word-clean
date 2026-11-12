"""Hidden-window regression checks for editor search. No user documents."""
import unittest, tempfile, importlib.util, importlib.machinery
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
from word_clean_core import load_mapping

class SearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        loader=importlib.machinery.SourceFileLoader('search_gui',str(Path(__file__).parent/'word_clean_gui.pyw'))
        spec=importlib.util.spec_from_loader(loader.name,loader);self.mod=importlib.util.module_from_spec(spec);loader.exec_module(self.mod)
        self.root=tk.Tk();self.root.withdraw();self.addCleanup(self.root.destroy)
        original_init=tk.Toplevel.__init__
        def hidden(win,*args,**kwargs):original_init(win,*args,**kwargs);win.withdraw()
        self.patches=[patch.object(tk.Toplevel,'__init__',hidden),patch.object(tk.Toplevel,'grab_set',return_value=None)]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.app=self.mod.App(self.root);self.original=self.base/'original.csv'
        self.original.write_text('旧字型,新字形\n吿,告\n說,説\n淨,浄\n',encoding='utf-8-sig');self.before=self.original.read_bytes();self.app.map_path.set(str(self.original));self.open_editor()
    def open_editor(self):
        self.app.edit_mapping();self.root.update();self.win=next(w for w in self.root.winfo_children() if isinstance(w,tk.Toplevel))
        def descendants(w):
            for c in w.winfo_children():yield c;yield from descendants(c)
        self.widgets=list(descendants(self.win));self.table=next(w for w in self.widgets if isinstance(w,ttk.Treeview))
        self.search=next(w for w in self.widgets if w.winfo_name()=='mapping_search')
        self.inputs=[next(w for w in self.widgets if w.winfo_name()==n) for n in ('old_input','new_input')]
    def click(self,label):
        next(w for w in self.widgets if isinstance(w,ttk.Button) and w.cget('text')==label).invoke();self.root.update()
    def query(self,value):
        self.search.delete(0,'end');self.search.insert(0,value);self.root.update()
    def rows(self):return [self.table.item(i,'values') for i in self.table.get_children()]
    def values(self,a,b):
        for w,v in zip(self.inputs,(a,b)):w.delete(0,'end');w.insert(0,v)
    def select_first(self):
        self.table.selection_set(self.table.get_children()[0]);self.table.event_generate('<<TreeviewSelect>>');self.root.update()
    def test_filter_edit_delete_save_full_table(self):
        self.assertEqual(len(self.rows()),3)
        for q in ('吿','告',' 告 '):self.query(q);self.assertEqual(self.rows(),[('吿','告')])
        self.query('不存在');self.assertEqual(self.rows(),[]);self.click('清空搜索');self.assertEqual(len(self.rows()),3)
        self.query('告');self.select_first();self.assertEqual([e.get() for e in self.inputs],['吿','告'])
        self.values('吿','古')
        with patch.object(self.mod.messagebox,'askyesno',return_value=False):self.click('添加 / 更新')
        self.assertEqual(self.rows(),[('吿','告')])
        with patch.object(self.mod.messagebox,'askyesno',return_value=True):self.click('添加 / 更新')
        self.assertEqual(self.rows(),[]);self.query('古');self.assertEqual(self.rows(),[('吿','古')])
        self.values('吿','古');self.click('添加 / 更新');self.assertEqual(len(self.rows()),1)
        self.query('告');self.values('𣙜','榷');self.click('添加 / 更新');self.assertEqual(self.rows(),[])
        self.query('榷');self.assertEqual(self.rows(),[('𣙜','榷')]);self.click('清空搜索');self.assertEqual(len(self.rows()),4)
        self.query('説');self.select_first()
        with patch.object(self.mod.messagebox,'askyesno',return_value=False):self.click('移除选中行')
        self.assertEqual(self.rows(),[('說','説')])
        with patch.object(self.mod.messagebox,'askyesno',return_value=True):self.click('移除选中行')
        self.assertEqual(self.rows(),[])
        with patch.object(self.mod.messagebox,'askyesno') as confirm:self.click('移除选中行');confirm.assert_not_called()
        self.query('古')
        with patch.object(self.mod.filedialog,'asksaveasfilename',return_value=''):self.click('另存副本并使用')
        self.assertTrue(self.win.winfo_exists())
        with patch.object(self.mod.filedialog,'asksaveasfilename',return_value=str(self.original)),patch.object(self.mod.messagebox,'showerror') as error:self.click('另存副本并使用');error.assert_called_once()
        self.assertEqual(self.original.read_bytes(),self.before)
        dest=self.base/'saved.csv';self.app.ready=('old preview',)
        with patch.object(self.mod.filedialog,'asksaveasfilename',return_value=str(dest)):self.click('另存副本并使用')
        self.assertEqual(load_mapping(dest),{'吿':'古','淨':'浄','𣙜':'榷'});self.assertEqual(self.app.map_path.get(),str(dest));self.assertIsNone(self.app.ready)
        self.open_editor();self.assertEqual(len(self.rows()),3);self.assertEqual(self.search.get(),'')
    def test_close_discards_edits_and_search(self):
        self.query('告');self.values('吿','古')
        with patch.object(self.mod.messagebox,'askyesno',return_value=True):self.click('添加 / 更新')
        self.win.destroy();self.assertEqual(self.original.read_bytes(),self.before);self.open_editor();self.assertEqual(len(self.rows()),3);self.assertIn(('吿','告'),self.rows());self.assertEqual(self.search.get(),'')

if __name__=='__main__':unittest.main(verbosity=2)