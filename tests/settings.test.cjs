const assert=require('node:assert/strict'), fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),codec=require('../settings.js');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const ids=new Set([...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]));
const nodes={},storage=new Map();let resizeCalls=0;
const box={console,MacroSettings:codec,window:{innerWidth:1440},requestAnimationFrame(){},localStorage:{setItem(k,v){storage.set(k,v)},getItem(k){return storage.get(k)||null}},document:{getElementById(id){assert(ids.has(id),'missing DOM '+id);return nodes[id]??={style:{},clientHeight:600,offsetHeight:30,clientWidth:1000,handlers:{},on(name,fn){this.handlers[name]=fn},removeAllListeners(name){delete this.handlers[name]}}}},Plotly:{async react(id,traces,layout){box.result={traces,layout};nodes[id].data=traces;nodes[id].layout=layout;},relayout(){resizeCalls++}}};
vm.createContext(box);vm.runInContext(html.split('<script>')[1].split('</script>')[0].replace(/boot\(\)\.catch\([\s\S]*$/,''),box);
const run=s=>vm.runInContext(s,box);
(async()=>{
 run(`DATA=${fs.readFileSync(path.join(root,'data.json'),'utf8')};Object.assign(S,freshState());`);await run('render()');
 const defaults=JSON.parse(run('JSON.stringify(S)'));
 assert.equal(box.result.traces.length,4);assert(defaults.showReg&&defaults.regLog);assert.deepEqual(Object.keys(defaults.show).filter(k=>defaults.show[k]),['nasdaq']);
 const custom=structuredClone(defaults);Object.assign(custom,{period:null,dateMode:'fixed',start:'2020-01-01',end:'2024-12-31',ctype:'Bar+Lines (봉차트)',stdMult:2.5});custom.style.nasdaq={color:'#ff6633',width:3.2,dash:'dash'};custom.show.fin_sp500_pe=true;custom.view={x:['2021-01-01','2023-12-31'],y:[3.7,4.4]};
 const encoded=codec.encode(custom);assert.deepEqual(codec.decode(JSON.parse(JSON.stringify(encoded)),defaults),custom);
 for(const change of [p=>p.schemaVersion=99,p=>p.state.start='2026-02-30',p=>p.state.end='1900-01-01',p=>p.state.style.nasdaq.color='<script>',p=>p.state.axis.nasdaq='y999',p=>p.state.stdMult=Infinity,p=>p.state.view.y=['bad',4]]){const invalid=structuredClone(encoded);change(invalid);assert.throws(()=>codec.decode(invalid,defaults));}
 const unknown=JSON.parse(JSON.stringify(encoded).replace('"state":{','"state":{"__proto__":{"polluted":true},'));codec.decode(unknown,defaults);assert.equal({}.polluted,undefined);
 run(`applySettings(${JSON.stringify(custom)});saveSettings();Object.assign(S,freshState());restoreSettings();`);assert.equal(run('S.style.nasdaq.color'),'#ff6633');assert.equal(run('S.start'),'2020-01-01');await run('render()');assert.equal(box.result.traces[0].type,'candlestick');assert(box.result.traces.some(t=>t.name==='S&P 500 PER · 연도별'));
 const plot=nodes['plotly-div'];const oldLayout=JSON.stringify(box.result.layout);plot.handlers.plotly_hover({points:[{data:{name:'나스닥'},x:'2021-01-01',y:12000}]});plot.handlers.plotly_unhover();assert.equal(resizeCalls,0);assert.equal(JSON.stringify(box.result.layout),oldLayout);
 plot.handlers.plotly_relayout({'xaxis.range[0]':'2022-01-01','xaxis.range[1]':'2023-01-01'});assert.equal(JSON.parse(storage.get(codec.KEY)).state.view.x[0],'2022-01-01');
 assert.equal(run("normalize({dates:['a','b','c'],values:[100,110,100]},'증감률 (수익률%)').values[2]"),0);
 assert.deepEqual(JSON.parse(run("JSON.stringify(normalize({dates:['a','b'],values:[0,1]},'지수화 (기준=100)').values)")),[null,null]);
 run("S.ymode='증감률 (수익률%)';S.log.nasdaq=false;S.view={};");await run('render()');assert(box.result.traces.filter(t=>/회귀|채널/.test(t.name)).every(t=>t.y.every(Number.isFinite)));
 const stockState=structuredClone(defaults);stockState.stocks=[{symbol:'AAPL',name:'Apple Inc.'}];stockState.show.stock_AAPL=true;stockState.axis.stock_AAPL='y3';stockState.style.stock_AAPL={color:'#123456',width:2,dash:'dot'};stockState.log.stock_AAPL=true;
 assert.deepEqual(codec.decode(codec.encode(stockState),defaults),stockState);
 for(const st of [[{symbol:'AAPL<script>',name:'bad'}],[{symbol:'AAPL',name:'Apple'},{symbol:'AAPL',name:'duplicate'}]]){const bad=structuredClone(stockState);bad.stocks=st;assert.throws(()=>codec.decode(codec.encode(bad),defaults));}
 run("Object.assign(S,freshState());S.show.m2=true;S.axis.m2='y';S.log.m2=false;S.log.nasdaq=true;");await run('render()');
 const ndTrace=box.result.traces.find(t=>t.name==='나스닥'),m2Trace=box.result.traces.find(t=>t.name==='M2 (십억달러)');assert.notEqual(ndTrace.yaxis,m2Trace.yaxis);assert.equal(box.result.layout.yaxis.type,'log');assert.equal(box.result.layout['yaxis'+m2Trace.yaxis.slice(1)].type,'linear');
 console.log('PASS: defaults, portable roundtrip, invalid files, restore, financial traces, hover stability, zoom persistence, transforms');
})().catch(e=>{console.error(e);process.exit(1)});
