/* Versioned, portable settings. Strict whitelist; data and filesystem paths are never stored. */
(function(root){
'use strict';
const KIND='macro-lens-settings', VERSION=1, KEY='macro-lens.settings.v1';
const clone=v=>JSON.parse(JSON.stringify(v));
function validDate(s){return typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;}
function decode(payload,defaults){
 if(!payload||payload.kind!==KIND||payload.schemaVersion!==VERSION||!payload.state||typeof payload.state!=='object'||Array.isArray(payload.state))throw new Error('지원하는 Macro Lens 설정 파일이 아닙니다.');
 const a=payload.state,o=clone(defaults),fail=()=>{throw new Error('설정 값의 형식이나 범위가 올바르지 않습니다.');};
 o.stocks=[];o.log=o.log||{nasdaq:true};
 if('stocks' in a){
  if(!Array.isArray(a.stocks)||a.stocks.length>20)fail();
  const seen=new Set();
  for(const stock of a.stocks){
   if(!stock||typeof stock.symbol!=='string'||! /^[A-Z][A-Z0-9.-]{0,14}$/.test(stock.symbol)||typeof stock.name!=='string'||stock.name.length>150||seen.has(stock.symbol))fail();
   seen.add(stock.symbol);o.stocks.push({symbol:stock.symbol,name:stock.name});
   const id='stock_'+stock.symbol;o.show[id]=true;o.axis[id]='y3';o.style[id]={color:'#4f77ba',width:1.8,dash:'solid'};o.log[id]=false;
  }
 }
 const choices={period:['YTD','1Y','3Y','5Y','10Y','20Y','30Y','MAX',null],dateMode:['rolling','fixed'],ymode:['다중 Y축','동일 Y축','지수화 (기준=100)','증감률 (수익률%)'],ctype:['Line','Bar+Lines (봉차트)']};
 for(const [key,values] of Object.entries(choices)){if(key in a){if(!values.includes(a[key]))fail();o[key]=a[key];}}
 for(const key of ['start','end']){if(key in a){if(!validDate(a[key]))fail();o[key]=a[key];}}
 if(!validDate(o.start)||!validDate(o.end)||o.start>o.end)fail();
 if(o.dateMode==='rolling'&&!o.period)fail();
 for(const key of ['showReg','regLog'])if(key in a){if(typeof a[key]!=='boolean')fail();o[key]=a[key];}
 if('stdMult' in a){if(typeof a.stdMult!=='number'||!Number.isFinite(a.stdMult)||a.stdMult<.5||a.stdMult>4)fail();o.stdMult=a.stdMult;}
 const axes=['y',...Array.from({length:39},(_,i)=>'y'+(i+2))];
 for(const key of ['show','axis','style','log'])if(key in a&&(!a[key]||typeof a[key]!=='object'||Array.isArray(a[key])))fail();
 for(const id of Object.keys(o.show)){
  if(a.log&&Object.hasOwn(a.log,id)){if(typeof a.log[id]!=='boolean')fail();o.log[id]=a.log[id];}
  if(a.show&&Object.hasOwn(a.show,id)){if(typeof a.show[id]!=='boolean')fail();o.show[id]=a.show[id];}
  if(a.axis&&Object.hasOwn(a.axis,id)){if(!axes.includes(a.axis[id]))fail();o.axis[id]=a.axis[id];}
  if(a.style&&Object.hasOwn(a.style,id)){
   const st=a.style[id];if(!st||typeof st!=='object')fail();
   if(!/^#[0-9a-f]{6}$/i.test(st.color)||typeof st.width!=='number'||!Number.isFinite(st.width)||st.width<.5||st.width>6||!['solid','dot','dash','dashdot','longdash','longdashdot'].includes(st.dash))fail();
   o.style[id]={color:st.color,width:st.width,dash:st.dash};
  }
 }
 o.view={};
 if(a.view){
  if(typeof a.view!=='object'||Array.isArray(a.view))fail();
  for(const key of ['x',...axes])if(Object.hasOwn(a.view,key)){
   const r=a.view[key];if(!Array.isArray(r)||r.length!==2)fail();
   if(key==='x'){if(!r.every(v=>typeof v==='string'&&v.length<40&&Number.isFinite(Date.parse(v)))||Date.parse(r[0])>=Date.parse(r[1]))fail();}
   else if(!r.every(v=>typeof v==='number'&&Number.isFinite(v))||r[0]===r[1])fail();
   o.view[key]=r.slice();
  }
 }
 return o;
}
function encode(state){return {kind:KIND,schemaVersion:VERSION,appVersion:'1.3.0',savedAt:new Date().toISOString(),state:clone(state)};}
const api={KEY,encode,decode,validDate};root.MacroSettings=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
