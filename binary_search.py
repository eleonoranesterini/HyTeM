#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import syntax_eval as se
import itertools
import random
# import data_collection as dc
import math
# import time
# import tree

class Interval:

      def __init__(self, bounds, monotonicity):
          
        self.bounds = bounds #[a,b] a,b delimit the bounds of the interval 
        self.monotonicity = monotonicity # '+' if increasing , '-' if decreasing 
 

def  select_parameters(box, numb_par, p_formula, numb_attempt):   
    
     # least likely to be satisfied
     if numb_attempt ==0: 
         param =[]
         for i in range(numb_par):
             if box.monotonicity[i] == '+': param.append(box.bounds[i][0])
             elif  box.monotonicity[i] == '-': param.append(box.bounds[i][1])
         
     # most likely to be satisfied
     elif numb_attempt ==1: 
         param =[]
         for i in range(numb_par):
             if box.monotonicity[i] == '+': param.append(box.bounds[i][1])
             elif  box.monotonicity[i] == '-': param.append(box.bounds[i][0])
         
     # mid-point
     elif numb_attempt ==2: param = [ sum(box.bounds[i])/2 for i in range(numb_par) ]
     
     index_mon = 0
     for i in range(10):
         #If timing parameter
         if f'[epsilon{i}-' in p_formula or f'epsilon{i}-]' in p_formula or \
         f'[ epsilon{i}-' in p_formula or f'epsilon{i}- ]' in p_formula: 
             if box.monotonicity[index_mon] == '+': param[index_mon] = int(param[index_mon]) 
             else: param[index_mon] = int(param[index_mon]) + 1
             index_mon +=1
             
     return param
         
     
     
def instantiate_formula(p_formula, parameter):
    
    ''' The function replaces the parameter symbols in the parametric formula
    with a concrete formula using the given parameter'''     
    
    formula = p_formula
    
    index_mon = 0
    for i in range(10): 
        if f'epsilon{i}-' in formula:
            formula = formula.replace(f'epsilon{i}-',f'{str(parameter[index_mon])}')
            index_mon +=1
            
    return formula


def check_inclusion(L, bounds): #between L and bound
    
    '''The function returns True if bounds is included in one box in L_sat or L_vio'''
    
    for box in L: #lop over boxes in L_sat
        for i,coordinate in enumerate(bounds): #Loop over parameter symbols 
            if ( box.bounds[i][0] > coordinate[0]) or (coordinate[1]>box.bounds[i][1]): #not included
                break
            if i == len(bounds)-1: return True
    return False

def check_belonging(L, param): #check whether param belongs to L
    
    '''The function returns True if bounds is included in one box in L_sat or L_vio'''
    
    for box in L: #lop over boxes in L_sat
        for i,coordinate in enumerate(param): #Loop over parameter symbols 
            if ( box.bounds[i][0] > coordinate) or (coordinate>box.bounds[i][1]): #not included
                break
            if i == len(param)-1: return True
    return False

def reduce_list(L):
    
    '''The function reduces the list L, eliminating boxes included in each other'''
    
    L_new = []
    
    for i, box1 in enumerate(L): #loop over boxes in L
        flag = False #box1 not included
        for j, box2 in enumerate(L):
            if i !=j and flag == False:
                for i_par,coordinate in enumerate(box2.bounds): #Loop over parameter symbols 
                    if ( box1.bounds[i_par][0] < coordinate[0]) or (coordinate[1] < box1.bounds[i_par][1]): #not included
                        break
                    if i_par == len(box2.bounds)-1: flag = True
                
        if flag == False:  L_new.append(box1)       
    return L_new

