(function(){
const $=s=>document.querySelector(s);

/* ================= CONEXÃO COM O BACK-END =================
   Endereço da API. Se o front for aberto pelo próprio servidor Python (porta 5000),
   usa o mesmo endereço; senão (Live Server, arquivo aberto direto) usa localhost:5000.
   Para apontar para outro servidor: defina window.API_URL antes de carregar este script. */
const BASE=window.API_URL||(/^https?:$/.test(location.protocol)&&(location.port==="5000"||location.port==="")?location.origin:"http://localhost:5000");
const API=BASE+"/api";

async function api(caminho,op={}){
  let r;
  try{r=await fetch(API+caminho,{method:op.method||"GET",
    headers:Object.assign({"Content-Type":"application/json"},S.tk?{Authorization:"Bearer "+S.tk}:{}),
    body:op.body!==undefined?JSON.stringify(op.body):undefined})}
  catch(e){throw new Error("Sem conexão com o servidor. O back-end está rodando?")}
  const d=await r.json().catch(()=>({}));
  if(r.status==401&&S.tk){S.tk=null;S.role=null;S.h=[];S.v={n:"login"};render()}
  if(!r.ok)throw new Error(d.erro||"Erro "+r.status);
  return d;
}

let TR={},KEYS=[];
const S={tk:null,role:null,nome:"",v:{n:"splash"},h:[],res:null,seg:"Treinos",per:"Semana",rk:"Evoluídos",rkD:{},du:null,ds:null,cq:null,hs:null,dark:false,
mf:"Todos",q:"",m:null,lock:false,rec:false,W:null,mem:[],total:0,painel:null,pl:null,fn:null,busy:false};
const CFG={notificacoes_treino:"Notificações de treino",sons_app:"Sons do app",lembretes_agua:"Lembretes de água"};

const tier=l=>l<=5?"Iniciante":l<=10?"Moderado":l<=15?"Intermediário":l<=20?"Avançado":"Evoluído";
const toast=m=>{const t=$("#tt");t.textContent=m;t.classList.add("on");clearTimeout(toast.i);toast.i=setTimeout(()=>t.classList.remove("on"),2200)};
const fmt=s=>String(Math.floor(s/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");
const back=()=>'<button class="back" data-a="back" aria-label="Voltar">‹</button>';
const hd=(t,s)=>'<h1>'+t+'</h1><p class="sub">'+s+'</p>';
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nf=n=>Number(n).toLocaleString("pt-BR");
const R0=n=>"R$ "+nf(n);
const R2=n=>"R$ "+Number(n).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
const dataBR=iso=>iso?iso.split("-").reverse().join("/"):"—";
const ini=n=>String(n).replace(/[^A-Za-zÀ-ú ]/g,"").split(" ").filter(Boolean).map(w=>w[0]).slice(0,2).join("").toUpperCase();
const load='<p class="mut">Carregando…</p>';

const ST=[["home","🏠","Início"],["treinos","🏋️","Treinos"],["ranking","🏆","Ranking"],["duelos","⚔️","Duelos"],["perfil","👤","Perfil"]];
const AD=[["ahome","🏠","Início"],["membros","👥","Membros"],["planos","📋","Planos"],["fin","💰","Financeiro"]];
const TABS={home:1,treinos:1,ranking:1,duelos:1,perfil:1,ahome:1,membros:1,planos:1,fin:1};

/* ================= CARREGAMENTO DE DADOS ================= */
const L={
  treinos:async()=>{const d=await api("/treinos");TR={};KEYS=d.map(t=>t.codigo);
    d.forEach(t=>TR[t.codigo]={n:t.nome,g:t.grupo,min:t.minutos,xp:t.xp,ex:t.exercicios.map(e=>[e.nome,e.grupo,e.series,e.reps,e.carga])})},
  resumo:async()=>{S.res=await api("/aluno/resumo")},
  hist:async()=>{S.hs=await api("/aluno/historico")},
  ranking:async()=>{S.rkD[S.rk]=await api("/ranking?categoria="+encodeURIComponent(S.rk))},
  duelos:async()=>{S.du=await api("/duelos")},
  desafios:async()=>{S.ds=await api("/desafios")},
  conq:async()=>{S.cq=await api("/aluno/conquistas")},
  painel:async()=>{S.painel=await api("/admin/painel")},
  membros:async()=>{const d=await api("/admin/membros");S.mem=d.membros;S.total=d.total},
  planos:async()=>{S.pl=await api("/admin/planos")},
  fin:async()=>{S.fn=await api("/admin/financeiro")}
};
const ONTAB={home:["resumo"],treinos:["hist"],ranking:["ranking"],duelos:["duelos"],perfil:["resumo"],streak:["resumo"],
  levels:["conq"],conq:["conq"],desafios:["desafios"],ahome:["painel"],membros:["membros"],planos:["planos"],fin:["fin"]};
async function carregar(n){if(ONTAB[n])try{await Promise.all(ONTAB[n].map(k=>L[k]()))}catch(e){toast(e.message)}}

/* ================= TELAS ================= */
const V={
splash:()=>'<div class="sv"><div><div class="lg">GS</div><h1>GymSystem</h1><p class="gt" style="letter-spacing:.04em;margin-top:8px">TREINE. EVOLUA. CONQUISTE.</p></div></div>',
login:()=>'<div class="row" style="margin-bottom:34px"><div class="logo">GS</div><b class="big" style="font-size:1.4rem">GymSystem</b></div><h1 style="font-weight:500;font-size:2rem">Bem-vindo de volta!</h1><p class="sub">Insira seus dados para acessar sua conta.</p><label for="em">E-mail</label><div class="inp">✉️<input id="em" type="email" value="lucas.oliveira@email.com" autocomplete="username"></div><label for="pw">Senha</label><div class="inp">🔒<input id="pw" type="password" value="senha1234567" autocomplete="current-password"><button data-a="eye" aria-label="Mostrar senha">👁️</button></div><button class="blue" style="display:block;margin:14px 0 0 auto;font-weight:700" data-a="forgot">Esqueci minha senha</button><button class="btn" data-a="login">Entrar</button><p class="mut" style="text-align:center;margin-top:16px">Não tem uma conta? <button class="blue" style="font-weight:700" data-a="signup">Criar conta</button></p><button class="mut" style="display:block;margin:26px auto 0;text-decoration:underline" data-a="admin">Acesso da academia</button>',
home:()=>{const R=S.res;if(!R||!TR[R.proximo_treino])return load;const T=TR[R.proximo_treino],pct=Math.min(100,Math.round(R.xp/R.xp_proximo_nivel*100)),D=R.desafio;
return '<div class="row sp"><div class="row"><div class="av">'+ini(R.nome)+'</div><div><div class="mut" style="font-size:1rem">Bem-vindo de volta,</div><b class="big" style="font-size:1.3rem">Olá, '+esc(R.nome.split(" ")[0])+'!</b></div></div><button class="pill" data-a="go" data-p="streak">🔥 '+R.sequencia+' dias</button></div><button class="dk" style="margin-top:18px" data-a="go" data-p="levels"><div class="row sp"><b class="big">Nível '+R.nivel+' — '+R.titulo+'</b>'+(R.posicao_ranking?'<span class="gt">#'+R.posicao_ranking+' no ranking</span>':'')+'</div><div class="row sp mut" style="margin-top:8px"><span>Progresso de XP</span><span class="gt">'+nf(R.xp)+' / '+nf(R.xp_proximo_nivel)+' XP</span></div><div class="bar"><i style="width:'+pct+'%"></i></div></button><h2 style="font-weight:500">Treino de Hoje</h2><div class="card" style="padding:20px"><div class="row sp"><div><b class="big" style="font-size:1.5rem">'+T.n+'</b><div class="mut" style="font-size:1.05rem">'+T.g+'</div></div><span class="tag">+'+T.xp+' XP</span></div><p class="mut" style="margin:14px 0 0">⏱️ '+T.min+' min &nbsp; 🎖️ '+T.ex.length+' Exercícios</p><button class="btn" data-a="start" data-p="'+R.proximo_treino+'">Começar Treino</button></div>'+(D?'<h2 style="font-weight:500">Competição Ativa</h2><button class="card row" data-a="go" data-p="desafios"><span class="tag y" style="font-size:1.4rem;padding:12px">🏅</span><div class="grow"><b class="big" style="font-size:1rem">'+esc(D.nome)+'</b><div class="mut">Faltam '+D.dias_restantes+' dias • Recompensa '+D.recompensa_xp+' XP</div></div>›</button>':'')},
treinos:()=>{let h=hd("Treinos","Escolha e comece")+'<div class="chips">'+["Treinos","Histórico"].map(c=>'<button class="chip'+(S.seg==c?" on":"")+'" data-a="seg" data-p="'+c+'">'+c+'</button>').join("")+'</div>';
if(S.seg=="Treinos")return h+KEYS.map(k=>{const T=TR[k];return '<div class="card"><div class="row sp"><div><b class="big">'+T.n+'</b><div class="mut">'+T.g+'</div></div><span class="tag">+'+T.xp+' XP</span></div><p class="mut" style="margin:10px 0 0">⏱️ '+T.min+' min &nbsp; 🎖️ '+T.ex.length+' Exercícios</p><ul class="mut" style="padding-left:18px;margin:8px 0 0">'+T.ex.map(e=>'<li>'+e[0]+' — '+e[2]+'x'+e[3]+' • '+e[4]+' kg</li>').join("")+'</ul><button class="btn" data-a="start" data-p="'+k+'">Começar</button></div>'}).join("");
const H=S.hs;if(!H)return h+load;
let graf="";const E=H.evolucao_carga;
if(E&&E[S.per]){const D=E[S.per],mn=Math.min(...D.valores)-4,mx=Math.max(...D.valores),n=D.valores.length,pts=D.valores.map((v,i)=>[30+i*(300/(n-1||1)),100-(v-mn)/((mx-mn)||1)*80]);
graf='<div class="chips">'+["Semana","Mês","Geral"].map(c=>'<button class="chip'+(S.per==c?" on":"")+'" data-a="per" data-p="'+c+'" style="padding:6px 14px">'+c+'</button>').join("")+'</div><div class="card"><div class="row sp"><b>Carga: '+esc(E.exercicio)+'</b><span class="tag" style="background:none;padding:0">'+esc(E.variacao)+'</span></div><svg viewBox="0 0 360 140" width="100%" role="img" aria-label="Evolução da carga"><polyline fill="none" stroke="var(--blue)" stroke-width="4" points="'+pts.map(p=>p.join(",")).join(" ")+'"/>'+pts.map(p=>'<circle cx="'+p[0]+'" cy="'+p[1]+'" r="6" fill="var(--blue)"/>').join("")+D.rotulos.map((l,i)=>'<text x="'+pts[i][0]+'" y="135" text-anchor="middle" font-size="12" fill="var(--mut)">'+esc(l)+'</text>').join("")+'</svg></div>'}
return h+graf+'<h2>Recordes Pessoais</h2><div class="g2">'+H.recordes.map(r=>'<div class="card"><span class="mut">'+esc(r.exercicio)+'</span><br><b class="big">'+nf(r.carga)+' kg 🏆</b></div>').join("")+'</div><h2>Treinos Recentes</h2>'+(H.treinos.length?H.treinos.map(x=>'<div class="card"><div class="row sp"><b class="mut">'+esc(x.quando)+'</b><b class="grt">+'+x.xp+' XP</b></div><b class="big" style="display:block;margin:6px 0">'+esc(x.nome)+' — '+esc(x.grupo)+'</b><span class="mut">⏱️ '+x.minutos+' min &nbsp; 🏋️ '+x.exercicios+' exercs.</span></div>').join(""):'<p class="mut">Nenhum treino ainda.</p>')},
ranking:()=>{const chips='<div class="chips">'+["Evoluídos","Moderados","Iniciantes"].map(c=>'<button class="chip'+(S.rk==c?" on":"")+'" data-a="rk" data-p="'+c+'">'+c+'</button>').join("")+'</div>',h=hd("Ranking","Competição saudável com a galera")+chips;
const G=(S.rkD[S.rk]||[]).map(x=>({n:x.eu?x.nome.split(" ")[0]+" (Você)":x.nome,xp:x.xp,e:x.emoji,me:x.eu,seq:x.sequencia}));
if(G.length<3)return h+load;
const P=[G[1],G[0],G[2]],col=["#C0C0C0","#FFD600","#CD7F32"],hh=[60,100,44];
return h+'<div class="pod">'+P.map((p,i)=>'<div><div class="c" style="border-color:'+col[i]+'">'+(p.e||esc(p.n[0]))+'</div><b>'+esc(p.n.split(" ")[0])+'</b><div class="mut'+(i==1?' gt':'')+'" style="font-size:.8rem">'+nf(p.xp)+' XP</div><div class="b" style="background:'+col[i]+';height:'+hh[i]+'px;margin-top:8px"></div></div>').join("")+'</div><h2>Quadro de Líderes</h2>'+G.slice(3).map((p,i)=>'<div class="card row" style="'+(p.me?"border-color:var(--blue);background:color-mix(in srgb,var(--blue) 9%,var(--card))":"")+'"><b class="mut" style="width:30px">#'+(i+4)+'</b><div class="av'+(p.me?"":" s")+'">'+ini(p.n.replace("(Você)",""))+'</div><div class="grow"><b>'+esc(p.n)+'</b>'+(p.me?'<div class="mut" style="font-size:.8rem">Sequência: '+p.seq+' dias 🔥</div>':"")+'</div><b class="'+(p.me?"blue":"")+'">'+nf(p.xp)+' XP</b></div>').join("")},
duelos:()=>{const h=hd("Duelos","Dispute XP com os seus amigos");if(!S.du)return h+load;const D=S.du.ativo,C=S.du.convites;let out=h;
if(D){const a=D.oponente.xp,b=D.voce.xp,pc=Math.round(a/((a+b)||1)*100);
out+='<div class="dk"><div class="row sp"><b class="gt" style="font-size:.8rem">DUELO ATIVO</b><span class="mut">'+D.dias_restantes+' dias restantes</span></div><div class="row sp" style="margin:16px 0;text-align:center"><div><div class="av" style="width:64px;height:64px;margin:auto">'+ini(D.oponente.nome)+'</div><b style="display:block;margin-top:8px">'+esc(D.oponente.nome)+'</b><span class="mut">Nível '+D.oponente.nivel+'</span></div><b class="gt tag n" style="background:#1c2340;color:var(--gr)">VS</b><div><div class="av" style="width:64px;height:64px;margin:auto;background:var(--yel);color:#0A0F24">'+ini(D.voce.nome)+'</div><b style="display:block;margin-top:8px">'+esc(D.voce.nome)+'</b><span class="mut">Nível '+D.voce.nivel+'</span></div></div><div class="mc"><span class="mut">Objetivo</span><br><b>'+esc(D.objetivo)+'</b></div><div class="row sp" style="margin-top:14px"><b>'+nf(a)+' XP</b><span class="mut">XP acumulado</span><b class="gt">'+nf(b)+' XP</b></div><div class="bar" style="background:var(--gr)"><i style="width:'+pc+'%;background:#fff;border-radius:0"></i></div></div>'}
else out+='<p class="mut">Nenhum duelo ativo.</p>';
return out+'<h2>Convites Recebidos</h2>'+(C.length?C.map(c=>'<div class="card"><div class="row"><div class="av" style="background:#FF8A65">'+ini(c.de)+'</div><div><b>'+esc(c.de)+'</b><div class="mut">Te desafiou para "'+esc(c.desafio)+'" • '+c.dias+' dias</div></div></div><div class="g2" style="margin-top:12px"><button class="btn out" style="margin:0" data-a="inv" data-p="'+c.id+':0">Recusar</button><button class="btn" style="margin:0" data-a="inv" data-p="'+c.id+':1">Aceitar</button></div></div>').join(""):'<p class="mut">Nenhum convite pendente.</p>')},
perfil:()=>{const R=S.res;if(!R)return load;return hd("Perfil","Sua conta e preferências")+'<div class="card row"><div class="av" style="width:60px;height:60px">'+ini(R.nome)+'</div><div><b class="big">'+esc(R.nome)+'</b><div class="mut">Nível '+R.nivel+' — '+R.titulo+'</div></div></div>'+[["streak","🔥","Sequência"],["levels","🎖️","Níveis e Títulos"],["conq","🏅","Conquistas"],["desafios","🎯","Desafios"]].map(x=>'<button class="card row" data-a="go" data-p="'+x[0]+'"><span style="font-size:1.4rem">'+x[1]+'</span><b class="grow">'+x[2]+'</b>›</button>').join("")+'<h2>Configurações</h2><div class="card">'+Object.keys(R.config).map(k=>'<div class="row sp" style="padding:8px 0"><span>'+(CFG[k]||k)+'</span><button class="tg'+(R.config[k]?" on":"")+'" data-a="cfg" data-p="'+k+'" role="switch" aria-checked="'+R.config[k]+'" aria-label="'+(CFG[k]||k)+'"></button></div>').join("")+'<div class="row sp" style="padding:8px 0"><span>Modo escuro</span><button class="tg'+(S.dark?" on":"")+'" data-a="dark" role="switch" aria-checked="'+S.dark+'" aria-label="Modo escuro"></button></div></div><button class="btn red" data-a="logout">Sair da conta</button>'},
streak:()=>{const R=S.res;if(!R)return back()+load;const F=R.frequencia_mes,pc=Math.min(100,Math.round(F.ativos/F.meta*100));
return back()+hd("Sequência","Mantenha o foco diário")+'<div class="dk mc" style="padding:26px"><div style="font-size:3rem;font-weight:800">'+R.sequencia+' dias 🔥</div><p class="gt">Melhor marca histórica: '+R.melhor_sequencia+' dias</p><hr style="border:0;border-top:1px solid #26305A;margin:14px 40px"><p class="mut">'+(R.treinou_hoje?"Treino de hoje concluído. Volte amanhã!":"Treine hoje para completar o "+(R.sequencia+1)+"º dia consecutivo!")+'</p></div><h2>Esta Semana</h2><div class="card"><div class="dots">'+R.semana.map(d=>'<div'+(d.hoje?' style="color:var(--blue)"':'')+'>'+d.dia+'<i class="'+(d.treinou?"on":"")+'"></i></div>').join("")+'</div></div><h2>Frequência Mensal</h2><div class="card"><div class="row sp"><span>Dias ativos: '+F.ativos+'/'+F.meta+'</span><b class="grt">'+pc+'% Consistência</b></div><div class="bar"><i style="width:'+pc+'%"></i></div><p class="mut" style="margin:0">Continue treinando para manter sua sequência!</p></div>'},
levels:()=>{const lvl=S.res?S.res.nivel:1;return back()+hd("Níveis e Títulos","Desbloqueie conquistas na sua evolução")+'<h2 style="margin-top:0">Progressão de Níveis</h2><div class="card">'+[["Iniciante","1 - 5"],["Moderado","6 - 10"],["Intermediário","11 - 15"],["Avançado","16 - 20"],["Evoluído","21+"]].map(x=>{const on=x[0]==tier(lvl);return '<div class="row sp" style="padding:9px 0"><span class="row"><i style="width:20px;height:20px;border-radius:50%;background:'+(on?"var(--gr)":"var(--line)")+'"></i><b class="'+(on?"blue":"")+'" style="font-weight:'+(on?700:400)+'">'+x[0]+'</b></span><span class="tag '+(on?"":"n")+'" style="'+(on?"background:var(--blue);color:#fff":"")+'">Nível '+x[1]+'</span></div>'}).join("")+'</div><h2>Títulos Disponíveis</h2>'+(S.cq?S.cq.titulos.map(x=>'<div class="card row sp"><div><b class="big">'+x.icone+' '+esc(x.nome)+'</b><div class="mut">'+esc(x.descricao)+'</div></div><span class="tag '+(x.liberado?"":"n")+'">'+(x.liberado?"Liberado":"Bloqueado")+'</span></div>').join(""):load)},
conq:()=>back()+hd("Conquistas","Sua galeria de troféus e medalhas")+(S.cq?'<div class="g2">'+S.cq.medalhas.map(x=>{const parcial=!x.concluida&&x.meta>1&&x.progresso>0,pc=Math.round(x.progresso/x.meta*100);
return '<div class="card mc" style="'+(x.concluida?"":"opacity:.6")+'"><div style="font-size:2rem">'+x.icone+'</div><b style="display:block;margin:6px 0 4px">'+esc(x.nome)+'</b><div class="mut" style="font-size:.8rem;margin-bottom:8px">'+esc(x.descricao)+'</div>'+(parcial?'<div class="bar"><i style="width:'+pc+'%"></i></div><small>'+x.progresso+' / '+x.meta+'</small>':'<span class="tag '+(x.concluida?"":"n")+'">'+(x.concluida?"Concluído":"Pendente")+'</span>')+'</div>'}).join("")+'</div>':load),
desafios:()=>{const h=back()+hd("Desafios","Participe de desafios e compita com amigos");if(!S.ds)return h+load;const D=S.ds.ativo;let out=h;
if(D){const pc=Math.round(D.progresso/D.treinos_meta*100);out+='<h2 style="margin-top:0">Competições Ativas</h2><div class="card"><div class="row sp"><b class="big">'+esc(D.nome)+'</b><span class="tag y">'+D.recompensa_xp+' XP 🏆</span></div><p class="mut">Meta: '+esc(D.meta)+'</p><div class="row sp"><span class="mut">Seu Progresso: '+D.progresso+'/'+D.treinos_meta+' Treinos</span><b class="blue">'+pc+'% feito</b></div><div class="bar"><i style="width:'+pc+'%"></i></div><div class="row sp" style="margin-top:8px"><span class="mut">👥 '+D.participantes+' participando • Faltam '+D.dias_restantes+' dias</span></div><button class="btn'+(D.participando?" out":"")+'" data-a="join" data-p="'+D.id+'">'+(D.participando?"Participando ✓":"Participar")+'</button></div>'}
return out+'<h2>Desafios da Academia</h2>'+S.ds.academia.map(x=>'<div class="card row sp"><div><b>'+x.icone+' '+esc(x.nome)+'</b><div class="mut">'+esc(x.descricao)+'</div></div><div style="text-align:right"><b class="grt">+'+x.xp+' XP</b><div class="mut">'+esc(x.status)+'</div></div></div>').join("")},
work:()=>{const W=S.W,T=TR[W.k],e=T.ex[W.i];
return '<div class="row sp"><b class="blue" style="font-size:.85rem">TREINO EM CURSO</b><b class="mut" style="font-size:.9rem">Tempo: <span id="el">'+fmt(W.el)+'</span></b></div><h1 style="margin-top:14px">'+e[0]+'</h1><p class="mut">'+e[1]+' • Exercício '+(W.i+1)+' de '+T.ex.length+'</p><div class="hero" role="img" aria-label="Ilustração do exercício">🏋️</div><div class="g3"><div class="card mc"><small>SÉRIE ATUAL</small><b>'+W.s+' / '+e[2]+'</b></div><div class="card mc"><small>REPETIÇÕES</small><b>'+e[3]+'</b></div><div class="card mc"><small>CARGA</small><div class="row" style="justify-content:center"><button class="stp" data-a="kg" data-p="-2.5" aria-label="Diminuir carga">−</button><b class="blue" style="font-size:1.2rem">'+W.kg+'</b><button class="stp" data-a="kg" data-p="2.5" aria-label="Aumentar carga">+</button></div></div></div>'+(W.rest>0?'<div class="card mc" style="margin-top:12px"><small>INTERVALO RESTANTE</small><div class="rest" id="rs">'+fmt(W.rest)+'</div></div><button class="btn out" data-a="skip">Pular intervalo</button>':'<button class="btn" data-a="serie">'+(S.busy?"Salvando…":"Concluir série")+'</button>')+'<button class="btn red" data-a="quit">Encerrar treino</button>'},
done:()=>{const R=S.r;return '<div class="ok">🎖️</div><h1 class="mc">Treino Concluído!</h1><p class="sub mc">Você dominou as séries hoje. Parabéns!</p><div class="card"><div class="row sp"><b class="mut">Resumo da Atividade</b><span class="tag">+'+R.xp+' XP</span></div><hr style="border:0;border-top:1px solid var(--line);margin:14px 0"><div class="g3 mc"><div><b>'+R.minutos+' min</b><br><span class="mut">Tempo Total</span></div><div><b>'+R.exercicios+'</b><br><span class="mut">Exercícios</span></div><div><b>'+R.series+'</b><br><span class="mut">Séries Totais</span></div></div><p class="mut" style="margin:14px 0 0">Treino +'+R.detalhe_xp.treino+' • Sequência +'+R.detalhe_xp.sequencia+' • Recordes +'+R.detalhe_xp.recordes+'</p></div>'+(R.subiu_de_nivel?'<div class="card row" style="background:var(--grbg);border-color:var(--gr)"><span style="font-size:1.8rem">⬆️</span><div><b class="big" style="font-size:1rem">Subiu para o nível '+R.nivel+'!</b></div></div>':'')+(R.recordes.length?'<div class="card row" style="background:var(--yelbg);border-color:var(--yel)"><span style="font-size:1.8rem">🏆</span><div><b class="big" style="font-size:1rem">Novo Recorde Pessoal!</b><div class="mut">'+R.recordes.map(x=>esc(x.exercicio)+' — '+nf(x.carga)+' kg').join("<br>")+'</div></div></div>':'')+'<button class="btn" data-a="tab" data-p="home">Voltar ao início</button>'},
ahome:()=>{const P=S.painel;if(!P)return load;return hd("Painel","Visão geral da academia")+'<div class="g2"><div class="card"><span class="mut">Alunos ativos</span><br><b class="big">'+nf(P.membros_ativos)+'/'+nf(P.total_membros)+'</b></div><div class="card"><span class="mut">Receita do mês</span><br><b class="big grt">'+R0(P.receita_mes)+'</b></div></div><h2>Atenção</h2><button class="card row sp" data-a="tab" data-p="planos"><span>'+P.vencendo_30d+' contratos vencem em 30 dias</span>›</button><button class="card row sp" data-a="tab" data-p="fin"><span>'+R0(P.inadimplencia)+' em inadimplência</span>›</button><button class="btn out" data-a="logout">Sair</button>'},
membros:()=>hd("Membros","Total de "+nf(S.total)+" cadastrados")+'<div class="inp" style="margin-bottom:14px">🔍<input id="q" placeholder="Buscar aluno por nome ou CPF..." value="'+esc(S.q)+'" aria-label="Buscar aluno"></div><div class="chips">'+["Todos","Ativos","Inativos"].map(c=>'<button class="chip'+(S.mf==c?" on":"")+'" data-a="mf" data-p="'+c+'">'+c+'</button>').join("")+'</div><div id="ml">'+ML()+'</div>',
ficha:()=>{const m=S.m;if(!m)return back()+load;return back()+'<h1>Ficha do Aluno</h1><div class="card" style="margin-top:16px"><div class="row"><div class="av" style="width:64px;height:64px">'+ini(m.nome)+'</div><div class="grow"><b class="big">'+esc(m.nome)+'</b><div class="mut">Cadastrado em '+dataBR(m.cadastro)+'</div></div><span class="tag'+(m.ativo?"":" r")+'">'+(m.ativo?"Ativo":"Inativo")+'</span></div><hr style="border:0;border-top:1px solid var(--line);margin:16px 0"><div class="g3"><div><span class="mut">Frequência</span><br><b class="big">'+(esc(m.frequencia)||"—")+'</b></div><div><span class="mut">Sequência</span><br><b class="big">'+m.sequencia+' dias</b></div><div><span class="mut">Nível</span><br><b class="big blue">Lvl '+m.nivel+'</b></div></div></div><div class="card"><b class="big">Informações de Matrícula</b><div class="row sp" style="margin-top:12px"><span class="mut">Plano Atual</span><b>'+esc(m.plano)+'</b></div><div class="row sp"><span class="mut">Valor Mensal</span><b>'+R2(m.valor_mensal)+'</b></div><div class="row sp"><span class="mut">Vencimento</span><b class="'+(m.vencido_ha_dias?"red":"grt")+'">'+dataBR(m.vencimento)+'</b></div></div><h2>Treinos Recentes</h2>'+(m.treinos_recentes.length?m.treinos_recentes.map(t=>'<div class="card row sp"><div><b>💪 '+esc(t.titulo)+'</b><div class="mut" style="font-size:.85rem">Duração: '+t.minutos+' min • Ganhou '+t.xp+' XP</div></div><span class="mut">'+esc(t.quando)+'</span></div>').join(""):'<p class="mut">Nenhum treino recente.</p>')+'<div class="g2"><button class="btn" style="margin:0" data-a="lock">'+(S.lock?"Desbloquear Ficha":"Bloquear Ficha / Editar")+'</button><button class="btn red" style="margin:0" data-a="deact">'+(m.ativo?"Desativar Aluno":"Reativar Aluno")+'</button></div>'},
planos:()=>{const P=S.pl;if(!P)return load;return hd("Planos e Matrículas","Controle de pacotes e vigência")+'<div class="card"><b class="big">Resumo de Contratos</b><div class="row sp mut" style="margin-top:10px"><span>Próximas do Vencimento (30d)</span><b style="color:#B58900">'+P.resumo.vencendo_30d+' alunos</b></div><div class="row sp mut"><span>Vencidas / Pendentes</span><b class="red">'+P.resumo.vencidas+' alunos</b></div><div class="row sp mut"><span>Novos este mês</span><b class="grt">+'+P.resumo.novos_mes+' contratos</b></div></div><h2>Planos Ativos</h2>'+P.planos.map(p=>'<button class="card row sp" data-a="plano" data-p="'+esc(p.nome)+'"><div><b class="big" style="font-size:1rem">Plano '+esc(p.nome)+'</b><div class="mut">'+p.alunos_ativos+' alunos ativos</div></div><b class="blue big">'+R0(p.preco)+'</b></button>').join("")+'<h2>Próximos Vencimentos</h2>'+P.vencimentos.map(x=>'<div class="card row sp"><div><b>'+esc(x.aluno)+'</b><div class="mut">'+esc(x.plano)+'</div></div><b class="red" style="font-size:.9rem">'+(x.dias>0?"Vence em "+x.dias+" dias":x.dias==0?"Vence hoje":"Venceu há "+(-x.dias)+" dias")+'</b></div>').join("")},
fin:()=>{const F=S.fn;if(!F)return load;const R=F.recebimentos.filter(r=>!S.rec||!r.confirmado),mx=Math.max(...F.evolucao.map(b=>b.valor));
return hd("Financeiro","Movimentações de caixa e mensalidades")+'<div class="g2"><div class="card"><span class="mut">Receita Estimada</span><br><b class="big">'+R0(F.receita_estimada)+'</b></div><div class="card"><span class="mut">Recebido</span><br><b class="big grt">'+R0(F.recebido)+'</b></div><div class="card"><span class="mut">Inadimplência</span><br><b class="big red">'+R0(F.inadimplencia)+'</b></div><div class="card"><span class="mut">Cancelamentos</span><br><b class="big mut">'+F.cancelamentos_mes+' este mês</b></div></div><div class="card" style="margin-top:12px"><b class="big" style="font-size:1rem">Evolução da Receita (R$ Milhares)</b><div class="row" style="align-items:flex-end;height:150px;margin-top:10px">'+F.evolucao.map(b=>'<div class="grow mc" style="font-size:.72rem;min-width:0"><b style="font-size:.72rem">'+nf(b.valor/1000)+'k</b><div style="height:'+Math.round(b.valor/mx*100)+'px;background:var(--blue);border-radius:8px 8px 0 0;margin:4px 6px 4px"></div><span class="mut">'+esc(b.mes)+'</span></div>').join("")+'</div></div><div class="row sp"><h2>Últimos Recebimentos</h2><button class="blue" style="font-weight:700" data-a="rec">'+(S.rec?"Ver todos":"Só pendentes")+'</button></div>'+(R.length?R.map(r=>'<div class="card row sp"><div><b class="big" style="font-size:1rem">'+esc(r.aluno)+'</b><div class="mut">'+esc(r.plano)+'</div></div><div style="text-align:right"><b>'+R2(r.valor)+'</b><br><span class="tag'+(r.confirmado?"":" r")+'">'+(r.confirmado?"Confirmado":"Pendente")+'</span></div></div>').join(""):'<p class="mut">Nenhum recebimento pendente.</p>')}
};
function ML(){const q=S.q.toLowerCase();const L2=S.mem.filter(m=>(S.mf=="Todos"||(S.mf=="Ativos")==m.ativo)&&(m.nome.toLowerCase().includes(q)||m.cpf.includes(q)));
return L2.length?L2.map(m=>'<button class="card row" data-a="ficha" data-p="'+m.id+'"><div class="av">'+ini(m.nome)+'</div><div class="grow"><b>'+esc(m.nome)+'</b><div class="mut" style="font-size:.85rem">'+(m.ativo?"Frequência: "+esc(m.frequencia)+" • Nív. "+m.nivel:(m.vencido_ha_dias?"Vencido há "+m.vencido_ha_dias+" dias":"Inativo")+" • Nív. "+m.nivel)+'</div></div><div style="text-align:right"><span class="tag'+(m.ativo?"":" r")+'">'+(m.ativo?"Ativo":"Inativo")+'</span><div class="mut" style="font-size:.72rem;margin-top:4px">Último: '+esc(m.ultimo_treino)+'</div></div></button>').join(""):'<p class="mut">Nenhum aluno encontrado.</p>'}

/* ================= NAVEGAÇÃO ================= */
function render(){
  const n=S.v.n,sc=$("#scr");
  sc.className=n=="splash"?"dark":"";sc.innerHTML=V[n]();
  const nv=$("#nav"),tabs=S.role=="admin"?AD:ST;
  nv.hidden=!TABS[n];
  if(!nv.hidden)nv.innerHTML=tabs.map(t=>'<button class="'+(t[0]==n?"on":"")+'" data-a="tab" data-p="'+t[0]+'"><i>'+t[1]+'</i>'+t[2]+'</button>').join("");
}
function show(n){S.v={n};render();$("#scr").scrollTop=0}
async function go(n){await carregar(n);S.h.push(S.v.n);show(n)}
async function tab(n){await carregar(n);S.h=[];show(n)}
function endWork(){clearInterval(S.tm);S.tm=null;S.W=null}
async function finish(){
  const W=S.W,T=TR[W.k];
  const d=await api("/treinos/concluir",{method:"POST",body:{treino:W.k,segundos:W.el,cargas:T.ex.map((e,i)=>W.cg[i]??e[4])}});
  S.r=d.resultado;S.res=d.resumo;S.hs=null;endWork();S.h=[];show("done");
  if(S.r.subiu_de_nivel)toast("Parabéns! Você subiu para o nível "+S.r.nivel);
}
function tick(){const W=S.W;if(!W)return;W.el++;const el=$("#el");if(el)el.textContent=fmt(W.el);
  if(W.rest>0){W.rest--;if(W.rest<=0)render();else{const r=$("#rs");if(r)r.textContent=fmt(W.rest)}}}
async function entrar(email,senha){
  const d=await api("/login",{method:"POST",body:{email,senha}});
  S.tk=d.token;S.role=d.usuario.papel;S.nome=d.usuario.nome;
  if(S.role=="admin"){await Promise.all(["painel","membros","planos","fin"].map(k=>L[k]()));await tab("ahome")}
  else{await Promise.all(["treinos","resumo","duelos"].map(k=>L[k]()));await tab("home")}
}
function sair(){if(S.tk)api("/logout",{method:"POST"}).catch(()=>{});endWork();
  Object.assign(S,{tk:null,role:null,h:[],res:null,hs:null,du:null,ds:null,cq:null,rkD:{},painel:null,pl:null,fn:null,mem:[],m:null});show("login")}

/* Ações que falam com o servidor passam por aqui: evita clique duplo e mostra o erro num aviso. */
const run=f=>async p=>{if(S.busy)return;S.busy=true;try{await f(p)}catch(e){toast(e.message)}finally{S.busy=false}};

const A={
go:run(go),tab:run(tab),back:()=>show(S.h.pop()||(S.role=="admin"?"ahome":"home")),
eye:()=>{const i=$("#pw");i.type=i.type=="password"?"text":"password"},
forgot:()=>toast("Recuperação de senha disponível em breve"),
signup:()=>toast("Cadastro disponível em breve"),
login:run(async()=>{const e=$("#em").value.trim(),p=$("#pw").value;
  if(!/^\S+@\S+\.\S+$/.test(e))return toast("Digite um e-mail válido");
  if(p.length<6)return toast("A senha precisa ter ao menos 6 caracteres");
  await entrar(e,p)}),
admin:run(()=>entrar("admin@gymsystem.com","admin123")),
logout:sair,
seg:run(async p=>{S.seg=p;if(p=="Histórico"&&!S.hs)await L.hist();render()}),
per:p=>{S.per=p;render()},
rk:run(async p=>{S.rk=p;render();await L.ranking();render()}),
inv:run(async p=>{const[id,ac]=p.split(":");S.du=await api("/duelos/convites/"+id,{method:"POST",body:{aceitar:ac=="1"}});render();toast(ac=="1"?"Duelo aceito! Boa sorte":"Convite recusado")}),
join:run(async p=>{const d=await api("/desafios/"+p+"/participar",{method:"POST"});Object.assign(S.ds.ativo,d);if(S.res&&S.res.desafio)S.res.desafio.participando=d.participando;render();toast(d.participando?"Você entrou no desafio":"Você saiu do desafio")}),
cfg:run(async p=>{const d=await api("/aluno/config",{method:"PUT",body:{chave:p,valor:!S.res.config[p]}});S.res.config=d.config;render()}),
dark:()=>{S.dark=!S.dark;document.documentElement.dataset.theme=S.dark?"dark":"light";render()},
start:p=>{const T=TR[p];if(!T)return;S.W={k:p,i:0,s:1,rest:0,el:0,kg:T.ex[0][4],cg:[]};S.h=[S.v.n];show("work");clearInterval(S.tm);S.tm=setInterval(tick,1000)},
kg:p=>{S.W.kg=Math.max(0,S.W.kg+ +p);render()},
serie:run(async()=>{const W=S.W,T=TR[W.k],e=T.ex[W.i];
  W.cg[W.i]=Math.max(W.cg[W.i]||0,W.kg);
  if(W.s<e[2]){W.s++;W.rest=90;render()}
  else if(W.i<T.ex.length-1){W.i++;W.s=1;W.rest=90;W.kg=T.ex[W.i][4];render();toast("Próximo: "+T.ex[W.i][0])}
  else{render();await finish()}}),
skip:()=>{S.W.rest=0;render()},
quit:()=>{if(confirm("Encerrar o treino sem salvar?")){endWork();S.h=[];show("home")}},
mf:p=>{S.mf=p;render()},
ficha:run(async p=>{S.m=await api("/admin/membros/"+p);S.lock=false;S.h.push(S.v.n);show("ficha")}),
lock:()=>{S.lock=!S.lock;render();toast(S.lock?"Ficha bloqueada para edição":"Ficha desbloqueada")},
deact:run(async()=>{const m=await api("/admin/membros/"+S.m.id,{method:"PATCH",body:{ativo:!S.m.ativo}});S.m=m;
  await Promise.all([L.membros(),L.painel()]);render();toast(m.ativo?"Aluno reativado":"Aluno desativado")}),
plano:p=>toast("Plano "+p+": edição em breve"),
rec:()=>{S.rec=!S.rec;render()}
};
document.addEventListener("click",e=>{const b=e.target.closest("[data-a]");if(b&&A[b.dataset.a])A[b.dataset.a](b.dataset.p)});
document.addEventListener("input",e=>{if(e.target.id=="q"){S.q=e.target.value;$("#ml").innerHTML=ML()}});
render();
S.sp=setTimeout(()=>{if(S.v.n=="splash")show("login")},1800);
$("#scr").addEventListener("click",()=>{if(S.v.n=="splash"){clearTimeout(S.sp);show("login")}});
})();
