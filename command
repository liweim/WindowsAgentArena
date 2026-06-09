conda activate winarena
cd scripts
./run-local.sh --start-client false

conda activate winarena
cd /home/weimingli/projects/WindowsAgentArena/scripts
python run_human.py \
    --example ../src/win-arena-container/client/evaluation_examples_windows/examples/accessibility/hearing/Information-child_visit_preparation.json \
    --container-name winarena-$USER-human1 \
    --browser-port 9016 \
    --rdp-port 3400