def BinarySearch(quantifiers, p_formula, traces, L_sat, L_vio, L_unk, par_bounds):
    
    '''
    
    INPUTS:
              
        - (quantifiers, p_formula) : (Parametric) hyperproperty for which we want to learn the parameters;
        - traces : set of data
        - L_sat, L_vio, L_unk: lists of (respectively) satisfied, violated, unkown hyperboxes
        - par_bounds: list of pair of parameter values that determine the parameter space
                            
    OUTPUTS:
            
        - L_sat, L_vio, L_unk updated              
    
    '''
    
    numb_par = len(L_unk[0].bounds) #number of parameters

    L_new_unk = []
    
    #Evaluate each hyperbox in the unknown region
    for box in L_unk:
     
      if check_inclusion(L_sat, box.bounds) == False and check_inclusion(L_vio, box.bounds)==False:
        
        bool_stop = False
        # First check whether the least likely to be satisfied is satisfied -> infer satisfaction of the whole region
        numb_attempt = 0 
        param = select_parameters(box, numb_par, p_formula, numb_attempt)
        
        #Check whether already in L_sat or in L_vio 
        if check_belonging(L_sat, param): sat  = 1
        elif check_belonging(L_vio, param): sat = -1
        else: 
            #Generate the concrete formula from the parameter and the parametric formula
            formula = instantiate_formula(p_formula, param)
            
            #Evaluate the satisfaction of the current parameter 
            sat = se.efficient_monitoring(traces, formula, quantifiers,True, None, False, None, None)#bool_temporal_operators=True
            
        #If satisfied
        if sat >= 0: 
            
            #The whole region is added to L_sat
            bounds = [] 
            for i in range(numb_par):
                if box.monotonicity[i] == '+': #increasing
                    bounds.append([box.bounds[i][0], par_bounds[i][1]])
                elif box.monotonicity[i] == '-': #decreasing
                    bounds.append([par_bounds[i][0] , box.bounds[i][1]])
            
            added_box = Interval(bounds, box.monotonicity)
            L_sat.append(added_box)
            bool_stop = True
            
        
        if not bool_stop:
            # Second attempt: check whether the most likely to be satisfied is violated -> infer violation of the whole region
            numb_attempt = 1
            
            param = select_parameters(box, numb_par, p_formula, numb_attempt)
            
            #Check whether already in L_sat or in L_vio 
            if check_belonging(L_sat, param): sat  = 1
            elif check_belonging(L_vio, param): sat = -1
            else:
                
                #Generate the concrete formula from the parameter and the parametric formula
                formula = instantiate_formula(p_formula, param)
                
                #Evaluate the satisfaction of the current parameter 
                sat = se.efficient_monitoring(traces, formula, quantifiers,True, None, False, None, None)#bool_temporal_operators=True
            
            #If violated
            if sat< 0: 
                    
                #The whole region is added to L_vio
                bounds = [] 
                for i in range(numb_par):
                    if box.monotonicity[i] == '+': #increasing
                        bounds.append([par_bounds[i][0] , box.bounds[i][1]])
                    elif box.monotonicity[i] == '-': #decreasing
                        bounds.append([box.bounds[i][0] , par_bounds[i][1]])
                
                added_box = Interval(bounds, box.monotonicity)
                L_vio.append(added_box)
                bool_stop = True
                
        if not bool_stop :
            # Third attempt: procede with binary search
            numb_attempt = 2
            
            #Parameter on which to instantiate the formula
            #Select point in the middle of box.bounds, but for temporal parameters
            #round the value depending on the monotonicity
            param = select_parameters(box, numb_par, p_formula, numb_attempt)
            
            #Generate the concrete formula from the parameter and the parametric formula
            formula = instantiate_formula(p_formula, param)
            
            #Evaluate the satisfaction of the current parameter 
            sat = se.efficient_monitoring(traces, formula, quantifiers,True, None, False, None, None)#bool_temporal_operators=True
            
            #If satisfied
            if sat >= 0: 
                
                #One is added to L_sat, all the others goes to L_new_unk
                bounds = [] 
                for i in range(numb_par):
                    if box.monotonicity[i] == '+': #increasing
                        bounds.append([sum(box.bounds[i])/2, par_bounds[i][1]])
                    elif box.monotonicity[i] == '-': #decreasing
                        bounds.append([par_bounds[i][0] , sum(box.bounds[i])/2])
                
                added_box = Interval(bounds, box.monotonicity)
                L_sat.append(added_box)
                     
            else: #Violated
            
                bounds = []
                for i in range(numb_par):
                    if box.monotonicity[i] == '+': #increasing
                        bounds.append([par_bounds[i][0] , sum(box.bounds[i])/2])
                    elif box.monotonicity[i] == '-': #decreasing
                        bounds.append([sum(box.bounds[i])/2, par_bounds[i][1]])
                
                added_box = Interval(bounds, box.monotonicity)
                L_vio.append(added_box)
                
            # Add all other generated hyperboxes  to L_new_unk    
            q = [[0,1]] * numb_par # q = [ [0,1] , [0,1], ... , [0,1]]
            # Loop long 2^(#number of parameters):    
            for iprod_car in itertools.product(*q): #For every combination of parameters
                new_par_bound = []
                # Definition of new parameters bounds
                for i in range(numb_par): 
                        # For every parameter decide whether to take the original or the mid point 
                        if iprod_car[i]==0: coordinate = [box.bounds[i][0], sum(box.bounds[i])/2 ]
                        elif iprod_car[i]==1: coordinate = [ sum(box.bounds[i])/2 , box.bounds[i][1] ]
                        new_par_bound.append(coordinate) 
                aux = Interval(new_par_bound, box.monotonicity)
                L_new_unk.append(aux)
    
    L_sat = reduce_list(L_sat)
    L_vio = reduce_list(L_vio)
    
    # Reduce boxes in L_unk
    L_unk = []
    for box in L_new_unk:
        if check_inclusion(L_sat, box.bounds) == False and check_inclusion(L_vio, box.bounds)==False: L_unk.append(box)
            
    return L_sat, L_vio, L_unk
        
        
        
