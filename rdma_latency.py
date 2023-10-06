import matplotlib.pyplot as plt
import numpy as np
import paramiko
import re

from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

# Cloudlab
USERNAME = 'seankim'
RDMA_CLIENT_MACHINE = 'amd214.utah.cloudlab.us'
RDMA_SERVER_MACHINE = 'amd205.utah.cloudlab.us'

def create_ssh_client(host):
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.connect(host, 22, username=USERNAME, allow_agent=False)
    return ssh_client

def exec_command(ssh_client, command):
    _, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode(), stderr.read().decode()

def parse_perf_test_output(output):
    #  #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec]
    #  4096    1000          5.64           5.82         5.70     	       5.70        	0.02   		5.77    		5.82
    pattern = r'\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
    match = re.search(pattern, output)
    return np.array([float(match.group(i)) for i in range(3, 10)]) # Exclude #bytes and #iterations

if __name__ == '__main__':
    # Initiate SSH clients for RDMA client and server machines
    rdma_client_ssh_client = create_ssh_client(RDMA_CLIENT_MACHINE)
    rdma_server_ssh_client = create_ssh_client(RDMA_SERVER_MACHINE)

    # Get IP address of RDMA server machine
    output, error = exec_command(rdma_server_ssh_client, 'hostname -I')
    rdma_server_ip_addr = output.split()[0]

    scan_sizes = [64, 128, 256, 512, 1024, 2048, 4096]
    unit_sizes = [64, 128, 256, 512, 1024, 2048, 4096]
    read_lats = []
    for unit_size in unit_sizes:
        print(f'unit_size: {unit_size}')
        rdma_server_ssh_client.exec_command('ib_read_lat')
        output, error = exec_command(rdma_client_ssh_client, f'ib_read_lat {rdma_server_ip_addr} -F -s {unit_size}') # -F to ignore CPU frequency warning
        read_lats_unit_size = []
        for scan_size in scan_sizes:
            # TODO: not sure if multiplying by the number of units to fetch makes sense, especially for p99
            print(f'scan_size: {scan_size}')
            print(max(scan_size/unit_size, 1))
            read_lats_unit_size.append(parse_perf_test_output(output) * max(scan_size/unit_size, 1))
        read_lats.append(read_lats_unit_size)

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    for unit_size, read_lat in zip(unit_sizes, read_lats):
        ax.plot(scan_sizes, [lat[2] for lat in read_lat], label=f'Unit Size: {unit_size}')

    plt.xscale('log', base=2)
    plt.xticks(scan_sizes, scan_sizes)  
    plt.xlabel('Scan Size (bytes)')
    plt.ylabel('Time (usec)')
    plt.title('RDMA Read Latencies')
    plt.legend()
    plt.grid(True, which='both', ls='--', c='0.65')

    # Inset plot (not working lol)
    # axins = zoomed_inset_axes(ax, zoom=2, loc='upper left') #
    # for i, lats in enumerate(read_lats):
    #     axins.plot(scan_sizes, [lat[2] for lat in lats])
    # axins.set_xlim(64, 512)
    # axins.set_ylim(0, 50)
    # axins.set_xticks([])
    # axins.set_yticks([])
    # mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")

    plt.savefig('rdma_latency_plot.png', dpi=600, bbox_inches='tight')
        
    # Close SSH clients
    rdma_client_ssh_client.close()
    rdma_server_ssh_client.close()
