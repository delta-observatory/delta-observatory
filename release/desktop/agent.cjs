'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { createInterface } = require('node:readline');

class AgentHost {
  constructor({payload, workspace, apiUrl, onEvent}) { Object.assign(this,{payload,workspace,apiUrl,onEvent}); this.pending=new Map(); this.sequence=0; }
  async start() {
    if(this.starting)return this.starting;
    if(this.process)return;
    this.starting=this.launch();
    try{await this.starting;}finally{this.starting=null;}
  }
  async launch() {
    const env={PATH:'/usr/bin:/bin',LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1',PYTHONNOUSERSITE:'1',
      PYTHONHOME:path.join(this.payload,'python'),PYTHONPATH:path.join(this.payload,'components/agents')};
    if (process.env.DBUS_SESSION_BUS_ADDRESS) env.DBUS_SESSION_BUS_ADDRESS=process.env.DBUS_SESSION_BUS_ADDRESS;
    this.process=spawn(path.join(this.payload,'python/bin/python3.12'),['-s','-m','managed.host',
      '--api-url',this.apiUrl+'/api','--runtime-dir',path.join(this.payload,'codex'),
      '--claude-runtime-dir',path.join(this.payload,'claude'),'--state-dir',path.join(this.workspace,'agent-profiles'),'--bwrap',path.join(this.payload,'host-bin/bwrap'),
      '--library-dir',path.join(this.payload,'host-lib')],{env,stdio:['pipe','pipe','pipe']});
    createInterface({input:this.process.stdout}).on('line',line=>{
      let message;try{message=JSON.parse(line);}catch{return;}
      if(message.event){this.onEvent(message);return;}
      const pending=this.pending.get(message.id);if(!pending)return;
      this.pending.delete(message.id);clearTimeout(pending.timer);
      if(message.error)pending.reject(new Error(message.error));else pending.resolve(message.result);
    });
    // Provider diagnostics can contain authentication details. They never enter renderer output or logs.
    this.process.stderr.on('data',()=>{});
    const fail=()=>{for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(new Error('The agent host stopped. Reconnect to continue.'));}this.pending.clear();this.process=null;this.onEvent({event:'connection',state:'disconnected'});};
    this.process.once('exit',fail);this.process.once('error',fail);
    await this.call('configure',{token:(await fs.readFile(path.join(this.workspace,'owner.token'),'utf8')).trim()});
  }
  call(action,params={}) {
    return new Promise((resolve,reject)=>{
      if(!this.process){reject(new Error('The agent host is unavailable.'));return;}
      const id=++this.sequence;const timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('The agent operation timed out. Reconnect before trying again.'));},90000);
      this.pending.set(id,{resolve,reject,timer});this.process.stdin.write(JSON.stringify({id,action,params})+'\n');
    });
  }
  async close(){
    if(this.starting){try{await this.starting;}catch{}}
    const child=this.process;if(!child)return;
    try{await this.call('shutdown');}catch{}
    if(child.exitCode!==null)return;
    await new Promise(resolve=>{
      const timer=setTimeout(()=>child.kill(),5000);
      child.once('exit',()=>{clearTimeout(timer);resolve();});
      child.stdin.end();
    });
  }
}
function providerLoginAddress(login) {
  const address=login?.authUrl||login?.verificationUrl;
  if(typeof address!=='string')throw new Error('Start login before opening the authorization page.');
  const url=new URL(address);
  if(url.protocol!=='https:'||url.username||url.password||url.port||!['auth.openai.com','chatgpt.com','claude.ai','claude.com','platform.claude.com','console.anthropic.com'].includes(url.hostname))throw new Error('The provider returned an unsupported login address.');
  return url.href;
}
module.exports={AgentHost,providerLoginAddress};