def compute_monotonic_parameters(quantifiers, p_formula, traces, threshold, par_bounds, mon):
    
    '''
    INPUTS:
        
                
        - (quantifiers, p_formula) : (Parametric) hyperproperty for which we want to learn the parameters;
        
        - traces : set of data
        
        - threshold: list of threshold dimension of the unknown space
        
        - parameters_bounds : list that defines the parameter space 
                            [[a1,b1], [a2, b2], ... , [am, bm]] being m the number of parameters
        
        - mon : list of flags that indicates the monotonicity of the parameters 
                '+' if increasing , '-' if decreasing 
       
        
        OUTPUTS:
            
        - mined_par : list of the m mined parameters  
                    
    '''
    #Inizialization
    numb_par = len(mon) #number of parameters
    
    if numb_par ==0: return []
    
    L_vio = [] # region of violated boxes
    
    #START WITH SATISFIED VALUES
    
    #'maximum in the monotonicity sense'
    max_mono = [[par_bounds[i][1] if mon[i]=='+' else  par_bounds[i][0]]+[par_bounds[i][1] if mon[i]=='+' else  par_bounds[i][0]] for i in range(numb_par)]
    L_sat = [Interval(max_mono, mon)] # region of satisfied boxes
    L_unk = [Interval(par_bounds, mon)] # region of unkown boxes
    
    total_area = math.prod([abs(par_bounds[i][1]-par_bounds[i][0]) for i in range(len(par_bounds)) ])
    
    numb_it = 0 #Counts the number of iterations
    max_it = 10 #Maximum number of iterations
    max_it_no_improvements = 5 #Maximum number of iterations with L_sat that remains empty
    
    while True: #Loop to compute the region
        
        numb_it += 1
        
        #Updates of the regions
        L_sat, L_vio, L_unk = BinarySearch(quantifiers, p_formula, traces, 
                                           L_sat, L_vio, L_unk, par_bounds)
        
        #Compute the current uncertanty on each dimension
        #as the sum of the length of the intervals in the unknown region
        uncovered_area = 0
        
        for box in L_unk:
            aux = 1
            for i in range(numb_par): aux *= abs(box.bounds[i][1]-box.bounds[i][0])
            uncovered_area += aux
            # if covered_area > (total_area - threshold): break
        print('uncovered', uncovered_area, 'threshold', threshold)    
        #Check the stopping conditiong
        if uncovered_area < threshold and len(L_sat) > 0: 
            # print('Exit loop with satisfied region')
            break #satisfied approximation
        if numb_it > max_it: break #run out of iterations
        if numb_it > max_it_no_improvements and len(L_sat) == 0 : 
            print('Exit loop without satisfied region')
            break #run out of iterations with no improvement
            
    if len(L_sat) > 0:
        
        ##Consider only the boxes in the approximated Pareto
        pareto = [] #list of points in the Pareto front 
        
        ## !!! Can be improved
        for current_box in L_sat:
            #minimum point in the box depending on monotonicity :
            #minimum if increasing, maximum if decreasing
            current_min = [ current_box.bounds[i][0] if current_box.monotonicity[i]=='+' else  current_box.bounds[i][1]
                           for i in range(numb_par)]
            for j, other_boxes in enumerate(L_sat): 
                other_boxes_min = [ other_boxes.bounds[i][0] if other_boxes.monotonicity[i]=='+' else  other_boxes.bounds[i][1]
                           for i in range(numb_par)]
                
                if current_min > other_boxes_min: break #if it not on the pareto
                if j == len(L_sat)-1: pareto.append(current_box)
                
                
        #Sample one point on the approximated Pareto
        sampled_box = random.sample(pareto,1)[0]
        
        # monotonicity-minimum in the sampled box on the pareto
        mined_parameter = [sampled_box.bounds[i][0] if sampled_box.monotonicity[i]=='+' else  sampled_box.bounds[i][1]
                           for i in range(numb_par)]
        
    # If no satisfied hyperboxes have been found, 
    # then just use the 'monotonicity maximum' in the given par_bounds  
    else: mined_parameter = [par_bounds[i][1] if mon[i]=='+' else  par_bounds.bounds[i][0]
                           for i in range(numb_par)]
    
    return  mined_parameter
    


