import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {BaseSceneProps} from '../VideoSpec.schema';
import {Backdrop} from '../theme/Backdrop';
import {useStyle} from '../theme/StyleContext';
import {getSafeArea} from '../lib/safeArea';
import {resolveMotion} from '../lib/motion';
import {fitOneLine, fitWrapped} from '../theme/layout';

type TextProps = BaseSceneProps & Record<string, unknown>;
const clamp = (value: number) => Math.max(0, Math.min(1, value));
const asText = (value: unknown, fallback = '') => typeof value === 'string' ? value : fallback;
const asRows = (value: unknown) => Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === 'object') : [];

const Stage: React.FC<{props: BaseSceneProps; children: React.ReactNode}> = ({props, children}) => {
  const {width, height} = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const {theme} = useStyle();
  return <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: theme.bg}}>
    <Backdrop />
    <div style={{position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, boxSizing: 'border-box'}}>{children}</div>
  </div>;
};

const Eyebrow: React.FC<{text: string}> = ({text}) => {
  const {height, width} = useVideoConfig();
  const {fonts, accent} = useStyle();
  return <div style={{fontFamily: fonts.display, color: accent, fontWeight: 850, fontSize: Math.round(height * 0.018), letterSpacing: Math.round(width * 0.0028), textTransform: 'uppercase'}}>{text}</div>;
};

/** High-retention opening claim with a compact proof pill. */
export const HookStack: React.FC<BaseSceneProps> = (props) => {
  const value = props as TextProps;
  const frame = useCurrentFrame(); const {width, height, fps} = useVideoConfig();
  const {theme, fonts, accent} = useStyle(); const enter = resolveMotion(props.motion ?? 'reveal', fps, 'reveal');
  const headline = asText(value.headline, asText(value.title, 'Важный сигнал'));
  const subhead = asText(value.subhead, asText(value.text, 'Проверьте детали до следующего шага'));
  const proof = asText(value.proof, 'ПЕРВОИСТОЧНИК ПРОВЕРЕН'); const urgency = asText(value.urgency, 'СЕЙЧАС');
  const progress = clamp(enter(frame, 0, 1)); const fit = fitWrapped({text: headline, maxWidth: width * 0.76, maxLines: 3, maxFontSize: Math.round(height * 0.080), minFontSize: Math.round(height * 0.040), fontFamily: fonts.display, fontWeight: 900, lineHeight: .94});
  return <Stage props={props}><div style={{height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: progress, transform: `translateY(${Math.round((1 - progress) * height * 0.035)}px)`}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 12}}><Eyebrow text={urgency}/><div style={{height: 1, flex: 1, background: `${theme.muted}55`}}/></div>
    <div style={{fontFamily: fonts.display, fontWeight: 900, color: theme.text, fontSize: fit.fontSize, lineHeight: .94, marginTop: Math.round(height * .025), maxWidth: width * .76, overflowWrap: 'normal', wordBreak: 'keep-all'}}>{headline}</div>
    <div style={{width: Math.round(width * .19), height: 5, borderRadius: 99, background: accent, marginTop: Math.round(height * .026), boxShadow: `0 0 18px ${accent}`}}/>
    <div style={{fontFamily: fonts.body, color: theme.muted, fontWeight: 650, fontSize: Math.round(height * .027), lineHeight: 1.2, maxWidth: width * .72, marginTop: Math.round(height * .025)}}>{subhead}</div>
    <div style={{alignSelf: 'flex-start', marginTop: Math.round(height * .04), border: `1px solid ${accent}88`, borderRadius: 999, padding: '8px 13px', color: accent, fontFamily: fonts.display, fontWeight: 800, fontSize: Math.round(height * .015), letterSpacing: 1}}>{proof}</div>
  </div></Stage>;
};

