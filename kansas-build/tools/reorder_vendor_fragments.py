#!/usr/bin/env python3
"""Order vendor_boot v4 RECOVERY fragments last to avoid stock archive shadowing.
Does not establish bootability, bootloader selection, or device compatibility.
Only operates on unsigned, structurally valid vendor_boot images; preserves all
fragment bytes, board IDs, DTB, bootconfig, header fields and image length.
"""
import argparse, hashlib, json, pathlib, struct

def reorder(data):
    b=bytearray(data)
    if b[:8] != b'VNDRBOOT': raise ValueError('Not vendor_boot')
    version,page=struct.unpack_from('<II',b,8)
    if version != 4 or page != 4096: raise ValueError('Expected v4, 4096-byte pages')
    rdsize=struct.unpack_from('<I',b,24)[0]
    hsize,dtbsize=struct.unpack_from('<II',b,2096)
    tsize,count,esize,bcsize=struct.unpack_from('<4I',b,2112)
    if esize < 108 or tsize != count*esize: raise ValueError('Unexpected fragment table')
    align=lambda n:(n+page-1)//page*page
    ro=align(hsize); to=ro+align(rdsize)+align(dtbsize)
    end=to+align(tsize)+align(bcsize)
    if end>len(b) or any(b[end:]): raise ValueError('Truncated or signed/trailing nonzero image')
    rows=[]
    for k in range(count):
        row=bytes(b[to+k*esize:to+(k+1)*esize])
        size,offset,kind=struct.unpack_from('<III',row)
        if offset+size>rdsize: raise ValueError('Fragment out of range')
        blob=bytes(b[ro+offset:ro+offset+size])
        rows.append((row,blob,kind,offset))
    ranges=sorted((x[3],x[3]+len(x[1])) for x in rows)
    if ranges and (ranges[0][0]!=0 or ranges[-1][1]!=rdsize or any(x[1]!=y[0] for x,y in zip(ranges,ranges[1:]))):
        raise ValueError('Fragments do not exactly cover ramdisk')
    ordered=sorted(rows,key=lambda x:x[2]==2)
    offset=0; report=[]
    for k,(row,blob,kind,oldoffset) in enumerate(ordered):
        row=bytearray(row); struct.pack_into('<I',row,4,offset)
        b[to+k*esize:to+(k+1)*esize]=row
        b[ro+offset:ro+offset+len(blob)]=blob
        report.append({'name':bytes(row[12:44]).split(b'\0')[0].decode(),'type':kind,'offset':offset,'size':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
        offset+=len(blob)
    assert offset==rdsize and len(b)==len(data)
    return bytes(b),report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('output');a=p.parse_args()
    source=pathlib.Path(a.input).read_bytes(); result,report=reorder(source)
    pathlib.Path(a.output).write_bytes(result)
    print(json.dumps({'input_sha256':hashlib.sha256(source).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'fragments':report},indent=2))
