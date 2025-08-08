"""
This file can generate topology of AlibabaHPN, Spectrum-X, DCN+.
Users can freely customize the topology according to their needs。
"""

import argparse
import warnings
import math

def Rail_Opti_SingleToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server']
    if(parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment) == 0):
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment))
    else:
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment))+1
    
    if(segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to "+str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] /  asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally "+ str(pod_num) + " pod(s)." )  

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int) (parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num']+ nv_switch_num ) # 
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num) # 
    links = (int)(parameters['psw_switch_num']/pod_num * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server']) # 
    if parameters['topology'] == 'Spectrum-X':
        file_name = "Spectrum-X_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    else:
        file_name = "Rail_Opti_SingleToR_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes)+" "+str(parameters['gpu_per_server'])+" "+str(nv_switch_num)+" "+str(switch_nodes-nv_switch_num)+" "+str(int(links))+" "+str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch) < parameters['asw_switch_num']:
                asw_switch.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                #cnt += 1
                line = str(i)+" "+str(nv_switch[ind_nv+j])+" "+str(parameters['nvlink_bw'])+" "+str(parameters['nv_latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i)+" "+str(asw_switch[group_num*asw_switch_num_per_segment+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            ind_asw = ind_asw + 1
            group_account = group_account + 1
            
            if ind_asw == asw_switch_num_per_segment:
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch: # asw - psw
                for j in psw_switch:
                    line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                    f.write(line)
                    f.write('\n')

def Rail_Opti_DualToR_SinglePlane(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server']*2
    if(parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment/2) == 0):
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))
    else:
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))+1
    
    if(segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to "+str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / (asw_switch_num_per_segment/2)):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally "+ str(pod_num) + " pod(s)." )  

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int) (parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num']+ nv_switch_num ) # 
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num) # 
    links = (int)(parameters['psw_switch_num']/pod_num * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server']) # 
    if parameters['topology'] == 'AlibabaHPN':
        file_name = "AlibabaHPN_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_DualToR_SinglePlane_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    else:
        file_name = "Rail_Opti_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_DualToR_SinglePlane_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes)+" "+str(parameters['gpu_per_server'])+" "+str(nv_switch_num)+" "+str(switch_nodes-nv_switch_num)+" "+str(int(links))+" "+str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num']/2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num']/2:
                asw_switch_2.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                #cnt += 1
                line = str(i)+" "+str(nv_switch[ind_nv+j])+" "+str(parameters['nvlink_bw'])+" "+str(parameters['nv_latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i)+" "+str(asw_switch_1[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            
            line = str(i)+" "+str(asw_switch_2[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            ind_asw = ind_asw + 1
            group_account = group_account + 1
            
            if ind_asw == int(asw_switch_num_per_segment/2):
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1: # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
        for i in asw_switch_2: # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')

def Rail_Opti_DualToR_DualPlane(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server']*2
    if(parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment/2) == 0):
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))
    else:
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))+1
    
    if(segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to "+str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / (asw_switch_num_per_segment/2)):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally "+ str(pod_num) + " pod(s)." )  

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int) (parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num']+ nv_switch_num ) # 
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num) # 
    links = (int)(parameters['psw_switch_num']/pod_num/2 * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server']) # 
    if parameters['topology'] == 'AlibabaHPN':
        file_name = "AlibabaHPN_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_DualToR_DualPlane_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    else:
        file_name = "Rail_Opti_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_DualToR_DualPlane_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes)+" "+str(parameters['gpu_per_server'])+" "+str(nv_switch_num)+" "+str(switch_nodes-nv_switch_num)+" "+str(int(links))+" "+str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch_1 = []
        psw_switch_2 = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num']/2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num']/2:
                asw_switch_2.append(i)
            elif len(psw_switch_1) < parameters['psw_switch_num']/2:
                psw_switch_1.append(i)
            elif len(psw_switch_2) < parameters['psw_switch_num']/2:
                psw_switch_2.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                #cnt += 1
                line = str(i)+" "+str(nv_switch[ind_nv+j])+" "+str(parameters['nvlink_bw'])+" "+str(parameters['nv_latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i)+" "+str(asw_switch_1[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            
            line = str(i)+" "+str(asw_switch_2[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            ind_asw = ind_asw + 1
            group_account = group_account + 1
            
            if ind_asw == int(asw_switch_num_per_segment/2):
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1: # asw - psw
            for j in psw_switch_1:
                line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
        for i in asw_switch_2: # asw - psw
            for j in psw_switch_2:
                line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')

def No_Rail_Opti_SingleToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = 1
    if(parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment) == 0):
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment))
    else:
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment))+1
    
    if(segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to "+str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] /  asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally "+ str(pod_num) + " pod(s)." )  

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int) (parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num']+ nv_switch_num ) # 
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num) # 
    links = (int)(parameters['psw_switch_num']/pod_num * parameters['asw_switch_num'] + servers * parameters['gpu_per_server']
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server']) # 
    if parameters['topology'] == 'DCN+':
        file_name = "DCN+SingleToR_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    else:
        file_name = "No_Rail_Opti_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_SingleToR_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes)+" "+str(parameters['gpu_per_server'])+" "+str(nv_switch_num)+" "+str(switch_nodes-nv_switch_num)+" "+str(int(links))+" "+str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch) < parameters['asw_switch_num']:
                asw_switch.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                #cnt += 1
                line = str(i)+" "+str(nv_switch[ind_nv+j])+" "+str(parameters['nvlink_bw'])+" "+str(parameters['nv_latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i)+" "+str(asw_switch[group_num*asw_switch_num_per_segment+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            group_account = group_account + 1
            
            if group_account == nodes_per_asw:
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch: # asw - psw
                for j in psw_switch:
                    line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                    f.write(line)
                    f.write('\n')

def No_Rail_Opti_DualToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = 2
    if(parameters['gpu'] % (nodes_per_asw * (asw_switch_num_per_segment/2)) == 0):
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))
    else:
        segment_num = (int)(parameters['gpu']/ (nodes_per_asw * asw_switch_num_per_segment/2))+1
    if(segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to "+str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] /  asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally "+ str(pod_num) + " pod(s)." )  

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int) (parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num']+ nv_switch_num ) # 
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num) # 
    links = (int)(parameters['psw_switch_num']/pod_num * parameters['asw_switch_num'] + servers * parameters['gpu_per_server']*2
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server']) # 
    if parameters['topology'] == 'DCN+':
        file_name = "DCN+DualToR_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    else:
        file_name = "No_Rail_Opti_"+str(parameters['gpu'])+"g_"+str(parameters['gpu_per_server'])+"gps_DualToR_"+parameters['bandwidth']+"_"+parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes)+" "+str(parameters['gpu_per_server'])+" "+str(nv_switch_num)+" "+str(switch_nodes-nv_switch_num)+" "+str(int(links))+" "+str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num']/2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num']/2:
                asw_switch_2.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                #cnt += 1
                line = str(i)+" "+str(nv_switch[ind_nv+j])+" "+str(parameters['nvlink_bw'])+" "+str(parameters['nv_latency'])+" "+str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i)+" "+str(asw_switch_1[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            line = str(i)+" "+str(asw_switch_2[group_num*int(asw_switch_num_per_segment/2)+ind_asw])+" "+str(parameters['bandwidth'])+" "+str(parameters['latency'])+" "+str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            group_account = group_account + 1

            if group_account == nodes_per_asw:
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1: # asw - psw
                for j in psw_switch:
                    line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                    f.write(line)
                    f.write('\n')
        for i in asw_switch_2: # asw - psw
                for j in psw_switch:
                    line = str(i) + " " + str(j) +" "+ str(parameters['ap_bandwidth'])+" " +str(parameters['latency'])+" "+str(parameters['error_rate'])
                    f.write(line)
                    f.write('\n')



'''
A UB Mesh topology function, using NVSwitches/Nvlink for on board GPU to GPU
connectivity and direct UB links for cross board mesh + GPU to HRS + HRS to HRS (1D FM B)
'''
def UB_Optimized_AI_Topology(parameters):

    G    = parameters['gpu']
    G_P_S    = parameters['gpu_per_server']
    NPS  = parameters['nv_switch_per_server']
    NVBW = parameters['nvlink_bw']
    NVLT = parameters['nv_latency']
    BW  = parameters['bandwidth']
    LT = parameters['latency']
    ERR  = parameters['error_rate']
    gpu_type = parameters['gpu_type']
    variant = parameters.get('fm_variant', '1D‑FM‑B')

    
    B      = G // G_P_S             #  boards number
    NV_total = B * NPS              # total NVSwitch nodes
    HPS    = 2                      # HRS per board
    H_total  = B * HPS              # total HRS nodes
    N_all  = G + NV_total + H_total  # total nodes

    # ID ranges
    gpu_ids = range(0, G)
    nv_ids  = range(G, G + NV_total)
    hr_ids  = range(G + NV_total, N_all)

    links = []

    # On‑board GPU to NVSwitch
    for b in range(B):
        base_gpu = b * G_P_S
        base_nv  = G + b * NPS
        for g in range(base_gpu, base_gpu + G_P_S):
            for n in range(NPS):
                links.append((g, base_nv + n, NVBW, NVLT, ERR))

    # 4D rank‑matched cross‑board mesh or 2D flattening: arrange boards in sqrt(B)x sqrt(B) grid
    if variant == '4D':
        for gi in range(G_P_S):
            group = [b * G_P_S + gi for b in range(B)]
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    links.append((group[i], group[j], BW, LT, ERR))

    elif variant == '2D-FM':
        sqrtB = int(math.sqrt(B))
        assert sqrtB * sqrtB == B, "B must be a perfect square for 2D-FM"
        for r in range(sqrtB):                                                  # row-dimension meshes
            for gi in range(G_P_S):
                group = [ (r*sqrtB + c)*G_P_S + gi for c in range(sqrtB) ]
                for i in range(len(group)):
                    for j in range(i+1, len(group)):
                        links.append((group[i], group[j], BW, LT, ERR))
        
        # column dimension meshes
        for c in range(sqrtB):
            for gi in range(G_P_S):
                # here we *define* r in the comprehension
                group = [ (r*sqrtB + c)*G_P_S + gi for r in range(sqrtB) ]
                for i in range(len(group)):
                    for j in range(i+1, len(group)):
                        links.append((group[i], group[j], BW, LT, ERR))


    # GPU to HRS
    for b in range(B):
        base_gpu = b * G_P_S
        base_hr  = G + NV_total + b * HPS
        for g in range(base_gpu, base_gpu + G_P_S):
            for h in range(HPS):
                links.append((g, base_hr + h, BW, LT, ERR))


    # HRS to HRS full mesh
    hr_list = list(hr_ids)
    for i in range(len(hr_list)):
        for j in range(i+1, len(hr_list)):
            links.append((hr_list[i], hr_list[j], BW, LT, ERR))


    # file
    fname = f"UB_AI_{G}g_{G_P_S}gps_{variant}_{BW}_{gpu_type}"
    with open(fname, 'w') as f:
        f.write(f"{N_all} {G_P_S} {NV_total} {H_total} {len(links)} {gpu_type}\n")    # header: total_nodes, gpus/board, #NV, #HRS, #links, GPU_type
        f.write(" ".join(str(i) for i in range(G, N_all)) + "\n")                     # list all "switch" IDs (NVSwitch + HRS)
        for s, d, bw, lt, er in links:
            f.write(f"{s} {d} {bw} {lt} {er}\n")

    print(f"Wrote UB‑Mesh ({variant}) topology to {fname}")


'''
Varian of UB Mesh topology to use direct GPU to GPU links in a 2D flat mesh
Connectivity  is shown as GPU to GPU direct links as switches 
As SimAI’s parser ignores any link where both endpoints are hosts, so those flattening edges never get used and MaxRTT never improves
'''
def UB_2D_FM_Direct(parameters):
    G        = parameters['gpu']
    G_P_S    = parameters['gpu_per_server']
    NPS      = parameters['nv_switch_per_server']
    NVBW     = parameters['nvlink_bw']
    NVLT     = parameters['nv_latency']
    BW       = parameters['bandwidth']
    LT       = parameters['latency']
    ERR      = parameters['error_rate']
    gpu_type = parameters['gpu_type']

    B        = G // G_P_S
    NV_total = B * NPS
    HPS      = 2
    H_total  = B * HPS
    N_base   = G + NV_total + H_total

    links = []

    sqrtB = int(math.sqrt(B))
    assert sqrtB*sqrtB == B, "B must be a perfect square"
    
    for b in range(B):
        base_gpu = b * G_P_S
        base_nv  = G + b * NPS
        for g in range(base_gpu, base_gpu + G_P_S):
            for n in range(NPS):
                links.append((g, base_nv + n, NVBW, NVLT, ERR))


    for i in range(G, G + NV_total):
       for j in range(i+1, G + NV_total):
          links.append((i, j, BW, LT, ERR))

    # row
    for r in range(sqrtB):
        for gi in range(G_P_S):
            group = [(r*sqrtB + c)*G_P_S + gi for c in range(sqrtB)]
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    links.append((group[i], group[j], BW, LT, ERR))
    # column
    for c in range(sqrtB):
        for gi in range(G_P_S):
            group = [(r*sqrtB + c)*G_P_S + gi for r in range(sqrtB)]
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    links.append((group[i], group[j], BW, LT, ERR))

    # GPU to HRS 
    for b in range(B):
        base_gpu = b * G_P_S
        base_hr  = G + NV_total + b * HPS
        for g in range(base_gpu, base_gpu + G_P_S):
            for h in range(HPS):
                links.append((g, base_hr + h, BW, LT, ERR))

    #HRS to HRS full mesh
    hr_ids = list(range(G + NV_total, N_base))
    for i in range(len(hr_ids)):
        for j in range(i+1, len(hr_ids)):
            links.append((hr_ids[i], hr_ids[j], BW, LT, ERR))

    
    total_nodes    = N_base
    #total_switches = NV_total + H_total + G  #total_switches = NV_total + H_total
    total_links    = len(links)

    fname = f"UB_AI_{G}g_{G_P_S}gps_2D-FM-Direct_{BW}_{gpu_type}"
    H_adj = H_total + G

    with open(fname, 'w') as f:
        f.write(f"{total_nodes} {G_P_S} {NV_total} {H_total} {total_links} {gpu_type}\n")
        switch_ids = list(range(G, G + NV_total + H_total))
        f.write(" ".join(str(s) for s in switch_ids) + "\n")
        for s, d, bw, lt, er in links:
            f.write(f"{s} {d} {bw} {lt} {er}\n")

    print(f"Wrote UB-Mesh (2D-FM-Direct) topology to {fname}")


# fat tree topology part
def next_even(n):
    """Return the next even integer ≥ n."""
    return n if n % 2 == 0 else n + 1


def compute_min_k(hosts):
    """
    Compute the smallest even fat-tree arity k such that k^3/4 ≥ hosts.
    """
    # Solve k^3 >= 4*hosts → k >= (4*hosts)^(1/3)
    from math import ceil
    base = (4 * hosts) ** (1/3)
    return next_even(ceil(base))



def fat_tree_gpu_level(parameters):

    G = parameters['gpu']
    # dynamic arity
    k = parameters.get('fat_tree_k') or compute_min_k(G)
    pods = k
    edge_per = k // 2
    agg_per = k // 2
    core_cnt = (k // 2) ** 2

    # ID ranges start after GPU IDs
    base_sw = G
    edge_ids = list(range(base_sw, base_sw + pods * edge_per))
    agg_ids = list(range(edge_ids[-1] + 1, edge_ids[-1] + 1 + pods * agg_per))
    core_ids = list(range(agg_ids[-1] + 1, agg_ids[-1] + 1 + core_cnt))

    links = []

    # each host (GPU) to edge switch
    for i in range(G):
        sw = edge_ids[i % len(edge_ids)]
        links.append((i, sw, parameters['bandwidth'], parameters['latency'], parameters['error_rate']))

    # edge switch to agg. switches within pods
    for pod in range(pods):
        pod_edge = edge_ids[pod * edge_per:(pod + 1) * edge_per]
        pod_agg = agg_ids[pod * agg_per:(pod + 1) * agg_per]
        for e in pod_edge:
            for a in pod_agg:
                links.append((e, a, parameters['bandwidth'], parameters['latency'], parameters['error_rate']))

    # aggregate  to  core switches
    # each core switch connects to k/2 agg switches
    # and each pod has k/2 agg switches
    for ci, c in enumerate(core_ids):
        for pod in range(pods):
            a_index = pod * agg_per + (ci // (k // 2))
            links.append((c, agg_ids[a_index], parameters['bandwidth'], parameters['latency'], parameters['error_rate']))

    
    fname = f"fat_tree_gpu_{G}g_k{k}_{parameters['gpu_type']}_{parameters['bandwidth']}"
    with open(fname, 'w') as f:
        total_nodes = G + len(edge_ids) + len(agg_ids) + len(core_ids)
        total_switches = len(edge_ids) + len(agg_ids) + len(core_ids)
        total_links = len(links)
        f.write(f"{total_nodes} 1 0 {total_switches} {total_links} {parameters['gpu_type']}\n")  # as we are considering each gpu as single host.
        sw_line = ' '.join(str(sw) for sw in edge_ids + agg_ids + core_ids)
        f.write(sw_line + '\n')
        for s, d, bw, lt, er in links:
            f.write(f"{s} {d} {bw} {lt} {er}\n")
    print(f"Wrote GPU-level fat-tree (k={k}) to {fname}")



''' Server-level fat-tree with NVSwitch layer.
    Groups GPUs into servers, adds NVSwitch fabric, then builds fat-tree on NVSwitch endpoints.
'''

def fat_tree_server_level(parameters):
    
    G = parameters['gpu']
    G_P_S = parameters.get('gpu_per_server', 8)
    NPS = parameters.get('nv_switch_per_server', 1)
    servers = G // G_P_S
    nv_switch_num = (G // G_P_S) * NPS

    # dynamically compute k for fat-tree pods based on NVSwitch count
    leaf_hosts = nv_switch_num
    k = parameters.get('fat_tree_k') or compute_min_k(leaf_hosts)
    pods = k
    edge_per = k // 2
    agg_per = k // 2
    core_cnt = (k // 2) ** 2

    # assign ID ranges
    gpu_ids = list(range(0, G))
    nv_start = G
    nv_ids = list(range(nv_start, nv_start + nv_switch_num))
    base_sw = nv_start + nv_switch_num
    edge_ids = list(range(base_sw, base_sw + pods * edge_per))
    agg_ids = list(range(edge_ids[-1] + 1,
                         edge_ids[-1] + 1 + pods * agg_per))
    core_ids = list(range(agg_ids[-1] + 1,
                          agg_ids[-1] + 1 + core_cnt))

    links = []
    # 1) GPU -> NVSwitch
    for srv in range(servers):
        base_gpu = srv * G_P_S
        base_nv = nv_start + srv * NPS
        for g in range(base_gpu, base_gpu + G_P_S):
            for n in range(NPS):
                links.append((g, base_nv + n,
                              parameters['nvlink_bw'],
                              parameters['nv_latency'],
                              parameters['error_rate']))
    # 2) NVSwitch -> edge switches
    for idx, nv in enumerate(nv_ids):
        sw = edge_ids[idx % len(edge_ids)]
        links.append((nv, sw,
                      parameters['bandwidth'],
                      parameters['latency'],
                      parameters['error_rate']))
    # 3) edge <-> agg
    for pod in range(pods):
        pod_edge = edge_ids[pod * edge_per:(pod + 1) * edge_per]
        pod_agg = agg_ids[pod * agg_per:(pod + 1) * agg_per]
        for e in pod_edge:
            for a in pod_agg:
                links.append((e, a,
                              parameters['bandwidth'],
                              parameters['latency'],
                              parameters['error_rate']))
    # 4) agg <-> core
    for ci, c in enumerate(core_ids):
        for pod in range(pods):
            a_idx = pod * agg_per + (ci // (k // 2))
            links.append((c, agg_ids[a_idx],
                          parameters['bandwidth'],
                          parameters['latency'],
                          parameters['error_rate']))
            
    # 5) **GPU -> edge NIC** (one 400 Gbps port per GPU into leaf fabric)
    for g in range(G):
        sw = edge_ids[g % len(edge_ids)]
        links.append((g, sw,
                      parameters['bandwidth'],
                      parameters['latency'],
                      parameters['error_rate']))

    # write topology file
    fname = f"fat_tree_server_{G}g_{G_P_S}gps_nvs{nv_switch_num}_k{k}_{parameters['bandwidth']}_{parameters['gpu_type']}"
    with open(fname, 'w') as f:
        total_nodes = G + nv_switch_num + len(edge_ids) + len(agg_ids) + len(core_ids)
        total_switches = nv_switch_num + len(edge_ids) + len(agg_ids) + len(core_ids)
        total_links = len(links)
        # header: nodes, GPUs/server, NV switches, total switches, total links, GPU type
        f.write(f"{total_nodes} {G_P_S} {nv_switch_num} {total_switches - nv_switch_num} {total_links} {parameters['gpu_type']}\n")

        # list all switch IDs: NVSwitch + edge + agg + core
        sw_list = nv_ids + edge_ids + agg_ids + core_ids
        f.write(' '.join(str(sw) for sw in sw_list) + "\n")
        for s, d, bw, lt, er in links:
            f.write(f"{s} {d} {bw} {lt} {er}\n")
    print(f"Wrote server-level fat-tree (k={k}, NVSwitch={nv_switch_num}) to {fname}")




def main():
    parser = argparse.ArgumentParser(description='Python script for generating a topology for SimAI')

    #Whole Structure Parameters:
    parser.add_argument('-topo','--topology', type=str, default=None,help='Template for AlibabaHPN, Spectrum-X, DCN+')
    parser.add_argument('--ro', action='store_true',help='use rail-optimized structure')
    parser.add_argument('--dt',action='store_true', help='enable dual ToR, only for DCN+')
    parser.add_argument('--dp', action='store_true', help='enable dual_plane, only for AlibabaHPN')
    parser.add_argument('-g','--gpu',type=int,default=None,help='gpus num, default 32')
    parser.add_argument('-er','--error_rate',type=str,default=None,help='error_rate, default 0')
    #Intra-Host Parameters:
    parser.add_argument('-gps','--gpu_per_server',type=int,default=None,help='gpu_per_server, default 8')
    parser.add_argument('-gt','--gpu_type',type=str,default=None,help='gpu_type, default H100')
    parser.add_argument('-nsps','--nv_switch_per_server',type=int,default=None,help='nv_switch_per_server, default 1')
    parser.add_argument('-nvbw','--nvlink_bw',type=str,default=None,help='nvlink_bw, default 2880Gbps')
    parser.add_argument('-nl','--nv_latency',type=str,default=None,help='nv switch latency, default 0.000025ms')
    parser.add_argument('-l','--latency',type=str,default=None,help='nic latency, default 0.0005ms')
    #Intra-Segment Parameters:
    parser.add_argument('-bw','--bandwidth',type=str,default=None,help='nic to asw bandwidth, default 400Gbps')
    parser.add_argument('-asn','--asw_switch_num',type=int,default=None,help='asw_switch_num, default 8')
    parser.add_argument('-npa','--nics_per_aswitch',type=int,default=None,help='nnics per asw, default 64')
    #Intra-Pod Parameters:
    parser.add_argument('-psn','--psw_switch_num',type=int,default=None,help='psw_switch_num, default 64')
    parser.add_argument('-apbw','--ap_bandwidth',type=str,default=None,help='asw to psw bandwidth,default 400Gbps')   
    parser.add_argument('-app','--asw_per_psw',type=int,default=None,help='asw for psw')

    #my added lines
    # parser.add_argument('--ocs', action='store_true', help='Enable OCS-based topology generation')
    # parser.add_argument('--ocs_degree', type=int, default=4, help='Degree of OCS connectivity per GPU')
    ##############

    parser.add_argument('--ub_intra_bw', type=str, default='600Gbps', help='Intra-board GPU-GPU bandwidth')
    parser.add_argument('--ub_intra_lat', type=str, default='0.000025ms', help='Intra-board GPU-GPU latency')
    parser.add_argument('--fm_variant', choices=['1D-FM-B','4D', '2D-FM', '2D-FM-Direct'], default='1D-FM-B', help='Which fat-mesh variant to generate (1D-FM-B, 4D or 2D-FM / 2D-FM-Direct).')


    parser.add_argument('--fat_tree', dest='fat_tree', choices=['gpu','server'],
                        help='Use GPU-level or server-level fat-tree')
    parser.add_argument('--fat_tree_k', dest='fat_tree_k', type=int,
                        help='Explicit fat-tree arity k')


    args = parser.parse_args()

    default_parameters = []
    parameters = analysis_template(args, default_parameters)
    parameters['fm_variant'] = args.fm_variant

    # if args.ocs:
    #     parameters = analysis_template(args, default_parameters)
    #     OCS_Topology(parameters)
    #     return

    if args.topology == 'fat_tree':
        if not args.fat_tree:
            raise ValueError('Please specify --fat_tree gpu or --fat_tree server')
        if args.fat_tree == 'gpu':
            fat_tree_gpu_level(parameters)
        else:
            fat_tree_server_level(parameters)
        return


    if args.topology == 'UB':
        if parameters['fm_variant'] == '2D-FM-Direct':
            UB_2D_FM_Direct(parameters)
        else:
            UB_Optimized_AI_Topology(parameters)
        return

    if not parameters['rail_optimized']:
        if parameters['dual_plane']:
            raise ValueError("Sorry, None Rail-Optimized Structure doesn't support Dual Plane")
        if parameters['dual_ToR']:
            No_Rail_Opti_DualToR(parameters)
        else:
            No_Rail_Opti_SingleToR(parameters)
    else:
        if parameters['dual_ToR']:
            if parameters['dual_plane']:
                Rail_Opti_DualToR_DualPlane(parameters)
            else:
                Rail_Opti_DualToR_SinglePlane(parameters)
        else:
            if parameters['dual_plane']:
                raise ValueError("Sorry, Rail-optimized Single-ToR Structure doesn't support Dual Plane")
            Rail_Opti_SingleToR(parameters)


def analysis_template(args, default_parameters):
    # Basic default parameters
    default_parameters = {'rail_optimized': True, 'dual_ToR': False, 'dual_plane': False, 'gpu': 32, 'error_rate':0,
                          'gpu_per_server': 8, 'gpu_type': 'H100', 'nv_switch_per_server': 1, 
                          'nvlink_bw': '2880Gbps','nv_latency': '0.000025ms', 'latency': '0.0005ms',
                          'bandwidth': '400Gbps', 'asw_switch_num': 8,  'nics_per_aswitch': 64,
                          'psw_switch_num': 64, 'ap_bandwidth': "400Gbps", 'asw_per_psw' : 64}
    parameters = {}
    parameters['topology'] = args.topology
    parameters['rail_optimized'] = bool(args.ro)
    parameters['dual_ToR'] = bool(args.dt)
    parameters['dual_plane'] = bool(args.dp)
    parameters['fm_variant'] = args.fm_variant

    
    if parameters['topology'] == 'Spectrum-X':
        default_parameters.update({
            'gpu': 4096
        })
        parameters.update({
            'rail_optimized': True, 
            'dual_ToR': False, 
            'dual_plane': False,
        })
    elif parameters['topology'] == 'AlibabaHPN':
        default_parameters.update({
            'gpu': 15360, 
            'bandwidth': '200Gbps', 
            'asw_switch_num': 240, 
            'nics_per_aswitch': 128, 
            'psw_switch_num': 120,
            'asw_per_psw':240
        })
        parameters.update({
            'rail_optimized': True, 
            'dual_ToR': True, 
            'dual_plane': False,
            
        })
        if args.dp:
            default_parameters.update({
                'asw_per_psw':120
            })
            parameters.update({
                'rail_optimized': True, 
                'dual_ToR': True, 
                'dual_plane': True, 
            })
    elif parameters['topology'] == 'DCN+':
        default_parameters.update({
            'gpu': 512, 
            'asw_switch_num': 8, 
            'asw_per_psw':8,
            'psw_switch_num': 8
        })
        parameters.update({
            'rail_optimized': False, 
            'dual_ToR': False, 
            'dual_plane': False, 
        })
        if args.dt:
            default_parameters.update({
                'bandwidth': '200Gbps',
                'nics_per_aswitch': 128, 
            })
            parameters.update({
                'rail_optimized': False, 
                'dual_ToR': True, 
                'dual_plane': False,
            })
    
    parameter_keys = [
        'gpu', 'error_rate', 'gpu_per_server', 'gpu_type', 'nv_switch_per_server',
        'nvlink_bw', 'nv_latency', 'latency', 'bandwidth', 'asw_switch_num',
        'nics_per_aswitch', 'psw_switch_num', 'ap_bandwidth','asw_per_psw','ub_intra_bw', 'ub_intra_lat' 
    ]
    for key in parameter_keys:
        parameters[key] = getattr(args, key, None) if getattr(args, key, None) is not None else default_parameters[key]
    # for key, value in parameters.items():
    #     print(f'{key}: {value}')
    # print("==================================")
    return parameters


if __name__ =='__main__':
    main()