/** Static reading dwell around one high-impact phrase. */
export const KineticPhrase: React.FC<BaseSceneProps> = (props) => {
  const value = props as TextProps; const frame = useCurrentFrame(); const {width, height, fps} = useVideoConfig(); const {theme, fonts, accent} = useStyle();
  const phrase = asText(value.phrase, asText(value.title, 'НЕ СРАВНИВАЙТЕ ЦЕНЫ В ЛОБ'));
  const highlight = asText(value.highlight, 'СМОТРИТЕ WORKLOAD'); const caption = asText(value.caption, asText(value.text));
  const enter = clamp(resolveMotion(props.motion ?? 'reveal', fps, 'reveal')(frame, 0, 1)); const fit = fitWrapped({text: phrase, maxWidth: width * .84, maxLines: 3, maxFontSize: Math.round(height * .094), minFontSize: Math.round(height * .042), fontFamily: fonts.display, fontWeight: 900, lineHeight: .90});
  return <Stage props={props}><div style={{height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: enter}}>
    <div style={{fontFamily: fonts.display, fontSize: fit.fontSize, fontWeight: 900, color: theme.text, letterSpacing: '-.04em', lineHeight: .90, maxWidth: width * .84, wordBreak: 'keep-all'}}>{phrase}</div>
    <div style={{fontFamily: fonts.display, color: accent, fontWeight: 900, fontSize: Math.round(height * .028), letterSpacing: 2, marginTop: Math.round(height * .035), paddingLeft: 16, borderLeft: `5px solid ${accent}`}}>{highlight}</div>
    {caption && <div style={{fontFamily: fonts.body, color: theme.muted, fontSize: Math.round(height * .023), lineHeight: 1.28, marginTop: 14, maxWidth: width * .76}}>{caption}</div>}
  </div></Stage>;
};

