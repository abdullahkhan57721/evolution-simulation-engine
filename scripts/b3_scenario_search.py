"""Run focused B3 viability-control experiments on current main.

Temporary analysis instrumentation only. Speed is the only standing variation;
max_intake_rate=8 is a shared background value for both variants.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
import attrs
from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch, UniformResourcePlacement
from evo_engine.engine import Simulation
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED
from evo_engine.presets.reference_ecology.config import ReferenceEcologyConfig
from evo_engine.presets.reference_ecology.genetics import build_balanced_reference_trait_world
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.world import WorldState

LOW_SPEED=1
HIGH_SPEED=4
SEEDS=(11,23,37,41,59,73,89,101)
MAX_STEPS=50

class Recorder:
    def __init__(self)->None:
        self.speed_by_id:dict[int,int]={}
        self.energy_by_step:dict[int,dict[int,int]]={}
    def should_observe(self, world_state:WorldState, *, step_index:int)->bool:
        del world_state,step_index
        return True
    def observe(self, world_state:WorldState, *, step_index:int)->None:
        energies={}
        for oid,org in world_state.organisms.items():
            self.speed_by_id[oid]=org.genetic_phenotype.int_value(MAX_SPEED)
            energies[oid]=org.energy
        self.energy_by_step[step_index]=energies

def patch(radius:int)->PatchyResourcePlacement:
    return PatchyResourcePlacement(patches=(ResourcePatch(center_x=2,center_y=5,radius=radius),ResourcePatch(center_x=9,center_y=5,radius=radius)))

def envs()->dict[str,tuple[int,object]]:
    return {
        'uniform_d16':(16,UniformResourcePlacement()),
        'patch_r1_d16':(16,patch(1)),
        'uniform_d32':(32,UniformResourcePlacement()),
        'patch_r1_d32':(32,patch(1)),
        'patch_r2_d32':(32,patch(2)),
    }

def config(seed:int,deposits:int,placement:object)->ReferenceEcologyConfig:
    base=ReferenceEcologyConfig()
    return attrs.evolve(base,initial_population=20,initial_energy=30,max_steps=MAX_STEPS,seed=seed,mutation_probability_ppm=0,resource_generation_amount=6,resource_deposits_per_step=deposits,resource_placement_model=placement,mating_radius=3,traits=attrs.evolve(base.traits,max_intake_rate=8,attack_strength=0,defense=1))

def dist(v:list[int])->dict[str,float|int|None]:
    return {'count':len(v),'mean':sum(v)/len(v) if v else None,'total':sum(v)}

def run_one(label:str,seed:int,deposits:int,placement:object)->dict[str,Any]:
    rec=Recorder(); cfg=config(seed,deposits,placement)
    eco=build_reference_ecology(cfg,additional_observers=(rec,))
    arch=eco.simulation.context.require(GENETIC_ARCHITECTURE)
    world=build_balanced_reference_trait_world(arch,trait_name=MAX_SPEED,variant_values=(LOW_SPEED,HIGH_SPEED),config=cfg)
    sim=Simulation(initial_domain_state=world,seed=seed,context=eco.simulation.context)
    eco.engine.run(sim)
    gh=[]
    for obs in eco.genetic_recorder.observations:
        locus=obs.locus(MAX_SPEED)
        gh.append({'step':obs.step_index,'population':obs.population_size,'high_allele_frequency':locus.allele_frequency(HIGH_SPEED),'genotypes':[{'alleles':list(x.allele_values),'count':x.count,'frequency':x.frequency} for x in locus.genotypes]})
    ph=[]
    for obs in eco.recorder.observations:
        ss=next(x for x in obs.traits if x.trait_name==MAX_SPEED)
        ph.append({'step':obs.step_index,'population':obs.population_size,'resources':obs.total_resources,'mean_energy':obs.energy.mean,'mean_speed':ss.summary.mean,'speed_counts':[list(x) for x in ss.value_counts]})
    consumption={1:0,4:0}; targeted={1:0,4:0}; examples={1:None,4:None}; cons_step={}
    for a in eco.event_recorder.events:
        e=a.event; oid=getattr(e,'organism_id',None)
        if a.process_name=='ResourceConsumption' and type(oid) is int:
            amount=getattr(e,'amount',0)
            if type(amount) is int: cons_step[(a.event_step_index+1,oid)]=amount
    reproduction=[]
    for a in eco.event_recorder.events:
        e=a.event; oid=getattr(e,'organism_id',None)
        if type(oid) is int:
            speed=rec.speed_by_id.get(oid)
            if speed in (1,4):
                if a.process_name=='ResourceConsumption':
                    amount=getattr(e,'amount',0)
                    if type(amount) is int: consumption[speed]+=amount
                elif a.process_name=='Movement' and getattr(e,'target_x',None) is not None:
                    targeted[speed]+=1
                    if examples[speed] is None:
                        dx=getattr(e,'dx',0);dy=getattr(e,'dy',0);nx=getattr(e,'new_x',None);ny=getattr(e,'new_y',None);completed=a.event_step_index+1
                        examples[speed]={'completed_step':completed,'organism_id':oid,'speed':speed,'start':[None if nx is None else nx-dx,None if ny is None else ny-dy],'end':[nx,ny],'target':[getattr(e,'target_x',None),getattr(e,'target_y',None)],'movement_energy_cost':getattr(e,'energy_cost',0),'resource_consumed_same_step':cons_step.get((completed,oid),0),'energy_before_step':rec.energy_by_step.get(completed-1,{}).get(oid),'energy_after_step':rec.energy_by_step.get(completed,{}).get(oid)}
        if a.process_name=='Reproduction' and len(reproduction)<20:
            reproduction.append({'event_step_index':a.event_step_index,'event_type':type(e).__name__,'event_repr':repr(e)})
    fr={1:[],4:[]}; ar={1:[],4:[]}; deaths={1:0,4:0}; causes={1:{},4:{}}
    for x in eco.pedigree_recorder.records:
        speed=rec.speed_by_id.get(x.organism_id)
        if speed not in (1,4): continue
        ar[speed].append(x.realized_reproductive_success)
        if x.is_founder: fr[speed].append(x.realized_reproductive_success)
        if not x.is_alive:
            deaths[speed]+=1; c=x.death_cause or 'unknown'; causes[speed][c]=causes[speed].get(c,0)+1
    extinct=next((x['step'] for x in ph if x['population']==0),None)
    last=next((x for x in reversed(gh) if x['population']>0),gh[0])
    return {'label':label,'seed':seed,'final_population':ph[-1]['population'],'extinction_step':extinct,'last_nonzero_step':last['step'],'last_nonzero_high_allele_frequency':last['high_allele_frequency'],'genetic_history':gh,'population_history':ph,'mechanism':{'consumption':{str(k):v for k,v in consumption.items()},'targeted_moves':{str(k):v for k,v in targeted.items()},'founder_reproductive_success':{str(k):dist(v) for k,v in fr.items()},'all_reproductive_success':{str(k):dist(v) for k,v in ar.items()},'deaths':{str(k):v for k,v in deaths.items()},'death_causes':{str(k):v for k,v in causes.items()}},'movement_examples':{str(k):v for k,v in examples.items()},'reproduction_examples':reproduction}

def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('outputs/b3-analysis/b3-scenario-search.json'));args=parser.parse_args()
    results=[]
    for label,(deposits,placement) in envs().items():
        for seed in SEEDS: results.append(run_one(label,seed,deposits,placement))
    payload={'analysis_only':True,'analysis_round':'shared_max_intake_8','focal_trait':MAX_SPEED,'low_speed':1,'high_speed':4,'seeds':list(SEEDS),'max_steps':MAX_STEPS,'founders':{'population':20,'high_allele_frequency':0.5,'mutation_probability_ppm':0,'mating_radius':3,'shared_max_intake_rate':8},'results':results}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(args.output)
if __name__=='__main__': main()
