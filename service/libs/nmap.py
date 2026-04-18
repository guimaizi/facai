# coding: utf-8

import nmap
def scan_host(target,port,param):
    '''
    扫描主机
    :param target: 目标主机
    :param port: 目标端口
    :param param: 扫描参数
    :return: 扫描结果
    '''
    nm = nmap.PortScanner()
    #-n --version-intensity=1 --min-rate  100 --min-parallelism 100 -open -p
    results = nm.scan(target,
                              arguments=' %s -open -p %s'%(param,port))
    return results