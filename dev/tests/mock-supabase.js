/* Mock of the supabase-js surface the app uses. State lives in window.__MOCK. */
(function(){
  var M = window.__MOCK = window.__MOCK || {};
  M.db = M.db || {};
  ["packs", "results", "students", "boards", "sheets", "phaseb"].forEach(function(t){ M.db[t] = M.db[t] || {}; });
  /* phaseb rows are flat ({ pack_id, status, at, by, note }) and keyed by pack_id; the other tables are { id, data } */
  function key(r){ return r.id != null ? r.id : r.pack_id; }
  M.log = []; M.handlers = []; M.session = M.session || null; M.teacher = M.teacher !== false; M.authCbs = [];
  function res(v){ return Promise.resolve(v); }
  function Query(t){ this.t = t; this.ops = []; }
  Query.prototype.select = function(c){ this.kind = this.kind || "select"; return this; };
  Query.prototype.order = function(c, o){ this.ord = c.replace("data->>", ""); return this; };
  Query.prototype.limit = function(n){ this.lim = n; return this; };
  Query.prototype.eq = function(c, v){ this.eqv = v; return this; };
  Query.prototype.in = function(c, v){ this.inv = [].concat(v); return this; };
  Query.prototype.maybeSingle = function(){ this.single = true; return this; };
  Query.prototype.upsert = function(rows, opts){ this.kind = "upsert"; this.rows = [].concat(rows); this.opts = opts; return this; };
  Query.prototype.delete = function(){ this.kind = "delete"; return this; };
  Query.prototype.then = function(a, b){ return this.run().then(a, b); };
  /* Guests (27 Nov): M.guest = true signs in as an email on the guest list. A copy of dev/sql/guests.sql's rules:
     only showcase rows are seen; a write must leave the row showcase; no new or deleted students; no id changes. */
  function slug(s){ return String(s || "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "student"; }
  function scName(n){
    if(n == null) return false; var id = slug(n), st = M.db.students[id], d = st && st.data;
    if(!d || d.showcase !== true || d.test === true) return false;
    return !Object.keys(M.db.packs).some(function(k){ return k.indexOf("~sc-") !== 0 && slug(M.db.packs[k].data && M.db.packs[k].data.student) === id; });
  }
  function scPack(pid){ var p = pid && M.db.packs[pid]; return typeof pid === "string" && pid.indexOf("~sc-") === 0 && !!p && scName(p.data && p.data.student); }
  var GUEST_RLS = {
    students: { read:function(r){ var d = r.data || {}; return d.showcase === true && d.test !== true && scName(d.name) && slug(d.name) === r.id; }, insert:false, del:false },
    packs: { read:function(r){ return String(r.id).indexOf("~sc-") === 0 && scName(r.data && r.data.student); } },
    results: { read:function(r){ var d = r.data || {}; return String(r.id).indexOf("~sc-") === 0 && scPack(d.packId) && scName(d.student); } },
    sheets: { read:function(r){ var d = r.data || {}; return scPack(r.id) && (d.packId == null ? r.id : d.packId) === r.id; } },
    phaseb: { read:function(r){ return scPack(r.pack_id); } },
    boards: { read:function(r){ return !!(r.data && r.data.showcase === true); }, insert:false, update:false, del:false }
  };
  M.guestRls = function(t, r){ return GUEST_RLS[t].read(r); };
  function denied(){ return res({ data:null, error:{ message:"new row violates row-level security policy", code:"42501" } }); }
  Query.prototype.run = function(){
    var t = M.db[this.t], self = this;
    var guest = !!(M.session && !M.teacher && M.guest), G = guest ? GUEST_RLS[this.t] : null;
    if(!M.session || (!M.teacher && !guest)) return res({ data:null, error:{ message:"permission denied", code:"42501" } });
    if(guest && this.kind === "upsert"){
      for(var i = 0; i < this.rows.length; i++){
        var nr = this.rows[i], old = t[key(nr)];
        if(old ? (G.update === false || !G.read(old) || !G.read(nr)) : (G.insert === false || !G.read(nr))) return denied();
      }
    }
    if(guest && this.kind === "delete"){
      if(G.del === false) return res({ data:null, error:null });
      M.log.push("delete " + this.t + (this.eqv ? " " + this.eqv : "") + (this.inv ? " in " + this.inv.join(",") : ""));
      (this.inv || [this.eqv]).forEach(function(k){ if(t[k] && G.read(t[k])) delete t[k]; });
      return res({ data:null, error:null });
    }
    if(M.failNext){ M.failNext = false; return res({ data:null, error:{ message:"network down" } }); }
    M.log.push(this.kind + " " + this.t + (this.eqv ? " " + this.eqv : "") + (this.inv ? " in " + this.inv.join(",") : "") + (this.rows ? " x" + this.rows.length : ""));
    if(this.kind === "upsert"){ this.rows.forEach(function(r){ t[key(r)] = JSON.parse(JSON.stringify(r)); }); return res({ data:null, error:null }); }
    if(this.kind === "delete"){ (this.inv || [this.eqv]).forEach(function(k){ delete t[k]; }); return res({ data:null, error:null }); }
    var rows = Object.keys(t).map(function(k){ return JSON.parse(JSON.stringify(t[k])); });
    if(guest) rows = rows.filter(function(r){ return G.read(r); });
    if(this.eqv) rows = rows.filter(function(r){ return key(r) === self.eqv; });
    if(this.ord) rows.sort(function(x, y){ return String(y.data[self.ord] || "").localeCompare(String(x.data[self.ord] || "")); });
    if(this.lim) rows = rows.slice(0, this.lim);
    return res({ data: this.single ? (rows[0] || null) : rows, error:null });
  };
  /* submit_homework: the same checks as dev/sql/submit_homework.sql (token, size, sid; insert-only, first copy wins).
     M.hwDown = true fails it like a dropped connection. Calls are logged in M.rpcs. */
  M.rpcs = [];
  M.submitHomework = function(a){
    a = JSON.parse(JSON.stringify(a || {})); M.rpcs.push(a);
    function err(m){ return res({ data:null, error:{ message:m, code:"P0001" } }); }
    if(M.hwDown){ return res({ data:null, error:{ message:"TypeError: Failed to fetch" } }); }
    if(!/^[0-9a-f]{32}$/.test(a.p_token || "")) return err("bad_link");
    var r = a.p_result; if(!r || typeof r !== "object" || Array.isArray(r)) return err("bad_result");
    if(JSON.stringify(r).length > 65536) return err("too_big");
    var pk = M.db.packs[a.p_pack], d = pk && pk.data;
    if(!d || !d.hw || d.hw[a.p_game] !== a.p_token) return err("bad_link");
    var g = (d.games || []).filter(function(x){ return x.id === a.p_game; })[0]; if(!g) return err("bad_link");
    if(!/^L?[a-z0-9]{6,20}$/.test(r.sid || "")) return err("bad_result");
    var id = a.p_pack + "_" + a.p_game + "_" + r.sid;
    if(M.db.results[id]) return res({ data:{ ok:true, "new":false }, error:null });
    var sum = String(r.summary || ""), i = sum.indexOf(" — ");
    sum = i !== -1 ? sum.slice(0, i) + " (homework, played 18 Nov 20:14)" + sum.slice(i) : "Homework, played 18 Nov 20:14" + (sum ? " — " + sum : "");
    var row = { id:id, data:{ id:id, packId:a.p_pack, student:d.student || "", lp:d.lp == null ? null : d.lp, gameId:a.p_game, type:g.type, title:(g.title || g.type) + " (homework)",
      at:new Date().toISOString(), summary:sum, score:r.score || null, items:r.items || [], activeSecs:r.activeSecs || 0, points:r.points == null ? null : r.points, homework:true, online:true } };
    if(r.sid[0] === "L") row.data.liveGen = r.sid.slice(1);
    M.db.results[id] = row; M.homework = (M.homework || []).concat([row]);
    return res({ data:{ ok:true, "new":true }, error:null });
  };
  M.remote = function(t, ev, row){ /* simulate another device */
    if(ev === "DELETE"){ delete M.db[t][key(row)]; } else M.db[t][key(row)] = row;
    M.handlers.forEach(function(h){ if(h.table === t) h.cb({ eventType:ev, new: ev === "DELETE" ? {} : row, old: ev === "DELETE" ? row : {} }); });
  };
  window.supabase = { createClient: function(url, key, opts){
    M.created = { url:url, key:key, opts:opts };
    var auth = {
      onAuthStateChange: function(cb){ M.authCbs.push(cb); return { data:{ subscription:{ unsubscribe:function(){} } } }; },
      getSession: function(){ return res({ data:{ session:M.session }, error:null }); },
      signInWithOtp: function(a){ M.otp = a; return res({ data:{}, error:null }); },
      verifyOtp: function(a){ if(a.token !== "123456") return res({ data:null, error:{ message:"bad" } });
        M.session = { user:{ email:a.email } }; M.authCbs.forEach(function(cb){ cb("SIGNED_IN", M.session); }); return res({ data:{ session:M.session }, error:null }); },
      signOut: function(){ M.session = null; M.authCbs.forEach(function(cb){ cb("SIGNED_OUT", null); }); return res({ error:null }); }
    };
    return {
      auth: auth,
      storage: { from: function(bk){ return {
        upload: function(path, blob, opts){ if(!M.session || !M.teacher) return res({ error:{ message:"denied" } }); M.uploads = (M.uploads||[]).concat([{ bk:bk, path:path, type:opts.contentType, size:blob.size, upsert:opts.upsert }]); return res({ data:{ path:path }, error:null }); },
        getPublicUrl: function(path){ return { data:{ publicUrl: "https://prglfopvovvxhzrejhzc.supabase.co/storage/v1/object/public/" + bk + "/" + path } }; } }; } },
      rpc: function(n, args){
        if(n === "submit_homework") return M.submitHomework(args);
        if(n === "am_i_guest") return res({ data: !!(M.session && M.guest), error:null });
        M.guests = M.guests || [];
        if(n === "guest_list") return res({ data: M.session && M.teacher ? M.guests.map(function(e){ return { email:e, added_at:"2026-11-27T00:00:00Z" }; }) : [], error:null });
        if(n === "guest_add" || n === "guest_remove"){
          if(!(M.session && M.teacher)) return res({ data:null, error:{ message:"not_teacher", code:"42501" } });
          var e = String(args && args.p_email || "").trim().toLowerCase();
          if(n === "guest_add"){ if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) return res({ data:null, error:{ message:"bad_email" } }); if(M.guests.indexOf(e) === -1) M.guests.push(e); }
          else M.guests = M.guests.filter(function(x){ return x !== e; });
          return res({ data:null, error:null });
        }
        return res({ data: !!(M.session && M.teacher), error:null }); },
      from: function(t){ return new Query(t); },
      channel: function(name, opts){
        var key = (opts && opts.config && opts.config.presence && opts.config.presence.key) || Math.random().toString(36).slice(2);
        var bc = null, bcb = [], pcb = [], members = {}, me = null;
        function psync(){ pcb.forEach(function(f){ f(); }); }
        var ch = {
          on:function(k, f, cb){ if(k === "postgres_changes") M.handlers.push({ table:f.table, cb:cb }); else if(k === "broadcast") bcb.push(cb); else if(k === "presence") pcb.push(cb); return ch; },
          subscribe:function(cb){
            if(bcb.length || pcb.length){
              bc = new BroadcastChannel("mockrt-" + name);
              bc.onmessage = function(e){ var d = e.data;
                if(d.op === "send") bcb.forEach(function(f){ f({ payload: JSON.parse(JSON.stringify(d.payload)) }); });
                else if(d.op === "track"){ members[d.key] = [d.meta]; psync(); if(me) bc.postMessage({ op:"here", key:key, meta:me }); }
                else if(d.op === "here"){ if(!members[d.key]){ members[d.key] = [d.meta]; psync(); } }
                else if(d.op === "leave"){ delete members[d.key]; psync(); } };
              M.channels = (M.channels || []).concat([name]); window.addEventListener('pagehide', function(){ if(bc) bc.postMessage({ op:'leave', key:key }); });
            }
            setTimeout(function(){ cb("SUBSCRIBED"); }, 10); return ch; },
          track:function(meta){ me = meta; members[key] = [meta]; if(bc) bc.postMessage({ op:"track", key:key, meta:meta }); psync(); return Promise.resolve(); },
          untrack:function(){ me = null; delete members[key]; if(bc) bc.postMessage({ op:"leave", key:key }); psync(); return Promise.resolve(); },
          presenceState:function(){ return members; },
          send:function(m){ M.sent = (M.sent || 0) + 1; if(bc) bc.postMessage({ op:"send", payload:m.payload }); return Promise.resolve("ok"); },
          unsubscribe:function(){ if(bc){ bc.postMessage({ op:"leave", key:key }); bc.close(); bc = null; } return Promise.resolve(); }
        }; return ch; },
      removeChannel: function(){ return Promise.resolve(); }
    };
  } };
})();
