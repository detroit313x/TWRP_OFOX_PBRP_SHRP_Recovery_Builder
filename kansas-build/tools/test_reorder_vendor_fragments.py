#!/usr/bin/env python3
"""Regression tests for unsigned vendor_boot v4 fragment-order postprocessing."""
import hashlib,struct,unittest
from reorder_vendor_fragments import reorder
PAGE=4096
align=lambda n:(n+PAGE-1)//PAGE*PAGE

def image(rows, suffix=b''):
    data=bytearray(PAGE);data[:8]=b'VNDRBOOT'
    rd=b''.join(blob for kind,name,blob in rows);dtb=b'DTB-test-unchanged';bc=b'androidboot.test=1\n'
    struct.pack_into('<II',data,8,4,PAGE);struct.pack_into('<I',data,24,len(rd))
    struct.pack_into('<IIQ',data,2096,2128,len(dtb),0x47c80000)
    struct.pack_into('<4I',data,2112,len(rows)*108,len(rows),108,len(bc))
    data+=rd+b'\0'*(align(len(rd))-len(rd));data+=dtb+b'\0'*(align(len(dtb))-len(dtb))
    offset=0;table=bytearray()
    for index,(kind,name,blob) in enumerate(rows):
        table+=struct.pack('<III32s16I',len(blob),offset,kind,name.encode(),*([index+11]*16));offset+=len(blob)
    data+=table+b'\0'*(align(len(table))-len(table));data+=bc+b'\0'*(align(len(bc))-len(bc))
    return bytes(data)+suffix

class Tests(unittest.TestCase):
    def test_reorder_preservation_and_idempotence(self):
        source=image([(0,'',b'empty-default'),(2,'recovery',b'compiled-pbrp'),(1,'platform',b'stock-platform'),(3,'dlkm',b'stock-dlkm')])
        result,report=reorder(source)
        self.assertEqual([r['type'] for r in report],[0,1,3,2])
        self.assertEqual(len(result),len(source));self.assertEqual(source[:PAGE],result[:PAGE])
        self.assertEqual(reorder(result)[0],result)
        # DTB, bootconfig and all bytes outside ramdisk/table must be unchanged.
        rdsize=struct.unpack_from('<I',source,24)[0];to=PAGE+align(rdsize)+PAGE
        self.assertEqual(source[PAGE+align(rdsize):to],result[PAGE+align(rdsize):to])
        self.assertEqual(source[to+PAGE:],result[to+PAGE:])
        for r in report:
            self.assertEqual(hashlib.sha256(result[PAGE+r['offset']:PAGE+r['offset']+r['size']]).hexdigest(),r['sha256'])
        old={source[to+k*108+12:to+k*108+108] for k in range(4)}
        new={result[to+k*108+12:to+k*108+108] for k in range(4)}
        self.assertEqual(old,new)
    def test_refuse_signature(self):
        with self.assertRaises(ValueError):reorder(image([(1,'platform',b'stock')],b'AVBf'+b'\0'*60))
    def test_refuse_truncated(self):
        with self.assertRaises(ValueError):reorder(image([(1,'platform',b'stock')])[:-4097])
    def test_refuse_overlap(self):
        x=bytearray(image([(1,'platform',b'stock'),(2,'recovery',b'new')]))
        to=PAGE+PAGE+PAGE;struct.pack_into('<I',x,to+108+4,0)
        with self.assertRaises(ValueError):reorder(x)
    def test_refuse_wrong_version(self):
        x=bytearray(image([(1,'platform',b'stock')]));struct.pack_into('<I',x,8,3)
        with self.assertRaises(ValueError):reorder(x)

if __name__=='__main__':unittest.main(verbosity=2)
