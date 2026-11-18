"""Standalone Open Image Denoise CPU pass; Blender's distro build lacks OIDN.
Input/output are the same pixel dimensions. This does not upscale images.
"""
from pathlib import Path
import argparse,json,subprocess,time
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent
PROJECT_ROOT=next(p for p in R.parents if (p/'AGENTS.md').exists() and (p/'stories').is_dir())
BIN=PROJECT_ROOT.parent/'quality-reset-2026-11-16/scene/oidn-2.5.1.x86_64.linux/bin/oidnDenoise'
def write_pfm(p,a):
 h,w,c=a.shape
 with p.open('wb') as f:f.write(f'PF\n{w} {h}\n-1.0\n'.encode());np.flipud(a).astype('<f4').tofile(f)
def read_pfm(p):
 with p.open('rb') as f:
  assert f.readline().strip()==b'PF';w,h=map(int,f.readline().split());scale=float(f.readline());a=np.fromfile(f,dtype='<f4' if scale<0 else '>f4').reshape(h,w,3)
 return np.flipud(a)
def denoise(src,dst):
 src=Path(src);dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);work=dst.parent/(dst.stem+'-oidn');work.mkdir(exist_ok=True);a=np.asarray(Image.open(src).convert('RGB'),dtype=np.float32)/255;inp=work/'input.pfm';out=work/'output.pfm';write_pfm(inp,a);t=time.time()
 p=subprocess.run([str(BIN),'--device','cpu','--ldr',str(inp),'--srgb','--threads','2','--affinity','0','--maxmem','512','--quality','high','--output',str(out)],capture_output=True,text=True,check=True)
 a=read_pfm(out);Image.fromarray(np.rint(np.clip(a,0,1)*255).astype('uint8')).save(dst)
 elapsed=time.time()-t
 inp.unlink();out.unlink();work.rmdir()
 return {'input':str(src),'output':str(dst),'seconds':round(elapsed,3),'engine':'Open Image Denoise 2.5.1 CPU RT, LDR/sRGB, high quality; beauty only','native_dimensions':list(Image.open(dst).size),'log':p.stdout[-1200:]}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('inputs',nargs='+');ap.add_argument('--out',required=True);a=ap.parse_args();rows=[]
 for src in a.inputs:
  row=denoise(src,Path(a.out)/Path(src).name);rows.append(row);print(json.dumps(row),flush=True)
 (Path(a.out)/'denoise-receipts.json').write_text(json.dumps(rows,indent=2)+'\n')
