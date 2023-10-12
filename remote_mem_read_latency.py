import matplotlib.pyplot as plt
import numpy as np
import random

GiB = 2**30

def experiment(remote_mem_fixed_time_us, link_rate_gbps, readahead):
    # fixed_time_us: initialization time + propagation delay (us)
    # link_rate_gbps: link speed between client and server (Gbps)

    LOCAL_MEM_READ_TIME_US = 0.05 # TODO: make more granular and incorporate data transfer rate
    LOCAL_MEMORY_SIZE_BYTES = 1*GiB
    DATA_SIZE_BYTES = 2*GiB
    TOTAL_READ_SIZE_BYTES = 2*GiB
    OBJECT_SIZE_BYTES = [64, 128, 256, 512, 1024, 2048, 4096]
    PAGE_SIZE_BYTES = [64, 128, 256, 512, 1024, 2048, 4096]

    read_times_us_data = []
    for page_size_bytes in PAGE_SIZE_BYTES:
        print(f'Page Size: {page_size_bytes} bytes')

        # Transmission delay (us) of reading cache line from remote memory 
        remote_mem_read_time_us = (8*page_size_bytes)/(link_rate_gbps*1e9*1e-6)

        read_times_us = []
        for object_size_bytes in OBJECT_SIZE_BYTES:
            print(f'\tObject Size: {object_size_bytes} bytes')

            # Set up local memory as full-associative cache with the first LOCAL_MEMORY_SIZE_BYTES portion of the array
            local_mem_pages_list = list(range(LOCAL_MEMORY_SIZE_BYTES // page_size_bytes))
            # Maintain set as well for local memory for fast lookup
            local_mem_pages_set = set(local_mem_pages_list)
            # Randomly sample objects with replacement
            random_objects = np.random.choice(range(DATA_SIZE_BYTES // object_size_bytes), size=TOTAL_READ_SIZE_BYTES // object_size_bytes)
            
            read_time_us = 0
            num_pages_read = 0
            for random_object in random_objects:
                random_object_pages = [] # Page(s) spanned by the random object
                if object_size_bytes <= page_size_bytes:
                    # Object is contained within one page
                    random_object_pages.append(random_object // (page_size_bytes // object_size_bytes))
                else:
                    # Object spans multiple pages
                    random_object_start_page = random_object * (object_size_bytes // page_size_bytes)
                    random_object_pages.extend(range(random_object_start_page, random_object_start_page + (object_size_bytes // page_size_bytes)))
                
                num_remote_mem_page_reads = 0
                for random_object_page in random_object_pages:
                    if random_object_page not in local_mem_pages_set:
                        # Random eviction must be done this way since python set.pop() picks arbitrary not random element
                        evict_index = random.randrange(len(local_mem_pages_list))
                        local_mem_pages_set.remove(local_mem_pages_list[evict_index])
                        local_mem_pages_set.add(random_object_page)
                        local_mem_pages_list[evict_index] = random_object_page
                        num_remote_mem_page_reads += 1
                read_time_us += num_remote_mem_page_reads * remote_mem_read_time_us
                if readahead:
                    # Assume all remote memory read requests per object are aggregated
                    read_time_us += (num_remote_mem_page_reads > 0) * remote_mem_fixed_time_us
                else:
                    read_time_us += num_remote_mem_page_reads * remote_mem_fixed_time_us
                num_pages_read += len(random_object_pages)

            # Add local memory access time for each page
            read_time_us += num_pages_read * LOCAL_MEM_READ_TIME_US
            print(f'\tRead Time: {read_time_us} us')
            read_times_us.append(read_time_us)
        read_times_us_data.append(read_times_us)

    plt.figure(figsize=(10, 6))
    for page_size_bytes, read_times_us in zip(PAGE_SIZE_BYTES, read_times_us_data):
        plt.plot(OBJECT_SIZE_BYTES, read_times_us, label=f'{page_size_bytes}')
    plt.xscale('log', base=2)
    plt.xticks(OBJECT_SIZE_BYTES, OBJECT_SIZE_BYTES)
    plt.xlabel('Object Size (bytes)')
    plt.ylabel('Total Read Time (us)')
    plt.legend(title='Page Size (bytes)')
    plt.title(f'Remote Memory Read Times\nremote_mem_fixed_time_us={remote_mem_fixed_time_us}us link_speed={link_rate_gbps}Gbps readahead={readahead}')
    plt.grid(True, which='both', ls='--', c='0.65')
    plt.savefig(f'remote_mem_read_latencies_{remote_mem_fixed_time_us}_{link_rate_gbps}_{readahead}.png', dpi=600, bbox_inches='tight')


if __name__ == '__main__':
    experiment(
        remote_mem_fixed_time_us=4,
        link_rate_gbps=40,
        readahead=False,
    )
    experiment(
        remote_mem_fixed_time_us=4,
        link_rate_gbps=40,
        readahead=True,
    )
    experiment(
        remote_mem_fixed_time_us=0.5,
        link_rate_gbps=180,
        readahead=False,
    )
    experiment(
        remote_mem_fixed_time_us=0.5,
        link_rate_gbps=180,
        readahead=True,
    )
