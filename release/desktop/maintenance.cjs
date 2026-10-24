'use strict';
const {spawn}=require('node:child_process');
const path=require('node:path');
function utility(payload,workspace,script,args=[]) {
  if(!['reproduction.py','recovery.py','settings.py'].includes(script))throw new Error('Unknown desktop utility.');
  const env={PATH:'/usr/bin:/bin',LANG:'C.UTF-8',PYTHONNOUSERSITE:'1',PYTHONDONTWRITEBYTECODE:'1',PYTHONHOME:path.join(payload,'python'),
    PYTHONPATH:[path.join(payload,'api-packages'),path.join(payload,'components/backend/src')].join(path.delimiter),LD_LIBRARY_PATH:path.join(payload,'postgres/lib')};
  return new Promise((resolve,reject)=>{
    const child=spawn(path.join(payload,'python/bin/python3.12'),['-s',path.join(__dirname,script),'--payload',payload,'--workspace',workspace,...args],{env,stdio:['ignore','pipe','pipe']});
    let output='',error='';
    const timer=setTimeout(()=>{child.kill('SIGTERM');reject(new Error('The desktop operation exceeded ten minutes. Inspect the workspace logs.'));},600000);
    child.stdout.on('data',chunk=>{output+=chunk;if(output.length>8*1024**2)child.kill('SIGTERM');});
    child.stderr.on('data',chunk=>{error=(error+chunk).slice(-2000);});
    child.once('error',e=>{clearTimeout(timer);reject(e);});
    child.once('exit',code=>{clearTimeout(timer);let result;try{result=JSON.parse(output.trim().split('\n').at(-1));}catch{}
      if(code||result?.error)reject(new Error(result?.error||'The desktop operation failed. '+error));else resolve(result);});
  });
}
module.exports={utility};
