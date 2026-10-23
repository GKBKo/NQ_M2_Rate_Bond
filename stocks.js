/* US stock API and local price cache; settings store only stock identifiers. */
(function(root){
let dbPromise;
function db(){return dbPromise||(dbPromise=new Promise((resolve,reject)=>{const req=indexedDB.open('macro-lens-prices',1);req.onupgradeneeded=()=>req.result.createObjectStore('stocks',{keyPath:'symbol'});req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);}));}
async function cached(symbol){try{const d=await db();return await new Promise(r=>{const q=d.transaction('stocks').objectStore('stocks').get(symbol);q.onsuccess=()=>r(q.result);q.onerror=()=>r(null);});}catch{return null;}}
async function put(value){try{const d=await db();await new Promise((r,j)=>{const tx=d.transaction('stocks','readwrite');tx.objectStore('stocks').put(value);tx.oncomplete=r;tx.onerror=j;});}catch{}}
async function api(path){const response=await fetch(path,{signal:AbortSignal.timeout(30000)});const type=response.headers.get('content-type')||'';if(!type.includes('application/json'))throw new Error('주식 검색은 압축을 푼 뒤 start.bat로 실행해 주세요. GitHub Pages에서는 주식 API 서버가 필요합니다.');const data=await response.json();if(!response.ok)throw new Error(data.error||'주식 데이터 요청 실패');return data;}
root.StockData={search:async q=>(await api('/api/search?q='+encodeURIComponent(q))).quotes, async load(symbol,refresh=false){const old=await cached(symbol);if(!refresh&&old&&Date.now()-Date.parse(old.fetchedAt)<86400000)return old;try{const data=await api('/api/history?symbol='+encodeURIComponent(symbol));await put(data);return data;}catch(error){if(old)return {...old,stale:true};throw error;}}};
})(window);
