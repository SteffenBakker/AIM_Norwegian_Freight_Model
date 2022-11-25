# -*- coding: utf-8 -*-
'''
Created on Thu Sep 22 13:19:20 2022

@author: steffejb
'''

import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import pandas as pd
import mpisppy.utils.sputils as sputils
import pyomo.environ as pyo

from Data.settings import *

class OutputData():
    
    def __init__(self,ef,base_data,instance_run,expected_value_problem):# or (self)
        
        #self.base_data = base_data
        self.instance_run = instance_run
        #self.ef = ef   #gives error when  pickling
        
        self.x_flow = None
        self.b_flow = None
        self.h_path = None

        self.y_charging =  None
        self.z_emission_violation= None
        self.total_emissions = None
        
        self.nu_node = None
        self.epsilon_edge = None
        self.upsilon_upgrade= None
        
        self.q_transp_amount = None
        self.q_max_transp_amount = None

        self.scenarios = []
        if expected_value_problem:
            self.scenarios = ['MMM']
        else:
            for scen in sputils.ef_scenarios(ef):
                self.scenarios.append(scen[0])

        self.ob_function_value = pyo.value(ef.EF_Obj)
        self.extract_model_results(base_data,ef,expected_value_problem)
        
        #self.cost_and_investment_table(base_data)
        #self.emission_results(base_data)
        #self.mode_mix_calculations(base_data)
        
    def extract_model_results(self,base_data,ef,expected_value_problem):  #currently only for extensive form
        
        self.x_flow =               pd.DataFrame(columns = ['variable','from','to','mode','route','fuel','product','time_period','weight', 'scenario'])
        self.b_flow =               pd.DataFrame(columns = ['variable','from','to','mode','route','fuel','vehicle_type','time_period','weight', 'scenario'])
        self.h_path =               pd.DataFrame(columns = ['variable','path','product','time_period','weight', 'scenario'])
        self.y_charging =           pd.DataFrame(columns = ['variable','from','to','mode','route','fuel','time_period','weight','scenario'])
        self.nu_node =               pd.DataFrame(columns = ['variable','from', 'terminal_type','mode', 'time_period', 'weight', 'scenario'])
        self.epsilon_edge =               pd.DataFrame(columns = ['variable','from','to','mode','route','time_period','weight','scenario'])
        self.upsilon_upgrade =            pd.DataFrame(columns = ['variable','from', 'to', 'mode', 'route','fuel', 'time_period', 'weight', 'scenario'])
        self.z_emission_violation = pd.DataFrame(columns = ['variable','time_period','weight','scenario'])
        self.total_emissions =      pd.DataFrame(columns = ['variable','time_period','weight','scenario'])
        self.q_transp_amount = pd.DataFrame(columns = ['variable','mode','fuel','time_period','weight','scenario'])
        self.q_max_transp_amount = pd.DataFrame(columns = ['variable','mode','fuel','weight','scenario'])
        
        scenario_names_and_models = []
        if expected_value_problem:
            scenario_names_and_models.append(('MMM',ef))
        else:
            for scen in sputils.ef_scenarios(ef):
                scenario_names_and_models.append((scen[0],scen[1]))
        for (scen_name,scen_model) in scenario_names_and_models:
            modell = scen_model

            variable = 'x_flow'
            for (i,j,m,r) in base_data.A_ARCS:
                a = (i,j,m,r)
                for f in base_data.FM_FUEL[m]:
                    for t in base_data.T_TIME_PERIODS:
                        for p in base_data.P_PRODUCTS:
                            weight = modell.x_flow[(a,f,p,t)].value
                            if weight > 0:
                                a_series = pd.Series([variable,i,j,m,r,f,p,t,weight, scen_name], index=self.x_flow.columns)
                                self.x_flow = pd.concat([self.x_flow, a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'b_flow'
            for (i,j,m,r) in base_data.A_ARCS:
                a = (i,j,m,r)
                for f in base_data.FM_FUEL[m]:
                    for t in base_data.T_TIME_PERIODS:
                        for v in base_data.VEHICLE_TYPES_M[m]:
                            weight = modell.b_flow[(a,f,v,t)].value
                            if weight > 0:
                                a_series = pd.Series([variable,i,j,m,r,f,v,t,weight, scen_name], index=self.b_flow.columns)
                                self.b_flow = pd.concat([self.b_flow, a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'h_path'
            for kk in base_data.K_PATHS:
                #k = self.K_PATH_DICT[kk]
                for t in base_data.T_TIME_PERIODS:
                    for p in base_data.P_PRODUCTS:
                        weight = modell.h_flow[(kk, p, t)].value
                        if weight > 0:
                            a_series = pd.Series([variable,kk, p, t, weight, scen_name], index=self.h_path.columns)
                            self.h_path = pd.concat([self.h_path,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'epsilon_edge'
            for t in base_data.T_TIME_PERIODS:
                for i,j,m,r in base_data.E_EDGES_RAIL:
                    e = (i,j,m,r)
                    weight = modell.epsilon_edge[(e, t)].value
                    if weight > 0:
                        a_series = pd.Series([variable,i,j,m,r, t, weight, scen_name], index=self.epsilon_edge.columns)
                        self.epsilon_edge = pd.concat([self.epsilon_edge,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'upsilon_upg'
            for t in base_data.T_TIME_PERIODS:
                for (e,f) in base_data.U_UPGRADE:
                    (i,j,m,r) = e
                    weight = modell.upsilon_upg[(i,j,m,r,f,t)].value
                    if weight > 0:
                        a_series = pd.Series([variable,i,j,m,r, f,t, weight, scen_name],index=self.upsilon_upgrade.columns)
                        self.upsilon_upgrade = pd.concat([self.upsilon_upgrade,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'nu_node'
            for t in base_data.T_TIME_PERIODS:
                for (i, m) in base_data.NM_LIST_CAP:
                    for c in base_data.TERMINAL_TYPE[m]:
                        weight = modell.nu_node[(i, c, m, t)].value
                        if weight > 0:
                            a_series = pd.Series([variable,i, c, m, t, weight, scen_name],index=self.nu_node.columns)
                            self.nu_node = pd.concat([self.nu_node,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'y_charging'
            for t in base_data.T_TIME_PERIODS:
                for (e,f) in base_data.EF_CHARGING:
                    (i,j,m,r) = e
                    weight = modell.y_charge[(i,j,m,r,f,t)].value
                    if weight > 0:
                        a_series = pd.Series([variable,i,j,m,r,f,t, weight, scen_name],index=self.y_charging.columns)
                        self.y_charging = pd.concat([self.y_charging,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'z_emission'
            for t in base_data.T_TIME_PERIODS:
                weight = modell.z_emission[t].value
                a_series = pd.Series([variable,t, weight, scen_name],index=self.z_emission_violation.columns)
                self.z_emission_violation = pd.concat([self.z_emission_violation,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'total_emissions'
            for t in base_data.T_TIME_PERIODS:
                weight5 = modell.total_emissions[t].value
                a_series2 = pd.Series([variable,t, weight5, scen_name],index=self.total_emissions.columns)
                self.total_emissions = pd.concat([self.total_emissions,a_series2.to_frame().T],axis=0, ignore_index=True)    
            variable = 'q_transp_amount'
            for m in base_data.M_MODES:
                for f in base_data.FM_FUEL[m]:
                    for t in base_data.T_TIME_PERIODS:
                        weight = modell.q_transp_amount[(m, f, t)].value
                        if weight > 0:
                            a_series = pd.Series([variable,m, f, t, weight, scen_name], index=self.q_transp_amount.columns)
                            self.q_transp_amount = pd.concat([self.q_transp_amount,a_series.to_frame().T],axis=0, ignore_index=True)
            variable = 'q_max_transp_amount'
            for m in base_data.M_MODES:
                for f in base_data.FM_FUEL[m]:
                    weight = modell.q_max_transp_amount[(m, f)].value
                    if weight > 0:
                        a_series = pd.Series([variable,m, f, weight, scen_name], index=self.q_max_transp_amount.columns)
                        self.q_max_transp_amount = pd.concat([self.q_max_transp_amount,a_series.to_frame().T],axis=0, ignore_index=True)

            self.all_variables = pd.concat([self.x_flow,self.b_flow,self.h_path,self.y_charging,self.nu_node,self.epsilon_edge,self.upsilon_upgrade,
                      self.z_emission_violation,self.total_emissions,self.q_transp_amount,self.q_max_transp_amount],ignore_index=True)
            
    