/** Directed problem → solution contrast. */
export const ProblemSolution: React.FC<BaseSceneProps> = (props) => {
  const value = props as TextProps; const frame = useCurrentFrame(); const {width, height, fps} = useVideoConfig(); const {theme, fonts, accent} = useStyle(); const inMotion = resolveMotion(props.motion ?? 'reveal', fps, 'reveal');
  const problem = asText(value.problem, 'Сравнивать только list price'); const solution = asText(value.solution, 'Считать цену под свой workload'); const title = asText(value.title, 'СМЕНА ПОДХОДА');
  const left = clamp(inMotion(frame, 0, 1)); const right = clamp(inMotion(frame - Math.round(fps * .15), 0, 1));
  const card = (label: string, text: string, active: boolean, progress: number) => {
    // Flex children default to min-width:auto; a long unbreakable visual word in
    // either card used to widen the row and clip the right column. Measure against
    // the real inner-card width and explicitly allow flex shrink instead.
    const textSize = fitWrapped({text, maxWidth: width * .32, maxLines: 4, maxFontSize: Math.round(height * .039), minFontSize: Math.round(height * .022), fontFamily: fonts.display, fontWeight: 900, lineHeight: 1.04});
    return <div style={{flex: 1, minWidth: 0, overflow: 'hidden', minHeight: Math.round(height * .30), boxSizing: 'border-box', borderRadius: 24, border: `2px solid ${active ? accent : `${theme.muted}66`}`, background: active ? `${accent}18` : `${theme.surface}E8`, padding: Math.round(width * .045), opacity: progress, transform: `translateY(${Math.round((1-progress) * height * (active ? .04 : -.04))}px)`, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
      <Eyebrow text={label}/><div style={{fontFamily: fonts.display, fontWeight: 900, color: theme.text, fontSize: textSize.fontSize, lineHeight: 1.04, overflowWrap: 'normal', wordBreak: 'normal'}}>{text}</div><div style={{height: 5, borderRadius: 9, background: active ? accent : theme.muted}}/>
    </div>;
  };
  return <Stage props={props}><div style={{height:'100%', display:'flex', flexDirection:'column', justifyContent:'center', minWidth:0}}><div style={{fontFamily: fonts.display, color: theme.text, fontWeight: 900, fontSize: Math.round(height*.039)}}>{title}</div><div style={{display:'flex', width:'100%', minWidth:0, gap: Math.round(width*.03), marginTop: Math.round(height*.045)}}>{card('ПРОБЛЕМА', problem, false, left)}{card('РЕШЕНИЕ', solution, true, right)}</div></div></Stage>;
};

/** Single capability, benefit and sequence marker. */
export const FeatureSpotlight: React.FC<BaseSceneProps> = (props) => {
  const value = props as TextProps; const frame = useCurrentFrame(); const {width, height, fps} = useVideoConfig(); const {theme, fonts, accent} = useStyle(); const p = clamp(resolveMotion(props.motion ?? 'reveal', fps, 'reveal')(frame, 0, 1));
  const feature = asText(value.feature, asText(value.title, 'КОНТРОЛЬ EFFORT')); const benefit = asText(value.benefit, asText(value.text, 'Выбирайте глубину reasoning под задачу')); const index = asText(value.index, '01');
  const numberSize = Math.round(height * .23); const featureFit = fitWrapped({text: feature, maxWidth: width*.66, maxLines: 2, maxFontSize: Math.round(height*.064), minFontSize: Math.round(height*.033), fontFamily: fonts.display, fontWeight: 900, lineHeight: .96});
  return <Stage props={props}><div style={{height:'100%', display:'flex', flexDirection:'column', justifyContent:'center', position:'relative', opacity:p}}><div style={{position:'absolute', right:0, top:Math.round(height*.15), fontFamily:fonts.display, fontSize:numberSize, fontWeight:900, color:`${accent}18`, lineHeight:1}}>{index}</div><Eyebrow text="FEATURE SPOTLIGHT"/><div style={{fontFamily:fonts.display, color:theme.text, fontSize:featureFit.fontSize, fontWeight:900, lineHeight:.96, marginTop:Math.round(height*.02), maxWidth:width*.66}}>{feature}</div><div style={{fontFamily:fonts.body, color:theme.muted, fontSize:Math.round(height*.027), lineHeight:1.25, maxWidth:width*.64, marginTop:Math.round(height*.03)}}>{benefit}</div><div style={{marginTop:Math.round(height*.05), width:Math.round(width*.46), height:Math.round(height*.018), borderRadius:999, background:`${theme.muted}33`, overflow:'hidden'}}><div style={{height:'100%', width:`${Math.round(45+p*50)}%`, borderRadius:999, background:accent, boxShadow:`0 0 16px ${accent}`}}/></div></div></Stage>;
};

/** Context/action/result evidence board. */
export const CaseStudyBoard: React.FC<BaseSceneProps> = (props) => {
  const value = props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const motion=resolveMotion(props.motion ?? 'reveal',fps,'reveal');
  const entries=[['КОНТЕКСТ',asText(value.context,'Команда выбирает provider')],['ДЕЙСТВИЕ',asText(value.action,'Тестирует на своём workload')],['РЕЗУЛЬТАТ',asText(value.result,'Фиксирует проверяемое решение')]];
  return <Stage props={props}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><Eyebrow text={asText(value.label,asText(value.title,'CASE STUDY'))}/><div style={{display:'flex',flexDirection:'column',gap:Math.round(height*.018),marginTop:Math.round(height*.032)}}>{entries.map(([tag,text],i)=>{const p=clamp(motion(frame-i*Math.round(fps*.12),0,1));return <div key={tag} style={{display:'flex',gap:Math.round(width*.03),alignItems:'center',border:`1px solid ${i===2?accent:`${theme.muted}55`}`,background:i===2?`${accent}14`:`${theme.surface}DD`,borderRadius:20,padding:`${Math.round(height*.018)}px ${Math.round(width*.028)}px`,opacity:p,transform:`translateX(${Math.round((1-p)*width*.06)}px)`}}><div style={{width:Math.round(height*.036),height:Math.round(height*.036),borderRadius:'50%',background:i===2?accent:theme.muted,color:theme.bg,fontFamily:fonts.display,fontWeight:900,display:'flex',alignItems:'center',justifyContent:'center',fontSize:Math.round(height*.018)}}>{i+1}</div><div><Eyebrow text={tag}/><div style={{fontFamily:fonts.display,color:theme.text,fontWeight:800,fontSize:Math.round(height*.027),lineHeight:1.1,marginTop:4}}>{text}</div></div></div>})}</div></div></Stage>;
};

/** Myth/fact education card. */
export const MythFact: React.FC<BaseSceneProps> = (props) => {
  const value=props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const m=resolveMotion(props.motion ?? 'reveal',fps,'reveal'); const myth=asText(value.myth,'Дешевле всегда хуже'); const fact=asText(value.fact,'Цена зависит от workload и caching');
  const block=(tag:string,text:string,ok:boolean,delay:number)=>{const p=clamp(m(frame-delay,0,1));const textSize=fitWrapped({text,maxWidth:width*.30,maxLines:5,maxFontSize:Math.round(height*.037),minFontSize:Math.round(height*.020),fontFamily:fonts.display,fontWeight:900,lineHeight:1.04});return <div style={{flex:1,minWidth:0,overflow:'hidden',boxSizing:'border-box',borderRadius:24,border:`2px solid ${ok?accent:'#E66A7A'}`,background:ok?`${accent}17`:'#E66A7A12',padding:Math.round(width*.04),opacity:p,transform:`translateY(${Math.round((1-p)*height*.035)}px)`}}><div style={{fontFamily:fonts.display,fontWeight:900,color:ok?accent:'#FF8895',fontSize:Math.round(height*.021),letterSpacing:2}}>{tag}</div><div style={{fontFamily:fonts.display,fontWeight:900,color:theme.text,fontSize:textSize.fontSize,lineHeight:1.04,marginTop:Math.round(height*.03),overflowWrap:'normal',wordBreak:'normal'}}>{text}</div></div>};
  return <Stage props={props}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center',minWidth:0}}><Eyebrow text={asText(value.title,'ПРОВЕРКА ТЕЗИСА')}/><div style={{display:'flex',width:'100%',minWidth:0,gap:Math.round(width*.026),marginTop:Math.round(height*.035)}}>{block('МИФ',myth,false,0)}{block('ФАКТ',fact,true,Math.round(fps*.14))}</div></div></Stage>;
};

/** Evidence-first quote with attribution. */
export const QuoteEvidence: React.FC<BaseSceneProps> = (props) => {
  const value=props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const p=clamp(resolveMotion(props.motion ?? 'reveal',fps,'reveal')(frame,0,1)); const quote=asText(value.quote,asText(value.text,'Проверяйте claim по первоисточнику.')); const source=asText(value.source,'Официальный источник'); const role=asText(value.role,'EVIDENCE'); const fit=fitWrapped({text:quote,maxWidth:width*.76,maxLines:5,maxFontSize:Math.round(height*.046),minFontSize:Math.round(height*.025),fontFamily:fonts.display,fontWeight:800,lineHeight:1.04});
  return <Stage props={props}><div style={{height:'100%',display:'flex',alignItems:'center',justifyContent:'center'}}><div style={{width:width*.84,boxSizing:'border-box',padding:Math.round(width*.055),borderRadius:28,border:`1.5px solid ${accent}88`,background:`${theme.surface}E8`,boxShadow:`0 0 40px ${accent}18`,opacity:p,transform:`translateY(${Math.round((1-p)*height*.04)}px)`}}><div style={{fontFamily:fonts.display,color:accent,fontSize:Math.round(height*.085),lineHeight:.6}}>“</div><div style={{fontFamily:fonts.display,color:theme.text,fontSize:fit.fontSize,fontWeight:800,lineHeight:1.04,marginTop:Math.round(height*.025)}}>{quote}</div><div style={{height:1,background:`${theme.muted}55`,margin:`${Math.round(height*.03)}px 0 ${Math.round(height*.018)}px`}}/><Eyebrow text={role}/><div style={{fontFamily:fonts.body,color:theme.muted,fontSize:Math.round(height*.021),marginTop:5}}>{source}</div></div></div></Stage>;
};

/** 2–4 horizontally aligned stat blocks. */
export const StatsBand: React.FC<BaseSceneProps> = (props) => {
  const value=props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const m=resolveMotion(props.motion ?? 'reveal',fps,'reveal'); const stats=asRows(value.stats).slice(0,4); const rows=stats.length?stats:[{value:'2x',label:'быстрее'},{value:'3',label:'источника'},{value:'1',label:'workflow'}];
  return <Stage props={props}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><Eyebrow text={asText(value.title,'КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ')}/><div style={{display:'flex',gap:Math.round(width*.018),marginTop:Math.round(height*.035)}}>{rows.map((row,i)=>{const p=clamp(m(frame-i*Math.round(fps*.1),0,1));const label=asText(row.label,'метрика');const stat=asText(row.value,asText(row.stat,'—'));return <div key={`${label}-${i}`} style={{flex:1,minWidth:0,borderTop:`4px solid ${i===0?accent:theme.cyan}`,paddingTop:Math.round(height*.02),opacity:p,transform:`translateY(${Math.round((1-p)*height*.025)}px)`}}><div style={{fontFamily:fonts.display,color:theme.text,fontSize:fitOneLine({text:stat,maxWidth:width*.18,fontFamily:fonts.display,maxFontSize:Math.round(height*.060),minFontSize:Math.round(height*.025)}),fontWeight:900,lineHeight:1}}>{stat}</div><div style={{fontFamily:fonts.body,color:theme.muted,fontSize:Math.round(height*.018),lineHeight:1.22,marginTop:8}}>{label}</div></div>})}</div>{asText(value.footnote)&&<div style={{fontFamily:fonts.body,color:theme.muted,fontSize:Math.round(height*.016),marginTop:Math.round(height*.035)}}>{asText(value.footnote)}</div>}</div></Stage>;
};

/** Stack of primary sources rather than unsupported logo claims. */
export const SourceStack: React.FC<BaseSceneProps> = (props) => {
  const value=props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const m=resolveMotion(props.motion ?? 'reveal',fps,'reveal'); const sources=asRows(value.sources).slice(0,4); const rows=sources.length?sources:[{title:'Official release note',url:'primary source'},{title:'Model documentation',url:'constraints'},{title:'Pricing page',url:'effective date'}];
  return <Stage props={props}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><Eyebrow text={asText(value.status,'EVIDENCE PACK')}/><div style={{fontFamily:fonts.display,color:theme.text,fontSize:Math.round(height*.041),fontWeight:900,marginTop:8}}>{asText(value.title,'ПЕРВОИСТОЧНИКИ')}</div><div style={{marginTop:Math.round(height*.035),display:'flex',flexDirection:'column',gap:Math.round(height*.014)}}>{rows.map((row,i)=>{const p=clamp(m(frame-i*Math.round(fps*.1),0,1));const title=asText(row.title,asText(row.label,'Источник'));const url=asText(row.url,asText(row.detail,'verified'));return <div key={`${title}-${i}`} style={{border:`1px solid ${i===0?accent:`${theme.muted}55`}`,borderRadius:18,background:i===0?`${accent}12`:`${theme.surface}D8`,padding:`${Math.round(height*.018)}px ${Math.round(width*.028)}px`,display:'flex',alignItems:'center',gap:Math.round(width*.024),opacity:p,transform:`translateX(${Math.round((1-p)*width*.05)}px)`}}><div style={{width:Math.round(height*.034),height:Math.round(height*.034),borderRadius:8,background:i===0?accent:theme.muted,color:theme.bg,display:'flex',alignItems:'center',justifyContent:'center',fontFamily:fonts.display,fontWeight:900,fontSize:Math.round(height*.016)}}>{i+1}</div><div style={{minWidth:0,flex:1}}><div style={{fontFamily:fonts.display,color:theme.text,fontWeight:800,fontSize:Math.round(height*.024),whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{title}</div><div style={{fontFamily:fonts.body,color:theme.muted,fontSize:Math.round(height*.016),marginTop:4,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{url}</div></div><div style={{color:i===0?accent:theme.muted,fontFamily:fonts.display,fontSize:Math.round(height*.015),fontWeight:900}}>✓</div></div>})}</div></div></Stage>;
};

/** Countdown / release-window ring with a static readable figure. */
export const CountdownRing: React.FC<BaseSceneProps> = (props) => {
  const value=props as TextProps; const frame=useCurrentFrame(); const {width,height,fps}=useVideoConfig(); const {theme,fonts,accent}=useStyle(); const p=clamp(resolveMotion(props.motion ?? 'reveal',fps,'reveal')(frame,0,1)); const label=asText(value.label,asText(value.title,'ДО ИЗМЕНЕНИЯ')); const display=asText(value.value,'16 AUG'); const caption=asText(value.caption,asText(value.text,'Проверьте дату и условия')); const fraction=typeof value.progress==='number'?clamp(value.progress):.72; const size=Math.round(Math.min(width,height)*.40); const stroke=Math.round(size*.055); const circumference=2*Math.PI*((size-stroke)/2);
  return <Stage props={props}><div style={{height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',opacity:p}}><Eyebrow text={label}/><div style={{width:size,height:size,position:'relative',marginTop:Math.round(height*.035)}}><svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{transform:'rotate(-90deg)'}}><circle cx={size/2} cy={size/2} r={(size-stroke)/2} fill="none" stroke={`${theme.muted}33`} strokeWidth={stroke}/><circle cx={size/2} cy={size/2} r={(size-stroke)/2} fill="none" stroke={accent} strokeLinecap="round" strokeWidth={stroke} strokeDasharray={circumference} strokeDashoffset={circumference*(1-fraction)} /></svg><div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',padding:size*.14,textAlign:'center',fontFamily:fonts.display,color:theme.text,fontWeight:900,fontSize:fitOneLine({text:display,maxWidth:size*.64,fontFamily:fonts.display,maxFontSize:Math.round(height*.051),minFontSize:Math.round(height*.024)})}}>{display}</div></div><div style={{fontFamily:fonts.body,color:theme.muted,fontWeight:650,fontSize:Math.round(height*.022),lineHeight:1.25,textAlign:'center',maxWidth:width*.68,marginTop:Math.round(height*.03)}}>{caption}</div></div></Stage>;
};