def check_monotonicity_singleparameter(par, indices_param, nodes):
    '''
    The function checks the monotonicity of a formula w.r.t. a given parameter.
            mono = +1 (increasing), -1 (decreasing), 'undef' otherwise.
     
        INPUTS:
            -f'epsilon{par}-' is the parameter symbol to evaluate
            - indices_param is a list with the indices of the nodes that contain f'epsilon{par}-'
            - nodes: nodes that define the formula
    '''
    
    
    #Check whether the parameter is a timing parameter
    if f'[epsilon{par}-' in nodes[indices_param[0]].data or f'epsilon{par}-]' in nodes[indices_param[0]].data: 
       
        indices_param =[] 
       
        # TIMING parameter --> all the predicates have 'undef' polarity
        #Assign 'undef' polarity to all other predicates
        for index, node in enumerate(nodes):
            if ('not' not in node.data and 'always' not in node.data and 'eventually' not in node.data\
                  and 'until' not in node.data and 'or' not in node.data and 'and' not in node.data\
                  and 'implies' not in node.data) and node.polarity is None: 
                        node.polarity = 'undef'
                        indices_param.append(index)
                        
      
        #Loop to find the polarity of the formula or a 'mixed' polarity               
        while True:
            
            #Polarity of the whole formula
            if nodes[0].polarity is not None: return nodes[0].polarity
            
            new_indices_param = []
            
            for i in indices_param:
                
                #Unary NON TEMPORAL operator
                if 'not' in nodes[i].parent.data:
                    nodes[i].parent.polarity =  change_polarity_magnitude_unary(nodes[i].parent.data, nodes[i].polarity)
                    new_i = nodes.index(nodes[i].parent)
                    new_indices_param.append(new_i) #index of the parent to be studied in the next iteration
                 
                #Unary TEMPORAL operator
                elif 'always' in nodes[i].parent.data or 'eventually' in nodes[i].parent.data:
                    nodes[i].parent.polarity =  change_polarity_temporal_unary(nodes[i].parent.data, nodes[i].polarity, par)
                    #Exit
                    if nodes[i].parent.polarity == 'mixed': return 'mixed'
                    new_i = nodes.index(nodes[i].parent)
                    new_indices_param.append(new_i) #index of the parent to be studied in the next iteration
               
                #Binary NON TEMPORAL operators
                elif  'and' in nodes[i].parent.data \
                  or 'or' in nodes[i].parent.data or 'implies' in nodes[i].parent.data:
                        #If both children's polarity has been computed:
                        if nodes[i].parent.rightchild.polarity is not None \
                        and  nodes[i].parent.leftchild.polarity is not None\
                        and nodes[i].parent.polarity is None:
                           
                            nodes[i].parent.polarity = change_polarity_binary\
                                (nodes[i].parent.data, [nodes[i].parent.leftchild.polarity, nodes[i].parent.rightchild.polarity])
                            #Exit
                            if nodes[i].parent.polarity == 'mixed': return 'mixed'
                            new_i = nodes.index(nodes[i].parent)
                            new_indices_param.append(new_i) #index of the parent to be studied in the next iteration
                
                #Binary TEMPORAL OPERATOR
                elif 'until' in nodes[i].parent.data:
                      #If both children's polarity has been computed:
                        if nodes[i].parent.rightchild.polarity is not None \
                        and  nodes[i].parent.leftchild.polarity is not None\
                        and nodes[i].parent.polarity is None:
                            
                            nodes[i].parent.polarity = change_polarity_temporal_until(nodes[i].parent.data, \
                                [nodes[i].parent.leftchild.polarity, nodes[i].parent.rightchild.polarity], par)
                            
                            if nodes[i].parent.polarity == 'mixed': return 'mixed'
                            new_i = nodes.index(nodes[i].parent)
                            new_indices_param.append(new_i)
                
            indices_param = new_indices_param.copy()  
       
       
    
    #MAGNITUDE PARAMETER 
    # -> all the nodes in indices_param are predicates
    else:
        
        #Assign the polarity to all the nodes with the parameter in the predicate
        for i in indices_param:
            
            if f'epsilon{par}- >=' in nodes[i].data or f'epsilon{par}->=' in nodes[i].data \
                or f'epsilon{par}- >' in nodes[i].data or f'epsilon{par}->' in nodes[i].data \
                or f'< epsilon{par}-' in nodes[i].data or f'<epsilon{par}-' in nodes[i].data \
                or f'<= epsilon{par}-' in nodes[i].data or f'<=epsilon{par}-' in nodes[i].data:
                    nodes[i].polarity = '+'
                    
            elif   f'epsilon{par}- <=' in nodes[i].data or f'epsilon{par}-<=' in nodes[i].data \
                or f'epsilon{par}- <' in nodes[i].data or f'epsilon{par}-<' in nodes[i].data \
                or f'> epsilon{par}-' in nodes[i].data or f'>epsilon{par}-' in nodes[i].data \
                or f'>= epsilon{par}-' in nodes[i].data or f'>=epsilon{par}-' in nodes[i].data:
                    nodes[i].polarity = '-'
                    
        #Assign 'undef' polarity to all other predicates (those not having the parameter)
        for index, node in enumerate(nodes):
            if ('not' not in node.data and 'always' not in node.data and 'eventually' not in node.data\
                  and 'until' not in node.data and 'or' not in node.data and 'and' not in node.data\
                  and 'implies' not in node.data) and node.polarity is None: 
                        node.polarity = 'undef'
                        indices_param.append(index)
                
                
        while True:
            
            #Polarity of the whole formula
            if nodes[0].polarity is not None: return nodes[0].polarity
            
            new_indices_param = []
            
            for i in indices_param:
                
                #Unary operator
                if 'not' in nodes[i].parent.data or 'always' in nodes[i].parent.data or 'eventually' in nodes[i].parent.data:
                    nodes[i].parent.polarity =  change_polarity_magnitude_unary(nodes[i].parent.data, nodes[i].polarity)
                    new_i = nodes.index(nodes[i].parent)
                    new_indices_param.append(new_i) #index of the parent to be studied in the next iteration
                    
                #Binary operators
                elif 'until' in nodes[i].parent.data or 'and' in nodes[i].parent.data \
                  or 'or' in nodes[i].parent.data or 'implies' in nodes[i].parent.data:
                        #If both children's polarity has been computed:
                        if nodes[i].parent.rightchild.polarity is not None \
                        and  nodes[i].parent.leftchild.polarity is not None\
                        and nodes[i].parent.polarity is None:
                           
                            nodes[i].parent.polarity = change_polarity_binary\
                                (nodes[i].parent.data, [nodes[i].parent.leftchild.polarity, nodes[i].parent.rightchild.polarity])
                            
                            if nodes[i].parent.polarity == 'mixed': return 'mixed'
                            new_i = nodes.index(nodes[i].parent)
                            new_indices_param.append(new_i) #index of the parent to be studied in the next iteration
                
            indices_param = new_indices_param.copy()                
                        
                        
                    
