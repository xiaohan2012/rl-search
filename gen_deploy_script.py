#each script does the following
#opening a screen and run python extract_contents.py (offset) (limit)
import sys
from glob import glob

def get_id_files(directory):
    paths = glob('%s/xa*' %directory)
    return paths
    
if __name__ == "__main__":

    DEFAULT_SERVERS = ['bolg','boldog','othrod','gorbag','golfimbul','shagrat']
    DEFAULT_CPU_NUMBER_EACH = 5
    SCREEN_PREFIX = 'ce-'
    
    id_file_paths = get_id_files('temp')

    if sys.argv[1] == 'all':
        servers = DEFAULT_SERVERS
    else:
        servers = sys.argv[1].split(',')
    
    cpu_num_per_server = len(id_file_paths) / len(servers) 

    acc = 0
    for i, server in enumerate(servers):
        print 'gen script for %s' %server
        with open('scripts/to-%s-screen.sh' %server, 'w') as f:
            script_content = "#!/bin/bash"
            for j,id_file_path in enumerate(id_file_paths[i * cpu_num_per_server: (i+1) * cpu_num_per_server]):
                screen_name = SCREEN_PREFIX + str(j+1)
                script_content += """
screen -dmS %s bash
screen -S %s -X stuff "cd ~/scinet3
python extract_contents.py %s
"
                """ %(screen_name, 
                      screen_name, 
                      id_file_path)
                
            script_content += "\nscreen -ls"
            print script_content
            f.write(script_content)

    print 'generating kill.sh...'
    with open('scripts/kill.sh', 'w') as f:
        script_content = """#!/bin/bash
array=(%s)

for item in ${array[*]}
do
    screen -S $item -X quit
done

screen -ls
        """ %(' '.join([SCREEN_PREFIX + str(i) for i in xrange(1, cpu_num_per_server + 1)]))
        print script_content
        f.write(script_content)
