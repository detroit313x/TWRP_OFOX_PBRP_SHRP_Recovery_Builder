#!/usr/bin/env python3
"""Inspect vendor_boot v4 without assuming it is bootable or device-compatible."""
import argparse, struct, pathlib, json, hashlib
p=argparse.ArgumentParser(); p.add_argument('image'); p.add_argument('--reference'); p.add_argument('--output'); a=p.parse_args()
def inspect(path):
 b=pathlib.Path(path).read_bytes()
 if b[:8]!=b'VNDRBOOT': raise ValueError('Not vendor_boot')
 version,page,kernel_addr,ramdisk_addr,ramdisk_size=struct.unpack_from('<5I',b,8)
 if version!=4: raise ValueError('Expected vendor_boot v4')
 tags,=struct.unpack_from('<I',b,2076)
 header_size,dtb_size,dtb_addr=struct.unpack_from('<IIQ',b,2096)
 table_size,count,entry_size,bootconfig_size=struct.unpack_from('<4I',b,2112)
 align=lambda n:(n+page-1)//page*page
 rd_offset=align(header_size); dtb_offset=rd_offset+align(ramdisk_size); table_offset=dtb_offset+align(dtb_size)
 if table_offset+table_size>len(b): raise ValueError('Truncated image')
 fragments=[]
 for i in range(count):
  off=table_offset+i*entry_size
  size,offset,kind=struct.unpack_from('<III',b,off)
  if offset+size>ramdisk_size: raise ValueError('Ramdisk fragment out of bounds')
  name=b[off+12:off+44].split(b'\0')[0].decode(errors='replace')
  fragment=b[rd_offset+offset:rd_offset+offset+size]
  fragments.append({'name':name,'size':size,'offset':offset,'type':kind,'sha256':hashlib.sha256(fragment).hexdigest(),'magic_hex':fragment[:8].hex()})
 return {'image':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'version':version,'page_size':page,'header_size':header_size,'kernel_address':hex(kernel_addr),'ramdisk_address':hex(ramdisk_addr),'tags_address':hex(tags),'dtb_address':hex(dtb_addr),'dtb_size':dtb_size,'dtb_sha256':hashlib.sha256(b[dtb_offset:dtb_offset+dtb_size]).hexdigest(),'ramdisk_size':ramdisk_size,'fragments':fragments,'bootconfig_size':bootconfig_size,'cmdline':b[28:2076].split(b'\0')[0].decode(errors='replace')}
r=inspect(a.image)
if a.reference:
 ref=inspect(a.reference); r['reference']=ref; r['comparison']={'dtb_equal':r['dtb_sha256']==ref['dtb_sha256'],'page_size_equal':r['page_size']==ref['page_size'],'within_reference_size':r['bytes']<=ref['bytes'],'stock_ramdisk_preserved':any(f['sha256']==ref['fragments'][0]['sha256'] for f in r['fragments']),'has_recovery_fragment':any(f['type']==2 and f['size']>0 for f in r['fragments'])}
s=json.dumps(r,indent=2); print(s)
if a.output:pathlib.Path(a.output).write_text(s+'\n')
