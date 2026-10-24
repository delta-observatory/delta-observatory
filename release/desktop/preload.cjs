'use strict';
const { contextBridge, ipcRenderer }=require('electron');
contextBridge.exposeInMainWorld('deltaDesktop',{
  agent:(action,params)=>ipcRenderer.invoke('delta:agent',action,params),
  onAgentEvent:callback=>{const listener=(_event,value)=>callback(value);ipcRenderer.on('delta:agent-event',listener);return()=>ipcRenderer.removeListener('delta:agent-event',listener);},
  settings:(action,params)=>ipcRenderer.invoke('delta:settings',action,params),
});
