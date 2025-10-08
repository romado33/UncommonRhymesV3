# rhyme_core/providers/datamuse.py
# Minimal Datamuse client with in-memory cache + polite throttle (no extra deps)
import time, json, urllib.parse, urllib.request, threading
from collections import OrderedDict

BASE = "https://api.datamuse.com"
UA = "UncommonRhymesV3/1.0 (+local)"
_LOCK = threading.Lock()
_LAST = [0.0]
QPS = 10.0  # keep it polite; service allows ~100k/day without key

class _LRU(OrderedDict):
    def __init__(self, cap=2048): super().__init__(); self.cap=cap
    def get(self,k):
        if k in self: self.move_to_end(k); return super().get(k)
    def put(self,k,v):
        self[k]=v; self.move_to_end(k)
        if len(self)>self.cap: self.popitem(last=False)

_cache = _LRU(2048)

def _fetch(path, params):
    key = path + "?" + urllib.parse.urlencode(params, doseq=True)
    v = _cache.get(key)
    if v is not None: return v
    with _LOCK:
        dt = time.time() - _LAST[0]
        wait = max(0.0, 1.0/QPS - dt)
        if wait: time.sleep(wait)
        _LAST[0] = time.time()
    url = f"{BASE}{path}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    _cache.put(key, data)
    return data

def sug(prefix, max_items=8, vocab=None):
    p = {"s": prefix, "max": max_items}
    if vocab: p["v"]=vocab
    return _fetch("/sug", p)

def words(params: dict, max_items=100, vocab=None):
    p = dict(params); p["max"]=max_items
    if vocab: p["v"]=vocab
    return _fetch("/words", p)

def sounds_like(term, **kw): return words({"sl": term}, **kw)
def means_like(term, **kw):  return words({"ml": term}, **kw)
def related(term, code, **kw): return words({f"rel_{code}": term}, **kw)
def adjectives_for(noun, **kw): return related(noun, "jjb", **kw)
def nouns_for(adj, **kw): return related(adj, "jja", **kw)
