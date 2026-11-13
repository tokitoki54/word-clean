import unittest,tempfile,zipfile,hashlib,importlib.util
from pathlib import Path
from word_clean_core import load_mapping,process_docx,transform_xml,W

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.xml=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>吿所&amp;說</w:t><w:drawing/></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>吿</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>').encode()
        self.mapping={'吿':'告','所':'所','說':'説','説':'说'}
    def tearDown(self):self.tmp.cleanup()
    def document(self):
        p=self.root/'sample.docx'
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('word/document.xml',self.xml)
            z.writestr('word/header1.xml',self.xml)
            z.writestr('word/footer1.xml',self.xml)
            z.writestr('word/footnotes.xml',self.xml)
            z.writestr('word/endnotes.xml',self.xml)
            z.writestr('word/comments.xml',self.xml)
            z.writestr('word/media/image1.png',b'opaque-image-data')
            z.writestr('[Content_Types].xml',b'<Types/>')
        return p
    def test_preview_and_preservation(self):
        p=self.document(); original=p.read_bytes(); counts=process_docx(p,self.mapping)
        self.assertEqual(counts,{'吿':10,'說':5});self.assertEqual(p.read_bytes(),original)
        dest=self.root/'new.docx';self.assertEqual(process_docx(p,self.mapping,dest),counts)
        self.assertEqual(p.read_bytes(),original)
        with zipfile.ZipFile(p) as a,zipfile.ZipFile(dest) as b:
            self.assertEqual(a.namelist(),b.namelist())
            for n in ['word/media/image1.png','word/comments.xml','[Content_Types].xml']:self.assertEqual(a.read(n),b.read(n))
            result=b.read('word/document.xml');self.assertIn('告所&amp;説'.encode(),result); self.assertIn(b'<w:drawing/>',result);self.assertIn(b'<w:b/>',result)
    def test_no_overwrite(self):
        p=self.document();data=p.read_bytes()
        with self.assertRaises(ValueError):process_docx(p,self.mapping,p)
        out=self.root/'exists.docx';out.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):process_docx(p,self.mapping,out)
        self.assertEqual(out.read_bytes(),b'keep');self.assertEqual(p.read_bytes(),data)
    def test_empty_map_preserves_exact_xml(self):
        result,stats=transform_xml(self.xml,{});self.assertEqual(result,self.xml);self.assertFalse(stats)
    def test_invalid_doc(self):
        p=self.root/'bad.docx';p.write_bytes(b'broken')
        with self.assertRaises(zipfile.BadZipFile):process_docx(p,self.mapping)
    def test_alternate_namespace_and_textbox(self):
        x=f'<x:document xmlns:x="{W}"><x:txbxContent><x:p><x:r><x:t xml:space="preserve"> 吿 </x:t></x:r></x:p></x:txbxContent></x:document>'.encode()
        result,c=transform_xml(x,self.mapping);self.assertEqual(c,{'吿':1});self.assertIn(' 告 '.encode(),result);self.assertIn(b'xml:space="preserve"',result)
    def test_special_chars_escape(self):
        result,c=transform_xml(self.xml,{'吿':'<'});self.assertIn(b'&lt;',result);self.assertEqual(c,{'吿':2})
    def test_original_mapping(self):
        if not (Path(__file__).parent/'新旧字形.xlsx').exists():self.skipTest('私有字表未随源码分发')
        m=load_mapping(Path(__file__).parent/'新旧字形.xlsx');self.assertEqual(len(m),81);self.assertEqual(m['所'],'所');self.assertEqual(m['吿'],'告')
    def test_dtd_rejected(self):
        with self.assertRaises(ValueError):transform_xml(b'<!DOCTYPE a><a/>',{})
    def test_gui_construct(self):
        import tkinter as tk
        import importlib.machinery
        loader=importlib.machinery.SourceFileLoader('word_clean_gui',str(Path(__file__).parent/'word_clean_gui.pyw'))
        spec=importlib.util.spec_from_loader(loader.name,loader);mod=importlib.util.module_from_spec(spec);loader.exec_module(mod)
        root=tk.Tk();root.withdraw()
        app=mod.App(root);root.update();self.assertFalse(app.ready);self.assertIn('disabled',app.convert.state());root.destroy()

    def test_gui_preview_convert_repeat(self):
        import tkinter as tk, importlib.machinery,time
        from unittest.mock import patch
        loader=importlib.machinery.SourceFileLoader('gui_flow',str(Path(__file__).parent/'word_clean_gui.pyw'))
        spec=importlib.util.spec_from_loader(loader.name,loader);mod=importlib.util.module_from_spec(spec);loader.exec_module(mod)
        mod.BASE=self.root
        root=tk.Tk();root.withdraw(); app=mod.App(root); sample=self.document();app.add([sample,sample]);self.assertEqual(len(app.files),1)
        fixture=self.root/'fixture.csv';fixture.write_text('旧字型,新字形\n吿,告\n所,所\n',encoding='utf-8-sig');app.map_path.set(str(fixture))
        app.out_path.set(str(self.root/'results'))
        def wait():
            until=time.monotonic()+10
            while app.busy and time.monotonic()<until:root.update();time.sleep(.02)
            self.assertFalse(app.busy)
        app.run(False);wait();self.assertTrue(app.ready);self.assertFalse((self.root/'results').exists())
        with patch.object(mod.messagebox,'askyesno',return_value=False):app.run(True)
        self.assertFalse((self.root/'results').exists())
        with patch.object(mod.messagebox,'askyesno',return_value=True):app.run(True);wait()
        self.assertEqual(len(mod.read_history(self.root/'history.jsonl')[0]),1)
        self.assertEqual({p.name for p in app.last_output.iterdir()},{'001_'+sample.stem+'_字形已转换.docx','字形统计.csv'})
        import csv
        with (app.last_output/'字形统计.csv').open(encoding='utf-8-sig',newline='') as f:detail_rows=list(csv.DictReader(f))
        self.assertEqual(sum(int(r['次数']) for r in detail_rows),10);self.assertEqual(set(detail_rows[0]),{'旧字型','新字形','次数'})
        self.assertEqual(app.files,[]);self.assertIsNone(app.ready)
        first=app.last_output;self.assertTrue((first/'字形统计.csv').exists());self.assertEqual(len(list(first.glob('*.docx'))),1)
        app.add([sample]);app.run(False);wait()
        with patch.object(mod.messagebox,'askyesno',return_value=True):app.run(True);wait()
        self.assertNotEqual(app.last_output,first);self.assertTrue(first.exists())
        self.assertEqual(len(mod.read_history(self.root/'history.jsonl')[0]),2)
        app.add([sample]);app.run(False);wait()
        with patch.object(mod,'append_history',side_effect=OSError('read only')),patch.object(mod.messagebox,'askyesno',return_value=True):app.run(True);wait()
        self.assertIn('处理记录写入失败',app.status.get());self.assertTrue(app.last_output.exists())
        self.assertEqual(len(mod.read_history(self.root/'history.jsonl')[0]),2)
        app.clear();self.assertFalse(app.ready);self.assertEqual(len(app.files),0);root.destroy()
    def test_txt_encodings_and_newlines(self):
        from word_clean_core import process_txt
        for encoding in ['utf-8','utf-8-sig','utf-16','utf-16-be','gb18030']:
            p=self.root/(encoding+'.txt'); original='吿\r\n所\n'.encode(encoding)
            if encoding=='utf-16-be':original=b'\xfe\xff'+original
            p.write_bytes(original);out=self.root/(encoding+'-out.txt')
            counts=process_txt(p,{'吿':'告','所':'所'},out,'gb18030' if encoding=='gb18030' else 'auto')
            expected='告\r\n所\n'.encode(encoding)
            if encoding=='utf-16-be':expected=b'\xfe\xff'+expected
            self.assertEqual(counts,{'吿':1});self.assertEqual(out.read_bytes(),expected);self.assertEqual(p.read_bytes(),original)
    def test_txt_unknown_encoding_requires_choice(self):
        from word_clean_core import process_txt
        p=self.root/'legacy.txt';p.write_bytes('吿'.encode('gb18030'))
        with self.assertRaises(ValueError):process_txt(p,self.mapping)
    def test_csv_editable_table_conflict(self):
        p=self.root/'table.csv';p.write_text('旧字型,新字形\n吿,告\n所,所\n',encoding='utf-8-sig')
        self.assertEqual(load_mapping(p),{'吿':'告','所':'所'})
        p.write_text('旧字型,新字形\n吿,告\n吿,古\n',encoding='utf-8-sig')
        with self.assertRaises(ValueError):load_mapping(p)
    def test_xml_numeric_entity_not_html(self):
        x=f'<w:document xmlns:w="{W}"><w:t>吿&#128;&amp;&quot;</w:t></w:document>'.encode()
        result,c=transform_xml(x,self.mapping)
        self.assertIn(('告'+chr(128)+'&amp;"').encode(),result);self.assertNotIn('€'.encode(),result)
    def test_strict_ooxml(self):
        strict=self.xml.replace(W.encode(),b'http://purl.oclc.org/ooxml/wordprocessingml/main')
        result,c=transform_xml(strict,self.mapping);self.assertEqual(c,{'吿':2,'說':1});self.assertIn('告所'.encode(),result)

    def test_synthetic_xlsx(self):
        p=self.root/'map.xlsx'
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="map" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            rows=''
            for i,pair in enumerate([('旧字型','新字形'),('吿','告'),('所','所')],1):
                rows+=f'<row r="{i}">'+''.join(f'<c r="{col}{i}" t="inlineStr"><is><t>{value}</t></is></c>' for col,value in zip('AB',pair))+'</row>'
            z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+rows+'</sheetData></worksheet>')
        self.assertEqual(load_mapping(p),{'吿':'告','所':'所'})
    def test_editor_controls(self):
        import tkinter as tk, importlib.machinery
        from tkinter import ttk
        from unittest.mock import patch
        loader=importlib.machinery.SourceFileLoader('gui_editor',str(Path(__file__).parent/'word_clean_gui.pyw'))
        spec=importlib.util.spec_from_loader(loader.name,loader);mod=importlib.util.module_from_spec(spec);loader.exec_module(mod)
        root=tk.Tk();root.withdraw();app=mod.App(root)
        original=self.root/'editor.csv';original.write_text('旧字型,新字形\n吿,告\n',encoding='utf-8-sig');before=original.read_bytes();app.map_path.set(str(original))
        app.edit_mapping();root.update();win=next(c for c in root.winfo_children() if isinstance(c,tk.Toplevel))
        def descendants(w):
            result=[]
            for child in w.winfo_children():result.append(child);result.extend(descendants(child))
            return result
        widgets=descendants(win);table=next(w for w in widgets if isinstance(w,ttk.Treeview));entries=[w for w in widgets if isinstance(w,ttk.Entry) and w.winfo_name() in ('old_input','new_input')]
        def click(label):next(w for w in widgets if isinstance(w,ttk.Button) and w.cget('text')==label).invoke();root.update()
        table.selection_set(table.get_children()[0]);table.event_generate('<<TreeviewSelect>>');root.update();self.assertEqual(entries[0].get(),'吿')
        for entry,value in zip(entries,['吾','吴']):entry.delete(0,'end');entry.insert(0,value)
        click('添加 / 更新');self.assertEqual(len(table.get_children()),2)
        entries[0].delete(0,'end');entries[0].insert(0,'吾')
        entries[1].delete(0,'end');entries[1].insert(0,'古')
        with patch.object(mod.messagebox,'askyesno',return_value=False):click('添加 / 更新')
        self.assertIn(('吾','吴'),[table.item(row,'values') for row in table.get_children()])
        with patch.object(mod.filedialog,'asksaveasfilename',return_value=''):click('另存副本并使用')
        self.assertTrue(win.winfo_exists())
        dest=self.root/'edited.csv'
        with patch.object(mod.filedialog,'asksaveasfilename',return_value=str(dest)):click('另存副本并使用')
        self.assertEqual(load_mapping(dest),{'吿':'告','吾':'吴'});self.assertEqual(original.read_bytes(),before);self.assertEqual(app.map_path.get(),str(dest));self.assertFalse(app.ready)
        app.edit_mapping();root.update();win=next(c for c in root.winfo_children() if isinstance(c,tk.Toplevel));win.destroy();self.assertEqual(app.map_path.get(),str(dest));root.destroy()


    def test_numeric_cr_preserved(self):
        import xml.etree.ElementTree as ET
        x=f'<w:document xmlns:w="{W}"><w:t>吿&#13;尾</w:t></w:document>'.encode()
        result,c=transform_xml(x,self.mapping)
        self.assertIn(b'&#13;',result)
        self.assertEqual(ET.fromstring(result).find('{'+W+'}t').text,'告\r尾')
        self.assertEqual(c,{'吿':1})
    def test_namespace_rebinding_rejected(self):
        x=f'<w:document xmlns:w="{W}"><w:t>吿</w:t><part xmlns:w="urn:other"><w:t>吿</w:t></part></w:document>'.encode()
        with self.assertRaisesRegex(ValueError,'重新绑定'):transform_xml(x,self.mapping)
    def test_namespace_attribute_whitespace(self):
        x=f'<w:document xmlns:w = "{W}"><w:t>吿</w:t></w:document>'.encode()
        result,c=transform_xml(x,self.mapping)
        self.assertIn('告'.encode(),result);self.assertEqual(c,{'吿':1});self.assertIn(b'xmlns:w = ',result)
    def test_nested_default_word_namespace_rejected(self):
        x=f'<w:document xmlns:w="{W}"><w:t>吿</w:t><t xmlns="{W}">吿</t></w:document>'.encode()
        with self.assertRaisesRegex(ValueError,'默认 Word XML'):transform_xml(x,self.mapping)


    def test_default61_all_pairs_and_exclusions(self):
        import xml.etree.ElementTree as ET
        p=Path(__file__).parent/'默认字表_部件新旧字形_v1.csv'
        if not p.exists():self.skipTest('私有审定字表未随源码分发')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'7057227e048b4013e57c02bf9359f74d06b5126a07fd3517e1016d01b2a97d77')
        mapping=load_mapping(p);self.assertEqual(len(mapping),61)
        for old,new in mapping.items():
            with self.subTest(old=old,new=new):
                xml=f'<w:document xmlns:w="{W}"><w:t>{old}</w:t></w:document>'.encode()
                result,counts=transform_xml(xml,mapping)
                self.assertEqual(ET.fromstring(result).find('{'+W+'}t').text,new)
                self.assertEqual(counts,{old:1})
        for old in ['寃','凈','茍','晋','吿']:
            self.assertNotIn(old,mapping)
            xml=f'<w:document xmlns:w="{W}"><w:t>{old}</w:t></w:document>'.encode()
            result,counts=transform_xml(xml,mapping);self.assertEqual(result,xml);self.assertFalse(counts)
        for old,new,forbidden in [('錄','録','录'),('說','説','说'),('淨','浄','净'),('綠','緑','绿')]:
            self.assertEqual(mapping[old],new);self.assertNotEqual(mapping[old],forbidden)
    def test_default61_badge_changed_missing_and_custom(self):
        import tkinter as tk, importlib.machinery
        from unittest.mock import patch
        loader=importlib.machinery.SourceFileLoader('gui_default61',str(Path(__file__).parent/'word_clean_gui.pyw'))
        spec=importlib.util.spec_from_loader(loader.name,loader);mod=importlib.util.module_from_spec(spec);loader.exec_module(mod)
        original=mod.DEFAULT_PATH
        if not original.exists():self.skipTest('私有审定字表未随源码分发')
        default=self.root/'default.csv';default.write_bytes(original.read_bytes())
        with patch.object(mod,'DEFAULT_PATH',default):
            root=tk.Tk();root.withdraw();app=mod.App(root)
            self.assertIn('新旧字形160条（项目逐项审阅）',app.map_info.get());self.assertEqual(app.map_path.get(),str(default))
            # Tamper after launch: pre-action refresh must remove the verified badge.
            default.write_bytes(default.read_bytes()+b'\n')
            with patch.object(mod.messagebox,'showinfo'):app.run(False)
            self.assertNotIn('项目逐项审阅',app.map_info.get());self.assertIn('待核对',app.map_info.get())
            default.write_bytes(original.read_bytes());app.update_map_info();self.assertIn('项目逐项审阅',app.map_info.get())
            custom=self.root/'custom.csv';custom.write_bytes(original.read_bytes());app.map_path.set(str(custom));app.update_map_info()
            self.assertNotIn('项目逐项审阅',app.map_info.get())
            root.destroy();default.unlink()
            root=tk.Tk();root.withdraw();app=mod.App(root)
            self.assertEqual(app.map_path.get(),str(default));self.assertIn('默认字表缺失',app.map_info.get());self.assertNotIn('项目逐项审阅',app.map_info.get());root.destroy()

    def test_expanded_default115_integrity_and_scope(self):
        import xml.etree.ElementTree as ET
        p=Path(__file__).parent/'默认字表_新旧字形_v2.csv'
        if not p.exists():self.skipTest('私有审定字表未随源码分发')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'5d277d607e2446d1cfac35503c87ff96dc9a66451127fd7ef441142dc0206a77')
        mapping=load_mapping(p);self.assertEqual(len(mapping),115)
        for old,new in mapping.items():
            self.assertNotEqual(old,new);self.assertNotIn(new,mapping)
            xml=f'<w:document xmlns:w="{W}"><w:t>{old}</w:t></w:document>'.encode()
            result,counts=transform_xml(xml,mapping)
            self.assertEqual(ET.fromstring(result).find('{'+W+'}t').text,new)
            self.assertEqual(transform_xml(result,mapping)[0],result)
        for old in ['寃','凈','茍','晋','晉','荊','吿','所','紛','禮','過']:
            self.assertNotIn(old,mapping)
        for old,new in [('縕','緼'),('轀','輼'),('鰮','鰛'),('餠','餅'),('騈','駢'),('𥁕','昷')]:
            self.assertEqual(mapping[old],new)

    def test_expanded_default120_integrity(self):
        import xml.etree.ElementTree as ET
        p=Path(__file__).parent/'默认字表_新旧字形_v3.csv'
        if not p.exists():self.skipTest('私有审定字表未随源码分发')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'574b1770bb9043dbb300eebde6df78027420cf3aec4f5c35625e9be295ad9d4c')
        mapping=load_mapping(p);self.assertEqual(len(mapping),120)
        for old,new in mapping.items():
            self.assertNotEqual(old,new);self.assertNotIn(new,mapping)
            xml=f'<w:document xmlns:w="{W}"><w:t>{old}</w:t></w:document>'.encode()
            result,counts=transform_xml(xml,mapping)
            self.assertEqual(ET.fromstring(result).find('{'+W+'}t').text,new)
            self.assertEqual(transform_xml(result,mapping)[0],result)
        for old,new in [('兗','兖'),('滾','滚'),('尙','尚'),('呑','吞'),('剎','刹')]:self.assertEqual(mapping[old],new)
        for old in ['寃','凈','茍','晋','晉','荊','嚔','所','煮','拼','礼']:self.assertNotIn(old,mapping)

    def test_user_review_default122(self):
        import xml.etree.ElementTree as ET
        p=Path(__file__).parent/'默认字表_新旧字形_v5.csv'
        if not p.exists():self.skipTest('私有审定字表未随源码分发')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'ee72aef282d1d82a7844d2f6b8dc47b0cded2d09f03f0883f510879737f505af')
        mapping=load_mapping(p);self.assertEqual(len(mapping),122)
        self.assertEqual(mapping['𣙜'],'榷')
        self.assertEqual(mapping['凈'],'净')
        self.assertEqual(mapping['淨'],'浄')
        for keep in '晋晉戩戬為爲偽僞媯嬀溈潙蒍蔿嚔嚏骨髓滑':self.assertNotIn(keep,mapping)
        original='𣙜凈净浄淨晋晉戩戬為爲偽僞媯嬀溈潙蒍蔿嚔嚏骨髓滑'
        expected='榷净净浄浄晋晉戩戬為爲偽僞媯嬀溈潙蒍蔿嚔嚏骨髓滑'
        xml=f'<w:document xmlns:w="{W}"><w:t>{original}</w:t></w:document>'.encode()
        result,counts=transform_xml(xml,mapping)
        self.assertEqual(ET.fromstring(result).find('{'+W+'}t').text,expected)
        self.assertEqual(counts,{'𣙜':1,'凈':1,'淨':1})
        self.assertEqual(transform_xml(result,mapping)[0],result)

if __name__=='__main__':unittest.main(verbosity=2)