def change_polarity_temporal_unary(operator, pol, par):

    if  f'always[epsilon{par}-' in operator or \
          ('eventually' in operator and f'epsilon{par}-]' in operator):
             
                  if pol == '+' or pol == 'undef' : return '+'
                  else: return 'mixed'
                 
           
    elif f'eventually[epsilon{par}-' in operator or \
                ('always' in operator and f'epsilon{par}-]' in operator):
               
                if pol == '-' or pol == 'undef' : return '-'
                else: return 'mixed'    
                        
    else: return pol        
    
    
        
def change_polarity_magnitude_unary(operator, pol):
    
    if  'not' in operator:
        if pol == '+': return '-'
        elif pol  == '-': return '+'
        else: return pol
        
    elif 'always' in operator or 'eventually' in operator: return pol
    
    #None of the operator--> it is a predicate --> return
    else: 
        print(f'Operator not recognized:{operator}')
        return 'undef' #undefined
    
def change_polarity_binary(operator, pol):
    
    if  'implies' in operator:
        pol[0] = change_polarity_magnitude_unary('not', pol[0])

    if (pol[0]== '+' and pol[1]== '+') or (pol[0]== 'undef' and pol[1]== '+') or (pol[0]== '+' and pol[1]== 'undef'):
        return '+'
    
    elif (pol[0]== '-' and pol[1]== '-') or (pol[0]== 'undef' and pol[1]== '-') or (pol[0]== '-' and pol[1]== 'undef'):
        return '-'
    
    elif (pol[0] == 'undef' and pol[1] == 'undef') : return 'undef'
    
    else: return 'mixed'
    
def change_polarity_temporal_until(operator, pol, par):
    
    partial = change_polarity_binary('and', pol)

    if ('until' in operator and f'epsilon{par}-]' in operator): 
        
        if partial == '+' or partial == 'undef': return '+' 
        elif partial == '-' or partial == 'mixed': return 'mixed'
                          
    elif f'until[epsilon{par}-' in operator : 
       
         if partial == '-' or partial == 'undef': return '-' 
         elif partial == '+' or partial == 'mixed': return 'mixed'
        
       
    else: return partial
    

def check_monotonicity(nodes):
    
    '''External function that calls the function checking the monotonicity of each parameter.'''
    
    vector_mono = [ ]
    
    for i in range(100): #Let us assume there are at most 100 different parameters
        
        indices_param = []
        
        for index_node, node in enumerate(nodes): 
            if f'epsilon{i}-' in node.data: indices_param.append(index_node)
        
        if len(indices_param) != 0:# no more parameters
            
            mono = check_monotonicity_singleparameter(i, indices_param, nodes)
            
            for node in nodes: node.polarity = None #Eliminate polarity of other parameters (for next runs)
            
            if mono == 'mixed' or mono == 'undef': return False #at least one parameter is non-monotonic
            
            vector_mono.append(mono)
    
    return vector_mono

